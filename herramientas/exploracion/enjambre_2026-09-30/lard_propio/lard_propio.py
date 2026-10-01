# -*- coding: utf-8 -*-
"""Camino 3 (enjambre 2026-09-30): LARD (juego 3) con su propio modelo. Ver PREREGISTRO.md.

Uso:
  python lard_propio.py            -> SOLO desarrollo (los datos se cortan en 2026-01-31: la ciega ni se carga)
  python lard_propio.py --ciega    -> la prueba ciega 2026-02-01..2026-09-22, UNA sola vez (se registra)
Escribe dev.json / ciega.json y añade una línea a registro.jsonl.
"""
import csv, io, json, os, sys, time, math
from datetime import date
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE  # noqa: E402

DATOS = os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv")
EXTRA = os.path.join(AQUI, "lard_extra.csv")     # 2026-09-23.. (anexo, opcional)
INI_EVAL_DEV = "2025-09-19"
FIN_DEV = "2026-02-01"          # exclusivo
CIEGA = ("2026-02-01", "2026-09-23")
SEIS = ("2026-04-01", "2026-09-23")
LA_HASTA = "2025-07-01"         # coeficientes de Lotto Activo ajustados con LA < esta fecha
K = 38; PAGO = 30
ESC = np.array([2, 2, 2, 1, 1], float)


