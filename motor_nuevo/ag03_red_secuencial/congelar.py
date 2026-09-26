# -*- coding: utf-8 -*-
"""Congela V_apilado: entrena con todo [2000, 9357) el nº de épocas = mediana del cross-fit (resultados.json)."""
import json, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI); sys.path.insert(0, os.path.dirname(AQUI))
import arnes as A, rasgos as R, red  # noqa: E402

res = json.load(open(os.path.join(AQUI, "resultados.json"), encoding="utf-8"))
ep = int(np.median(res["V_apilado (primaria)"]["epocas"]))
D = A.datos(); P_ens, y = A.base()
X = R.construir(D, A.W, A.CORTE)
off = np.log(np.clip(P_ens, 1e-12, None)).astype(np.float32)
p, _ = red.entrenar(X, y, off, fijo=ep, semilla=0)
np.savez(os.path.join(AQUI, "parametros.npz"), epocas=ep, nombres=np.array(R.NOMBRES), **p)
print("épocas", ep, "guardado parametros.npz")
