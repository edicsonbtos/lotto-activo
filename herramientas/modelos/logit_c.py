"""Logit condicional (softmax sobre los 38 candidatos, pesos compartidos) por MLE + L2.

Todas las features son causales: la fila t usa seq[:t] y el calendario (dia/hora) del
propio sorteo t, conocido de antemano.

Features por candidato (cada bloque se activa en cfg):
  tablas one-hot (una categoría de referencia implícita por tabla, fijada a 0):
    gap      retraso exacto g=1..G1, tramos después, "nunca"
    hoy      si salió hoy: (k jugados hoy 1..11) x (veces hoy 1 / 2+)
    dias     si NO salió hoy: (días desde su última salida 1,2,3,4+) x (grupo de k)
    ayerpos  si NO salió hoy y salió ayer: hora de esa salida
  densas:
    cnt_w    conteos en ventanas w (z-score bajo azar)
    g2       penúltimo retraso (tramos)
    gxk      tramos cortos de g x (k/11)
Reajuste cada R sorteos con datos[:T] (ventana creciente o deslizante, peso exp. opcional).
Los ajustes se memorizan por huella de (config, seq[:T], dia[:T]): función pura del
pasado, así que no hay fuga; solo acelera la prueba de fuga (4 llamadas a predecir).
"""
import hashlib
import numpy as np
from scipy.optimize import minimize

K = 38
_CACHE = {}


def _estado(datos):
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia)
    n = len(seq); ar = np.arange(n)
    oh = np.zeros((n, K), np.float32); oh[ar, seq] = 1
    C = np.vstack([np.zeros((1, K), np.float32), np.cumsum(oh, axis=0)])
    nuevo = np.r_[True, dia[1:] != dia[:-1]]
    didx = np.cumsum(nuevo) - 1                      # índice de día consecutivo (0,1,2..)
    ini = np.maximum.accumulate(np.where(nuevo, ar, 0))
    k = ar - ini                                      # sorteos ya jugados hoy
    G = np.empty((n, K), np.int32); G2 = np.empty((n, K), np.int32)
    DD = np.empty((n, K), np.int32); HL = np.empty((n, K), np.int32)
    last = np.full(K, -100000); prev = np.full(K, -100000)
    lastd = np.full(K, -100000); lasth = np.zeros(K, np.int32)
    for t in range(n):
        G[t] = t - last; G2[t] = last - prev
        DD[t] = didx[t] - lastd; HL[t] = lasth
        v = seq[t]; prev[v] = last[v]; last[v] = t; lastd[v] = didx[t]; lasth[v] = k[t]
    G = np.minimum(G, 100000); G2 = np.minimum(G2, 100000); DD = np.minimum(DD, 100000)
    hoy = (C[ar] - C[ini]).astype(np.int32)
    return dict(n=n, ar=ar, C=C, k=k, G=G, G2=G2, DD=DD, HL=HL, hoy=hoy)


def construir(datos, cfg):
    s = _estado(datos)
    n, ar, C, k, G, G2, DD, HL, hoy = (s[x] for x in ("n", "ar", "C", "k", "G", "G2", "DD", "HL", "hoy"))
    kk = np.broadcast_to(k[:, None], (n, K))
    salio = hoy > 0
    tablas = []                                       # (nombre, idx (n,K) int32, tamaño); idx 0 = referencia

    G1 = cfg.get("G1", 30); tramos = cfg.get("tramos", [31, 41, 61, 101, 100000])
    gb = np.where(G <= G1, G, 0)
    nb = G1 + 1
    for a, b in zip(tramos[:-1], tramos[1:]):
        gb = np.where((G >= a) & (G < b), nb, gb); nb += 1
    gb = np.where(G >= tramos[-1], nb, gb); nb += 1
    ref = cfg.get("gref", 12)                         # g=12 ~ azar
    gb = np.where(gb == ref, 0, gb)
    tablas.append(("gap", gb.astype(np.int32), nb))

    if cfg.get("hoy", True):
        vh = np.minimum(hoy, 2)
        idx = np.where(salio, (np.minimum(kk, 11) - 1) * 2 + vh, 0)
        tablas.append(("hoy[k,veces]", idx.astype(np.int32), 23))
    if cfg.get("dias", True):
        kg = np.array(cfg.get("kgrupos", [0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]))[np.minimum(kk, 11)]
        ng = int(kg.max()) + 1
        dm = cfg.get("ddmax", 4)
        dd = np.minimum(DD, dm) - 1
        idx = np.where(~salio & (DD <= dm), dd * ng + kg + 1, 0)
        tablas.append(("dias[dd,kg]", idx.astype(np.int32), dm * ng + 1))
    if cfg.get("ayerpos", False):
        idx = np.where(~salio & (DD == 1), np.minimum(HL, 11) + 1, 0)
        tablas.append(("ayerpos[h]", idx.astype(np.int32), 13))

    cols = []; nombres = []
    for w in cfg.get("ventanas", [12, 24, 38, 76, 152]):
        lo = np.maximum(ar - w, 0)
        cols.append((C[ar] - C[lo] - w / K) / np.sqrt(w / K)); nombres.append(f"cnt{w}")
    if cfg.get("g2", True):
        for a, b in [(1, 4), (4, 13), (13, 30)]:
            cols.append((G2 >= a) & (G2 < b)); nombres.append(f"g2_{a}-{b-1}")
    if cfg.get("gxk", False):
        for a, b in [(13, 21), (21, 30)]:
            cols.append(((G >= a) & (G < b)) * kk / 11.0); nombres.append(f"g{a}-{b-1}*k")
    D = (np.stack([np.asarray(np.broadcast_to(c, (n, K)), np.float32) for c in cols], axis=2)
         if cols else np.zeros((n, K, 0), np.float32))
    return tablas, D, nombres


