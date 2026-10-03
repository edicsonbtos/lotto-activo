# Definición de los candidatos y ajuste del multiplicador (SOLO dev)
import numpy as np
from scipy.optimize import minimize_scalar
from comun import *

def conteo(t, cand):
    """vector (38,) con el nº de veces que cada animal cumple el rasgo para la fila t"""
    c = np.zeros(38); dd = int(DI[t])
    if cand == "C1_ultimos2dias":      # salió ayer (posición>=1) o anteayer (cualquier posición)
        for k, j0 in ((1, 1), (2, 0)):
            L = DIAS.get(dd - k)
            if L is None: continue
            for tt in L[j0:]: c[S[tt]] = 1          # indicador (sin repetición dentro del día)
    elif cand == "C2_pos3_14dias":     # nº de veces que salió en la posición j=3 en los días d-1..d-14
        for k in range(1, 15):
            a = ganador(dd - k, 3)
            if a is not None: c[a] += 1
    elif cand == "C3_k8_j6":            # ganador de la posición 6 de hace 8 días
        a = ganador(dd - 8, 6)
        if a is not None: c[a] = 1
    return c

def aplicar(t, logm, cand, base=PAJ):
    q = base[t] * np.exp(logm * conteo(t, cand)); return q / q.sum()

def ajustar(filas, cand, l2=1.0):
    C = np.array([conteo(t, cand) for t in filas]); B = PAJ[filas]; y = S[filas]
    def nll(lm):
        q = B * np.exp(lm * C); q /= q.sum(1, keepdims=True)
        return -np.log(q[np.arange(len(y)), y]).sum() + 0.5 * l2 * lm**2
    r = minimize_scalar(nll, bounds=(-3, 3), method="bounded"); return r.x

def stats_cand(filas, cand):
    C = np.array([conteo(t, cand) for t in filas]); B = PAJ[filas]; y = S[filas]
    O = C[np.arange(len(y)), y].sum(); E = (C * B).sum(); return O, E

CANDS = ["C1_ultimos2dias", "C2_pos3_14dias", "C3_k8_j6"]
