import numpy as np, time, itertools
from concurrent.futures import ProcessPoolExecutor
from comb import *
WG = np.load(os.path.join(SP, "M5_ens.npz"))["WG"]; E2 = np.load(os.path.join(SP, "M5_ens.npz"))["E2"]
EX_ = np.load(os.path.join(SP, "M5_exp.npz"))
DOWd = np.asarray(A.D.dow)
def run(c):
    tipo, hl, kap = c; g = DOWd if tipo == "DOW" else Hd
    return f"{tipo}_hl{hl}_k{kap}", exp_diaria(hl, 20, WG, grupo=g, kappa=kap)
if __name__ == "__main__":
    res = {}
    cfg = list(itertools.product(["DOW", "HORA"], [2, 8], [20, 100]))
    with ProcessPoolExecutor(4) as ex:
        for k, P in ex.map(run, cfg): res[k] = P; print(k, flush=True)
    # Hedge: expertos = 3 bases + ensamble_v2 (probabilidades)
    EXP = np.concatenate([np.exp(L[T0 - a0:]), E2[:, None, :]], 1)
    for eta, al, geo in itertools.product([0.5, 1, 2], [0.001, 0.01, 0.05], [False, True]):
        res[f"HEDGE_{'geo' if geo else 'mix'}_eta{eta}_a{al}"] = hedge(EXP, eta, al, geo)
    # Temperatura dinámica encima de ensamble_v2 y de EXP_hl2_lam20 (elegida en AJUSTE)
    for base, Q in (("E2", E2), ("EXPhl2", EX_["EXP_hl2_lam20"])):
        for hl in (2, 4, 8): res[f"TEMP_{base}_hl{hl}"] = temp_din(Q, hl)
    np.savez(os.path.join(SP, "M5_otras.npz"), **res)
    for k, P in res.items(): A.evaluar(ajustar(P), k)
