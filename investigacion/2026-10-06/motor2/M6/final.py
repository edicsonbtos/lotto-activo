# -*- coding: utf-8 -*-
"""M6 final CONGELADO: V1 = PROD·exp(β1·[RD (h−1):30] + β2·[par_evita]), β walk-forward mensual (λ=2, w=1).
Prueba de fuga con A.chequear_fuga recalculando rasgos y β desde la secuencia alterada; luego PRUEBA26 una vez."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import correccion as C, rasgos as R; A = C.A
LISTA = C.VAR["V1_conf"]
rdD = A.LE.cargar("/home/user/lotto-activo/rdint_historial.txt")
rd = {(f, int(h)): int(s) for f, h, s in zip(rdD.fecha, rdD.hora, rdD.seq)}
pos = {int(t): j for j, t in enumerate(A.T)}

def fn(S, hora, dow, fecha, i):
    j = pos[i]; filas = A.T[: j + 1]
    nom, fam, M, DF = R.construir(S, hora, fecha, rd, filas)
    X = np.stack([M[nom.index(r)] for r in LISTA]).astype(float)
    yy = S[filas]; mes = A.F[j][:7]; prev = np.where(np.array([f[:7] for f in A.F[: j + 1]]) < mes)[0]
    Cy = C.y; C.y = np.r_[yy, C.y[j + 1:]]                   # y alterado para el ajuste de β
    LP0 = C.LP; C.LP = C.LP[: j + 1]
    Xp = X
    b = C.ajustar(Xp, prev) if len(prev) >= 1000 else np.zeros(len(LISTA))
    C.y = Cy; C.LP = LP0
    L = np.log(A.PROD[j]) + b @ X[:, j]; p = np.exp(L - L.max()); return p / p.sum()
A.chequear_fuga(fn)
P = np.load(os.path.join(A.SP, "m6_V1_conf_wf.npy")).astype(float)
for c in (6000, 9000, 12000):   # coincide con la matriz guardada
    assert np.allclose(fn(np.asarray(A.D.seq), np.asarray(A.D.hora), np.asarray(A.D.dow), list(A.D.fecha), c), P[pos[c]], atol=1e-5)
print("matriz guardada = pipeline walk-forward: OK")
np.savez_compressed(os.path.join(A.SP, "motor2_M6.npz"), P=P, t=A.T, nombre="M6_V1_RD1igual_par_evita_wf")
A.evaluar(P, "M6_final", tramos=("AJUSTE", "ELECCION"))
A.evaluar(P, "M6_final", tramos=("PRUEBA26",), extra="M6 V1 congelado: PROD*exp(b1*RD(h-1):30 + b2*par_evita), b wf mensual")
