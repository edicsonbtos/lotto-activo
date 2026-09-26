# -*- coding: utf-8 -*-
"""lotto_eval.prueba_fuga del Modelo sobre datos.prefijo(2600), desde 2000; y coherencia con la caché."""
import os, sys, time
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A
from arnes import LE
import modelo as M
D = A.datos().prefijo(2600)
m = M.Modelo()
t = time.time()
print("prueba_fuga:", LE.prueba_fuga(m, D, 2000), f"{time.time()-t:.0f} s")
P = m.predecir(D, 2000)
Pc, _ = A.base()
Pe = M._ensamble().predecir(D, 2000)
print("ensamble_v2 vs caché, max |dif| (600 filas):", float(np.abs(Pe - Pc[:600] / Pc[:600].sum(1, keepdims=True)).max()))
print("forma", P.shape, "sumas", float(P.sum(1).min()), float(P.sum(1).max()))
