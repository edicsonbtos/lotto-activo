"""Modelo generativo "casi sin reemplazo" por día natural (familia intradía).

Mecanismo (medido en datos[:corte]): el operador evita repetir un animal dentro
del mismo día natural; la exclusión es fuerte en las primeras horas y se relaja
al final del día (ligada a la HORA del sorteo, no a una ventana móvil ni a un
ciclo de N distintos). Entre días solo queda un leve rechazo a repetir el sorteo
inmediatamente anterior y un ligero efecto por días desde la última salida.

P(x_t = i) ∝ exp( sum_tablas w[tabla][categoria_i(t)] )   (muestreo ponderado)
Pesos por MLE + L2 (Newton), reajuste cada R sorteos con datos[:T] y decaimiento
exponencial tau (el mecanismo se endurece con el tiempo).
Categorías causales: usan seq[:t] y la hora/día (conocidos) del propio sorteo t.
"""
import hashlib
import numpy as np

K = 38
_CACHE = {}
GBINS = [1, 2, 3, 4, 5, 6, 7, 9, 11, 13, 15, 17, 19, 22, 25, 29, 36, 46, 60, 80, 10**7]


def estado(datos):
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); n = len(seq); ar = np.arange(n)
    nuevo = np.r_[True, dia[1:] != dia[:-1]]
    didx = np.cumsum(nuevo) - 1
    ini = np.maximum.accumulate(np.where(nuevo, ar, 0))
    G = np.empty((n, K), np.int64); DD = np.empty((n, K), np.int64)
    HOY = np.empty((n, K), np.int64); REP = np.zeros(n, np.int64)
    hora = np.clip(np.asarray(datos.hora), 0, 11)
    MH = np.empty((n, K), np.int64); lastat = np.full((12, K), -10**7)
    last = np.full(K, -10**7); lastd = np.full(K, -10**7); cnt = np.zeros(K, np.int64); rep = 0
    for t in range(n):
        if nuevo[t]:
            cnt[:] = 0; rep = 0
        G[t] = t - last; DD[t] = didx[t] - lastd; HOY[t] = cnt; REP[t] = rep
        MH[t] = didx[t] - lastat[hora[t]]
        v = seq[t]; last[v] = t; lastd[v] = didx[t]; lastat[hora[t], v] = didx[t]
        if cnt[v] > 0:
            rep += 1
        cnt[v] += 1
    # conteos por día: CD[j] = apariciones en los días didx < j (acumulado por día)
    nd = int(didx[-1]) + 1 if n else 1
    CD = np.zeros((nd + 1, K), np.int64)
    np.add.at(CD, (didx + 1, seq), 1)
    CD = np.cumsum(CD, axis=0)
    return dict(MH=MH, CD=CD, didx=didx, n=n, G=np.minimum(G, 10**7), DD=np.minimum(DD, 10**7), HOY=HOY,
                rep=REP, k=ar - ini, hora=np.asarray(datos.hora))


