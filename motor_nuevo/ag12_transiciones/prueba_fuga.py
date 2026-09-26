# -*- coding: utf-8 -*-
import os, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI)
sys.path.insert(0, MN); sys.path.insert(0, AQUI)
import arnes as A, lotto_eval as LE, numpy as np
import modelo as M
D = A.datos()
for v in ("V1", "V0"):
    t = time.time()
    print(v, LE.prueba_fuga(M.Modelo(v), D.prefijo(2600), 2000), f"{time.time()-t:.0f} s")
# coherencia: modelo congelado sobre desarrollo con el P del ensamble en caché
Pens, y = A.base()
Q = M.Modelo("V1", P_ens=Pens).predecir(D.prefijo(A.CORTE), A.W)
print(A.informe(Q, "V1 congelado DENTRO de muestra (optimista, solo coherencia)"))
