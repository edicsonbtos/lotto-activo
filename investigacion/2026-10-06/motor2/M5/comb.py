"""M5: combinaciones de las bases de ensamble_v2 que se adaptan más rápido. Todo walk-forward (pesos de cada día
se ajustan con filas anteriores al primer sorteo del día; Hedge se actualiza tras cada sorteo)."""
import sys, os, numpy as np
from scipy.optimize import minimize
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
sys.path.insert(0, "/home/user/lotto-activo/herramientas/modelos"); import exposicion as EX
SP = A.SP; K = 38
z = np.load(os.path.join(SP, "M5_bases.npz")); a0 = int(z["desde"])
L = np.log(np.clip(z["L"], 1e-9, None)); L -= np.log(np.exp(L).sum(2, keepdims=True))   # (n-a0, M, K)
S = np.asarray(A.D.seq); Fd = np.array(A.D.fecha); Hd = np.asarray(A.D.hora); n = len(S)
y = S[a0:]; N, M, _ = L.shape
T0 = int(A.T[0]); assert np.all(A.T == np.arange(T0, n))
SEM = 84  # sorteos por semana

# ---------- ajustes de PROD (misma lógica que prediccion.py / calib.py) como multiplicadores por fila evaluada
def multiplicadores():
    ADJ = np.ones((n - T0, K)); primero = {}; vistos = set()
    from datetime import date, timedelta
    for t in range(n):
        if Fd[t] not in vistos:
            vistos.add(Fd[t])
            if t >= T0:
                m = np.ones(K); f0 = date.fromisoformat(Fd[t])
                for k, mult in {1: 0.272, 3: 1.736}.items():
                    x = primero.get((f0 - timedelta(days=k)).isoformat())
                    if x is not None and x[0] == int(Hd[t]): m[x[1]] *= mult
                if Hd[t] == 0: m = m * np.array(EX.aplicar_8am([1.0] * K, Fd[t], 0))
                ADJ[t - T0] = m
            primero[Fd[t]] = (int(Hd[t]), int(S[t]))
    return ADJ
ADJ = multiplicadores()
def ajustar(P):
    P = P * ADJ; return P / P.sum(1, keepdims=True)

def softmax_lin(Lr, w):
    zz = np.einsum("nmk,m->nk", Lr, w); zz -= zz.max(1, keepdims=True); p = np.exp(zz); return p / p.sum(1, keepdims=True)

def fit_w(Lr, yr, peso, prior, lam, w0, cota=(-0.5, 2.0)):
    Ly = Lr[np.arange(len(yr)), :, yr]
    def f(w):
        zz = np.einsum("nmk,m->nk", Lr, w); zm = zz.max(1, keepdims=True); e = np.exp(zz - zm); Ssum = e.sum(1); p = e / Ssum[:, None]
        nll = -(peso * (Ly @ w - np.log(Ssum) - zm[:, 0])).sum() + 0.5 * lam * np.sum((w - prior) ** 2)
        g = -(peso[:, None] * (Ly - np.einsum("nk,nmk->nm", p, Lr))).sum(0) + lam * (w - prior)
        return nll, g
    return minimize(f, w0, jac=True, method="L-BFGS-B", bounds=[cota] * len(w0), options={"maxiter": 100}).x

# ---------- reproducción de ensamble_v2 (R=250, tau=3000, lam=5) -> pesos globales walk-forward
def ensamble_v2():
    w = np.full(M, 1 / M); out = np.empty((n - T0, K)); W = np.empty((n - T0, M))
    for T in range(T0, n, 250):
        j = T - a0
        w = fit_w(L[:j], y[:j], np.exp(-(j - 1 - np.arange(j)) / 3000.0), np.full(M, 1 / M), 5.0, w)
        b = min(T + 250, n); out[T - T0:b - T0] = softmax_lin(L[T - a0:b - a0], w); W[T - T0:b - T0] = w
    return out, W

INI = np.r_[[t for t in range(T0, n) if t == T0 or Fd[t] != Fd[t - 1]], n]   # primeras filas de cada día (y fin)

def exp_diaria(hl_sem, lam, WG, grupo=None, kappa=None):
    """Pesos reajustados cada día con olvido exponencial (vida media hl_sem semanas), L2 hacia el peso global WG.
    grupo: vector por fila absoluta (dow u hora); entonces cada grupo tiene sus pesos con L2 kappa hacia los comunes."""
    hl = hl_sem * SEM; tau = hl / np.log(2); ven = int(8 * hl); out = np.empty((n - T0, K)); w = WG[0].copy(); wg = {}
    for s, e in zip(INI[:-1], INI[1:]):
        j = s - a0; i0 = max(0, j - ven); pe = np.exp(-(j - 1 - np.arange(i0, j)) / tau)
        prior = WG[s - T0]
        w = fit_w(L[i0:j], y[i0:j], pe, prior, lam, w)
        if grupo is None:
            out[s - T0:e - T0] = softmax_lin(L[s - a0:e - a0], w); continue
        for t in range(s, e):
            g = grupo[t]
            key = (s, g)
            if key not in wg:
                idx = np.arange(i0, j); sel = idx[grupo[a0 + idx] == g]
                pe2 = np.exp(-(j - 1 - sel) / tau)
                wg[key] = fit_w(L[sel], y[sel], pe2, w, kappa, w)
            out[t - T0] = softmax_lin(L[t - a0:t - a0 + 1], wg[key])[0]
    return out

def hedge(EXP, eta, alpha, geom=False):
    """Fixed-share sobre expertos EXP (n_filas_abs, E, K) de probabilidades; actualiza tras cada sorteo."""
    E = EXP.shape[1]; pi = np.full(E, 1 / E); out = np.empty((n - T0, K)); lE = np.log(np.clip(EXP, 1e-12, None))
    for t in range(n - T0):
        if geom:
            zz = pi @ lE[t]; p = np.exp(zz - zz.max()); out[t] = p / p.sum()
        else:
            out[t] = pi @ EXP[t]
        pi = pi * EXP[t, :, A.Y[t]] ** eta; pi /= pi.sum(); pi = (1 - alpha) * pi + alpha / E
    return out

def temp_din(Q, hl_sem, cota=(0.5, 1.5)):
    """p ∝ Q^τ con τ ajustada cada día sobre el pasado reciente (olvido exponencial) de las propias Q."""
    hl = hl_sem * SEM; tau = hl / np.log(2); ven = int(8 * hl); lQ = np.log(np.clip(Q, 1e-12, None)); out = np.empty_like(Q)
    from scipy.optimize import minimize_scalar
    ly = lQ[np.arange(len(Q)), A.Y]; tt = 1.0
    for s, e in zip(INI[:-1], INI[1:]):
        j = s - T0; i0 = max(0, j - ven)
        if j - i0 >= 100:
            pe = np.exp(-(j - 1 - np.arange(i0, j)) / tau); lq = lQ[i0:j]; lyy = ly[i0:j]
            def f(x):
                zz = x * lq; zm = zz.max(1); return -(pe * (x * lyy - zm - np.log(np.exp(zz - zm[:, None]).sum(1)))).sum()
            tt = minimize_scalar(f, bounds=cota, method="bounded").x
        zz = tt * lQ[j:e - T0]; zz -= zz.max(1, keepdims=True); p = np.exp(zz); out[j:e - T0] = p / p.sum(1, keepdims=True)
    return out
