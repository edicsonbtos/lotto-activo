# -*- coding: utf-8 -*-
"""PRUEBA ÚNICA en el tramo sellado (Lotto Activo < 2023-09-04). Una sola corrida; queda en registro_sellado.jsonl.

Pasos: 1) ensamble_v2 walk-forward sobre sellado_la.txt desde la fila 2000 (calentamiento = 2000 primeros);
2) cada candidato congelado (candidatos.json) en un proceso aparte, con el mismo P del ensamble;
3) Δmbits candidato − ensamble con IC bootstrap por jornadas corregido por Bonferroni (1 − 0,05/k).
Secundarias: Top-3, Top-5, Top-15 y retorno del Top-5 escalonado.

Uso: python motor_nuevo/sellado/prueba.py            (no reajusta nada; los pesos vienen del commit)
"""
import json, os, subprocess, sys, time, hashlib
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
MN = os.path.dirname(AQUI); WT = os.path.dirname(MN)
sys.path.insert(0, os.path.join(WT, "herramientas")); sys.path.insert(0, MN)
import lotto_eval as LE  # noqa: E402
import arnes as A  # noqa: E402

ENSAYO = os.environ.get("SELLADO_ENSAYO")          # ruta a datos de ensayo (dry-run): no registra nada
DATOS = ENSAYO or os.path.join(AQUI, "sellado_la.txt")
SAL = os.environ.get("SELLADO_SALIDA", AQUI)
CAND = json.load(open(os.path.join(AQUI, "candidatos.json"), encoding="utf-8"))
DESDE = 2000
REG = os.path.join(AQUI, "registro_sellado.jsonl")


def ensamble(D, huella):
    """P del ensamble; la caché solo se reutiliza si es de estos mismos datos (huella sha256)."""
    ruta = os.path.join(SAL, "P_ens_sellado.npy"); rh = ruta + ".sha256"
    if os.path.exists(ruta) and os.path.exists(rh) and open(rh).read().strip() == huella:
        return np.load(ruta)
    m = LE.cargar_modelo(os.path.join(WT, "herramientas", "modelos", "ensamble_v2.py"))
    P = LE.normalizar(m.predecir(D, DESDE)); np.save(ruta, P)
    open(rh, "w").write(huella)
    return P


def integridad(ruta):
    """Sin mirar animales: una sola fila por (fecha, hora) y sorteos por día."""
    import collections
    claves = collections.Counter(); por_dia = collections.Counter()
    for ln in open(ruta, encoding="utf-8"):
        p = ln.split()
        if len(p) == 3:
            claves[(p[0], p[1])] += 1; por_dia[p[0]] += 1
    dup = [k for k, v in claves.items() if v > 1]
    print("integridad: filas", sum(claves.values()), "· (fecha,hora) duplicadas", len(dup),
          "· sorteos/día", collections.Counter(por_dia.values()).most_common(6))
    if dup:
        sys.exit(f"ABORTA: {len(dup)} (fecha,hora) con más de un animal, p. ej. {dup[:3]}")


HIJO = r'''
import sys, os, importlib.util, numpy as np
sys.path.insert(0, {wt!r}); sys.path.insert(0, os.path.join({wt!r}, "herramientas"))
import lotto_eval as LE
carpeta = {carpeta!r}; sys.path.insert(0, carpeta); kw = {kw!r}
spec = importlib.util.spec_from_file_location("modelo_cand", os.path.join(carpeta, "modelo.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
D = LE.cargar({datos!r}); P_ens = np.load({pens!r})
m = mod.Modelo(**kw)
if hasattr(m, "corregir"):
    P = m.corregir(D, {desde}, P_ens)
else:
    m.P_ens = P_ens; P = m.predecir(D, {desde})
np.save({salida!r}, LE.normalizar(P))
'''


def main():
    integridad(DATOS)
    D = LE.cargar(DATOS)
    n = len(D); k = len(CAND)
    h = hashlib.sha256(open(DATOS, "rb").read()).hexdigest()
    print(f"sellado: {n} sorteos, {len(set(D.fecha))} días, {D.fecha[0]}..{D.fecha[-1]}, sha256 {h[:16]}")
    t0 = time.time(); Pens = ensamble(D, h); print(f"ensamble listo [{time.time()-t0:.0f} s]", flush=True)
    y = np.asarray(D.seq[DESDE:]); dia = np.asarray(D.dia[DESDE:])
    alfa = 0.05 / k
    out = {"n": int(len(y)), "sha256": h, "k": k, "resultados": {}}
    mb_e = A.mbits_fila(Pens, y); pos_e = A.puestos(Pens, y)
    out["ensamble"] = {"mbits": float(mb_e.mean()), "top3": float((pos_e <= 3).mean()),
                       "top5": float((pos_e <= 5).mean()), "top15": float((pos_e <= 15).mean()),
                       "ret_t5": float(A.retorno_t5(pos_e).mean())}
    print("ensamble:", out["ensamble"])
    for nombre, (carpeta, kw) in CAND.items():
        sal = os.path.join(SAL, f"P_{nombre}.npy")
        codigo = HIJO.format(wt=WT, carpeta=os.path.join(MN, carpeta), kw=kw, datos=DATOS,
                             pens=os.path.join(SAL, "P_ens_sellado.npy"), desde=DESDE, salida=sal)
        subprocess.run([sys.executable, "-c", codigo], check=True)
        P = np.load(sal)
        d = A.mbits_fila(P, y) - mb_e
        _, inv = np.unique(dia, return_inverse=True)
        sums = np.bincount(inv, weights=d); cnt = np.bincount(inv)
        rng = np.random.default_rng(7); B = rng.integers(0, len(sums), size=(4000, len(sums)))
        m = sums[B].sum(1) / cnt[B].sum(1)
        lo, hi = np.percentile(m, [100 * alfa / 2, 100 * (1 - alfa / 2)])
        pos = A.puestos(P, y)
        r = {"delta_mbits": float(d.mean()), "ic_bonferroni": [float(lo), float(hi)], "pasa": bool(lo > 0),
             "top3": float((pos <= 3).mean()), "top5": float((pos <= 5).mean()), "top15": float((pos <= 15).mean()),
             "delta_ret_t5": A.ic_bloques(A.retorno_t5(pos) - A.retorno_t5(pos_e), dia)}
        out["resultados"][nombre] = r
        print(nombre, json.dumps(r, ensure_ascii=False), flush=True)
    if ENSAYO:
        print("ENSAYO: no se registra nada")
        return
    with open(REG, "a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
    json.dump(out, open(os.path.join(AQUI, "resultado_sellado.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    if os.path.exists(REG) and not ENSAYO:
        sys.exit("El tramo sellado ya se usó (registro_sellado.jsonl existe). No se repite.")
    main()
