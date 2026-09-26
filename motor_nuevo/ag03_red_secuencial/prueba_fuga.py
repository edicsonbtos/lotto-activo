# -*- coding: utf-8 -*-
"""lotto_eval.prueba_fuga sobre prefijo(2600), desde 2000, y coincidencia con el experimento."""
import os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI); sys.path.insert(0, os.path.dirname(AQUI))
import arnes as A  # noqa: E402
from modelo import Modelo  # noqa: E402
D = A.datos().prefijo(2600)
m = Modelo()
print("prueba_fuga:", A.LE.prueba_fuga(m, D, 2000))
P_ens, _ = A.base()
Q = m.predecir(D, 2000)
print("ensamble recalculado vs caché, máx |dif| del ensamble:",
      float(np.abs(__import__('modelo')._ensamble().predecir(D, 2000) - P_ens[:600]).max()))
print("filas", Q.shape, "suma", float(Q.sum(1).min()), float(Q.sum(1).max()))
