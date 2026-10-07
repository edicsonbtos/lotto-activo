"""C2: motor de RD walk-forward, igual que herramientas/rdint/prueba_ciega.py (E1):
B0 = secuencia_v3 con solo la secuencia RD (desde la fila 2000, reajuste cada 250);
B1 = modelo.cruzado(P0, features LA, R=250, minimo=500, lam=1), b walk-forward.
Guarda <SP>/T1_rd_motor.npz con P0, P1 (filas 2000..n-1)."""
import sys, time, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/herramientas"); sys.path.insert(0, "/home/user/lotto-activo/herramientas/rdint")
import lotto_eval as LE, modelo as MB
SP = "/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad"
z = np.load(SP + "/T1_rd_datos.npz")
rd = LE.Datos(z["seq"], z["hora"], z["dow"], z["dia"], [str(x) for x in z["fecha"]])
t0 = time.time()
mod = LE.cargar_modelo("/home/user/lotto-activo/herramientas/modelos/secuencia_v3.py")
P0, P1, hist = MB.predecir(mod, rd, z["la_h"], z["la_h1"], z["la_hoy"], 2000)
np.savez_compressed(SP + "/T1_rd_motor.npz", P0=P0, P1=P1, desde=2000, b=np.array([b for _, b in hist]))
print("ok", P0.shape, f"{time.time() - t0:.0f}s", "b final", np.round(hist[-1][1], 3))
