# -*- coding: utf-8 -*-
"""Cuánto mueve H1 (×0,807 a los 2 vecinos de rueda del anterior) en Top-N y plata: desarrollo (in-sample) y vivo."""
import sys, os, json, numpy as np
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lotto_eval as LE
from rasgos import mascaras
F = 0.807
def plan(t):
    f = [0] * 39
    for a, b, n in t:
        for p in range(a, b + 1): f[p] = n
    return np.array(f)
PL = {"Top-5 esc": plan([(1, 3, 2), (4, 5, 1)]), "Top-15 pond": plan([(1, 3, 3), (4, 5, 2), (6, 15, 1)])}
def evalua(casos, nombre):
    res = {}
    for lbl, corr in (("motor", False), ("motor+H1", True)):
        t3 = t5 = t15 = 0; mb = []; neto = {k: 0.0 for k in PL}; ap = {k: 0 for k in PL}
        for p, w, mk in casos:
            q = p.copy()
            if corr and mk is not None: q[mk] *= F; q /= q.sum()
            rank = int((q > q[w]).sum()) + 1
            t3 += rank <= 3; t5 += rank <= 5; t15 += rank <= 15; mb.append(1000 * np.log2(q[w] * 38))
            for k, f in PL.items(): neto[k] += 30 * f[rank] - f.sum(); ap[k] += f.sum()
        n = len(casos)
        print(f"  {nombre:9s} {lbl:9s} n={n}  Top-3 {t3/n*100:5.2f}%  Top-5 {t5/n*100:5.2f}%  Top-15 {t15/n*100:5.2f}%  "
              f"mbits {np.mean(mb):+6.1f}  " + "  ".join(f"{k} {neto[k]/ap[k]*100:+5.1f}%" for k in PL))
D = LE.cargar(os.path.join(RAIZ, "verificacion/hilo9/datos/historial.txt"))
c = np.load(os.path.join(RAIZ, "verificacion/hilo9/datos/calor_cache.npz")); P = c["P"] / c["P"].sum(1, keepdims=True); y = c["y"]
casos = []
for i in range(len(y)):
    t = 2000 + i
    prev = int(D.seq[t - 1]) if D.dia[t - 1] == D.dia[t] else None
    casos.append((P[i], int(y[i]), None if prev is None else mascaras(prev, 1, 0)["H1_rueda"]))
print("Desarrollo (in-sample: el factor se estimó aquí)"); evalua(casos, "ensamble")
import csv
from rasgos import IDX
gan = {(f, int(h)): int(s) for f, h, s in zip(D.fecha, D.hora, D.seq)}
for r in csv.DictReader(open(os.path.join(RAIZ, "datos_multiloteria/oficial_multi.csv"))):
    if r["juego"] == "1": gan.setdefault((r["fecha"], int(r["hora"][:2]) - 8), IDX[r["codigo"]])
AQ = os.path.dirname(os.path.abspath(__file__))
mesas = {m: [r for r in json.load(open(os.path.join(AQ, f"vivo/mesa_{m}_2026-10-22.json"))) if r and r["winner"] is not None]
         for m in ("ensamble", "principal")}
for rows in mesas.values():
    for r in rows: gan.setdefault((r["fecha"], r["hora"]), r["winner"])
print("Vivo (ciega: factor fijado en desarrollo)")
for m, rows in mesas.items():
    casos = []
    for r in rows:
        if r["p"] is None or None in r["p"]: continue
        p = np.array(r["p"], float); p /= p.sum()
        prev = gan.get((r["fecha"], r["hora"] - 1)) if r["hora"] > 0 else None
        casos.append((p, r["winner"], None if prev is None else mascaras(prev, 1, 0)["H1_rueda"]))
    evalua(casos, m)
