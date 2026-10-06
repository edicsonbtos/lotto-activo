import numpy as np, time, itertools, json
from concurrent.futures import ProcessPoolExecutor
from comb import *
WG = np.load(os.path.join(SP, "M5_ens.npz"))["WG"]
def run(c):
    hl, lam = c; t0 = time.time(); P = exp_diaria(hl, lam, WG); return c, P, time.time() - t0
if __name__ == "__main__":
    cfg = list(itertools.product([2, 4, 8, 16], [5, 20]))
    res = {}
    with ProcessPoolExecutor(4) as ex:
        for c, P, s in ex.map(run, cfg):
            res[f"EXP_hl{c[0]}_lam{c[1]}"] = P; print(c, round(s), "s", flush=True)
    np.savez(os.path.join(SP, "M5_exp.npz"), **res)
    for k, P in res.items(): A.evaluar(ajustar(P), k)
