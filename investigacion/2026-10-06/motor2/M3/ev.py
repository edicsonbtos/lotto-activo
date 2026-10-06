import sys, numpy as np, io, contextlib
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
SP=A.SP
def cargar(nm):
    z=np.load(SP+f"/m3_cfg_{nm}.npz"); return z["P"]
if __name__=="__main__":
    for nm in sys.argv[1:]:
        A.evaluar(cargar(nm), nm, tramos=("ANTIGUO","AJUSTE","ELECCION"))
