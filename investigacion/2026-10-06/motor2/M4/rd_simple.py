# Control adversarial: ¿cuánto da solo un multiplicador log-lineal de RD (h-1), (h-2) sobre PROD, ajustado en AJUSTE?
import sys, numpy as np
from scipy.optimize import minimize
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
import arnes as A
z = np.load(A.SP + "/m4_rasgos.npz"); nm = list(z["nm"]); X = z["X"][A.T]
R1 = np.nan_to_num(X[:, :, nm.index("rd1")]); R2 = np.nan_to_num(X[:, :, nm.index("rd2")])
L = np.log(A.PROD)
def P(b):
    s = L + b[0] * R1 + b[1] * R2; s -= s.max(1, keepdims=True); e = np.exp(s); return e / e.sum(1, keepdims=True)
i = np.where(A.TRAMOS["AJUSTE"])[0]
f = lambda b: -np.log(P(b)[i, A.Y[i]]).mean()
b = minimize(f, [0, 0], method="Nelder-Mead").x
print("multiplicadores RD h-1, h-2:", np.round(np.exp(b), 3))
Q = P(b); np.savez(A.SP + "/m4_rdsimple.npz", P=Q)
A.evaluar(Q, "RD-simple")
