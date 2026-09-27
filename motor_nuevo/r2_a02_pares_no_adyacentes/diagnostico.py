# -*- coding: utf-8 -*-
"""Diagnóstico descriptivo (no es variante): solapamiento de C/D@1-1 y D@2-7 con la variable 17 de ag02
(mismo_dia_que_s1_ant = animales del día de la ocurrencia anterior de s1) y O/E de la pareja no ordenada ayer."""
import os, sys, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI)
sys.path.insert(0, MN); sys.path.insert(0, AQUI); sys.path.insert(0, os.path.join(MN, "ag02_residuo_boost"))
import arnes as A, rasgos as R2
import importlib.util as iu
_s = iu.spec_from_file_location('exp_r2', os.path.join(AQUI, 'experimento.py')); X = iu.module_from_spec(_s); _s.loader.exec_module(X)
D = A.datos().prefijo(A.CORTE); _, y = A.base()
P = np.load(os.path.join(MN, "ag12_transiciones", "P_V1.npy")); P = P / P.sum(1, keepdims=True)
Xn = X.rasgos(D, A.W); X2, _ = R2.construir(D, A.W); f17 = X2[:, :, 17] > 0
n = len(y); h = n // 2
ix = {nm: i for i, nm in enumerate(X.NOMBRES)}
C1 = Xn[:, :, ix["C_s1i_desf3+@1-1"]] >= 1; D1 = Xn[:, :, ix["D_is1_desf3+@1-1"]] >= 1; D27 = Xn[:, :, ix["D_is1_desf3+@2-7"]] >= 1
for nm, M in [("C|D ayer (pareja no ordenada, desf>=3)", C1 | D1), ("C|D ayer y var17", (C1 | D1) & f17),
              ("C|D ayer sin var17", (C1 | D1) & ~f17), ("D 2-7 y var17", D27 & f17), ("D 2-7 sin var17", D27 & ~f17),
              ("var17 sola", f17)]:
    for lab, sl in [("m1", slice(0, h)), ("m2", slice(h, n)), ("tot", slice(0, n))]:
        r = X.prueba(M[sl], P[sl], y[sl]); print(f"{nm:40s} {lab:3s} obs {r['obs']:5d} esp {r['esp']:8.1f} O/E {r['OE']} z {r['z']:+.2f}")
