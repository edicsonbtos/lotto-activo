"""Logit condicional (softmax sobre 38 candidatos, pesos compartidos), MLE + L2 vía L-BFGS.

Representación eficiente: features categóricas como tablas one-hot (índice entero por
candidato) + features densas.  Todo causal: la fila t usa seq[:t] y el calendario de t.
Reajuste cada R sorteos con datos[:T]; memoización de ajustes por huella de datos[:T]
(función pura del pasado, así que no introduce fuga; solo acelera la prueba de fuga).
"""
import hashlib
import numpy as np
from scipy.optimize import minimize

K = 38
_CACHE = {}
self_nit = []


def _bins_gap(G, G1, tramos):
    b = np.where(G <= G1, G - 1, 0)
    nb = G1
    for a, c in zip(tramos[:-1], tramos[1:]):
        b = np.where((G >= a) & (G < c), nb, b); nb += 1
    b = np.where(G >= tramos[-1], nb, b); nb += 1
    return b.astype(np.int32), nb


def construir(datos, cfg):
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); hora = np.asarray(datos.hora)
    n = len(seq); ar = np.arange(n)
    oh = np.zeros((n, K), np.float32); oh[ar, seq] = 1
    C = np.vstack([np.zeros((1, K), np.float32), np.cumsum(oh, axis=0)])
    ini = np.zeros(n, int); ini_prev = np.zeros(n, int)
    s = 0; sp = 0
    for t in range(1, n):
        if dia[t] != dia[t - 1]:
            sp = s; s = t
        ini[t] = s; ini_prev[t] = sp
    G = np.empty((n, K), np.int32); G2 = np.empty((n, K), np.int32)
    last = np.full(K, -100000); prev = np.full(K, -100000)
    for t in range(n):
        G[t] = t - last; G2[t] = last - prev
        v = seq[t]; prev[v] = last[v]; last[v] = t
    G = np.minimum(G, 999); G2 = np.minimum(G2, 999)
    k = np.broadcast_to((ar - ini)[:, None], (n, K))
    hoy = C[ar] - C[ini]
    ayer = C[ini] - C[ini_prev]
    salio = hoy > 0

    tablas = []   # (nombre, indice (n,K) int32, tamaño)
    gb, nb = _bins_gap(G, cfg.get("G1", 30), cfg.get("tramos", [31, 41, 61, 101, 999]))
    if cfg.get("gap_x_hoy", False):
        tablas.append(("gap|no_hoy", np.where(salio, nb, gb).astype(np.int32), nb + 1))
    else:
        tablas.append(("gap", gb, nb))
    if cfg.get("tabla_hoy", False):
        # (jugados hoy k, veces hoy 0/1/2+) -> 12*3
        vh = np.minimum(hoy, 2).astype(np.int32)
        tablas.append(("k*veces_hoy", (np.minimum(k, 11) * 3 + vh).astype(np.int32), 36))
    if cfg.get("tabla_gk", False):
        # retraso de la salida de hoy (1..11) x jugados hoy k, solo si salió hoy
        gg = np.minimum(G, 11)
        idx = np.where(salio, (gg - 1) * 12 + np.minimum(k, 11) + 1, 0)
        tablas.append(("g_hoy*k", idx.astype(np.int32), 11 * 12 + 1))

    cols = []; nombres = []
    if cfg.get("hoy", True):
        cols += [salio, hoy, salio * k / 11.0, (G <= 12) * (~salio)]
        nombres += ["salio_hoy", "veces_hoy", "salio_hoy*k", "g<=12_no_hoy"]
    if cfg.get("gxk", True):
        for a, b in [(1, 4), (4, 8), (8, 13), (13, 21)]:
            cols.append(((G >= a) & (G < b)) * k / 11.0); nombres.append(f"g{a}-{b-1}*k")
    for w in cfg.get("ventanas", [12, 24, 38, 76, 152]):
        lo = np.maximum(ar - w, 0)
        cols.append((C[ar] - C[lo] - w / K) / np.sqrt(w / K)); nombres.append(f"cnt{w}")
    if cfg.get("penult", True):
        for a, b in [(1, 4), (4, 13), (13, 30)]:
            cols.append((G2 >= a) & (G2 < b)); nombres.append(f"g2_{a}-{b-1}")
    if cfg.get("ayer", True):
        cols.append(ayer > 0); nombres.append("salio_ayer")
    if cfg.get("dia12", False):
        # ¿el día anterior tuvo 12 sorteos? (régimen) x salió hoy
        d12 = np.zeros(n, np.float32)
        d12[:] = ((ini - ini_prev) >= 12)
        cols += [salio * d12[:, None], hoy * d12[:, None], salio * k / 11.0 * d12[:, None]]
        nombres += ["salio_hoy*d12", "veces_hoy*d12", "salio_hoy*k*d12"]
    for nm, extra in cfg.get("extra", lambda **z: [])(G=G, G2=G2, k=k, hoy=hoy, ayer=ayer, C=C, ar=ar,
                                                         hora=hora, ini=ini, ini_prev=ini_prev):
        cols.append(extra); nombres.append(nm)
    D = np.stack([np.asarray(np.broadcast_to(c, (n, K)), np.float32) for c in cols], axis=2) \
        if cols else np.zeros((n, K, 0), np.float32)
    return tablas, D, nombres


