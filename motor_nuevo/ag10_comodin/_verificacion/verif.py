import os, sys, time
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); AG = os.path.dirname(AQUI); MN = os.path.dirname(AG)
sys.path.insert(0, MN); sys.path.insert(0, AG)
import arnes as A, lotto_eval as LE, rasgos as R, modelo as M
D = A.datos(); Dp = D.prefijo(A.CORTE)
P_ens, y = A.base()
# 1) prueba_fuga con prefijo corto, 5 cortes, otra semilla
t0=time.time()
print("fuga prefijo 2400 semilla 3:", LE.prueba_fuga(M.Modelo(), D.prefijo(2400), 2000, cortes=5, semilla=3), f"{time.time()-t0:.0f}s")
# 2) ensamble recomputado vs cache (primeras 400 filas)
Pe = M._ensamble().predecir(D.prefijo(2400), 2000)
Pe = Pe/Pe.sum(1,keepdims=True); Pc = P_ens[:400]/P_ens[:400].sum(1,keepdims=True)
print("ensamble recomputado vs cache max diff:", np.abs(Pe-Pc).max())
# 3) rasgos: truncación por fila (t aleatorios), X de la fila t con datos[:t+1] con seq[t] reemplazado
rng = np.random.default_rng(1)
X = R.construir(Dp, A.W)
mx = 0
for t in rng.integers(A.W+50, A.CORTE, 40):
    s = Dp.seq.copy(); s[t:] = rng.integers(0,38,len(s)-t)
    D2 = LE.Datos(s, Dp.hora, Dp.dow, Dp.dia, Dp.fecha)
    X2 = R.construir(D2, t)
    mx = max(mx, np.abs(X2[0]-X[t-A.W]).max())
print("rasgos fila t con futuro (incl. t) barajado, max diff:", mx)
# 4) reimplementacion ingenua de trans1_30 / trans2_30 / ayer_cooc
seq = np.asarray(Dp.seq); dia = np.asarray(Dp.dia)
mx = 0
for t in rng.integers(A.W, A.CORTE, 300):
    d = dia[t]; s1 = seq[t-1]; s2 = seq[t-2]
    f4 = np.zeros(38); f5 = np.zeros(38)
    for u in range(2, t):
        if dia[u] >= d-30:
            if seq[u-1]==s1: f4[seq[u]]+=1
            if seq[u-2]==s2: f5[seq[u]]+=1
    S = seq[(dia==d)&(np.arange(len(seq))<t)]
    prev = dia[dia<d].max(); Y1 = np.zeros(38); Y1[seq[dia==prev]] = 1
    f1 = Y1*Y1[S].sum() if len(S) else np.zeros(38)
    mx = max(mx, np.abs(f4-X[t-A.W,:,3]).max(), np.abs(f5-X[t-A.W,:,4]).max(), np.abs(f1-X[t-A.W,:,0]).max())
print("reimpl. ingenua f1,f4,f5 max diff:", mx)
# 5) modelo.py congelado sobre desarrollo con P_ens=cache vs cross-fit
Q = M.Modelo(P_ens=P_ens).predecir(Dp, A.W)
Pcf = np.load(os.path.join(AG, "P_V1.npy")).astype(float)
print("modelo congelado (in-sample):"); print(A.informe(Q, "modelo.py congelado, desarrollo (in-sample)"))
print("corr log-ratio modelo vs cross-fit:", np.corrcoef(np.log(Q/P_ens*P_ens.sum(1,keepdims=True)).ravel(), np.log(Pcf/P_ens*P_ens.sum(1,keepdims=True)).ravel())[0,1], "max|Q-Pcf|", np.abs(Q-Pcf).max())
# 6) placebo: permutar transiciones -> trans1_30 con s1 aleatorio (misma distribucion) 
import experimento as E
LPE = np.log(np.clip(P_ens,1e-12,None)); LPE -= np.log(np.exp(LPE).sum(1,keepdims=True))
blo = E.bloques_jornada(dia[A.W:A.CORTE])
Xp = X.copy(); perm = rng.permutation(len(X)); Xp[:,:,3] = X[perm][:,:,3]; Xp[:,:,4] = X[perm][:,:,4]
Pp,_ = E.cross_fit(Xp, LPE, y, blo)
r = A.evaluar(Pp); print("placebo (f4,f5 permutados entre filas): delta", r["delta_mbits"])
# 7) solo f4 (1 variable) y cross-fit con 10 bloques
P4,_ = E.cross_fit(X[:,:,[3]], LPE, y, blo); print("solo trans1_30:", A.evaluar(P4)["delta_mbits"])
