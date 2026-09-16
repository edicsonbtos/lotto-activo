"""Familia no-estacionariedad: logit condicional con filtro de Kalman extendido (Newton online
de matriz completa) con factor de olvido lambda, y mezcla bayesiana online de aprendices con
distinta memoria.

P(x_t=i) ∝ exp(x_{t,i}·w).  Objetivo de cada aprendiz en t:
    J_t(w) = sum_s lambda^(t-s) loglik_s(w) - 1/2 w' P w      (P: ridge + suavizado en cadenas)
Aproximación recursiva: A <- lambda A + (1-lambda) P + Fisher_t ; w <- w + A^-1 (grad_t - (1-lambda) P w).
Mezcla: peso_L ∝ exp(sum_s rho^(t-s) log p_L(x_s)).
Causal: la fila t solo usa seq[:t] y el calendario del propio sorteo t.
"""
import numpy as np
import scipy.linalg as _sl

K = 38


def estado(datos):
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); n = len(seq); ar = np.arange(n)
    nuevo = np.r_[True, dia[1:] != dia[:-1]]
    didx = np.cumsum(nuevo) - 1
    ini = np.maximum.accumulate(np.where(nuevo, ar, 0))
    G = np.empty((n, K), np.int64); G2 = np.empty((n, K), np.int64)
    DD = np.empty((n, K), np.int64); HOY = np.empty((n, K), np.int64)
    last = np.full(K, -10**7); prev = np.full(K, -10**7); lastd = np.full(K, -10**7); cnt = np.zeros(K, np.int64)
    for t in range(n):
        if nuevo[t]:
            cnt[:] = 0
        G[t] = t - last; G2[t] = last - prev; DD[t] = didx[t] - lastd; HOY[t] = cnt
        v = seq[t]; prev[v] = last[v]; last[v] = t; lastd[v] = didx[t]; cnt[v] += 1
    oh = np.zeros((n, K)); oh[ar, seq] = 1
    C = np.vstack([np.zeros((1, K)), np.cumsum(oh, axis=0)])
    return seq, ar, nuevo, didx, ini, ar - ini, G, G2, DD, HOY, C


def cat_orden(V, edges):
    return np.clip(np.searchsorted(np.array(edges), V, side="right") - 1, 0, len(edges) - 1)


def construir(datos, cfg):
    seq, ar, nuevo, didx, ini, kk, G, G2, DD, HOY, C = estado(datos)
    n = len(seq)
    k = np.broadcast_to(np.minimum(kk, 11)[:, None], (n, K))
    salio = HOY > 0
    tabs = []   # (idx, size, chains)
    ge = list(range(1, cfg.get("G1", 40) + 1)) + [41, 51, 61, 81, 101, 151, 10**6]
    gi = cat_orden(G, ge)
    tabs.append((gi, len(ge), [list(range(len(ge) - 1))]))
    hi = np.where(salio, 1 + (k - 1) * 2 + (HOY >= 2), 0)
    tabs.append((hi, 1 + 24, [[1 + 2 * j for j in range(1, 12)], [2 + 2 * j for j in range(1, 12)]]))
    dm = cfg.get("ddmax", 3)
    di = np.where(~salio & (DD <= dm), 1 + (np.minimum(DD, dm) - 1) * 12 + k, 0)
    cad = [[1 + d * 12 + j for j in range(12)] for d in range(dm)]
    tabs.append((di, 1 + dm * 12, cad))
    if cfg.get("g2", True):
        e2 = list(range(1, 31)) + [31, 46, 61, 91, 10**6]
        v = (G2 > 0) & (G2 < 10**6)
        tabs.append((np.where(v, 1 + cat_orden(G2, e2), 0), 1 + len(e2), [list(range(1, len(e2)))]))
    if cfg.get("cuota", True):
        # candidatos que salieron ayer (y no hoy): cuántos de ayer ya salieron hoy x grupo de k
        inis = np.r_[np.flatnonzero(nuevo), n]
        p0 = didx - 1; ok = p0 >= 0
        a0 = inis[np.maximum(p0, 0)]; a1 = inis[np.maximum(p0, 0) + 1]
        dset = ((C[a1] - C[a0]) > 0) & ok[:, None]
        cn = (dset & salio).sum(1)
        kg = np.array([0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3])[k]
        cm = 5
        ci = np.where(dset & ~salio, 1 + np.minimum(cn, cm)[:, None] * 4 + kg, 0)
        tabs.append((ci, 1 + (cm + 1) * 4, [[1 + c * 4 + g for c in range(cm + 1)] for g in range(4)]))
    dens = []
    for wv in cfg.get("ventanas", [12, 38, 152]):
        if wv == 0:      # acumulado desde el inicio
            ef = np.maximum(ar, 1) / K
            dens.append((C[ar] - ef[:, None]) / np.sqrt(ef)[:, None])
            continue
        lo = np.maximum(ar - wv, 0); ef = np.maximum(ar - lo, 1) / K
        dens.append((C[ar] - C[lo] - ef[:, None]) / np.sqrt(ef)[:, None])
    Dc = sum(t[1] for t in tabs); m = len(dens); D = Dc + m
    Pen = np.zeros((D, D)); off = 0; F = []
    s = cfg.get("s", 30.0)
    for idx, sz, chains in tabs:
        for ch in chains:
            for a, b in zip(ch[:-1], ch[1:]):
                a += off; b += off
                Pen[a, a] += s; Pen[b, b] += s; Pen[a, b] -= s; Pen[b, a] -= s
        F.append(idx + off); off += sz
    Pen += cfg.get("ridge", 1.0) * np.eye(D)
    F = np.stack(F, axis=2).astype(np.int64)
    Xd = np.stack(dens, axis=2) if m else np.zeros((n, K, 0))
    return F, Xd, Dc, Pen


