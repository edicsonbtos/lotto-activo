"""Corre S2 (C, vida 90) y la base (ensamble_v2) sobre la serie sellada, walk-forward. UNA corrida."""
import sys, types, time, numpy as np
SP = "/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad"
sys.path.insert(0, "/home/user/lotto-activo/herramientas")
import lotto_eval as LE
D = LE.cargar("/home/user/lotto-activo/investigacion/2026-10-07/sellado/sellado_2019_2023.txt")
F = np.array(D.fecha); T = np.where(F >= "2020-01-01")[0]
shim = types.ModuleType("arnes"); shim.D = D; shim.T = T; shim.F = F[T]; shim.SP = SP
sys.modules["arnes"] = shim
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
sys.path.insert(0, '/home/user/lotto-activo/investigacion/2026-10-07/sellado'); import motor_s2_sellado as M
z = np.load(SP + "/sel_rasgos.npz"); X = z["X"]; nm = [str(x) for x in z["nm"]]; etq = z["etq"]
t0 = time.time()
P, info, _ = M.correr("C", 90.0, X, nm, etq, "2020-01", 1, "2023-09", log=lambda *a, **k: print(*a, flush=True))
print("S2", round(time.time() - t0), "s", np.isfinite(P).all(), flush=True)
ens = LE.cargar_modelo("/home/user/lotto-activo/herramientas/modelos/ensamble_v2.py")
t0 = time.time(); PB = LE.normalizar(ens.predecir(D, LE.W))      # fila i-ésima de PB = sorteo LE.W + i
print("ens", round(time.time() - t0), "s", PB.shape, flush=True)
base = np.full((len(T), 38), np.nan); ok = T >= LE.W
base[ok] = PB[T[ok] - LE.W]
np.savez(SP + "/sel_resultado.npz", S2=P, base=base, T=T, y=np.asarray(D.seq)[T], f=F[T], h=np.asarray(D.hora)[T], dow=np.asarray(D.dow)[T])
print("guardado", flush=True)
