"""Hazard suavizado como logit condicional (walk-forward, reajuste periodico).

score(i, t) = f(g) + a[S] + b[D] + sum_w c_w[n_w]
  g  : sorteos desde la ultima aparicion (exacto 1..40, 40 = 40+), curva suave
       por penalizacion de 2a diferencia (spline discreto).
  S  : veces que ya salio hoy (0, 1, 2+).
  D  : dias desde la ultima aparicion (0..7+), suavizado.
  n_w: apariciones en ventanas de dias anteriores [1-3], [4-14], [15-30], [31-60]
       (one-hot con penalizacion de suavidad).
P(i) = softmax(score). Ajuste por maxima verosimilitud penalizada con pesos
exponenciales en el tiempo (vida media 4000 sorteos, ventana max. 6000),
reajustado cada 500 sorteos usando SOLO sorteos anteriores al bloque.
"""
import numpy as np
from scipy.optimize import minimize

K = 38


def _features(seq, dia, gmax, dmax, wins):
    n = len(seq)
    G = np.empty((n, K), np.int64); D = np.empty((n, K), np.int64); S = np.empty((n, K), np.int64)
    last = np.full(K, -10**6); lastday = np.full(K, -10**6); cnt = np.zeros(K, np.int64); cur = None
    for t in range(n):
        if dia[t] != cur:
            cnt[:] = 0; cur = dia[t]
        G[t] = t - last; D[t] = dia[t] - lastday; S[t] = cnt
        v = seq[t]; last[v] = t; lastday[v] = dia[t]; cnt[v] += 1
    ud = dia - dia[0]; nd = int(ud.max()) + 1
    DC = np.zeros((nd + 1, K), np.int64); np.add.at(DC, (ud, seq), 1)
    CUM = np.vstack([np.zeros((1, K), np.int64), np.cumsum(DC, 0)])
    blocks = []; pen = []; off = 0
    blocks.append(np.minimum(G, gmax) - 1); pen.append((0, gmax)); off = gmax
    blocks.append(np.minimum(S, 2) + off); off += 3
    blocks.append(np.minimum(D, dmax) + off); pen.append((off + 1, dmax)); off += dmax + 1
    for (a, b, cap) in wins:          # dias ud-b .. ud-a (todos anteriores a hoy)
        hi = np.maximum(ud - a + 1, 0); lo = np.maximum(ud - b, 0)
        c = CUM[hi] - CUM[lo]
        blocks.append(np.minimum(c, cap) + off); pen.append((off, cap + 1)); off += cap + 1
    return np.stack(blocks, -1), off, pen


def _fit(X, yy, nf, pen, lam, w, theta0, maxiter):
    T = X.shape[0]; rows = np.arange(T); ws = w / w.sum()
    flat = [X[:, :, j].ravel() for j in range(X.shape[2])]

    def f(th):
        s = th[X].sum(-1)
        m = s.max(1, keepdims=True); e = np.exp(s - m); Z = e.sum(1, keepdims=True); p = e / Z
        ll = s[rows, yy] - m[:, 0] - np.log(Z[:, 0])
        L = -(ws * ll).sum()
        gp = ws[:, None] * p; gp[rows, yy] -= ws
        gr = gp.ravel(); grad = np.zeros(nf)
        for fl in flat:
            grad += np.bincount(fl, gr, nf)
        for (a, n) in pen:
            v = th[a:a + n]; d2 = v[2:] - 2 * v[1:-1] + v[:-2]
            L += lam * (d2 ** 2).sum()
            gg = np.zeros(n); gg[2:] += 2 * d2; gg[1:-1] -= 4 * d2; gg[:-2] += 2 * d2
            grad[a:a + n] += lam * gg
        L += 1e-4 * (th ** 2).sum(); grad += 2e-4 * th
        return L, grad

    return minimize(f, theta0, jac=True, method="L-BFGS-B", options={"maxiter": maxiter}).x


class Modelo:
    nombre = "haz_v1 (logit hazard suave g+S+D+ventanas)"

    def __init__(self, gmax=40, dmax=7, wins=((1, 3, 4), (4, 14, 8), (15, 30, 14), (31, 60, 16)),
                 lam=0.01, vida_media=4000, ventana=6000, cada=500, inicio=800, maxiter=300):
        self.gmax = gmax; self.dmax = dmax; self.wins = wins; self.lam = lam
        self.hl = vida_media; self.mw = ventana; self.R = cada; self.start = inicio; self.maxiter = maxiter

    def predecir(self, datos, desde):
        seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); n = len(seq)
        X, nf, pen = _features(seq, dia, self.gmax, self.dmax, self.wins)
        out = np.empty((n - desde, K)); th = np.zeros(nf)
        for b in range(desde, n, self.R):
            e = min(b + self.R, n)
            lo = max(self.start, b - self.mw)
            if b - lo >= 200:
                idx = np.arange(lo, b)
                w = 0.5 ** ((b - idx) / self.hl)
                th = _fit(X[idx], seq[idx], nf, pen, self.lam, w, th, self.maxiter)
            s = th[X[b:e]].sum(-1)
            p = np.exp(s - s.max(1, keepdims=True))
            out[b - desde:e - desde] = p / p.sum(1, keepdims=True)
        return out