def construir(datos, cfg):
    s = estado(datos); n = s["n"]
    G, DD, HOY = s["G"], s["DD"], s["HOY"]
    hora = np.broadcast_to(np.clip(s["hora"], 0, 11)[:, None], (n, K))
    kk = np.broadcast_to(np.clip(s["k"], 0, 11)[:, None], (n, K))
    pos = hora if cfg.get("reloj", "hora") == "hora" else kk
    hoy = HOY > 0
    tabs = []
    # 1) exclusión intradía: pertenece a hoy (1 vez) x hora del sorteo
    if cfg.get("rep", False):
        rf = np.broadcast_to(np.minimum(s["rep"], 1)[:, None], (n, K))
        tabs.append(np.where(HOY == 1, pos + 1 + 12 * rf, 0))   # 25
    else:
        tabs.append(np.where(HOY == 1, pos + 1, 0))           # 13
    # 2) repetido 2+ veces hoy
    if cfg.get("hoy2", True):
        tabs.append(np.where(HOY >= 2, 1 + (pos >= 8), 0))  # 3
    # 3) inmediato anterior cruzando día
    if cfg.get("g1", True):
        tabs.append(np.where(~hoy & (G == 1), 1, 0))        # 2
    # 4) no salió hoy: días desde última salida x grupo de hora
    dm = cfg.get("dd", 3)
    if dm:
        hg = np.array(cfg.get("hgrupos", [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2]))[pos]
        ng = int(max(cfg.get("hgrupos", [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2]))) + 1
        tabs.append(np.where(~hoy & (DD <= dm), (DD - 1) * ng + hg + 1, 0))   # dm*ng+1
    # 5) retraso largo / gap en tramos (no hoy)
    if cfg.get("gap", False):
        b = np.searchsorted(GBINS, G, side="right")
        ref = np.searchsorted(GBINS, cfg.get("gref", 12), side="right")
        tabs.append(np.where(~hoy & (b != ref), b, 0))
    # 5b) salió ayer a la misma hora
    if cfg.get("mh", False):
        tabs.append(np.where(~hoy & (s["MH"] == 1), 1, 0))
    if cfg.get("numero", False):             # efecto fijo por número (lento, vía tau)
        tabs.append(np.broadcast_to(np.arange(K)[None, :], (n, K)).copy())
    # 6) apariciones en los D días anteriores (sin hoy), tope 3
    for D in cfg.get("cntd", []):
        j = s["didx"]; c = s["CD"][j] - s["CD"][np.maximum(j - D, 0)]
        tabs.append(np.minimum(c, cfg.get("cap", 3)))
    dens = []
    seq = np.asarray(datos.seq)
    for hl in cfg.get("ema", []):
        a = 0.5 ** (1.0 / hl); E = np.zeros((n, K)); e = np.full(K, 1.0 / K) * hl / np.log(2) * 0 + 1e-9
        for t in range(n):
            E[t] = e
            e = e * a; e[seq[t]] += 1
        tot = E.sum(1, keepdims=True)
        rel = (E + cfg.get("ema_a", 0.5)) / (tot + K * cfg.get("ema_a", 0.5)) * K
        dens.append(np.log(rel))
    for hl in cfg.get("emaz", []):          # desviación lineal estandarizada (déficit tipo urna)
        a = 0.5 ** (1.0 / hl) if hl else 1.0
        E = np.zeros((n, K)); e = np.zeros(K)
        for t in range(n):
            E[t] = e
            e = e * a; e[seq[t]] += 1
        m = E.sum(1, keepdims=True) / K
        dens.append((E - m) / np.sqrt(m + 1.0))
    bl = cfg.get("bloques", [])
    if bl:
        oh = np.zeros((n, K)); oh[np.arange(n), seq] = 1
        Cc = np.vstack([np.zeros((1, K)), np.cumsum(oh, 0)])        # Cc[t] = conteo en seq[:t]
        ar = np.arange(n)
        for a_, b_ in zip(bl[:-1], bl[1:]):                         # sorteos t-b_ .. t-a_-1
            hi = np.maximum(ar - a_, 0); lo = np.maximum(ar - b_, 0)
            c = Cc[hi] - Cc[lo]; m = ((hi - lo) / K)[:, None]
            dens.append((c - m) / np.sqrt(m + 1.0))
    per = cfg.get("periodos", [])            # conteos en periodo natural actual / anterior
    if per:
        oh = np.zeros((n, K)); oh[np.arange(n), seq] = 1
        Cc = np.vstack([np.zeros((1, K)), np.cumsum(oh, 0)]); ar = np.arange(n)
        fe = list(datos.fecha)
        for nombre in per:
            if nombre == "semana":
                clave = (np.asarray(datos.dia) - np.asarray(datos.dow)) // 7
            elif nombre == "quincena":
                clave = np.array([int(f[:4]) * 24 + (int(f[5:7]) - 1) * 2 + (int(f[8:10]) > 15) for f in fe])
            elif nombre == "mes":
                clave = np.array([int(f[:4]) * 12 + int(f[5:7]) for f in fe])
            nv = np.r_[True, clave[1:] != clave[:-1]]
            ini = np.maximum.accumulate(np.where(nv, ar, 0))            # inicio del periodo actual
            # inicio del periodo anterior
            starts = ar[nv]; pi = np.searchsorted(starts, ini) - 1
            ini_prev = np.where(pi >= 0, starts[np.maximum(pi, 0)], ini)
            c = Cc[ar] - Cc[ini]; m = ((ar - ini) / K)[:, None]
            dens.append((c - m) / np.sqrt(m + 1.0))
            c = Cc[ini] - Cc[ini_prev]; m = ((ini - ini_prev) / K)[:, None]
            dens.append((c - m) / np.sqrt(m + 1.0))
    D = np.stack(dens, axis=2) if dens else np.zeros((n, K, 0))
    return tabs, D


