# -*- coding: utf-8 -*-
"""M1: detector en línea de "modo relajado" (filtro bayesiano por día). Ver PREREGISTRO.md.
Uso: python m1.py ajustar   -> ajusta V0..V3 + VC (constante) en AJUSTE, guarda params en params.json
     python m1.py elegir    -> evalúa en AJUSTE/ELECCION, log-lineal w, validaciones, calibración por hora
     python m1.py fuga      -> chequear_fuga
     python m1.py prueba    -> PRUEBA26 (una vez, con lo congelado en final.json)
"""
import sys, os, json, time
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
import arnes as A  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
D = A.D
FECHA_D = np.array(D.fecha)
T = A.T; PROD = A.PROD; F = A.F; n = len(T)
LP = np.log(np.clip(PROD, 1e-12, None))
# índices de día para filas evaluables
dias = sorted(set(F)); di = {d: k for k, d in enumerate(dias)}; ND = len(dias)
DN = np.array([di[x] for x in F])
from datetime import date  # noqa: E402
WD = np.array([date.fromisoformat(d).weekday() for d in dias])
ORD = np.array([date.fromisoformat(d).toordinal() for d in dias])
# primera fila de cada día y posición dentro del día
primera = np.r_[True, DN[1:] != DN[:-1]]


def mascara_hoy(seq):
    """M[i, a] = 1 si el animal a ya salió hoy antes del sorteo T[i] (usa seq[:T[i]] del mismo día)."""
    seq = np.asarray(seq)
    M = np.zeros((n, 38), bool)
    for k, t in enumerate(T):
        j = t - 1; f = FECHA_D[t]
        while j >= 0 and FECHA_D[j] == f:
            M[k, seq[j]] = True; j -= 1
    return M


def sig(x): return 1 / (1 + np.exp(-x))
def logit(p): p = np.clip(p, 1e-4, 1 - 1e-4); return np.log(p / (1 - p))


NOMBRES = ["rho", "tau_l", "u_l", "kap_l", "a0", "a1", "a2", "hs_l", "hr_l"]
INI = np.array([1.0, 1.5, -2.0, -0.5, -1.0, 1.0, 1.0, np.log(4.0), np.log(7.0)])


def decodificar(th):
    rho, tl, ul, kl, a0, a1, a2, hsl, hrl = th
    return dict(r=float(np.exp(rho)), tau=float(sig(tl)), u=float(sig(ul)), kap=float(np.exp(kl)), a0=float(a0),
                a1=float(a1), a2=float(a2), hs=float(np.exp(hsl)), hr=float(np.exp(hrl)))


def motor(seq, th, var, M=None, detalle=False):
    """Devuelve P (n,38). var en {'V0','V1','V2','V3','VC'}. Walk-forward: la fila i usa seq[:T[i]] y PROD[:i+1]."""
    seq = np.asarray(seq); y = seq[T]
    if M is None: M = mascara_hoy(seq)
    p = decodificar(th)
    PB = np.exp(p["tau"] * LP); PB /= PB.sum(1, keepdims=True)
    PB = (1 - p["u"]) * PB + p["u"] / 38
    PB = PB * np.where(M, p["r"], 1.0); PR = PB / PB.sum(1, keepdims=True)
    llr = np.log(PR[np.arange(n), y]) - LP[np.arange(n), y]
    # acumulado de llr de hoy ANTES de cada fila
    cs = np.cumsum(llr); ini = np.where(primera)[0]
    base = np.repeat(cs[ini] - llr[ini], np.diff(np.r_[ini, n]))
    antes = cs - llr - base                      # suma de llr de filas anteriores del mismo día
    LLRd = np.bincount(DN, llr, ND)              # día completo (solo se usa para días ya pasados)
    ev = sig(p["kap"] * LLRd)
    a1 = p["a1"] if var in ("V2", "V3") else 0.0
    a2 = p["a2"] if var in ("V1", "V3") else 0.0
    ls = 0.5 ** (1 / p["hs"]); lr = 0.5 ** (1 / p["hr"])
    Sw = np.zeros(7); Ww = np.zeros(7); Sr = 0.0; Wr = 0.0; G = 0.3; NG = 1.0
    pri = np.zeros(ND); msem = np.zeros(ND); mrec = np.zeros(ND)
    prev_ord = None
    for d in range(ND):
        if prev_ord is not None:
            gap = ORD[d] - prev_ord
            Sr *= lr ** (gap - 1); Wr *= lr ** (gap - 1)
        mg = G / NG
        w = WD[d]
        ms = (Sw[w] + 1.0 * mg) / (Ww[w] + 1.0)
        mr = (Sr + 1.0 * mg) / (Wr + 1.0)
        msem[d] = ms; mrec[d] = mr
        pri[d] = sig(p["a0"] + a1 * logit(ms) + a2 * logit(mr))
        # actualizar memorias con la evidencia del día d (se usa a partir del día d+1)
        e = ev[d]
        # olvido por semanas en el mismo día de la semana
        Sw[w] = ls * Sw[w] + e; Ww[w] = ls * Ww[w] + 1
        Sr = lr * Sr + e; Wr = lr * Wr + 1
        G += e; NG += 1; prev_ord = ORD[d]
    if var == "VC":
        q = np.full(n, sig(p["a0"]))
    else:
        q = sig(logit(pri[DN]) + p["kap"] * antes)
    P = (1 - q)[:, None] * PROD + q[:, None] * PR
    if detalle:
        return P, dict(q=q, pri=pri, ev=ev, LLRd=LLRd, msem=msem, mrec=mrec, PR=PR, llr=llr, M=M)
    return P


def perdida(th, var, M, m):
    P = motor(D.seq, th, var, M)
    y = A.Y[m]
    return -np.log2(P[m][np.arange(m.sum()), y] * 38).mean()


def ajustar(vars_=("VC", "V0", "V1", "V2", "V3")):
    M = mascara_hoy(D.seq); m = A.TRAMOS["AJUSTE"]
    res = {}
    for var in vars_:
        t0 = time.time(); th = INI.copy()
        r = minimize(perdida, th, args=(var, M, m), method="Powell", options=dict(maxiter=6000, xtol=1e-3, ftol=1e-6))
        r = minimize(perdida, r.x, args=(var, M, m), method="Nelder-Mead", options=dict(maxiter=3000, xatol=1e-3, fatol=1e-7))
        res[var] = dict(th=r.x.tolist(), mbits=-1000 * r.fun, **decodificar(r.x))
        print(var, f"{time.time()-t0:.0f}s", json.dumps({k: round(v, 3) if isinstance(v, float) else v for k, v in res[var].items() if k != "th"}), flush=True)
        json.dump(res[var], open(os.path.join(AQUI, f"params_{var}.json"), "w"), indent=1)


if __name__ == "__main__":
    if sys.argv[1] == "ajustar": ajustar(sys.argv[2:] or ("VC", "V0", "V1", "V2", "V3"))
    else: globals()[sys.argv[1]]()
