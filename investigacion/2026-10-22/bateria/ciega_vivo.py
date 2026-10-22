# -*- coding: utf-8 -*-
"""Ciega 1 de H1 (PREREGISTRO.md, adenda): pronósticos congelados en vivo."""
import sys, os, json, csv, numpy as np
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lotto_eval as LE
from rasgos import mascaras, IDX
AQ = os.path.dirname(os.path.abspath(__file__))
F = 0.807
gan = {}
D = LE.cargar(os.path.join(RAIZ, "verificacion/hilo9/datos/historial.txt"))
for f, h, s in zip(D.fecha, D.hora, D.seq): gan[(f, int(h))] = int(s)
chk = [0, 0]
for r in csv.DictReader(open(os.path.join(RAIZ, "datos_multiloteria/oficial_multi.csv"))):
    if r["juego"] != "1": continue
    k = (r["fecha"], int(r["hora"][:2]) - 8); v = IDX[r["codigo"]]
    if k in gan: chk[0] += 1; chk[1] += gan[k] == v
    else: gan[k] = v
print("oficial juego 1 vs historial: coinciden", chk[1], "de", chk[0])
mesas = {m: [r for r in json.load(open(os.path.join(AQ, f"vivo/mesa_{m}_2026-10-22.json"))) if r and r["winner"] is not None]
         for m in ("ensamble", "principal")}
for rows in mesas.values():
    for r in rows: gan.setdefault((r["fecha"], r["hora"]), r["winner"])
rng = np.random.default_rng(20261022)
for m, rows in mesas.items():
    reg = []
    for r in rows:
        if r["hora"] == 0 or r["p"] is None or None in r["p"]: continue
        prev = gan.get((r["fecha"], r["hora"] - 1))
        if prev is None: continue
        p = np.array(r["p"], float); p /= p.sum()
        mk = mascaras(prev, int(r["fecha"][5:7]), 0)["H1_rueda"]
        q = p.copy(); q[mk] *= F; q /= q.sum()
        w = r["winner"]
        reg.append((r["fecha"], float(mk[w]), p[mk].sum(), 1000 * np.log2(q[w] / p[w])))
    o = sum(x[1] for x in reg); e = sum(x[2] for x in reg); dm = np.array([x[3] for x in reg])
    por = {}
    for x in reg: por.setdefault(x[0], []).append(x[3])
    dias = list(por.values()); B = []
    for _ in range(5000):
        s = [dias[i] for i in rng.integers(0, len(dias), len(dias))]
        B.append(np.concatenate(s).mean())
    B = np.array(B); p1 = (B <= 0).mean()
    print(f"{m}: n={len(reg)}  vecinos de rueda: obs {o:.0f}  esp {e:.1f}  O/E {o/e:.2f}  "
          f"Δmbits {dm.mean():+.2f}  IC90 [{np.percentile(B,5):+.2f}; {np.percentile(B,95):+.2f}]  p(Δ≤0) {p1:.3f}")
