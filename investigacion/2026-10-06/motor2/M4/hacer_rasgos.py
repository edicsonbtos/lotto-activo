import sys, time, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); sys.path.insert(0, ".")
import arnes as A, rasgos as R
SP = A.SP
t0 = time.time(); D = A.D; rd = R.cargar_rd()
X, nm = R.construir(D.seq, D.hora, D.dia, list(D.fecha), rd)
print("rasgos", X.shape, round(time.time() - t0, 1), "s")
# fuga a nivel de rasgos: alterar seq[c:] no cambia filas <= c
for c in (6000, 9000, 12000):
    S2 = np.asarray(D.seq).copy(); S2[c:] = (S2[c:] + 7) % 38
    X2, _ = R.construir(S2, D.hora, D.dia, list(D.fecha), rd)
    assert np.allclose(np.nan_to_num(X[:c + 1], nan=-9), np.nan_to_num(X2[:c + 1], nan=-9)), c
print("fuga rasgos: OK")
np.savez_compressed(SP + "/m4_rasgos.npz", X=X, nm=np.array(nm))
