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


NOMBRES = ["r", "tau", "u", "kap", "a0", "a1", "a2", "hs", "hr"]
# Cotas (2.ª ronda): la 1.ª ronda sin cotas degeneró (r→0 = "más estricto" en vez de relajado, a1→7·10^5 = umbral duro).
# r ≥ 1 y τ ≤ 1 ya estaban en el pre-registro; a1, a2 ≥ 0 (la memoria empuja en el sentido de la evidencia) y vidas medias acotadas.
LO = np.array([1.0, 0.3, 0.0, 0.05, -6.0, 0.0, 0.0, 0.5, 1.0])
HI = np.array([6.0, 1.0, 0.5, 3.0, 4.0, 3.0, 3.0, 26.0, 60.0])
INI = np.zeros(9)


def decodificar(th):
    x = LO + (HI - LO) * sig(np.asarray(th, float))
    return dict(zip(NOMBRES, map(float, x)))


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


# ----------------------------------------------------------------------------------------------- evaluación
DSEM = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def cargar(var):
    return np.array(json.load(open(os.path.join(AQUI, f"params_{var}.json")))["th"])


def dmb_por(P, m, grupos):
    y = A.Y; v = 1000 * np.log2(P[np.arange(n), y] / PROD[np.arange(n), y])
    out = []
    for g in grupos:
        mm = m & g[1]
        if mm.sum() < 30: continue
        lo, hi = A._ic90(v[mm], mm)
        out.append(f"{g[0]}:{v[mm].mean():+.1f}[{lo:+.0f};{hi:+.0f}]")
    return " ".join(out)


def auc(s, l):
    from scipy.stats import rankdata
    l = l.astype(bool)
    if l.sum() == 0 or (~l).sum() == 0: return np.nan
    r = rankdata(s); return (r[l].sum() - l.sum() * (l.sum() + 1) / 2) / (l.sum() * (~l).sum())


def elegir():
    M = mascara_hoy(D.seq)
    Ps = {}
    for var in ("VC", "V0", "V1", "V2", "V3"):
        try: th = cargar(var)
        except FileNotFoundError: continue
        print(var, {k: round(v, 3) for k, v in decodificar(th).items()})
        Ps[var] = motor(D.seq, th, var, M)
        A.evaluar(Ps[var], f"M1-{var}")
    # día de la semana y mes en AJUSTE y ELECCION
    for var in Ps:
        for tr in ("AJUSTE", "ELECCION"):
            m = A.TRAMOS[tr]
            print(f"  {var} {tr} por día:", dmb_por(Ps[var], m, [(DSEM[k], A.DOW == k) for k in range(7)]))
        print(f"  {var} ELECCION por mes:", dmb_por(Ps[var], A.TRAMOS["ELECCION"], [(mm, np.char.startswith(F.astype(str), mm)) for mm in ("2026-03", "2026-04", "2026-05", "2026-06")]))
    me = max(Ps, key=lambda v: np.log2(Ps[v][A.TRAMOS["ELECCION"]][np.arange(A.TRAMOS["ELECCION"].sum()), A.Y[A.TRAMOS["ELECCION"]]]).mean())
    print("mejor variante en ELECCION:", me)
    for w in (0.25, 0.5, 0.75, 1.0, 1.25, 1.5):
        Q = PROD ** (1 - w) * Ps[me] ** w; Q /= Q.sum(1, keepdims=True)
        A.evaluar(Q, f"M1-{me} loglin w={w}")
    return Ps, me


def validar():
    M = mascara_hoy(D.seq)
    for var in ("V1", "V3", "V2", "V0"):
        th = cargar(var)
        P, X = motor(D.seq, th, var, M, detalle=True)
        print(f"== {var}: π medio y evidencia e_d media por día de la semana y periodo")
        for lab, a, b in (("2024-03..2024-06", "2024-03", "2024-06-31"), ("2024-07..2025-06 (ANTIGUO dom)", "2024-07", "2025-06-31"),
                          ("2025-07..2025-11", "2025-07", "2025-11-31"), ("2025-12..2026-02", "2025-12", "2026-02-31"),
                          ("2026-03..2026-06 (ELECCION)", "2026-03", "2026-06-31")):
            dd = np.array([(x >= a) and (x <= b) for x in dias])
            pm = [X["pri"][dd & (WD == k)].mean() for k in range(7)]
            em = [X["ev"][dd & (WD == k)].mean() for k in range(7)]
            orden = [DSEM[k] for k in np.argsort(pm)[::-1][:3]]; ordene = [DSEM[k] for k in np.argsort(em)[::-1][:3]]
            print(f"  {lab:32} π: " + " ".join(f"{DSEM[k]} {pm[k]:.2f}" for k in range(7)) + f"  top3 {orden}")
            print(f"  {'':32} e: " + " ".join(f"{DSEM[k]} {em[k]:.2f}" for k in range(7)) + f"  top3 {ordene}")


def horas():
    """¿A qué hora sabe? AUC/Brier de q_h contra el modo real a posteriori del día."""
    M = mascara_hoy(D.seq)
    for var in ("V3", "V1", "V0"):
        th = cargar(var); p = decodificar(th)
        P, X = motor(D.seq, th, var, M, detalle=True)
        lab = (X["LLRd"] > 0)[DN]                           # etiqueta a posteriori (prior plano, κ = 1)
        rep = np.bincount(DN, M[np.arange(n), A.Y], ND)     # repeticiones del día
        labr = (rep >= 2)[DN]
        print(f"== {var} (κ={p['kap']:.2f}) fracción de días 'relajados' a posteriori por periodo:",
              {tr: round(lab[A.TRAMOS[tr]].mean(), 3) for tr in ("ANTIGUO", "AJUSTE", "ELECCION")})
        for tr in ("AJUSTE", "ELECCION", "ANTIGUO"):
            m = A.TRAMOS[tr]
            fila = []
            for h in range(12):
                mm = m & (A.H == h)
                fila.append(f"{h+8}h:{auc(X['q'][mm], lab[mm]):.2f}/{auc(X['q'][mm], labr[mm]):.2f}")
            print(f"  {tr:8} AUC q_h (etiqueta LLR / ≥2 rep):", " ".join(fila))
            br = [np.mean((X['q'][m & (A.H == h)] - lab[m & (A.H == h)]) ** 2) for h in range(12)]
            print(f"  {tr:8} Brier:", " ".join(f"{b:.3f}" for b in br), f"(base {np.mean(lab[m])*(1-np.mean(lab[m])):.3f})")
        m = A.TRAMOS["AJUSTE"] | A.TRAMOS["ELECCION"]
        bins = [0, .1, .2, .3, .4, .5, .6, .8, 1.01]
        cal = []
        for a, b in zip(bins[:-1], bins[1:]):
            mm = m & (X["q"] >= a) & (X["q"] < b)
            if mm.sum(): cal.append(f"[{a:.1f},{b:.1f}) n={mm.sum()} q={X['q'][mm].mean():.2f} real={lab[mm].mean():.2f}")
        print("  calibración (AJUSTE+ELECCION):", " | ".join(cal))


def fuga():
    var = sys.argv[2] if len(sys.argv) > 2 else "V3"; th = cargar(var); pos = {t: k for k, t in enumerate(T)}

    def fn(S, hora, dow, fecha, i):
        return motor(S, th, var)[pos[i]]
    A.chequear_fuga(fn, cortes=(6000, 9000, 12000, 12743))