def cargar_lard(hasta, extra=False):
    filas = []
    with io.open(DATOS, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["juego"] == "3" and r["fecha"] < hasta and r["codigo"] in LE.IDX:
                filas.append((r["fecha"], int(r["hora"][:2]), LE.IDX[r["codigo"]]))
    if extra and os.path.exists(EXTRA):
        vistos = {(f, h) for f, h, _ in filas}
        with io.open(EXTRA, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                k = (r["fecha"], int(r["hora"][:2]))
                if k not in vistos and r["codigo"] in LE.IDX:
                    filas.append((k[0], k[1], LE.IDX[r["codigo"]]))
    filas.sort()
    d0 = date.fromisoformat(filas[0][0])
    fe = [f for f, _, _ in filas]
    return LE.Datos(np.array([c for _, _, c in filas]), np.array([h - 8 for _, h, _ in filas]),
                    np.array([date.fromisoformat(f).weekday() for f in fe]),
                    np.array([(date.fromisoformat(f) - d0).days for f in fe]), fe)


def cargar_mod(nombre):
    return LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", nombre + ".py"))


def pred_transfer(lard):
    """secuencia_v3 con coeficientes de Lotto Activo (historial.txt < 2025-07-01), aplicados a LARD."""
    sv = cargar_mod("secuencia_v3")
    import importlib
    sf = sys.modules.get("secuencia_final")
    if sf is None:
        spec = importlib.util.spec_from_file_location("sf_", os.path.join(RAIZ, "herramientas", "modelos", "secuencia_final.py"))
        sf = importlib.util.module_from_spec(spec); spec.loader.exec_module(sf)
    la = LE.cargar()
    T = sum(1 for f in la.fecha if f < LA_HASTA)
    la = la.prefijo(T)
    est, Pen, _ = sf.construir(la, sv.cfg)
    Pen = Pen + sv.lam * np.eye(Pen.shape[0])
    a = sv.inicio; edad = T - 1 - np.arange(a, T)
    beta = sf.ajustar(est, slice(a, T), la.seq[a:T], np.exp(-edad / sv.tau), Pen)
    del est
    est2, Pen2, _ = sf.construir(lard, sv.cfg)
    assert Pen2.shape == Pen.shape
    z = sf.logits(est2, beta, slice(0, len(lard)))
    z -= z.max(1, keepdims=True); p = np.exp(z)
    return p / p.sum(1, keepdims=True), T


def medir(P, y, dias, horas, nboot=2000, semilla=7):
    P = LE.normalizar(P); n = len(y)
    orden = LE.rankings(P)
    pos = np.argmax(orden == y[:, None], axis=1)
    L = np.log2(P * K)
    lb = L[np.arange(n), y]                                   # bits por sorteo
    L2 = np.log(P * K); s = L2[np.arange(n), y].sum(); m0 = L2.mean(1).sum(); v0 = L2.var(1).sum()
    zlog = (s - m0) / math.sqrt(v0)
    top3 = (pos < 3).astype(float)
    fichas = np.where(pos < 5, ESC[np.minimum(pos, 4)], 0.0)
    r5 = PAGO * fichas / ESC.sum() - 1
    r15 = PAGO * (pos < 15) / 15.0 - 1
    # bootstrap por jornada
    ud, inv = np.unique(dias, return_inverse=True)
    nd = len(ud)
    def sums(v): return np.bincount(inv, weights=v, minlength=nd)
    cnt = np.bincount(inv, minlength=nd).astype(float)
    S = {k: sums(v) for k, v in dict(mb=lb, t3=top3, r5=r5, r15=r15).items()}
    rng = np.random.default_rng(semilla)
    B = {k: [] for k in S}
    for _ in range(nboot):
        ix = rng.integers(0, nd, nd); c = cnt[ix].sum()
        for k in S:
            B[k].append(S[k][ix].sum() / c)
    ic = {k: [float(np.percentile(B[k], 2.5)), float(np.percentile(B[k], 97.5))] for k in B}
    out = {
        "n": int(n), "dias": int(nd),
        "mbits": 1000 * float(lb.mean()), "mbits_ic95": [1000 * x for x in ic["mb"]], "z_logver": float(zlog),
        "top1": float(np.mean(pos < 1)), "top3": float(top3.mean()), "top3_ic95": ic["t3"], "top3_azar": 3 / K,
        "top5": float(np.mean(pos < 5)), "top15": float(np.mean(pos < 15)), "top15_azar": 15 / K,
        "ret_top5_esc": float(r5.mean()), "ret_top5_esc_ic95": ic["r5"],
        "pago_equilibrio_top5_esc": float(ESC.sum() / fichas.mean()) if fichas.mean() > 0 else None,
        "ret_top15": float(r15.mean()), "ret_top15_ic95": ic["r15"],
        "pago_equilibrio_top15": float(15 / np.mean(pos < 15)),
        "rango_medio": float(pos.mean()),
        "mbits_por_hora": {str(h + 8): round(1000 * float(lb[horas == h].mean()), 1) for h in range(14) if np.any(horas == h)},
    }
    return out


def predicciones(lard):
    n = len(lard)
    preds = {"U": np.full((n, K), 1.0 / K)}
    w = 400
    for clave, nom in (("H", "hazard_actual"), ("B", "secuencia_v3")):
        m = cargar_mod(nom)
        p = np.full((n, K), 1.0 / K)
        p[w:] = LE.normalizar(m.predecir(lard, w))
        preds[clave] = p
    preds["C"], T_la = pred_transfer(lard)
    preds["M"] = 0.5 * preds["B"] + 0.5 * preds["C"]
    return preds, T_la


def fuga_ok(lard):
    m = cargar_mod("secuencia_v3")
    ok, c, d = LE.prueba_fuga(m, lard, 400, cortes=2)
    return ok, c, d


def main():
    ciega = "--ciega" in sys.argv
    t0 = time.time()
    if ciega:
        reg = os.path.join(AQUI, "registro.jsonl")
        if os.path.exists(reg) and any('"fase": "ciega"' in ln for ln in io.open(reg, encoding="utf-8")):
            sys.exit("La ciega ya se miró (registro.jsonl). No se repite.")
        dev = json.load(io.open(os.path.join(AQUI, "dev.json"), encoding="utf-8"))
        ganador = dev["ganador"]
        lard = cargar_lard(CIEGA[1])
    else:
        lard = cargar_lard(FIN_DEV)
    preds, T_la = predicciones(lard)
    fe = np.array(lard.fecha)
    res = {"fase": "ciega" if ciega else "dev", "n_total": len(lard), "LA_filas_usadas_para_C": T_la}
    if not ciega:
        ok, c, d = fuga_ok(lard)
        res["fuga_secuencia_v3"] = "sin fuga" if ok else f"FUGA en {c} ({d})"
        sel = (fe >= INI_EVAL_DEV) & (fe < FIN_DEV)
        res["ventana"] = [INI_EVAL_DEV, "2026-01-31"]
        res["modelos"] = {k: medir(P[sel], lard.seq[sel], lard.dia[sel], lard.hora[sel]) for k, P in preds.items()}
        cand = {k: v["mbits"] for k, v in res["modelos"].items() if k != "U"}
        res["ganador"] = max(cand, key=cand.get)
        # mitades de desarrollo para el ganador y B
        idx = np.flatnonzero(sel); h1, h2 = idx[: len(idx) // 2], idx[len(idx) // 2:]
        res["mitades_mbits"] = {k: [medir(preds[k][h], lard.seq[h], lard.dia[h], lard.hora[h], nboot=200)["mbits"] for h in (h1, h2)]
                                for k in preds if k != "U"}
        out = os.path.join(AQUI, "dev.json")
    else:
        res["ganador_de_desarrollo"] = ganador
        res["ventanas"] = {}
        for nom, (a, b) in (("ciega_2026-02-01_09-22", CIEGA), ("seis_meses_2026-04-01_09-22", SEIS)):
            sel = (fe >= a) & (fe < b)
            res["ventanas"][nom] = {k: medir(P[sel], lard.seq[sel], lard.dia[sel], lard.hora[sel]) for k, P in preds.items()}
        g = res["ventanas"]["ciega_2026-02-01_09-22"][ganador]
        pasa = g["mbits_ic95"][0] > 0 and g["z_logver"] >= 3
        res["veredicto"] = "PASA" if pasa else "NO PASA"
        out = os.path.join(AQUI, "ciega.json")
    res["segundos"] = round(time.time() - t0, 1)
    json.dump(res, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with io.open(os.path.join(AQUI, "registro.jsonl"), "a", encoding="utf-8") as fh:
        resumen = {"cuando": time.strftime("%Y-%m-%d %H:%M:%S"), "fase": res["fase"]}
        if ciega:
            resumen.update(ganador=ganador, veredicto=res["veredicto"],
                           mbits={k: round(v["mbits"], 1) for k, v in res["ventanas"]["ciega_2026-02-01_09-22"].items()})
        else:
            resumen.update(ganador=res["ganador"], mbits={k: round(v["mbits"], 1) for k, v in res["modelos"].items()})
        fh.write(json.dumps(resumen, ensure_ascii=False) + "\n")
    print(json.dumps(res, ensure_ascii=False, indent=1)[:6000])


if __name__ == "__main__":
    main()
