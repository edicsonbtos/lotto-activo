# -*- coding: utf-8 -*-
"""Walk-forward de ensamble_v2 (cada fila solo con el pasado). Uso: python 0_walkforward.py HIST SALIDA.npz"""
import os, sys, time
import numpy as np
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE  # noqa: E402

D = LE.cargar(sys.argv[1])
ens = LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", "ensamble_v2.py"))
t0 = time.time(); P = LE.normalizar(ens.predecir(D, LE.W))
print("filas", len(D), "seg", round(time.time() - t0))
np.savez(sys.argv[2], P=P, desde=LE.W)
