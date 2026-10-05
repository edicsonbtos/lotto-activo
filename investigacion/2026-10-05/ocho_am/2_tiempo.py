# -*- coding: utf-8 -*-
"""Descriptivo por trimestre a las 8:00: ¿cuándo cambió la regla 'ayer como hoy'? Uso: python 2_tiempo.py HIST WF.npz"""
import sys, runpy
sys.argv = sys.argv[:3]
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "1_analisis.py"))
ocho, PB, S, F, ayer_set, EX, K = (g[k] for k in ("ocho", "PB", "S", "F", "ayer_set", "EX", "K"))
import numpy as np
def trim(f): return f[:4] + "-T" + str((int(f[5:7]) - 1) // 3 + 1)
print(f"{'trimestre':10} {'n':>4} | ayer crudo O/E | ayer motor O/E | anteayer crudo | ventana fecha O/E(C)")
for q in sorted({trim(F[t]) for t in ocho}):
    x = [t for t in ocho if trim(F[t]) == q]
    r = {"ac": [0, 0.], "am": [0, 0.], "an": [0, 0.], "v": [0, 0.]}
    for t in x:
        w = S[t]; y = sorted(set(ayer_set(t) or [])); y2 = sorted(set(ayer_set(t, 2) or []))
        if y:
            r["ac"][0] += w in y; r["ac"][1] += len(y) / K
            r["am"][0] += w in y; r["am"][1] += float(PB[t][y].sum())
        if y2:
            r["an"][0] += w in y2; r["an"][1] += len(y2) / K
        c = np.array(EX.aplicar(PB[t], F[t], 0)); d = int(F[t][8:10])
        vv = [EX.IDX[str(n)] for n in (d - 1, d, d + 1) if 1 <= n <= 36]
        r["v"][0] += w in vv; r["v"][1] += float(c[vv].sum())
    s = "  ".join(f"{k}: {o:3d}/{e:5.1f}={o / e:4.2f}" for k, (o, e) in r.items())
    print(f"{q:10} {len(x):4d} | {s}")
