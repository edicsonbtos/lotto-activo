import numpy as np
from comb import *
O = np.load(os.path.join(SP, "M5_otras.npz")); X = np.load(os.path.join(SP, "M5_exp.npz"))
Q = ajustar(O["DOW_hl2_k20"])
for w in (0.25, 0.5, 0.75):
    P = np.exp((1 - w) * np.log(A.PROD) + w * np.log(Q)); A.evaluar(P / P.sum(1, keepdims=True), f"mezcla_DOWhl2k20_w{w}")
# estabilidad: Δ por mes (AJUSTE+ELECCION) de la elegida y de EXP_hl2_lam20
yy = A.Y; m = A.TRAMOS["AJUSTE"] | A.TRAMOS["ELECCION"]
for nom, P in (("DOW_hl2_k20", Q), ("EXP_hl2_lam20", ajustar(X["EXP_hl2_lam20"]))):
    d = 1000 * np.log2(P[np.arange(len(yy)), yy] / A.PROD[np.arange(len(yy)), yy]); mes = np.array([f[:7] for f in A.F])
    print(nom, " ".join(f"{u[2:]}:{d[m & (mes == u)].mean():+.1f}" for u in np.unique(mes[m])))
    print("   por día (lun..dom) ELECCION:", " ".join(f"{d[A.TRAMOS['ELECCION'] & (A.DOW == k)].mean():+.1f}" for k in range(7)))
