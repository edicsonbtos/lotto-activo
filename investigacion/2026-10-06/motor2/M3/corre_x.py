import sys, time, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2/M3")
import arnes as A, m3
t0=time.time()
X, nombres, nb, dia, dow = m3.construir(A.D.seq, A.D.hora, A.D.fecha)
print("X", X.shape, time.time()-t0)
np.save(A.SP+"/m3_X.npy", X); np.savez(A.SP+"/m3_meta.npz", nombres=np.array(nombres), nb=nb, dia=dia, dow=dow, y=np.asarray(A.D.seq))
