# -*- coding: utf-8 -*-
"""lotto_eval.prueba_fuga sobre datos.prefijo(2600), desde 2000 (recalcula el ensamble_v2 del repo)."""
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa: E402
import lotto_eval as LE  # noqa: E402
import modelo as M  # noqa: E402
print("prueba_fuga:", LE.prueba_fuga(M.Modelo(), A.datos().prefijo(2600), 2000))
