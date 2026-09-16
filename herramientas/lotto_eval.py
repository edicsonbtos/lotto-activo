#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Banco de pruebas estadístico para Lotto Activo.

Protocolo (igual para todos los modelos):
  * Walk-forward: la fila t de predicciones solo puede usar seq[:t].
  * Prueba de fuga: se barajan los sorteos futuros y se exige que las
    predicciones pasadas no cambien.
  * Partición fija: calentamiento [0, W), desarrollo [W, CORTE), prueba [CORTE, n).
    La prueba solo se evalúa con --final y cada evaluación queda registrada en
    registro_final.jsonl (así se ve cuántas veces se miró la prueba).
  * Métricas bajo la hipótesis nula EXACTA (sorteos iid uniformes e
    independientes del pasado): Top-k tiene probabilidad k/38 por sorteo
    sea cual sea el modelo, y la log-verosimilitud tiene media/varianza
    calculables fila a fila. Así los p-valores no dependen de supuestos.

Interfaz de un modelo (archivo en herramientas/modelos/<nombre>.py):

    class Modelo:
        nombre = "..."
        def predecir(self, datos, desde):
            # devuelve np.ndarray (n - desde, 38): fila j = distribución
            # de probabilidad para el sorteo desde+j usando SOLO datos[:desde+j]
