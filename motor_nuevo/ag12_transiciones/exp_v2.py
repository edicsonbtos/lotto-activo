# -*- coding: utf-8 -*-
"""ag12 V2 exploratoria: transiciones en 8 ventanas por sentido."""
import os, sys, json
import numpy as np, importlib.util as iu
AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI)
sys.path.insert(0, MN); sys.path.insert(0, AQUI); sys.path.insert(0, os.path.join(MN, "ag02_residuo_boost"))
import arnes as A, rasgos12 as R
sp = iu.spec_from_file_location('exp_ag02', os.path.join(MN, 'ag02_residuo_boost', 'experimento.py')); E2 = iu.module_from_spec(sp); sp.loader.exec_module(E2)
R.VENT = [(1, 1), (2, 2), (3, 3), (4, 7), (8, 14), (15, 30), (31, 45), (46, 60)]
def trans(datos, desde):
    seq = np.asarray(datos.seq); _, dn = np.unique(np.asarray(datos.dia), return_inverse=True); n = len(seq); V = R.VENT; nv = len(V)
    X = np.zeros((n - desde, 38, 2 * nv), np.float32); fwd, bwd = {}, {}
    for t in range(n):
        if t >= desde and t >= 1 and dn[t-1] == dn[t]:
            s1 = int(seq[t-1]); d = dn[t]; x = X[t - desde]
            for jd, b in fwd.get(s1, ()):
                for v, (lo, hi) in enumerate(V):
                    if lo <= d - jd <= hi: x[b, v] += 1
            for jd, a in bwd.get(s1, ()):
                for v, (lo, hi) in enumerate(V):
                    if lo <= d - jd <= hi: x[a, nv + v] += 1
        if t >= 1 and dn[t-1] == dn[t]:
            a, b = int(seq[t-1]), int(seq[t]); fwd.setdefault(a, []).append((dn[t], b)); bwd.setdefault(b, []).append((dn[t], a))
    return np.log1p(X)
D = A.datos().prefijo(A.CORTE); Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True); LPE = np.log(np.clip(Pens, 1e-12, None))
import rasgos as R2
X2, _ = R2.construir(D, A.W); X = np.concatenate([X2, trans(D, A.W)], axis=2).astype(float)
dia = np.asarray(D.dia[A.W:A.CORTE]); blo = E2.bloques_jornada(dia)
P, pars = E2.cross_fit(lambda tr: E2.ajustar_lineal(X[tr], LPE[tr], y[tr], 30.0), lambda w, te: E2.predecir_lineal(w, X[te], LPE[te]), blo)
print(A.informe(P, "V2_fina_exploratoria"))
Wb = np.array(pars)[:, 27:]
print("pesos s1->i por ventana:", np.round(Wb[:, :8].mean(0), 3)); print("pesos i->s1 por ventana:", np.round(Wb[:, 8:].mean(0), 3))
P1 = np.load(os.path.join(AQUI, "P_V1.npy"))
print("V2 - V1 mbits:", A.ic_bloques(A.mbits_fila(P, y) - A.mbits_fila(P1, y), dia))
np.save(os.path.join(AQUI, "P_V2.npy"), P)
