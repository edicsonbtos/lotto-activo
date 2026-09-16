# Guarda predicciones walk-forward de modelos base (solo filas < CORTE) para pruebas de residuos
import sys,os,time; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, lotto_eval as e
d=e.cargar(); N=len(d); W,CORTE=e.particion(N)
dd=d.prefijo(CORTE)   # nunca se pasan datos de prueba
SCR=sys.argv[1]
for nm in ["hazard_actual","logit_final"]:
    t0=time.time(); m=e.cargar_modelo(f"modelos/{nm}.py")
    P=e.normalizar(m.predecir(dd, W)); np.save(f"{SCR}/base_{nm}.npy", P)
    y=dd.seq[W:]; print(nm, time.time()-t0, np.mean(np.log2(P[np.arange(len(y)),y]*38))*1000)
