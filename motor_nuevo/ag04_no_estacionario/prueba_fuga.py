# -*- coding: utf-8 -*-
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa
import modelo as M  # noqa
D = A.datos().prefijo(2600)
print("prueba_fuga prefijo(2600) desde 2000:", A.LE.prueba_fuga(M.Modelo(), D, 2000))
