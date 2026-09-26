# -*- coding: utf-8 -*-
"""Ablación INFORMATIVA (añadida después de ver V1; no elige nada): qué grupo de variables aporta."""
import os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A, rasgos as R, experimento as E  # noqa: E401

D = A.datos().prefijo(A.CORTE)
P_ens, y = A.base()
LPE = np.log(np.clip(P_ens, 1e-12, None)); LPE -= np.log(np.exp(LPE).sum(1, keepdims=True))
X = R.construir(D, A.W)
blo = E.bloques_jornada(np.asarray(D.dia[A.W:A.CORTE]))
grupos = {
    "solo transiciones 30 d (f4, f5)": [3, 4],
    "solo composición del día (f1-f3, f6-f9)": [0, 1, 2, 5, 6, 7, 8],
    "solo ayer (f1, f7)": [0, 6],
    "solo co-ocurrencia semana/mes + orden (f2, f3, f6, f8, f9)": [1, 2, 5, 7, 8],
}
for nm, idx in grupos.items():
    P, _ = E.cross_fit(X[:, :, idx], LPE, y, blo)
    print(A.informe(P, "ablación: " + nm))
