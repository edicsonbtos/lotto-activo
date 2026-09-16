"""Familia no-estacionariedad: logit condicional ONLINE con olvido exponencial.

P(x_t=i) ∝ exp(sum_tablas w[cat_tabla(i,t)])
Cada aprendiz L usa Newton diagonal online con Fisher descontado por lambda_L
(memoria efectiva 1/(1-lambda)).  Las predicciones de los aprendices se mezclan con
pesos bayesianos online (BMA con olvido): peso_L ∝ exp(eta * sum_descontada log p_L).
Todo es incremental: la fila t solo usa seq[:t] y el calendario del propio sorteo t.
"""
import numpy as np

K = 38


def features(datos):
    """Devuelve F (n, K, T) con índices globales de categoría, y D."""
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); n = len(seq)
    ar = np.arange(n)
    nuevo = np.r_[True, dia[1:] != dia[:-1]]
    didx = np.cumsum(nuevo) - 1
    ini = np.maximum.accumulate(np.where(nuevo, ar, 0))
    kk = ar - ini
    G = np.empty((n, K), np.int64); DD = np.empty((n, K), np.int64); HOY = np.empty((n, K), np.int64)
    last = np.full(K, -10**7); lastd = np.full(K, -10**7); cnt = np.zeros(K, np.int64)
    for t in range(n):
        if nuevo[t]:
            cnt[:] = 0
        G[t] = t - last; DD[t] = didx[t] - lastd; HOY[t] = cnt
        v = seq[t]; last[v] = t; lastd[v] = didx[t]; cnt[v] += 1
    k = np.minimum(kk, 11)[:, None] + np.zeros((1, K), np.int64)
    tabs = []
    # gap
    edges = list(range(1, 31)) + [31, 36, 41, 51, 61, 81, 121, 10**6]
    gcat = np.searchsorted(np.array(edges), G, side="right") - 1   # 0..len-1
    gcat = np.clip(gcat, 0, len(edges) - 1)
    tabs.append((gcat, len(edges)))
    # hoy: k x (1, 2+)
    hc = np.where(HOY > 0, 1 + k * 2 + (HOY >= 2), 0)
    tabs.append((hc, 1 + 24))
    # dias: dd in 1,2 x k
    dc = np.where((HOY == 0) & (DD >= 1) & (DD <= 2), 1 + (DD - 1) * 12 + k, 0)
    tabs.append((dc, 1 + 24))
    off = 0; F = []
    for c, m in tabs:
        F.append(c + off); off += m
    return np.stack(F, axis=2).astype(np.int64), off


class Modelo:
    nombre = "tiempo_v2 (logit online con olvido + BMA)"

    def __init__(self, lambdas=(1.0, 0.9995, 0.999, 0.998, 0.996, 0.993), kappas=(5.0, 20.0, 50.0), eta=1.0,
                 rho=0.9995, modo="bma", devolver_todo=False):
        ll, kk = np.meshgrid(np.array(lambdas, float), np.array(kappas, float), indexing="ij")
        self.lambdas = ll.ravel(); self.kappas = kk.ravel()[:, None]; self.eta = eta
        self.rho = rho; self.modo = modo; self.devolver_todo = devolver_todo

    def predecir(self, datos, desde):
        seq = np.asarray(datos.seq); n = len(seq)
        F, D = features(datos); T = F.shape[2]
        L = len(self.lambdas); lam = self.lambdas[:, None]
        w = np.zeros((L, D)); H = np.zeros((L, D))
        offL = (np.arange(L) * D)[:, None]
        S = np.zeros(L)   # log-verosimilitud descontada de cada aprendiz
        out = np.empty((n - desde, K)); todo = np.empty((n - desde, L, K)) if self.devolver_todo else None
        for t in range(n):
            f = F[t]                                  # (K, T)
            sc = w[:, f].sum(axis=2)                  # (L, K)
            sc -= sc.max(axis=1, keepdims=True)
            p = np.exp(sc); p /= p.sum(axis=1, keepdims=True)
            if t >= desde:
                if self.modo == "bma":
                    a = self.eta * S; a = np.exp(a - a.max()); a /= a.sum()
                    out[t - desde] = a @ p
                else:
                    out[t - desde] = p[int(self.modo)]
                if todo is not None:
                    todo[t - desde] = p
            y = seq[t]
            S = self.rho * S + np.log(p[:, y])
            idx = (f.ravel()[None, :] + offL).ravel()
            wt = np.repeat(p, T, axis=1).ravel()
            e = np.bincount(idx, weights=wt, minlength=L * D).reshape(L, D)
            fis = np.bincount(idx, weights=np.repeat(p * (1 - p), T, axis=1).ravel(), minlength=L * D).reshape(L, D)
            o = np.zeros((L, D)); o[:, f[y]] += 1
            H = lam * H + fis
            w += (o - e) / (H + self.kappas)
        self.todo = todo
        return out
