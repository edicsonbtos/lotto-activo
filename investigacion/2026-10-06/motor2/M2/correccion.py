# -*- coding: utf-8 -*-
"""M2: corrección multiplicativa sobre PROD para los patrones confirmados (todos de día de la semana) + control EXPO.
logit_i = tau_clase * log PROD_i + sum_k beta_k * cat_k ; clase = lun-mar / mié-vie / sáb-dom. Penalización L2 (prec. 5)."""
import numpy as np, sys, time
from scipy.optimize import minimize
import comun as C
n, K = C.n, 38
CL = np.where(np.isin(C.DOW, [2, 3, 4]), 1, np.where(C.DOW >= 5, 2, 0))
LP = np.log(np.clip(C.PROD, 1e-12, None))
H0 = (C.H == 0)[:, None]
FE1 = C.FECHA & ~H0; FE0 = C.FECHA & H0

def diseno(var):
    """lista de máscaras (n,38) y si hay tau por clase."""
    X, nom = [], []
    if var in ("V1", "V2", "V4"):
        for c in range(3):
            q = (CL == c)[:, None]
            X += [C.HOY & q, C.AYAA & q]; nom += [f"hoy_c{c}", f"ayaa_c{c}"]
    if var in ("V3", "V4"):
        X += [FE1, FE0, C.HORA12]; nom += ["fecha", "fecha8", "hora12"]
    return (np.stack(X, -1).astype(np.float32) if X else np.zeros((n, K, 0), np.float32)), nom, var in ("V2", "V4")

def logits(th, X, tau, rows):
    p = X.shape[-1]; b = th[:p]
    z = LP[rows] * (th[p:][CL[rows]][:, None] if tau else 1.0) + X[rows] @ b
    return z

def ajustar(X, tau, rows, w, lam=2.5, th0=None):
    p = X.shape[-1]; npar = p + (3 if tau else 0)
    if npar == 0: return np.zeros(0)
    Xr = X[rows]; LPr = LP[rows]; yr = C.Y[rows]; cl = CL[rows]; ar = np.arange(len(rows))
    def f(th):
        t = th[p:][cl][:, None] if tau else 1.0
        z = LPr * t + Xr @ th[:p]; z -= z.max(1, keepdims=True)
        ez = np.exp(z); Z = ez.sum(1); pr = ez / Z[:, None]
        ll = (z[ar, yr] - np.log(Z)); g = np.zeros(npar)
        R = -pr; R[ar, yr] += 1                                  # d ll / d z
        g[:p] = np.einsum("i,ik,ikp->p", w, R, Xr)
        if tau:
            gt = w * (R * LPr).sum(1); g[p:] = np.bincount(cl, gt, 3)
        pen = th[:p] @ th[:p] + (((th[p:] - 1) ** 2).sum() if tau else 0)
        gp = np.r_[2 * th[:p], 2 * (th[p:] - 1)] if tau else 2 * th[:p]
        return -(w @ ll) + lam * pen, -g + lam * gp
    x0 = th0 if th0 is not None else np.r_[np.zeros(p), np.ones(3 if tau else 0)]
    return minimize(f, x0, jac=True, method="L-BFGS-B").x

def predecir(th, X, tau, rows):
    if len(th) == 0: return C.PROD[rows]
    z = logits(th, X, tau, rows); z -= z.max(1, keepdims=True); e = np.exp(z); return e / e.sum(1, keepdims=True)

def walk_forward(var, Hd, paso=7):
    """Re-ajuste cada `paso` días con filas de días ESTRICTAMENTE anteriores; peso 0,5^(edad/Hd)."""
    X, nom, tau = diseno(var); P = C.PROD.copy(); dia = C.DIA[C.T]; th = None
    d0 = dia.min(); cortes = np.arange(d0 + 28, dia.max() + paso, paso)
    for a in cortes:
        rows = np.where((dia >= a) & (dia < a + paso))[0]
        if not len(rows): continue
        tr = np.where(dia < a)[0]
        if Hd is not None: tr = tr[dia[tr] >= a - 4 * Hd]
        w = np.ones(len(tr)) if Hd is None else 0.5 ** ((a - dia[tr]) / Hd)
        th = ajustar(X, tau, tr, w, th0=th)
        P[rows] = predecir(th, X, tau, rows)
    return P, nom, th
