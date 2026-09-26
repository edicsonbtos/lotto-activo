# -*- coding: utf-8 -*-
"""EXPLORATORIO (variante 4, añadida DESPUÉS de ver que V_dinero falló): pérdida de dinero con τ=0,05
arrancando desde la solución log-loss del mismo bloque de entrenamiento (afinado). Cross-fit 5 bloques.
Probabilidad: softmax(c·s), c por log-loss en el entrenamiento. No es candidato: >3 variantes."""
import json, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A, rasgos as R, nucleo as N
D = A.datos().prefijo(A.CORTE); P, y = A.base()
X = R.construir(D, A.W).astype(float); Pn = P / P.sum(1, keepdims=True); L = np.log(np.clip(Pn, 1e-12, None))
dia = np.asarray(D.dia[A.W:]); ud = np.unique(dia)
blq = np.minimum((np.arange(len(ud)) * 5) // len(ud), 4)[np.searchsorted(ud, dia)]
Pc = np.zeros_like(Pn); ws = []
for b in range(5):
    tr, te = blq != b, blq == b
    w0 = N.ajustar(L[tr], X[tr], y[tr], "log")
    w = N.ajustar(L[tr], X[tr], y[tr], "dinero", w0=w0, tau=0.05)
    c = N.ajustar_c(L[tr] + X[tr] @ w, y[tr])
    Pc[te] = N.softmax(c * (L[te] + X[te] @ w)); ws.append(w.tolist())
    print(f"bloque {b}: w0 {np.round(w0,2).tolist()}\n          w  {np.round(w,2).tolist()} c {c:.3f}")
print(A.informe(Pc, "V4_exploratorio_dinero_desde_logloss_tau0.05"))
json.dump({"exploratorio": True, "resultado": A.evaluar(Pc), "w_por_bloque": ws},
          open(os.path.join(AQUI, "resultados_exploratorio_v4.json"), "w", encoding="utf-8"), indent=1)
