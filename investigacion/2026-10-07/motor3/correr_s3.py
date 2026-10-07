"""python correr_s3.py <S2|S3> <vida> : walk-forward 2025-07..2026-10, reentreno mensual."""
import sys, time, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
import arnes as A, motor_s2 as M
SP = A.SP; nombre, vida = sys.argv[1], float(sys.argv[2])
z = np.load(SP + "/s2_rasgos.npz"); X = z["X"]; nm = [str(x) for x in z["nm"]]; etq = z["etq"]
if nombre == "S3":
    m4 = np.load(SP + "/m4_rasgos.npz"); n4 = [str(x) for x in m4["nm"]]
    cols = [n4.index(k) for k in ("rd1", "rd2", "hay_rd")]
    X = np.concatenate([X, m4["X"][:, :, cols]], 2).astype(np.float32); nm = nm + ["rd1", "rd2", "hay_rd"]
t0 = time.time()
P, info, _ = M.correr("C", vida, X, nm, etq, "2025-07", 1, "2026-10", log=lambda *a, **k: print(*a, flush=True))
np.savez(f"{SP}/s3run_{nombre}_{int(vida)}.npz", P=P, info=np.array(info, dtype=object))
print(nombre, vida, round(time.time() - t0), "s", np.isfinite(P[A.TRAMOS["PRUEBA26"]]).all(), flush=True)
