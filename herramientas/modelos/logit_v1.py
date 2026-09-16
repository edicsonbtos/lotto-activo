"""Logit condicional (softmax sobre los 38 candidatos, pesos compartidos) por MLE + L2.

Features por candidato (todas causales: fila t usa seq[:t] y el calendario del sorteo t):
  * one-hot del retraso exacto g=1..G1 y tramos después
  * veces que salió hoy, si salió hoy, jugados hoy x salió hoy, retraso x jugados hoy
  * conteos en ventanas 12/24/38/76/152 (centrados)
  * penúltimo retraso (tramos), salió ayer
Reajuste periódico cada `R` sorteos con datos[:T] (ventana creciente, peso temporal opcional).
"""
import numpy as np
from scipy.optimize import minimize

K = 38


def construir(datos, cfg):
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); n = len(seq)
    oh = np.zeros((n, K), np.float32); oh[np.arange(n), seq] = 1
    C = np.vstack([np.zeros((1, K), np.float32), np.cumsum(oh, axis=0)])  # C[t] = conteos en seq[:t]
    # inicio del día de cada t y del día anterior
    ini = np.zeros(n, int); ini_prev = np.zeros(n, int)
    s = 0; sp = 0
    for t in range(1, n):
        if dia[t] != dia[t - 1]:
            sp = s; s = t
        ini[t] = s; ini_prev[t] = sp
    # último y penúltimo índice de aparición antes de t
    G = np.empty((n, K), np.int32); G2 = np.empty((n, K), np.int32)
    last = np.full(K, -100000); prev = np.full(K, -100000)
    for t in range(n):
        G[t] = t - last; G2[t] = last - prev
        v = seq[t]; prev[v] = last[v]; last[v] = t
    G = np.minimum(G, 999); G2 = np.minimum(G2, 999)
    k = (np.arange(n) - ini)[:, None]                      # jugados hoy
    hoy = C[np.arange(n)] - C[ini]
    ayer = C[ini] - C[ini_prev]
    cols = []; nombres = []
    G1 = cfg.get("G1", 30)
    for g in range(1, G1 + 1):
        cols.append(G == g); nombres.append(f"g={g}")
    tr = cfg.get("tramos", [31, 41, 61, 101, 999])
    for a, b in zip(tr[:-1], tr[1:]):
        cols.append((G >= a) & (G < b)); nombres.append(f"g{a}-{b-1}")
    cols.append(G >= tr[-1]); nombres.append(f"g>={tr[-1]}")
    salio = (hoy > 0)
    kk = np.broadcast_to(k, (n, K))
    if cfg.get("hoy", True):
        cols += [salio, hoy, salio * kk / 11.0, (G <= 12) * (~salio)]
        nombres += ["salio_hoy", "veces_hoy", "salio_hoy*k", "g<=12_no_hoy"]
    if cfg.get("gxk", True):
        # retraso (tramos cortos) x jugados hoy
        for a, b in [(1, 4), (4, 8), (8, 13), (13, 21)]:
            cols.append(((G >= a) & (G < b)) * kk / 11.0); nombres.append(f"g{a}-{b-1}*k")
    for w in cfg.get("ventanas", [12, 24, 38, 76, 152]):
        lo = np.maximum(np.arange(n) - w, 0)
        cnt = C[np.arange(n)] - C[lo]
        cols.append(cnt - w / K); nombres.append(f"cnt{w}")
    if cfg.get("penult", True):
        for a, b in [(1, 4), (4, 13), (13, 30)]:
            cols.append((G2 >= a) & (G2 < b)); nombres.append(f"g2_{a}-{b-1}")
    if cfg.get("ayer", True):
        cols.append(ayer > 0); nombres.append("salio_ayer")
    F = np.stack([np.asarray(c, np.float32) for c in cols], axis=2)
    return F, nombres


def ajustar(F, y, lam, w=None, x0=None):
    N, _, d = F.shape
    X = np.ascontiguousarray(F.reshape(N * K, d), dtype=np.float32)
    Fy = F[np.arange(N), y].astype(np.float64)
    if w is None:
        w = np.ones(N)
    W = w.sum()
    Fyw = (Fy * w[:, None]).sum(0) / W

    def f(beta):
        z = (X @ beta.astype(np.float32)).reshape(N, K).astype(np.float64)
        m = z.max(axis=1, keepdims=True)
        ez = np.exp(z - m); S = ez.sum(axis=1, keepdims=True)
        lse = (m + np.log(S))[:, 0]
        P = ez / S
        nll = (w * lse).sum() / W - Fyw @ beta
        g = (((P * (w / W)[:, None]).astype(np.float32).reshape(-1)) @ X).astype(np.float64) - Fyw
        return nll + 0.5 * lam * beta @ beta, g + lam * beta

    r = minimize(f, np.zeros(d) if x0 is None else x0, jac=True, method="L-BFGS-B",
                 options={"maxiter": 300})
    return r.x


class Modelo:
    nombre = "logit_v1"

    def __init__(self, R=500, lam=1e-4, inicio=200, tau=None, ventana=None, **cfg):
        self.R = R; self.lam = lam; self.inicio = inicio; self.tau = tau; self.ventana = ventana
        self.cfg = cfg

    def predecir(self, datos, desde):
        F, self.nombres = construir(datos, self.cfg)
        seq = np.asarray(datos.seq); n = len(seq)
        out = np.empty((n - desde, K))
        beta = None
        for T in range(desde, n, self.R):
            a = self.inicio if self.ventana is None else max(self.inicio, T - self.ventana)
            idx = np.arange(a, T)
            w = None if self.tau is None else np.exp(-(T - 1 - idx) / self.tau)
            beta = ajustar(F[idx], seq[idx], self.lam, w, beta)
            b = min(T + self.R, n)
            z = F[T:b].astype(np.float64) @ beta
            z -= z.max(axis=1, keepdims=True)
            p = np.exp(z)
            out[T - desde:b - desde] = p / p.sum(axis=1, keepdims=True)
        self.beta = beta
        return out
