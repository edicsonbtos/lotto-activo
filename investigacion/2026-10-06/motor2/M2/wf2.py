"""Robustez: V1 con 7 clases (una por día de la semana, sin usar la elección MVF que vino de mirar 2026) y mezcla w."""
import numpy as np, comun as C, correccion as R, io, contextlib
A = C.A
def ev(P, nom):
    f = io.StringIO()
    with contextlib.redirect_stdout(f): r = A.evaluar(P, nom)
    return " | ".join(f"{x['tramo']} Δ {x['dmbits_vs_prod']:+.2f} [{x['ic90'][0]:+.2f};{x['ic90'][1]:+.2f}] T5 {x['top5']}/{x['top5_prod']} T15 {x['top15']}/{x['top15_prod']}" for x in r)
CL3 = R.CL.copy()
R.CL = C.DOW.copy()                    # 7 clases
def diseno7(var):
    X, nom = [], []
    for c in range(7):
        q = (R.CL == c)[:, None]; X += [C.HOY & q, C.AYAA & q]; nom += [f"hoy_d{c}", f"ayaa_d{c}"]
    return np.stack(X, -1).astype(np.float32), nom, False
R.diseno = diseno7
res = {}
for Hd in (60, 120):
    P, nom, th = R.walk_forward("V1d", Hd); res[Hd] = P
    print(f"V1d H={Hd}: {ev(P, 'x')}", flush=True)
z = np.load(A.SP + "/m2_wf_variantes.npz")
for k in ("V1_H60", "V1_H120"):
    Q = z[k]
    for w in (0.5, 0.75, 1.0, 1.25):
        M = np.exp((1 - w) * np.log(C.PROD) + w * np.log(Q)); M /= M.sum(1, keepdims=True)
        print(f"{k} w={w}: {ev(M, 'x')}")
np.savez_compressed(A.SP + "/m2_wf_v1d.npz", H60=res[60], H120=res[120])
