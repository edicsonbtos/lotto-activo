# -*- coding: utf-8 -*-
"""S2: rasgos nuevos (todo walk-forward) que se añaden a los de M4 (sin RD).

nuevos(seq, hora, dia, fecha) -> (X_nuevo (n, 38, f) float32, nombres, info) donde info trae la etiqueta blanda de
modo relajado por sorteo (etq_dia, solo válida para días ya terminados; se usa SOLO para entrenar con días pasados).
"""
import numpy as np
from datetime import date, timedelta
from sklearn.linear_model import LogisticRegression

K = 38
NUM = np.array([0, -1] + list(range(1, 37)))
PRIOR_R = 0.2


def _p_rep(j, rho):
    return rho * j / (rho * j + K - j)


def esperanza_reps(rho, k=12):
    """E[repeticiones] en k sorteos con peso rho de repetir (DP sobre nº de distintos)."""
    pj = np.zeros(k + 1); pj[0] = 1.0; er = 0.0
    for t in range(k):
        nuevo = np.zeros(k + 1)
        for j in range(t + 1):
            if pj[j] == 0: continue
            pr = _p_rep(j, rho) if j > 0 else 0.0
            er += pj[j] * pr; nuevo[j] += pj[j] * pr; nuevo[j + 1] += pj[j] * (1 - pr)
        pj = nuevo
    return er


def calibrar_rho(seq, dia, fecha, desde="2025-07-01", hasta="2025-12-31"):
    reps = []
    for d in np.unique(dia):
        ii = np.where(dia == d)[0]
        if len(ii) == 12 and desde <= fecha[ii[0]] <= hasta:
            reps.append(12 - len(set(seq[ii])))
    m = np.mean(reps); lo, hi = 0.01, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if esperanza_reps(mid) < m: lo = mid
        else: hi = mid
    return (lo + hi) / 2, m


def llr_secuencia(animales, rho):
    """log L(relajado)/L(normal) de una secuencia del día (en orden)."""
    vis = set(); s = 0.0
    for a in animales:
        j = len(vis)
        if j > 0:
            if a in vis:
                s += np.log(_p_rep(j, 1.0)) - np.log(_p_rep(j, rho))
            else:
                s += np.log(1 - _p_rep(j, 1.0)) - np.log(1 - _p_rep(j, rho))
        vis.add(a)
    return s