class Problema:
    def __init__(self, tablas, D, y, w):
        N = len(y); self.N = N
        self.idx = []; off = 0
        for _, ix, sz in tablas:
            self.idx.append((ix.reshape(-1) + off, sz)); off += sz
        self.nt = off
        self.X = np.ascontiguousarray(D.reshape(N * K, D.shape[2]))
        self.d = self.nt + D.shape[2]
        self.w = w / w.sum()
        r = np.arange(N) * K + y
        # estadístico observado
        o = np.zeros(self.d)
        for ix, sz in self.idx:
            o[:self.nt] += np.bincount(ix[r], weights=self.w, minlength=self.nt)
        o[self.nt:] = self.w @ self.X[r].astype(np.float64)
        self.obs = o

    def f(self, beta):
        N = self.N
        z = (self.X @ beta[self.nt:].astype(np.float32)).astype(np.float64)
        bt = beta[:self.nt]
        for ix, _ in self.idx:
            z = z + bt[ix]
        z = z.reshape(N, K)
        m = z.max(axis=1, keepdims=True)
        ez = np.exp(z - m); S = ez.sum(axis=1, keepdims=True)
        lse = (m + np.log(S))[:, 0]
        Pw = (ez / S * self.w[:, None]).reshape(-1)
        g = np.empty(self.d)
        gt = np.zeros(self.nt)
        for ix, _ in self.idx:
            gt += np.bincount(ix, weights=Pw, minlength=self.nt)
        g[:self.nt] = gt
        g[self.nt:] = (Pw.astype(np.float32) @ self.X).astype(np.float64)
        return self.w @ lse - self.obs @ beta, g - self.obs

    def z(self, beta, tablas, D):
        n = D.shape[0]
        zz = (D.reshape(n * K, -1) @ beta[self.nt:].astype(np.float32)).astype(np.float64)
        off = 0
        for _, ix, sz in tablas:
            zz += beta[off + ix.reshape(-1)]; off += sz
        return zz.reshape(n, K)


def ajustar(pr, lam, x0=None, refs=()):
    def f(b):
        v, g = pr.f(b)
        return v + 0.5 * lam * b @ b, g + lam * b
    bnds = [(None, None)] * pr.d
    for i in refs:
        bnds[i] = (0.0, 0.0)
    x = np.zeros(pr.d) if x0 is None else x0.copy()
    x[list(refs)] = 0.0
    r = minimize(f, x, jac=True, method="L-BFGS-B", bounds=bnds,
                 options={"maxiter": 500})
    self_nit.append(r.nit)
    return r.x


class Modelo:
    nombre = "logit_v2"

    def __init__(self, R=500, lam=1e-4, inicio=200, tau=None, ventana=None, **cfg):
        self.R = R; self.lam = lam; self.inicio = inicio; self.tau = tau; self.ventana = ventana
        self.cfg = cfg

    def predecir(self, datos, desde):
        seq = np.asarray(datos.seq); n = len(seq)
        tablas, D, self.nombres_dens = construir(datos, self.cfg)
        clave_cfg = repr((desde, self.R, self.lam, self.inicio, self.tau, self.ventana,
                          sorted((k, repr(v)) for k, v in self.cfg.items())))
        out = np.empty((n - desde, K))
        beta = None
        h = hashlib.sha1(clave_cfg.encode())
        pos = 0
        for T in range(desde, n, self.R):
            h.update(seq[pos:T].tobytes()); h.update(np.asarray(datos.dia)[pos:T].tobytes()); pos = T
            clave = h.copy().hexdigest()
            a = self.inicio if self.ventana is None else max(self.inicio, T - self.ventana)
            sl = slice(a, T)
            tb = [(nm, ix[sl], sz) for nm, ix, sz in tablas]
            pr = Problema(tb, D[sl], seq[sl],
                          np.ones(T - a) if self.tau is None else np.exp(-(T - 1 - np.arange(a, T)) / self.tau))
            if clave in _CACHE:
                beta = _CACHE[clave]
            else:
                refs = []; off = 0
                for nm, ix, sz in tablas:
                    refs.append(off + (11 if nm.startswith("gap") else 0)); off += sz
                beta = ajustar(pr, self.lam, beta, refs)
                _CACHE[clave] = beta
            b = min(T + self.R, n)
            z = pr.z(beta, [(nm, ix[T:b], sz) for nm, ix, sz in tablas], D[T:b])
            z -= z.max(axis=1, keepdims=True)
            p = np.exp(z)
            out[T - desde:b - desde] = p / p.sum(axis=1, keepdims=True)
        self.beta = beta
        self.nombres = [f"{nm}[{i}]" for nm, _, sz in tablas for i in range(sz)] + self.nombres_dens
        return out
