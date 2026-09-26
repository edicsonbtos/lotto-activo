# -*- coding: utf-8 -*-
"""Ajusta V1 (λ=30) con TODO el desarrollo [2000, 9357) y congela parametros.json. Nada >= 9357."""
import json, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A, rasgos as R, experimento as E  # noqa: E401

D = A.datos().prefijo(A.CORTE)
P_ens, y = A.base()
LPE = np.log(np.clip(P_ens, 1e-12, None)); LPE -= np.log(np.exp(LPE).sum(1, keepdims=True))
X = R.construir(D, A.W)
w, mu, sd = E.ajustar(X, LPE, y)
json.dump({"nombres": R.NOMBRES, "w_estandarizado": w.tolist(), "mu": mu.tolist(), "sd": sd.tolist(),
           "lambda": E.LAMBDA, "filas_ajuste": [A.W, A.CORTE],
           "w_crudo": (w / sd).tolist()},
          open(os.path.join(AQUI, "parametros.json"), "w", encoding="utf-8"), indent=1)
print({n: round(float(v), 4) for n, v in zip(R.NOMBRES, w / sd)})
