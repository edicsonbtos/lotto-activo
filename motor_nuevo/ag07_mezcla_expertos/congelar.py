# -*- coding: utf-8 -*-
"""Congela los parámetros de V1 (log-lineal con pesos por contexto) ajustados con TODAS las filas [1000, 9357)."""
import os, sys, json
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa
import nucleo as N  # noqa
A0 = 1000
REPO = ["intradia_v2", "secuencia_v3", "haz_v1"]
D = A.datos().prefijo(A.CORTE)
Lrepo = np.stack([N.lognorm(np.load(os.path.join(AQUI, f"cache_sub_{m}.npy"))) for m in REPO], 1)
L4 = np.concatenate([Lrepo, N.lognorm(N.recencia(D.seq)[A0:])[:, None, :]], 1)
X = N.contexto(D.seq, D.dia, np.concatenate([np.zeros((A0, 3, 38)), Lrepo], 0))[A0:]
Wm = N.ajustar_loglineal(L4, X, D.seq[A0:])
json.dump({"expertos": REPO + ["recencia"], "variables": ["1", "k/11", "(k/11)^2", "min(rep,3)/3", "log38-H"],
           "W": Wm.tolist(), "filas_ajuste": [A0, A.CORTE]}, open(os.path.join(AQUI, "parametros.json"), "w"), indent=1)
print(np.round(Wm, 3))
