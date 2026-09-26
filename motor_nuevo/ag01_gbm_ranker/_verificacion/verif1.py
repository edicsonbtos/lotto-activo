# -*- coding: utf-8 -*-
import os, sys, time, numpy as np
AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A, variables as V, lotto_eval as LE, lightgbm as lgb
import modelo as M
D = A.datos(); P_ens, y = A.base(); W = A.W
m = M.Modelo()
# 1) prueba de fuga con prefijo corto
for T, cortes in ((2600, 5), (3200, 4)):
    t0=time.time(); print("prueba_fuga prefijo", T, LE.prueba_fuga(m, D.prefijo(T), W, cortes=cortes, semilla=11), f"{time.time()-t0:.0f}s", flush=True)
# 2) coherencia: modelo.predecir sobre prefijo vs booster congelado sobre variables del experimento
T = 3200
Pm = m.predecir(D.prefijo(T), W)
Pens_m = M._ensamble().predecir(D.prefijo(T), W)
print("ensamble recargado vs cache: max dif", np.abs(LE.normalizar(Pens_m) - P_ens[:T-W]/P_ens[:T-W].sum(1,keepdims=True)).max())
seq = np.asarray(D.seq)[:A.CORTE]; X = V.construir(seq, np.asarray(D.hora)[:A.CORTE], np.asarray(D.dia)[:A.CORTE], W, A.CORTE)
XB, lp = V.con_ensamble(X, P_ens)
s = m.bst.predict(XB.reshape(-1, XB.shape[2]), raw_score=True).reshape(-1, 38) + lp
s -= s.max(1, keepdims=True); Pfull = np.exp(s); Pfull /= Pfull.sum(1, keepdims=True)
print("modelo.predecir(prefijo) vs congelado sobre desarrollo completo: max dif", np.abs(Pm - Pfull[:T-W]).max())
r = A.evaluar(Pfull); print("congelado in-sample (esperado optimista):", r["delta_mbits"])
# 3) congruencia con P cross-fit guardado: correlación de las correcciones
Pcf = np.load(os.path.join(AQUI, "P_B_apilado.npy")).astype(float)
Pe = P_ens/P_ens.sum(1,keepdims=True)
c1 = np.log(Pcf/Pe).ravel(); c2 = np.log(Pfull/Pe).ravel()
print("corr(corrección cross-fit, corrección congelada)", np.corrcoef(c1, c2)[0,1])
# 4) causalidad de variables: X con seq truncado en c idéntico para filas < c... (fila c usa seq[:c])
rng = np.random.default_rng(3)
for c in rng.integers(W+100, A.CORTE-100, 3):
    s2 = seq.copy(); s2[c:] = rng.integers(0, 38, len(s2)-c)
    X2 = V.construir(s2, np.asarray(D.hora)[:A.CORTE], np.asarray(D.dia)[:A.CORTE], W, A.CORTE)
    print("variables causales corte", c, np.array_equal(X[:c-W+1], X2[:c-W+1]))
# 5) filas >= CORTE nunca tocadas
print("len historial", len(D), "CORTE", A.CORTE, "X filas", X.shape[0], "=", A.CORTE-W)
