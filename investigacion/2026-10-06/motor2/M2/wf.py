import numpy as np, comun as C, correccion as R, io, contextlib
A = C.A; SP = A.SP; out = {}
def ev(P, nom):
    f = io.StringIO()
    with contextlib.redirect_stdout(f): r = A.evaluar(P, nom)
    return r
for var in ("V1", "V2", "V3", "V4"):
    for Hd in (60, 120, None):
        P, nom, th = R.walk_forward(var, Hd); out[f"{var}_H{Hd}"] = P
        r = ev(P, f"{var}_H{Hd}")
        print(f"{var} H={Hd}: " + " | ".join(f"{x['tramo']} Δ {x['dmbits_vs_prod']:+.2f} {x['ic90']} T15 {x['top15']}/{x['top15_prod']}" for x in r), flush=True)
np.savez_compressed(SP + "/m2_wf_variantes.npz", **out)
