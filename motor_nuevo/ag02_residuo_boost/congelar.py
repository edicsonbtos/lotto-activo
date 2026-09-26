# -*- coding: utf-8 -*-
"""Congela V1 (g lineal, λ = 30) ajustado con TODO el tramo de desarrollo [2000, 9357) -> parametros.json.
Uso: PYTHONIOENCODING=utf-8 python motor_nuevo/ag02_residuo_boost/congelar.py"""
import json, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A, rasgos as R, experimento as E

D = A.datos().prefijo(A.CORTE)
Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True)
X, _ = R.construir(D, A.W)
w = E.ajustar_lineal(X.astype(float), np.log(np.clip(Pens, 1e-12, None)), y, E.LAMBDA_PRIM)
json.dump({"variante": "V1_lineal_lambda30", "filas_ajuste": [A.W, A.CORTE], "lambda": E.LAMBDA_PRIM,
           "nombres": R.NOMBRES, "w": [float(v) for v in w]},
          open(os.path.join(AQUI, "parametros.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for n, v in zip(R.NOMBRES, w):
    print(f"{n:22s} {v:+.4f}")
