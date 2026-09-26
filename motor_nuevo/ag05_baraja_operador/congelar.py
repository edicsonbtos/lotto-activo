# -*- coding: utf-8 -*-
"""Congela theta del apilado elegido (G1 en los 5 bloques) con TODO el desarrollo [2000, 9357)
(ensamble de la caché walk-forward como offset). Escribe parametros.json."""
import json, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa: E402
import baraja as B  # noqa: E402

D = A.datos().prefijo(A.CORTE)
P, y = A.base(); P = P / P.sum(1, keepdims=True)
cfg = ("G1",)
X = B.construir(D, A.W, cfg)
th, ll = B.ajustar(X, y, np.log(P))
json.dump({"config": list(cfg), "theta": th.tolist(), "filas": [A.W, A.CORTE]},
          open(os.path.join(AQUI, "parametros.json"), "w", encoding="utf-8"), indent=1)
print("config", cfg, "theta", th)
