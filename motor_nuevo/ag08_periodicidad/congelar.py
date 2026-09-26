# -*- coding: utf-8 -*-
"""Congela θ del candidato primario con TODO el desarrollo [2000, 9357) (nada >= 9357) -> parametros.json."""
import json, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A
import rasgos as R
from experimento import PRIMARIO
D = A.datos().prefijo(A.CORTE); P, y = A.base(); P = P / P.sum(1, keepdims=True)
th = R.ajustar(P, R.construir(D, A.W, PRIMARIO), y, 1.0)
json.dump({"specs": [list(s) for s in PRIMARIO], "theta": th.tolist(), "lam": 1.0,
           "ajustado_con": "historial.txt filas [2000, 9357)"}, open(os.path.join(AQUI, "parametros.json"), "w"), indent=1)
print("theta congelado:", np.round(th, 4).tolist())
