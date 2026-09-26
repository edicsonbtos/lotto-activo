# -*- coding: utf-8 -*-
"""Ajusta w (λ=30) con TODAS las filas de desarrollo [2000, 9357) y lo guarda. V1 = 33 variables; V0 = solo las 6 de transiciones."""
import os, sys, json
import numpy as np, importlib.util as iu
AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI)
sys.path.insert(0, MN); sys.path.insert(0, AQUI)
import arnes as A, rasgos12 as R
sp = iu.spec_from_file_location('exp_ag02', os.path.join(MN, 'ag02_residuo_boost', 'experimento.py')); E2 = iu.module_from_spec(sp); sp.loader.exec_module(E2)
D = A.datos().prefijo(A.CORTE); Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True); LPE = np.log(np.clip(Pens, 1e-12, None))
X, _ = R.construir(D, A.W); X = X.astype(float)
for nombre, cols in [("V1", list(range(R.F))), ("V0", list(range(27, R.F)))]:
    w = np.zeros(R.F); w[cols] = E2.ajustar_lineal(X[:, :, cols], LPE, y, 30.0)
    json.dump({"variante": nombre, "lambda": 30.0, "filas": [A.W, A.CORTE], "nombres": R.NOMBRES, "w": [float(v) for v in w]},
              open(os.path.join(AQUI, f"parametros_{nombre}.json"), "w", encoding="utf-8"), indent=1)
    print(nombre, "congelado;", {n: round(float(v), 3) for n, v in zip(R.NOMBRES, w) if abs(v) > 0.1})
