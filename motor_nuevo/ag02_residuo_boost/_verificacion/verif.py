# -*- coding: utf-8 -*-
"""Verificación independiente de ag02 (no modifica el código del agente)."""
import os, sys, json
import numpy as np
V = os.path.dirname(os.path.abspath(__file__)); AG = os.path.dirname(V); MN = os.path.dirname(AG)
sys.path.insert(0, MN); sys.path.insert(0, AG)
import arnes as A, rasgos as R, experimento as E, modelo as M
from arnes import LE

D = A.datos().prefijo(A.CORTE)
assert len(D.seq) == A.CORTE
Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True); LPE = np.log(np.clip(Pens, 1e-12, None))
assert (y == np.asarray(D.seq[A.W:A.CORTE])).all(), "y de la caché != seq"
X, _ = R.construir(D, A.W); Xf = X.astype(float)

# A. rasgos de la fila t no dependen de seq[t:] (truncado y futuro barajado)
rng = np.random.default_rng(99)
malas = 0
for t in rng.integers(A.W, A.CORTE, size=60):
    Xt, _ = R.construir(D.prefijo(int(t) + 1), int(t))
    s2 = D.seq.copy(); s2[t:] = rng.integers(0, 38, size=len(s2) - t)
    D2 = LE.Datos(s2, D.hora, D.dow, D.dia, D.fecha)
    Xb, _ = R.construir(D2, A.W)
    if not (np.array_equal(Xt[0], X[t - A.W]) and np.array_equal(Xb[:t - A.W + 1], X[:t - A.W + 1])):
        malas += 1
print("A. filas con rasgos dependientes del futuro:", malas, "de 60")

# B. modelo.py en todo desarrollo == lineal con w congelado; Δ in-sample vs cross-fit
w = np.array(json.load(open(os.path.join(AG, "parametros.json"), encoding="utf-8"))["w"])
Pm = M.Modelo(P_ens=Pens).predecir(D, A.W)
Pl = E.predecir_lineal(w, Xf, LPE)
print("B. max|modelo.py - lineal(w)|:", float(np.abs(Pm - Pl).max()))
r = A.evaluar(Pm); print("B. Δ in-sample modelo congelado:", [round(v, 2) for v in r["delta_mbits"]])
blo = E.bloques_jornada(np.asarray(D.dia[A.W:A.CORTE]))
Pcf, pars = E.cross_fit(lambda tr: E.ajustar_lineal(Xf[tr], LPE[tr], y[tr], 30.0),
                        lambda ww, te: E.predecir_lineal(ww, Xf[te], LPE[te]), blo)
rc = A.evaluar(Pcf); print("B. Δ cross-fit recalculado:", [round(v, 2) for v in rc["delta_mbits"]])
print("B. max|w_bloque - w_final| :", float(np.abs(np.array(pars) - w).max()))
print("B. bloques tamaños:", np.bincount(blo).tolist())

# D. nulo: permutar filas de X dentro de cada bloque (rompe la asociación) -> Δ debe ser <= ~0
for s in range(3):
    rr = np.random.default_rng(s); idx = np.arange(len(y))
    for k in range(5):
        m = np.where(blo == k)[0]; idx[m] = rr.permutation(m)
    Xp = Xf[idx]
    Pp, _ = E.cross_fit(lambda tr: E.ajustar_lineal(Xp[tr], LPE[tr], y[tr], 30.0),
                        lambda ww, te: E.predecir_lineal(ww, Xp[te], LPE[te]), blo)
    print(f"D. nulo permutado {s}: Δ", [round(v, 2) for v in A.evaluar(Pp)["delta_mbits"]])

# E. forward-chaining estricto por jornada con reajuste cada 20 bloques (solo pasado) sobre la 2a mitad
nb = 20; b20 = E.bloques_jornada(np.asarray(D.dia[A.W:A.CORTE]), nb)
Pfw = Pens.copy()
for k in range(1, nb):
    ww = E.ajustar_lineal(Xf[b20 < k], LPE[b20 < k], y[b20 < k], 30.0)
    Pfw[b20 == k] = E.predecir_lineal(ww, Xf[b20 == k], LPE[b20 == k])
rf = A.evaluar(Pfw); print("E. forward 20 bloques: Δ", [round(v, 2) for v in rf["delta_mbits"]],
                          "m1", round(rf["delta_mitad1"][0], 2), "m2", round(rf["delta_mitad2"][0], 2))
