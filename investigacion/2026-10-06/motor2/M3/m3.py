# -*- coding: utf-8 -*-
"""M3: modelo generativo del operador (logit condicional, 38 alternativas) con β dinámicos.

β_d = argmax Σ_{t en días < d} 0,5^{(d-día_t)/vm} log P(y_t | x_t; β) - ridge/2 |β_base|² - λ/2 |δ_dow|²
Se reajusta cada día (inicio en caliente + pasos de Newton con gradiente exacto y Hessiano acumulado con olvido).
Los rasgos de cada fila usan solo sorteos anteriores; β del día d usa solo días anteriores.
"""
import numpy as np
from datetime import date, timedelta

POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}
K = 38
TRAMOS_HUECO = [(1, 3), (4, 12), (13, 24), (25, 36), (61, 90), (91, 130), (131, 200), (201, 10 ** 9)]  # ref 37-60
DOWFEAT = ["hoy", "d1", "d2", "d3"]


def construir(seq, hora, fecha):
    """X (N, 38, p) float64, nombres, índice de columnas dow, dia (int), dow."""
    seq = np.asarray(seq); hora = np.asarray(hora); N = len(seq)
    fechas = [date.fromisoformat(x) for x in fecha]
    d0 = fechas[0]
    dia = np.array([(x - d0).days for x in fechas]); dow = np.array([x.weekday() for x in fechas])
    base = ["hoy", "ant1"] + [f"d{k}" for k in range(1, 8)] + [f"gap{a}-{b}" for a, b in TRAMOS_HUECO] + \
           ["prim1", "prim2", "prim3", "fecha", "fecha+1", "fecha-1", "hora12", "vent8", "mismahora", "f7", "f30", "hoy_x_av"]
    nb = len(base); col = {n: i for i, n in enumerate(base)}
    p = nb + len(DOWFEAT) * 7
    X = np.zeros((N, K, p))
    last = np.full(K, -10 ** 9)
    por_dia = {}      # dia -> lista de animales (en orden)
    hora_dia = {}     # (dia, hora) -> animal
    hoyset = np.zeros(K); nhoy = 0; dcur = None
    cnt_dia = {}      # dia -> vector de cuentas
    for t in range(N):
        d = dia[t]
        if d != dcur:
            dcur = d; hoyset = np.zeros(K); nhoy = 0
        x = X[t]
        x[:, col["hoy"]] = hoyset > 0
        x[:, col["hoy_x_av"]] = (hoyset > 0) * (nhoy / 12.0)
        if t > 0:
            x[seq[t - 1], col["ant1"]] = 1
        for k in range(1, 8):
            if d - k in por_dia:
                x[por_dia[d - k], col[f"d{k}"]] = 1
        g = t - last
        for a, b in TRAMOS_HUECO:
            x[:, col[f"gap{a}-{b}"]] = (g >= a) & (g <= b)
        first = nhoy == 0
        if first:
            for k in (1, 2, 3):
                if d - k in por_dia:
                    x[por_dia[d - k][0], col[f"prim{k}"]] = 1
        f = fechas[t]
        dom = f.day; ma = (f + timedelta(days=1)).day; ay = (f - timedelta(days=1)).day
        x[IDX[str(dom)], col["fecha"]] = 1; x[IDX[str(ma)], col["fecha+1"]] = 1; x[IDX[str(ay)], col["fecha-1"]] = 1
        h12 = (8 + int(hora[t]) - 1) % 12 + 1
        x[IDX[str(h12)], col["hora12"]] = 1
        if first:
            for v in (dom, ma, ay):
                x[IDX[str(v)], col["vent8"]] = 1
        if (d - 1, int(hora[t])) in hora_dia:
            x[hora_dia[(d - 1, int(hora[t]))], col["mismahora"]] = 1
        c7 = np.zeros(K); c30 = np.zeros(K)
        for k in range(1, 31):
            if d - k in cnt_dia:
                c30 += cnt_dia[d - k]
                if k <= 7: c7 += cnt_dia[d - k]
        for c, nm in ((c7, "f7"), (c30, "f30")):
            m = c.mean(); x[:, col[nm]] = (c - m) / np.sqrt(m + 1.0)
        # columnas por día de la semana (desviación δ_dow)
        for j, fn in enumerate(DOWFEAT):
            x[:, nb + j * 7 + dow[t]] = x[:, col[fn]]
        # actualizar estado con el resultado del sorteo t (solo para filas posteriores)
        a = seq[t]; last[a] = t; hoyset[a] += 1; nhoy += 1
        por_dia.setdefault(d, []).append(a); hora_dia[(d, int(hora[t]))] = a
        cnt_dia.setdefault(d, np.zeros(K))[a] += 1
    nombres = base + [f"{fn}@{w}" for fn in DOWFEAT for w in range(7)]
    return X, nombres, nb, dia, dow


