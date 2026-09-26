# -*- coding: utf-8 -*-
"""Robustez: semillas, nº de bloques, embargo; Δ por bloque cross-fit vs forward; placebo de variables."""
import os, sys, numpy as np
AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A, variables as V, experimento as E
D = A.datos(); P_ens, y = A.base(); W, C = A.W, A.CORTE
seq = np.asarray(D.seq)[:C]; X = V.construir(seq, np.asarray(D.hora)[:C], np.asarray(D.dia)[:C], W, C)
Y1 = np.zeros((len(y), 38), np.float32); Y1[np.arange(len(y)), y] = 1
dia = np.asarray(D.dia)[W:C]
XB, lp = V.con_ensamble(X, P_ens); lp = lp.astype(float)
d_mb = lambda P: A.mbits_fila(P, y) - A.mbits_fila(P_ens, y)
Pcf = np.load(os.path.join(AQUI, "P_B_apilado.npy")).astype(float)
dias = np.unique(dia); tz = np.array_split(dias, 5)
print("Δ por bloque (cross-fit original):", [round(d_mb(Pcf)[np.isin(dia, t)].mean(), 2) for t in tz], flush=True)
def corre(etq, **kw):
    old = {k: getattr(E, k) for k in kw}
    for k, v in kw.items(): setattr(E, k, v)
    P, arb = E.cross_fit(XB, Y1, lp, dia, etq)
    for k, v in old.items(): setattr(E, k, v)
    r = A.evaluar(P); print(f"### {etq}: Δ {r['delta_mbits']} m1 {r['delta_mitad1'][0]:.2f} m2 {r['delta_mitad2'][0]:.2f} arb {arb}", flush=True)
    return P
for s in (1, 2, 3):
    corre(f"semilla{s}", PARAMS=dict(E.PARAMS, seed=s))
corre("10bloques", NBLOQ=10)
corre("3bloques", NBLOQ=3)
corre("embargo7", EMBARGO=7)
# Placebo: barajar las variables propias entre sorteos (conservando log P_ens/rango alineados)
rng = np.random.default_rng(5); perm = rng.permutation(len(y))
XP = XB.copy(); XP[:, :, :V.NF] = XB[perm][:, :, :V.NF]
P, arb = E.cross_fit(XP, Y1, lp, dia, "placebo")
r = A.evaluar(P); print("### placebo variables barajadas: Δ", r["delta_mbits"], arb, flush=True)
