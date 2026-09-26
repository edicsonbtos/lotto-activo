# -*- coding: utf-8 -*-
import os, sys, json, time
import numpy as np
V = os.path.dirname(os.path.abspath(__file__)); AG = os.path.dirname(V); MN = os.path.dirname(AG)
sys.path.insert(0, MN); sys.path.insert(0, AG)
import arnes as A, rasgos as R, experimento as E, modelo as M
from arnes import LE
Dfull = A.datos()
for fin, desde, sem in ((3000, 2500, 5), (5400, 5000, 11)):
    D = Dfull.prefijo(fin); m = M.Modelo(); t = time.time()
    print(f"prueba_fuga prefijo({fin}) desde {desde} semilla {sem}:", LE.prueba_fuga(m, D, desde, cortes=4, semilla=sem), f"{time.time()-t:.0f}s")
    Pm = m.predecir(D, desde)
    Pc, y = A.base(); Pc = Pc / Pc.sum(1, keepdims=True)
    a, b = desde - A.W, fin - A.W
    w = np.array(json.load(open(os.path.join(AG, "parametros.json"), encoding="utf-8"))["w"])
    X, _ = R.construir(D, desde)
    Pl = E.predecir_lineal(w, X.astype(float), np.log(np.clip(Pc[a:b], 1e-12, None)))
    print("  max|modelo.py(ensamble recalculado) - lineal sobre caché|:", float(np.abs(Pm - Pl).max()))
