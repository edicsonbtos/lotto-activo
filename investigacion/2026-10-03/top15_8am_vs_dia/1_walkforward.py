import sys, time, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/herramientas")
import lotto_eval as LE, os
D = LE.cargar(sys.argv[1])
h = np.asarray(D.hora); n=len(D)
desde = 0
desde = max(desde, LE.W)
print("n", n, "desde", desde, D.fecha[desde], flush=True)
ens = LE.cargar_modelo("/home/user/lotto-activo/herramientas/modelos/ensamble_v2.py")
t0=time.time()
P = LE.normalizar(ens.predecir(D, desde))
print("seg", time.time()-t0, P.shape, flush=True)
np.savez(sys.argv[2], P=P, desde=desde, y=np.asarray(D.seq)[desde:], hora=h[desde:], dia=np.asarray(D.dia)[desde:], fecha=np.array(D.fecha[desde:]))
