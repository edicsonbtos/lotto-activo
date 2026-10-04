import sys, time, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/herramientas"); sys.path.insert(0, "/home/user/lotto-activo")
import lotto_eval as LE
D = LE.cargar("hist.txt"); n=len(D)
desde = max(2000, LE.W)
ens = LE.cargar_modelo("/home/user/lotto-activo/herramientas/modelos/ensamble_v2.py")
t0=time.time(); P = LE.normalizar(ens.predecir(D, desde)); print("seg", time.time()-t0)
np.savez("wf.npz", P=P, desde=desde)
