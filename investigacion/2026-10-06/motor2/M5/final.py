import numpy as np
from comb import *
O = np.load(os.path.join(SP, "M5_otras.npz")); Q = ajustar(O["DOW_hl2_k20"]); w = 0.75
P = np.exp((1 - w) * np.log(A.PROD) + w * np.log(Q)); P /= P.sum(1, keepdims=True)
np.savez(os.path.join(SP, "motor2_M5.npz"), P=P, t=A.T)
A.evaluar(P, "M5_final_mezcla075_DOWhl2k20", tramos=("AJUSTE", "ELECCION", "PRUEBA26", "ANTIGUO"),
          extra="p∝PROD^0.25·ajustar(DOW_hl2_k20)^0.75; pesos log-lineales diarios, vida media 2 sem, lam 20, κ 20 por día de la semana")
d = 1000 * np.log2(P[np.arange(len(A.Y)), A.Y] / A.PROD[np.arange(len(A.Y)), A.Y]); m = A.TRAMOS["PRUEBA26"]
print("PRUEBA26 por día (lun..dom):", " ".join(f"{d[m & (A.DOW == k)].mean():+.1f}" for k in range(7)))
