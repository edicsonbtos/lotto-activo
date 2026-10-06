# -*- coding: utf-8 -*-
"""M6: corrección multiplicativa p ∝ PROD·exp(Σβ·x). β en AJUSTE (congelada) y walk-forward mensual."""
import sys, os, json, numpy as np
from scipy.optimize import minimize
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
z = np.load(os.path.join(A.SP, "m6_rasgos.npz")); nom = list(z["nom"]); Mall = z["M"]
LP = np.log(A.PROD); y = A.Y; n = len(y)

def X_de(lista): return np.stack([Mall[nom.index(r)] for r in lista]).astype(np.float32)

def ajustar(X, filas, lam=2.0):
    Xs = X[:, filas]; lp = LP[filas]; yy = y[filas]; xy = Xs[:, np.arange(len(filas)), yy]
    def f(b):
        L = lp + np.tensordot(b, Xs, 1); L -= L.max(1, keepdims=True); E = np.exp(L); S = E.sum(1)
        p = E / S[:, None]; ll = (L[np.arange(len(yy)), yy] - np.log(S)).sum()
        g = xy.sum(1) - np.einsum("knj,nj->k", Xs, p)
        return -ll + lam * (b @ b), -g + 2 * lam * b
    return minimize(f, np.zeros(X.shape[0]), jac=True, method="L-BFGS-B").x

def aplicar(X, B):  # B: (n, k) β por fila
    L = LP + np.einsum("nk,knj->nj", B, X); P = np.exp(L - L.max(1, keepdims=True)); return P / P.sum(1, keepdims=True)

def walk_forward(X, lam=2.0, ventana=None):
    meses = np.array([f[:7] for f in A.F]); B = np.zeros((n, X.shape[0]))
    for mes in sorted(set(meses)):
        prev = np.where(meses < mes)[0]
        if ventana: prev = prev[A.F[prev] >= f"{int(mes[:4]) - (1 if int(mes[5:]) <= ventana // 30 else 0)}"] if False else prev[-ventana:]
        if len(prev) < 1000: continue
        B[meses == mes] = ajustar(X, prev, lam)
    return B

VAR = {
 "V1_conf": ["RD1:igual", "par_evita"],
 "V2_conf+z": ["RD1:igual", "par_evita", "z:dia-1", "z:dia", "z:dia+1", "z:dia+2", "z:hora12"],
 "V3_explor": ["RD1:igual", "par_evita", "z:dia-1", "z:dia", "z:dia+1", "z:dia+2", "z:hora12", "RD2:igual",
               "L1:columna", "L1:sumadig", "L1:ultdig", "L1:rueda1", "trans_cero", "trans_baja"],
}
if __name__ == "__main__":
    aj = np.where(A.TRAMOS["AJUSTE"])[0]; out = {}
    for v, lista in VAR.items():
        X = X_de(lista)
        b = ajustar(X, aj); print(v, "β AJUSTE:", {r: round(float(np.exp(x)), 3) for r, x in zip(lista, b)})
        Pc = aplicar(X, np.tile(b, (n, 1)))
        A.evaluar(Pc, v + "_congelada")
        for ven in (None, 4000):
            B = walk_forward(X, ventana=ven); Pw = aplicar(X, B)
            A.evaluar(Pw, f"{v}_wf{'' if ven is None else '_v' + str(ven)}")
            np.save(os.path.join(A.SP, f"m6_{v}_wf{'' if ven is None else ven}.npy"), Pw.astype(np.float32))
