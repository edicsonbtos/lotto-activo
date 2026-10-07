"""C2: S2 (C, vida 90) CONGELADO entrenado con RD, reentreno mensual 2025-07..2026-09.
python c2_correr.py [todos|solo_lah]   todos = 3 rasgos LA (principal); solo_lah = solo LA h:00 (informativo).
motor_s2.correr se usa SIN cambios: solo se sustituye su arnés (A.D, A.T, A.F) por los datos de RD."""
import sys, time, types, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
sys.path.insert(0, "/home/user/lotto-activo/herramientas")
import motor_s2 as M, lotto_eval as LE
SP = "/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad"
var = sys.argv[1] if len(sys.argv) > 1 else "todos"
d = np.load(SP + "/T1_rd_datos.npz"); z = np.load(SP + "/T1_rd_rasgos.npz")
X = z["X"]; nm = [str(x) for x in z["nm"]]; etq = z["etq"]
if var == "solo_lah":
    keep = [j for j, n in enumerate(nm) if n not in ("la_h1", "la_antes_hoy")]
    X = np.ascontiguousarray(X[:, :, keep]); nm = [nm[j] for j in keep]
fecha = [str(x) for x in d["fecha"]]
D = LE.Datos(d["seq"], d["hora"], d["dow"], d["dia"], fecha)
T = np.arange(2000, len(fecha))
M.A = types.SimpleNamespace(D=D, T=T, F=np.array(fecha)[T])
t0 = time.time()
P, info, _ = M.correr("C", 90.0, X, nm, etq, desde="2025-07", paso=1, hasta="2026-09")
np.savez(SP + f"/T1_c2_s2rd_{var}.npz", P=P, t=T, info=np.array(info, dtype=object), nm=np.array(nm))
print(f"[{var}] total {time.time() - t0:.0f}s", flush=True)
