"""C1: S2 CONGELADO (C, vida 90) en ANTIGUO 2024-03..2025-06 con REENTRENO MENSUAL (paso = 1). Sin reajustar nada.
Usa la matriz de rasgos ya construida (s2_rasgos.npz, la misma del motor congelado) y motor_s2.correr tal cual."""
import sys, time, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
import arnes as A, motor_s2 as M
z = np.load(A.SP + "/s2_rasgos.npz"); X = z["X"]; nm = [str(x) for x in z["nm"]]; etq = z["etq"]
t0 = time.time()
P, info, _ = M.correr("C", 90.0, X, nm, etq, desde="2024-03", paso=1, hasta="2025-06")
np.savez(A.SP + "/T1_c1_C_90_2024-03_1_2025-06.npz", P=P, info=np.array(info, dtype=object))
print(f"total {time.time() - t0:.0f}s")
