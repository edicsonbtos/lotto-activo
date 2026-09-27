# -*- coding: utf-8 -*-
"""X4 EXPLORATORIA (4.a variante, elegida DESPUES de ver el barrido): corrección sobre ag12 V1 con
C@1-1, D@1-1 y D@2-7 (las tres celdas con |z total| > 3,5). No es candidata: sirve para acotar el techo del ángulo."""
import os, sys, json, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI); sys.path.insert(0, MN)
import arnes as A
import importlib.util as iu
_s = iu.spec_from_file_location('exp_r2', os.path.join(AQUI, 'experimento.py')); X = iu.module_from_spec(_s); _s.loader.exec_module(X)
E2 = X.E2
D = A.datos().prefijo(A.CORTE); _, y = A.base()
P = np.load(os.path.join(MN, "ag12_transiciones", "P_V1.npy")); P = P / P.sum(1, keepdims=True); LPR = np.log(np.clip(P, 1e-12, None))
dia = np.asarray(D.dia[A.W:A.CORTE]); blo = E2.bloques_jornada(dia)
Xl = np.log1p(X.rasgos(D, A.W)).astype(np.float64)
cols = [X.NOMBRES.index(c) for c in ["C_s1i_desf3+@1-1", "D_is1_desf3+@1-1", "D_is1_desf3+@2-7"]]
Xc = Xl[:, :, cols]
fit = lambda tr: E2.ajustar_lineal(Xc[tr], LPR[tr], y[tr], X.LAM); pred = lambda w, te: E2.predecir_lineal(w, Xc[te], LPR[te])
Pc, W = E2.cross_fit(fit, pred, blo); W = np.array(W)
r = A.evaluar(Pc, P_ref=P, y=y)
Pf = E2.forward(fit, pred, blo); Pf[blo == 0] = P[blo == 0]
dd = A.mbits_fila(Pf, y) - A.mbits_fila(P, y); m = blo > 0; fw = A.ic_bloques(dd[m], dia[m])
print("X4 delta", r["delta_mbits"], "m1", r["delta_mitad1"], "m2", r["delta_mitad2"])
print("Top-5 %.2f%% vs %.2f%%  Top-15 %.2f%% vs %.2f%%" % (r["top5_cand"]*100, r["top5_ens"]*100, r["top15_cand"]*100, r["top15_ens"]*100))
print("pesos", W.mean(0), "forward b1-4", fw, "PASA(formal)", r["pasa_barra_dev"])
json.dump({"X4": r, "X4_forward_b1a4": fw, "pesos_media": W.mean(0).tolist()}, open(os.path.join(AQUI, "resultados_x4.json"), "w"), indent=1)
