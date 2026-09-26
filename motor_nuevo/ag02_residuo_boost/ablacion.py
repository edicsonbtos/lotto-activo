# -*- coding: utf-8 -*-
"""Ablación informativa (no elige el candidato): V1 λ=30 cross-fit con subgrupos de variables."""
import os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A, rasgos as R, experimento as E
D = A.datos().prefijo(A.CORTE)
Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True); LPE = np.log(np.clip(Pens, 1e-12, None))
X, _ = R.construir(D, A.W); X = X.astype(float)
blo = E.bloques_jornada(np.asarray(D.dia[A.W:A.CORTE]))
grupos = {"tablero (0-13)": list(range(0, 14)), "pares/sucesor (14-17)": list(range(14, 18)),
          "ayer (18-26)": list(range(18, 27))}
for nom, cols in grupos.items():
    Xs = X[:, :, cols]
    P, _ = E.cross_fit(lambda tr: E.ajustar_lineal(Xs[tr], LPE[tr], y[tr], 30.0),
                       lambda w, te: E.predecir_lineal(w, Xs[te], LPE[te]), blo)
    r = A.evaluar(P)
    print(f"{nom:24s} Δ {r['delta_mbits'][0]:+.2f} [{r['delta_mbits'][1]:+.2f}, {r['delta_mbits'][2]:+.2f}]"
          f" · m1 {r['delta_mitad1'][0]:+.2f} · m2 {r['delta_mitad2'][0]:+.2f} · Top-5 {r['top5_cand']*100:.2f}%")