def ajustar_newton(X, y, wts, lam, b0=None, iters=20):
    """MLE ponderado + L2 por Newton amortiguado. X: (N,K,d) float32 (tablas one-hot
    sin categoría de referencia + densas)."""
    N, _, d = X.shape
    rows = np.arange(N)
    Xf = X.reshape(-1, d)
    Xy = X[rows, y].astype(np.float64).T @ wts
    b = np.zeros(d) if b0 is None or len(b0) != d else b0.copy()

    def valor(b):
        z = (Xf @ b.astype(np.float32)).reshape(N, K).astype(np.float64)
        zm = z.max(1, keepdims=True); e = np.exp(z - zm); S = e.sum(1)
        lz = np.log(S) + zm[:, 0]
        return -(wts * (z[rows, y] - lz)).sum() + 0.5 * lam * b @ b, e / S[:, None]

    f, p = valor(b)
    for _ in range(iters):
        pw = (p * wts[:, None]).astype(np.float32)
        M = np.einsum("nk,nkd->nd", p.astype(np.float32), X).astype(np.float64)       # E_p[x] por fila
        g = (pw.reshape(-1) @ Xf).astype(np.float64) - Xy + lam * b
        H = ((Xf * pw.reshape(-1, 1)).T @ Xf).astype(np.float64) - (M * wts[:, None]).T @ M + lam * np.eye(d)
        paso = np.linalg.solve(H, g)
        t = 1.0
        while True:
            nb = b - t * paso
            nf, npp = valor(nb)
            if nf <= f + 1e-9 or t < 1e-3:
                break
            t *= 0.5
        mejora = f - nf
        b, f, p = nb, nf, npp
        if mejora < 1e-6 * N * 1e-3 or np.abs(t * paso).max() < 1e-5:
            break
    return b


class Modelo:
    nombre = "intradia_v1"

    def __init__(self, R=500, lam=1.0, tau=None, inicio=100, **cfg):
        self.R, self.lam, self.tau, self.inicio, self.cfg = R, lam, tau, inicio, cfg

    def predecir(self, datos, desde):
        seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); n = len(seq)
        tabs, D = construir(datos, self.cfg)
        sizes = [max(int(t.max()) + 1, 2) for t in tabs]
        d = sum(sz - 1 for sz in sizes) + D.shape[2]
        a0 = self.inicio
        X = np.zeros((n - a0, K, d), np.float32)
        o = 0
        for t_, sz in zip(tabs, sizes):
            ix = t_[a0:]
            r, c = np.nonzero(ix)
            X[r, c, o + ix[r, c] - 1] = 1.0
            o += sz - 1
        X[:, :, o:] = D[a0:]
        del D, tabs
        h = hashlib.sha1(repr((type(self).__name__, self.R, self.lam, self.tau, self.inicio,
                               sorted((k_, repr(v_)) for k_, v_ in self.cfg.items()), sizes)).encode())
        out = np.empty((n - desde, K)); beta = None; pos = 0
        for T in range(desde, n, self.R):
            h.update(seq[pos:T].tobytes()); h.update(dia[pos:T].tobytes()); pos = T
            clave = h.copy().hexdigest()
            if clave in _CACHE:
                beta = _CACHE[clave]
            else:
                w = np.exp(-(T - 1 - np.arange(a0, T)) / self.tau) if self.tau else np.ones(T - a0)
                beta = ajustar_newton(X[:T - a0], seq[a0:T], w, self.lam, beta)
                _CACHE[clave] = beta
            b = min(T + self.R, n)
            z = (X[T - a0:b - a0].reshape(-1, d) @ beta.astype(np.float32)).reshape(b - T, K).astype(np.float64)
            z -= z.max(1, keepdims=True)
            p = np.exp(z); out[T - desde:b - desde] = p / p.sum(1, keepdims=True)
        self.beta = beta; self.sizes = sizes
        return out