def nuevos(seq, hora, dia, fecha, rho=None):
    seq = np.asarray(seq); hora = np.asarray(hora); dia = np.asarray(dia); n = len(seq)
    if rho is None:
        rho, _ = calibrar_rho(seq, dia, fecha)
    dias = np.unique(dia); pos = {d: i for i, d in enumerate(dias)}
    ini_dia = {}; fin_dia = {}
    for i in range(n):
        ini_dia.setdefault(int(dia[i]), i); fin_dia[int(dia[i])] = i
    fdia = {int(dia[i]): fecha[i] for i in range(n)}
    # --- etiqueta blanda por día (con el día COMPLETO; solo para días pasados)
    lp = np.log(PRIOR_R / (1 - PRIOR_R))
    etq = {}
    for d in dias:
        a = seq[ini_dia[d]:fin_dia[d] + 1]
        etq[int(d)] = 1 / (1 + np.exp(-(lp + llr_secuencia(list(a), rho))))
    # --- rasgos del prior (por día, con días anteriores): medias con olvido en este dow y en todos los días
    dl = sorted(int(d) for d in dias)
    ew_dow = {}; ew_all = {}; ew_dow13 = {}
    for d in dl:
        prev = [x for x in dl if x < d and d - x <= 400]
        if not prev:
            ew_dow[d] = ew_all[d] = ew_dow13[d] = np.nan; continue
        pv = np.array(prev); e = np.array([etq[x] for x in prev])
        w = 0.5 ** ((d - pv) / 7.0); ew_all[d] = (w * e).sum() / w.sum()
        same = (d - pv) % 7 == 0
        if same.any():
            ws = 0.5 ** ((d - pv[same]) / 28.0); ew_dow[d] = (ws * e[same]).sum() / ws.sum()
            ws = 0.5 ** ((d - pv[same]) / 91.0); ew_dow13[d] = (ws * e[same]).sum() / ws.sum()
        else:
            ew_dow[d] = ew_dow13[d] = np.nan
    # --- q_prior: logística walk-forward por mes (entrena con días < día 1 del mes)
    def zf(d):
        v = [ew_dow[d], ew_all[d], ew_dow13[d]]
        v = [PRIOR_R if not np.isfinite(x) else x for x in v]
        return np.log(np.clip(v, 1e-3, 1 - 1e-3) / (1 - np.clip(v, 1e-3, 1 - 1e-3)))
    qpri = {}
    meses = sorted(set(fdia[d][:7] for d in dl))
    for mes in meses:
        dm = [d for d in dl if fdia[d][:7] == mes]
        tr = [d for d in dl if fdia[d] < mes + "-01" and np.isfinite(ew_all[d])]
        if len(tr) < 60:
            for d in dm: qpri[d] = PRIOR_R
            continue
        Xt = np.array([zf(d) for d in tr]); yt = np.array([etq[d] for d in tr])
        Xd = np.vstack([Xt, Xt]); yd = np.r_[np.ones(len(tr)), np.zeros(len(tr))]
        edad = np.array([(dm[0] - d) for d in tr], float); wt = 0.5 ** (edad / 180.0)
        wd = np.r_[yt * wt, (1 - yt) * wt]
        lr = LogisticRegression(C=1.0).fit(Xd, yd, sample_weight=wd)
        pr = lr.predict_proba(np.array([zf(d) for d in dm]))[:, 1]
        for d, p in zip(dm, pr): qpri[d] = float(p)
    # --- por sorteo
    nm = ["num_fecha_m1", "evita_cnt", "loglift_hoy", "q_prior", "q_post", "llr_hoy"]
    X = np.zeros((n, K, len(nm)), np.float32)
    etq_s = np.zeros(n)
    # par_evita: lift de pares en el mismo día, 365 días previos al mes
    Mdia = np.zeros((len(dias), K), bool)
    for i in range(n): Mdia[pos[int(dia[i])], seq[i]] = True
    fd_arr = np.array([fdia[int(d)] for d in dias])
    off = ~np.eye(K, dtype=bool)
    lift_mes = {}
    for mes in meses:
        ini = mes + "-01"; d0 = (date.fromisoformat(ini) - timedelta(days=365)).isoformat()
        sel = (fd_arr >= d0) & (fd_arr < ini)
        if sel.sum() < 60:
            lift_mes[mes] = None; continue
        Xm = Mdia[sel].astype(float); N = Xm.shape[0]
        C = Xm.T @ Xm; na = Xm.sum(0); E = np.outer(na, na) / N
        lift = (C + 5) / (E + 5); lo = np.quantile(lift[off], 0.1)
        LL = np.log(lift); np.fill_diagonal(LL, 0.0)
        lift_mes[mes] = (LL, (lift <= lo) & off)
    for i in range(n):
        d = int(dia[i]); dt = date.fromisoformat(fecha[i])
        X[i, :, 0] = NUM == dt.day - 1
        hoy = list(seq[ini_dia[d]:i])
        lm = lift_mes[fecha[i][:7]]
        if hoy and lm is not None:
            LL, EV = lm
            X[i, :, 1] = EV[hoy].sum(0)
            X[i, :, 2] = LL[hoy].mean(0)  # media de log-lift con los de hoy (diagonal = 0)
        qp = qpri[d]; llr = llr_secuencia(hoy, rho) if hoy else 0.0
        X[i, :, 3] = qp
        X[i, :, 4] = 1 / (1 + np.exp(-(np.log(qp / (1 - qp)) + llr)))
        X[i, :, 5] = llr
        etq_s[i] = etq[d]
    return X, nm, dict(etq=etq_s, rho=rho, fin_dia=np.array([fin_dia[int(dia[i])] for i in range(n)]))