def _grad_hess(Xw, yw, ww, beta, hess=True):
    T_, A_, p_ = Xw.shape; Xf = Xw.reshape(T_ * A_, p_)
    s = (Xf @ beta).reshape(T_, A_); s -= s.max(1, keepdims=True); e = np.exp(s); P = e / e.sum(1, keepdims=True)
    R = -P * ww[:, None]; R[np.arange(len(yw)), yw] += ww
    g = Xf.T @ R.ravel()
    ll = (ww * np.log(P[np.arange(len(yw)), yw])).sum()
    if not hess:
        return g, ll, None
    PW = P * ww[:, None]
    H = (Xf * PW.reshape(-1, 1)).T @ Xf
    xb = np.einsum("tap,ta->tp", Xw, P)
    H -= (xb * ww[:, None]).T @ xb
    return g, ll, H


def walk_forward(X, y, dia, nb, vm, lam, ridge=1.0, fila_ini=2000, fila_entreno=300, hasta=None,
                 iters=2, trunc=6.0, guardar_beta=True):
    """Devuelve P (filas fila_ini..hasta-1, 38) y la trayectoria de β (por día)."""
    N = len(y) if hasta is None else hasta
    p = X.shape[2]
    pen = np.full(p, ridge); pen[nb:] = (0.0 if not np.isfinite(lam) else lam)
    usa_dow = np.isfinite(lam)
    if not usa_dow:
        pen[nb:] = 1e9   # δ_dow = 0 en la práctica
    # rangos por día
    cambios = np.r_[0, np.where(np.diff(dia[:N]) != 0)[0] + 1, N]
    ini_dias = cambios[:-1]; fin_dias = cambios[1:]
    P = np.zeros((N - fila_ini, K)); betas = []; dias_b = []
    beta = np.zeros(p); H = None; d_H = None
    for j in range(len(ini_dias)):
        a0, a1 = ini_dias[j], fin_dias[j]
        if a1 <= fila_ini:
            continue
        dd = dia[a0]
        lo_dia = dd - trunc * vm
        lo = max(fila_entreno, int(np.searchsorted(dia[:a0], lo_dia, side="left")))
        Xw = X[lo:a0]; yw = y[lo:a0]; ww = 0.5 ** ((dd - dia[lo:a0]) / vm)
        if H is None:
            for _ in range(30):   # ajuste inicial completo
                g, ll, Hc = _grad_hess(Xw, yw, ww, beta)
                g -= pen * beta; Hc = Hc + np.diag(pen)
                step = np.linalg.solve(Hc, g); beta = beta + step
                if np.abs(step).max() < 1e-6: break
            H = Hc - np.diag(pen); d_H = dd
        else:
            # Hessiano acumulado con olvido: añadir los días nuevos (entre el último añadido y hoy)
            H = H * 0.5 ** ((dd - d_H) / vm)
            nuevos = np.arange(ult_fin, a0)
            if len(nuevos):
                _, _, Hn = _grad_hess(X[nuevos], y[nuevos], 0.5 ** ((dd - dia[nuevos]) / vm), beta)
                H += Hn
            d_H = dd
            Hp = H + np.diag(pen)
            for _ in range(iters):
                g, ll, _ = _grad_hess(Xw, yw, ww, beta, hess=False)
                g -= pen * beta
                beta = beta + np.linalg.solve(Hp, g)
        ult_fin = a0
        s = X[a0:a1] @ beta; s -= s.max(1, keepdims=True); e = np.exp(s)
        lo_p = max(a0, fila_ini)
        P[lo_p - fila_ini:a1 - fila_ini] = (e / e.sum(1, keepdims=True))[lo_p - a0:]
        if guardar_beta:
            betas.append(beta.copy()); dias_b.append(dd)
    return P, np.array(betas), np.array(dias_b)