"""
import argparse, importlib.util, json, math, os, sys, time
from dataclasses import dataclass
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(RAIZ, "historial.txt")
AQUI = os.path.dirname(os.path.abspath(__file__))
REGISTRO_FINAL = os.path.join(AQUI, "registro_final.jsonl")

POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}
K = 38
PAGO = 30
W = 2000            # calentamiento mínimo
FRAC_DEV = 0.75     # desarrollo hasta el 75 % del histórico


@dataclass
class Datos:
    seq: np.ndarray      # índices 0..37
    hora: np.ndarray     # 0..11
    dow: np.ndarray      # 0=lunes
    dia: np.ndarray      # nº de día consecutivo (para agrupar por fecha)
    fecha: list

    def __len__(self):
        return len(self.seq)

    def prefijo(self, t):
        return Datos(self.seq[:t], self.hora[:t], self.dow[:t], self.dia[:t], self.fecha[:t])


def cargar(ruta=HIST):
    from datetime import date
    filas = []
    with open(ruta, encoding="utf-8") as f:
        for ln in f:
            p = ln.split()
            if len(p) == 3 and p[2] in IDX:
                filas.append((p[0], int(p[1]), IDX[p[2]]))
    filas.sort(key=lambda r: (r[0], r[1]))
    d0 = date.fromisoformat(filas[0][0])
    fechas = [r[0] for r in filas]
    dias = np.array([(date.fromisoformat(r[0]) - d0).days for r in filas])
    dows = np.array([date.fromisoformat(r[0]).weekday() for r in filas])
    return Datos(np.array([r[2] for r in filas]), np.array([r[1] for r in filas]), dows, dias, fechas)


CORTE_FIJO = 9357  # = int(0.75 * 12476), congelado al terminar la exploración del enjambre


def particion(n):
    # Corte fijo: si dependiera de n, las filas de prueba migrarían a desarrollo
    # a medida que se registran sorteos nuevos.
    return W, min(CORTE_FIJO, n)


def cargar_modelo(ruta, **kw):
    spec = importlib.util.spec_from_file_location(os.path.basename(ruta)[:-3], ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Modelo(**kw)


# --------------------------------------------------------------------------- #
#  Validación
# --------------------------------------------------------------------------- #
def normalizar(P):
    P = np.asarray(P, dtype=float)
    if not np.all(np.isfinite(P)):
        raise ValueError("el modelo devolvió NaN/inf")
    P = np.clip(P, 1e-6, None)
    return P / P.sum(axis=1, keepdims=True)


def prueba_fuga(modelo, datos, desde, cortes=3, semilla=0):
    """Baraja el futuro a partir de c y exige que las filas t <= c no cambien."""
    rng = np.random.default_rng(semilla)
    n = len(datos)
    base = normalizar(modelo.predecir(datos, desde))
    for c in rng.integers(desde + 50, n - 50, size=cortes):
        s2 = datos.seq.copy()
        s2[c:] = rng.integers(0, K, size=n - c)
        d2 = Datos(s2, datos.hora, datos.dow, datos.dia, datos.fecha)
        alt = normalizar(modelo.predecir(d2, desde))
        filas = c - desde + 1          # filas desde..c inclusive
        diff = np.max(np.abs(base[:filas] - alt[:filas]))
        if diff > 1e-9:
            return False, int(c), float(diff)
    return True, None, 0.0


# --------------------------------------------------------------------------- #
#  Métricas
# --------------------------------------------------------------------------- #
def wilson(k, n, z=1.959964):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def binom_sf(k, n, p):
    """P(X >= k), X~Bin(n,p)."""
    from scipy.stats import binom
    return float(binom.sf(k - 1, n, p))


def rankings(P, semilla=12345):
    """Orden descendente con desempate aleatorio (así Top-k vale k/38 bajo H0)."""
    rng = np.random.default_rng(semilla)
    jit = rng.random(P.shape) * 1e-12
    return np.argsort(-(P + jit), axis=1)


def metricas(P, y, pago=PAGO):
    P = normalizar(P)
    n = len(y)
    orden = rankings(P)
    pos = np.argmax(orden == y[:, None], axis=1)   # rango del resultado (0 = primero)
    out = {"n": int(n)}
    for k in (1, 3, 5):
        hits = int(np.sum(pos < k))
        p0 = k / K
        lo, hi = wilson(hits, n)
        z = (hits - n * p0) / math.sqrt(n * p0 * (1 - p0))
        out[f"top{k}"] = {
            "aciertos": hits, "tasa": hits / n, "azar": p0,
            "ic95": [lo, hi], "z": z, "p_valor": binom_sf(hits, n, p0),
            "roi_por_apuesta": (pago * hits - k * n) / (k * n),
        }
    # log-verosimilitud frente al uniforme con nula exacta fila a fila
    L = np.log(P * K)                       # (n, 38)
    obs = L[np.arange(n), y]
    media0 = L.mean(axis=1)
    var0 = L.var(axis=1)
    s = float(obs.sum()); m0 = float(media0.sum()); v0 = float(var0.sum())
    out["logver"] = {
        "bits_por_sorteo": s / n / math.log(2),
        "z": (s - m0) / math.sqrt(v0) if v0 > 0 else 0.0,
        "p_valor": float(0.5 * math.erfc(((s - m0) / math.sqrt(v0)) / math.sqrt(2))) if v0 > 0 else 1.0,
    }
    out["rango_medio"] = float(pos.mean())   # 18.5 bajo azar
    # Estabilidad: Top-3 por cuartos del periodo
    trozos = np.array_split(np.arange(n), 4)
    out["top3_por_cuarto"] = [float(np.mean(pos[t] < 3)) for t in trozos]
    return out


def evaluar(modelo, datos, final=False, fuga=True):
    n = len(datos)
    w, corte = particion(n)
    t0 = time.time()
    if fuga:
        ok, c, diff = prueba_fuga(modelo, datos, w)
        if not ok:
            return {"modelo": modelo.nombre, "error": f"FUGA DE DATOS: filas <= {c} cambian (dif {diff:.3g})"}
    P = normalizar(modelo.predecir(datos, w))
    if P.shape != (n - w, K):
        return {"modelo": modelo.nombre, "error": f"forma {P.shape}, esperaba {(n - w, K)}"}
    y = datos.seq[w:]
    res = {"modelo": modelo.nombre, "segundos": round(time.time() - t0, 1),
           "fuga": "sin fuga" if fuga else "no comprobada"}
    res["desarrollo"] = metricas(P[: corte - w], y[: corte - w])
    if final:
        res["prueba"] = metricas(P[corte - w:], y[corte - w:])
        with open(REGISTRO_FINAL, "a", encoding="utf-8") as f:
            f.write(json.dumps({"cuando": time.strftime("%Y-%m-%d %H:%M:%S"), "modelo": modelo.nombre,
                                "top1": res["prueba"]["top1"]["tasa"], "top3": res["prueba"]["top3"]["tasa"],
                                "bits": res["prueba"]["logver"]["bits_por_sorteo"]}) + "\n")
    return res


def resumen(res):
    if "error" in res:
        return f"{res['modelo']}: ERROR {res['error']}"
    lineas = [f"== {res['modelo']}  ({res['fuga']}, {res['segundos']} s)"]
    for parte in ("desarrollo", "prueba"):
        if parte not in res:
            continue
        m = res[parte]
        t1, t3 = m["top1"], m["top3"]
        lineas.append(
            f"  {parte:<10} n={m['n']:>5}  Top1 {t1['tasa']*100:5.2f}% [{t1['ic95'][0]*100:.2f}-{t1['ic95'][1]*100:.2f}] "
            f"p={t1['p_valor']:.3f} ROI {t1['roi_por_apuesta']*100:+.1f}%  |  Top3 {t3['tasa']*100:5.2f}% "
            f"(azar 7.89) p={t3['p_valor']:.3f}  |  {m['logver']['bits_por_sorteo']*1000:+.2f} mbits "
            f"z={m['logver']['z']:+.2f}  |  cuartos Top3 {[round(x*100,1) for x in m['top3_por_cuarto']]}")
    return "\n".join(lineas)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modelos", nargs="+", help="rutas a archivos de modelo")
    ap.add_argument("--hist", default=HIST)
    ap.add_argument("--final", action="store_true", help="evalúa también el tramo de prueba (queda registrado)")
    ap.add_argument("--sin-fuga", action="store_true", help="omite la prueba de fuga (más rápido)")
    ap.add_argument("--json", help="guarda resultados completos en este archivo")
    a = ap.parse_args()
    datos = cargar(a.hist)
    w, corte = particion(len(datos))
    print(f"historial: {len(datos)} sorteos | calentamiento <{w} | desarrollo {w}-{corte} | prueba {corte}-{len(datos)}")
    todos = []
    for ruta in a.modelos:
        res = evaluar(cargar_modelo(ruta), datos, final=a.final, fuga=not a.sin_fuga)
        print(resumen(res)); sys.stdout.flush()
        todos.append(res)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(todos, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
