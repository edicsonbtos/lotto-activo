"""Paso 1: predicción walk-forward de cada submodelo de ensamble_v2 (desde la fila 1000, como el ensamble)."""
import sys, time, os, numpy as np
from concurrent.futures import ProcessPoolExecutor
SP = "/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad"
sys.path.insert(0, "/home/user/lotto-activo/herramientas")
import lotto_eval as LE
BASES = ["intradia_v2", "secuencia_v3", "haz_v1"]
def uno(b):
    D = LE.cargar(os.path.join(SP, "hist_0605.txt")); t0 = time.time()
    m = LE.cargar_modelo(f"/home/user/lotto-activo/herramientas/modelos/{b}.py")
    P = m.predecir(D, 1000); print(b, P.shape, round(time.time() - t0), "s", flush=True)
    return P
if __name__ == "__main__":
    with ProcessPoolExecutor(3) as ex: R = list(ex.map(uno, BASES))
    np.savez(os.path.join(SP, "M5_bases.npz"), L=np.stack(R, 1), desde=1000, nombres=np.array(BASES))
    print("ok")
