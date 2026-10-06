# -*- coding: utf-8 -*-
"""M4: tabla de variantes, mezcla log-lineal con PROD (w elegido en ELECCION) e importancias.
python elegir.py V1 V4"""
import sys
import numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
import arnes as A

L = np.log(np.clip(A.PROD, 1e-9, None))


def mezcla(P, w):
    z = (1 - w) * L + w * np.log(np.clip(P, 1e-9, None)); z -= z.max(1, keepdims=True); e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def dmb(P, tr):
    i = np.where(A.TRAMOS[tr])[0]; y = A.Y[i]
    return 1000 * np.log2(P[i, y] / A.PROD[i, y]).mean()


res = {}
for v in sys.argv[1:]:
    z = np.load(A.SP + f"/m4_{v}.npz", allow_pickle=True); P = z["P"]
    for w in (0.25, 0.5, 0.75, 1.0, 1.25):
        Q = mezcla(P, w); res[(v, w)] = (dmb(Q, "AJUSTE"), dmb(Q, "ELECCION"))
        print(f"{v} w={w:4.2f}  AJUSTE {res[(v, w)][0]:+6.2f}  ELECCION {res[(v, w)][1]:+6.2f}")
    # importancia (último modelo, octubre 2026)
    g = z["imp"]; nm = z["imp_nm"]; o = np.argsort(-g)
    print(f"{v} importancia (ganancia, % del total):", ", ".join(f"{nm[k]} {100 * g[k] / g.sum():.1f}" for k in o[:20]))
ok = {k: r for k, r in res.items() if r[0] > 0}
best = max(ok, key=lambda k: ok[k][1])
print("ELEGIDA:", best, res[best])
