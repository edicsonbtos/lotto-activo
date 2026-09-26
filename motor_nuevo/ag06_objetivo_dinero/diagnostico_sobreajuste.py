# -*- coding: utf-8 -*-
"""Diagnóstico (no es variante nueva): retorno Top-5 escalonado DENTRO de muestra vs fuera, bloque a bloque,
para V_dinero y V_logloss. Muestra si la pérdida de dinero sobreajusta."""
import os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A, rasgos as R, nucleo as N
D = A.datos().prefijo(A.CORTE); P, y = A.base()
X = R.construir(D, A.W).astype(float); Pn = P / P.sum(1, keepdims=True); L = np.log(np.clip(Pn, 1e-12, None))
dia = np.asarray(D.dia[A.W:]); ud = np.unique(dia)
blq = np.minimum((np.arange(len(ud)) * 5) // len(ud), 4)[np.searchsorted(ud, dia)]
ret = lambda s, yy: A.retorno_t5(A.puestos(s, yy)).mean()
for tipo in ("dinero", "log"):
    for b in range(5):
        tr, te = blq != b, blq == b
        w = N.ajustar(L[tr], X[tr], y[tr], tipo)
        f = lambda m: np.exp(L[m] + X[m] @ w)
        print(f"{tipo:6s} bloque {b}: ret dentro {ret(f(tr), y[tr]):+.3f} (ens {ret(Pn[tr], y[tr]):+.3f}) · "
              f"fuera {ret(f(te), y[te]):+.3f} (ens {ret(Pn[te], y[te]):+.3f})")
