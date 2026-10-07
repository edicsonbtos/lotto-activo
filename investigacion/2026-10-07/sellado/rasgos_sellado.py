"""Rasgos S2 (M4 sin RD + nuevos) sobre la serie sellada. Causales (comprobado por fuga en 2026-10-06)."""
import sys, time, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2/M4"); sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
sys.path.insert(0, "/home/user/lotto-activo/herramientas")
import lotto_eval as LE, rasgos as R4, rasgos_s2 as R
SP = "/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad"
D = LE.cargar("/home/user/lotto-activo/investigacion/2026-10-07/sellado/sellado_2019_2023.txt")
print("filas", len(D), D.fecha[0], D.fecha[-1])
t0 = time.time()
X4, nm4 = R4.construir(D.seq, D.hora, D.dia, list(D.fecha), None)
keep = [j for j, n in enumerate(nm4) if n not in ("rd1", "rd2", "hay_rd")]
RHO = float(np.load(SP + "/s2_rasgos.npz")["rho"])
Xn, nmn, info = R.nuevos(D.seq, D.hora, D.dia, list(D.fecha), rho=RHO)
X = np.concatenate([X4[:, :, keep], Xn], 2).astype(np.float32); nm = [nm4[j] for j in keep] + nmn
ref = [str(x) for x in np.load(SP + "/s2_rasgos.npz")["nm"]]
assert nm == ref, (nm, ref)
np.savez_compressed(SP + "/sel_rasgos.npz", X=X, nm=np.array(nm), etq=info["etq"], rho=RHO)
print("rho", RHO, X.shape, round(time.time() - t0), "s")