def denso(tablas, D):
    """Tablas one-hot (sin la columna de referencia 0) + densas -> (n, K, d) float32."""
    n = D.shape[0]
    cols = []
    for _, ix, sz in tablas:
        oh = np.zeros((n, K, sz), np.float32)
        np.put_along_axis(oh, ix[:, :, None], 1.0, axis=2)
        cols.append(oh[:, :, 1:])
    return np.concatenate(cols + [D], axis=2)


def ajustar(X, y, wts, lam, b0=None, iters=12, tol=1e-7):
    """MLE + L2 por Newton (Hessiano exacto del softmax condicional)."""
    N, _, d = X.shape
    Xf = X.reshape(-1, d)
    wn = (wts / wts.sum())
    Xy = (X[np.arange(N), y].astype(np.float64) * wn[:, None]).sum(0)
    b = np.zeros(d) if b0 is None else b0.copy()
    prev = np.inf
    for _ in range(iters):
        z = (Xf @ b.astype(np.float32)).reshape(N, K).astype(np.float64)
        z -= z.max(1, keepdims=True); e = np.exp(z); S = e.sum(1, keepdims=True); p = e / S
        nll = -(wn * (z[np.arange(N), y] - np.log(S[:, 0]))).sum() + 0.5 * lam * b @ b
        pw = p * wn[:, None]
        g = (pw.astype(np.float32).reshape(-1) @ Xf).astype(np.float64) - Xy + lam * b
        if np.abs(g).max() < tol:
            break
        M = np.einsum("nk,nkd->nd", p.astype(np.float32), X).astype(np.float64)
        Hs = ((Xf * pw.astype(np.float32).reshape(-1, 1)).T @ Xf).astype(np.float64)             - (M * wn[:, None]).T @ M + lam * np.eye(d)
        step = np.linalg.solve(Hs, g)
        b = b - step
        prev = nll
    return b


class Modelo:
    nombre = "logit_c"

    def __init__(self, R=500, lam=3e-5, inicio=200, tau=None, ventana=None, **cfg):
        self.R = R; self.lam = lam; self.inicio = inicio; self.tau = tau; self.ventana = ventana
        self.cfg = cfg

    def predecir(self, datos, desde):
        seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); n = len(seq)
        tablas, D, nd = construir(datos, self.cfg)
        X = denso(tablas, D); del D
        h = hashlib.sha1(repr((type(self).__name__, self.R, self.lam, self.inicio, self.tau, self.ventana,
                               sorted((a, repr(b)) for a, b in self.cfg.items()))).encode())
        out = np.empty((n - desde, K)); beta = None; pos = 0
        for T in range(desde, n, self.R):
            h.update(seq[pos:T].tobytes()); h.update(dia[pos:T].tobytes()); pos = T
            clave = h.copy().hexdigest()
            if clave in _CACHE:
                beta = _CACHE[clave]
            else:
                a = self.inicio if self.ventana is None else max(self.inicio, T - self.ventana)
                wts = np.ones(T - a) if self.tau is None else np.exp(-(T - 1 - np.arange(a, T)) / self.tau)
                beta = ajustar(X[a:T], seq[a:T], wts, self.lam, beta)
                _CACHE[clave] = beta
            b = min(T + self.R, n)
            z = (X[T:b].reshape(-1, X.shape[2]) @ beta.astype(np.float32)).reshape(b - T, K).astype(np.float64)
            z -= z.max(axis=1, keepdims=True)
            p = np.exp(z)
            out[T - desde:b - desde] = p / p.sum(axis=1, keepdims=True)
        self.beta = beta
        self.nombres = [f"{nm}[{i}]" for nm, _, sz in tablas for i in range(1, sz)] + nd
        return out
