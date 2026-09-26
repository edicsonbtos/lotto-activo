# -*- coding: utf-8 -*-
"""Diagnóstico (informativo, no predictor): ¿añade algo la frontera FIJA del mazo sobre la recencia pura?
Modelo solo (sin ensamble): G5 (días desde la última aparición) + [salió en el mazo actual antes de hoy]
para cada (D, fase). Si hubiera mazo con fronteras fijas, la fase verdadera daría una ganancia clara
sobre G5 y las demás fases no. Cross-fit en los mismos 5 bloques contiguos de jornadas. Filas [2000, 9357)."""
import math, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa: E402
import baraja as B  # noqa: E402

D = A.datos().prefijo(A.CORTE)
_, y = A.base()
n = len(y); rows = np.arange(n)
dia = D.dia[A.W:]; ud = np.unique(dia); cs = np.array_split(ud, 5)
bloque = np.zeros(n, int)
for b, ds in enumerate(cs):
    bloque[np.isin(dia, ds)] = b
st = B.estado(D)
X5 = B.construir(D, A.W, ("G5",), st)


def cf(X):
    LP = np.zeros((n, 38))
    for b in range(5):
        tr, te = bloque != b, bloque == b
        th, _ = B.ajustar(X[tr], y[tr])
        LP[te] = B.logp(X[te], th)
    v = (LP[rows, y] + math.log(38)) / math.log(2) * 1000
    return v


b5 = cf(X5)
print(f"G5 solo: {b5.mean():+.2f} mbits")
for Dd in (2, 3, 4, 5, 7):
    out = []
    for p in range(Dd):
        X2 = B.construir(D, A.W, ("G2", Dd, p), st)[:, :, 1:]
        m, lo, hi = A.ic_bloques(cf(np.concatenate([X5, X2], -1)) - b5, dia)
        out.append(f"fase {p}: {m:+.2f} [{lo:+.2f},{hi:+.2f}]")
    print(f"D={Dd}: " + " | ".join(out), flush=True)