class Modelo:
    nombre = "tiempo_v3 (logit EKF con olvido + BMA)"

    def __init__(self, lambdas=(0.9998, 0.9993, 0.998), rho=0.999, cada=1, devolver_todo=False, **cfg):
        self.lambdas = np.array(lambdas, float); self.rho = rho; self.cada = cada
        self.cfg = cfg; self.devolver_todo = devolver_todo

    def predecir(self, datos, desde):
        seq = np.asarray(datos.seq); n = len(seq)
        F, Xd, Dc, Pen = construir(datos, self.cfg)
        D = Pen.shape[0]; L = len(self.lambdas)
        lam = self.lambdas[:, None, None]; lam1 = self.lambdas[:, None]
        w = np.zeros((L, D)); A = np.broadcast_to(Pen, (L, D, D)).copy()
        S = np.zeros(L); T = F.shape[2]; nd = Xd.shape[2]
        offL = (np.arange(L) * D * D)[:, None]; offD = (np.arange(L) * D)[:, None]
        out = np.empty((n - desde, K)); todo = np.empty((n - desde, L, K)) if self.devolver_todo else None
        dia = np.asarray(datos.dia)
        cortes = np.r_[0, np.flatnonzero(dia[1:] != dia[:-1]) + 1, n]
        for a0, a1 in zip(cortes[:-1], cortes[1:]):
            m = a1 - a0
            X = np.zeros((m, K, D))
            X[np.arange(m)[:, None, None], np.arange(K)[None, :, None], F[a0:a1]] = 1.0
            X[:, :, Dc:] = Xd[a0:a1]
            sc = np.einsum("ld,mkd->lmk", w, X)
            sc -= sc.max(axis=2, keepdims=True)
            p = np.exp(sc); p /= p.sum(axis=2, keepdims=True)       # (L,m,K)
            y = seq[a0:a1]
            lp = np.log(p[:, np.arange(m), y])                        # (L,m)
            for j in range(m):
                t = a0 + j
                if t >= desde:
                    a = np.exp(S - S.max()); a /= a.sum()
                    out[t - desde] = a @ p[:, j]
                    if todo is not None:
                        todo[t - desde] = p[:, j]
                S = self.rho * S + lp[:, j]
            mu = np.einsum("lmk,mkd->lmd", p, X)                     # (L,m,D)
            g = X[np.arange(m), y].sum(0)[None] - mu.sum(1)
            Fr = F[a0:a1].reshape(m * K, T)                          # (R,T)
            pr = p.reshape(L, m * K)                                  # (L,R)
            pair = (Fr[:, :, None] * D + Fr[:, None, :]).reshape(1, -1) + offL  # (L, R*T*T)
            Fi = np.bincount(pair.ravel(), weights=np.repeat(pr, T * T, axis=1).ravel(),
                             minlength=L * D * D).reshape(L, D, D)
            if nd:
                Xdr = Xd[a0:a1].reshape(m * K, nd)
                pxd = pr[:, :, None] * Xdr[None]                       # (L,R,nd)
                for j in range(nd):
                    cj = np.bincount((Fr.reshape(1, -1) + offD).ravel(),
                                     weights=np.repeat(pxd[:, :, j], T, axis=1).ravel(),
                                     minlength=L * D).reshape(L, D)
                    Fi[:, :, Dc + j] += cj; Fi[:, Dc + j, :] += cj
                    Fi[:, Dc + j, Dc:] -= cj[:, Dc:]; Fi[:, Dc:, Dc + j] -= cj[:, Dc:]
                Fi[:, Dc:, Dc:] += np.einsum("lrj,rk->ljk", pxd, Xdr)
            Fi -= np.matmul(mu.transpose(0, 2, 1), mu)
            dec = lam ** m
            A = dec * A + (1 - dec) * Pen[None] + Fi
            rhs = g - (1 - lam1 ** m) * (w @ Pen)
            for l in range(L):
                w[l] += _sl.solve(A[l], rhs[l], assume_a="pos", check_finite=False)
        self.todo = todo; self.w = w; self.Dc = Dc
        return out
