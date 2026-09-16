"""intradia_v2: muestreo casi-sin-reemplazo por dia natural + memoria de frecuencia.

Mecanismo medido en datos[:corte] (exploracion/intradia_*.py):
  * La exclusion es por DIA NATURAL, no por ventana movil ni por ciclo de N
    distintos: a igual retraso g<=11, un numero que salio HOY tiene tasa ~0,4x y
    uno que salio AYER ~1,0x. En verosimilitud (in-sample, 1 parametro):
    "salio hoy" +53 mbits vs mejor ventana movil (m=6) +32 y mejor ciclo (<8
    distintos) +26.  "hoy x hora" +70 mbits.
  * La exclusion depende de la HORA del sorteo (fuerte 8AM-5PM, casi nula a las
    6-7PM) y se endurece con el tiempo; si ya hubo una repeticion hoy, otra es aun
    menos probable (presupuesto de repeticiones).
  * Entre dias: el primer sorteo (8AM) evita los numeros de ayer (~0,5x); el
    inmediato anterior cruzando dia ~0,57x.
  * Memoria lenta por numero: frecuencia reciente (vida media ~40 y ~160 sorteos)
    a favor (numeros "calientes"), exceso a ~640 sorteos en contra (equilibrado),
    mes natural en curso/anterior en contra.

P(x_t=i) ~ exp(w . x_i(t)), logit condicional (pesos compartidos entre numeros),
MLE + L2 por Newton, reajuste cada R=100 sorteos con los ultimos 4500 de datos[:T],
peso exp(-(T-t)/tau), tau=1500.
Todas las features usan seq[:t] y calendario (dia/hora/fecha) del sorteo t.
"""
import hashlib
import numpy as np

K = 38
_CACHE = {}
GBINS = [1, 2, 3, 4, 5, 6, 7, 9, 11, 13, 15, 17, 19, 22, 25, 29, 36, 46, 60, 80, 10**7]
HGRUPOS = np.array([0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3])


def _ema(seq, n, hl):
    a = 0.5 ** (1.0 / hl) if hl else 1.0
    E = np.zeros((n, K)); e = np.zeros(K)
    for t in range(n):
        E[t] = e
        e *= a; e[seq[t]] += 1
    return E


def construir(datos, cfg):
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); n = len(seq); ar = np.arange(n)
    hora = np.clip(np.asarray(datos.hora), 0, 11)
    nuevo = np.r_[True, dia[1:] != dia[:-1]]
    didx = np.cumsum(nuevo) - 1
    G = np.empty((n, K), np.int64); DD = np.empty((n, K), np.int64)
    HOY = np.empty((n, K), np.int64); REP = np.zeros(n, np.int64)
    last = np.full(K, -10**7); lastd = np.full(K, -10**7); cnt = np.zeros(K, np.int64); rep = 0
    for t in range(n):                       # estado ANTES del sorteo t
        if nuevo[t]:
            cnt[:] = 0; rep = 0
        G[t] = t - last; DD[t] = didx[t] - lastd; HOY[t] = cnt; REP[t] = rep
        v = seq[t]; last[v] = t; lastd[v] = didx[t]
        rep += int(cnt[v] > 0); cnt[v] += 1
    H = np.broadcast_to(hora[:, None], (n, K))
    hoy = HOY > 0
    tabs = []                                # (indices (n,K), tamano); 0 = referencia
    rf = np.broadcast_to(np.minimum(REP, 1)[:, None], (n, K))
    tabs.append((np.where(HOY == 1, H + 1 + 12 * rf, 0), 25))          # hoy x hora x ya-hubo-repeticion
    tabs.append((np.where(HOY >= 2, 1 + (H >= 8), 0), 3))              # 2+ veces hoy
    tabs.append((np.where(~hoy & (G == 1), 1, 0), 2))                  # inmediato anterior (cruza dia)
    dm = cfg.get("dd", 2); ng = int(HGRUPOS.max()) + 1
    tabs.append((np.where(~hoy & (DD <= dm), (DD - 1) * ng + HGRUPOS[H] + 1, 0), dm * ng + 1))  # dias desde x hora
    b = np.searchsorted(GBINS, np.minimum(G, 10**7), side="right")
    ref = np.searchsorted(GBINS, 12, side="right")
    tabs.append((np.where(~hoy & (b != ref), b, 0), len(GBINS) + 1))   # retraso en tramos
    dens = []
    for hl in cfg.get("ema", [40, 160]):     # log frecuencia relativa reciente
        E = _ema(seq, n, hl)
        dens.append(np.log((E + 0.5) / (E.sum(1, keepdims=True) + K * 0.5) * K))
    for hl in cfg.get("emaz", [640, 2560]):  # desviacion estandarizada (deficit tipo urna)
        E = _ema(seq, n, hl); m = E.sum(1, keepdims=True) / K
        dens.append((E - m) / np.sqrt(m + 1.0))
    oh = np.zeros((n, K)); oh[ar, seq] = 1
    Cc = np.vstack([np.zeros((1, K)), np.cumsum(oh, 0)])               # Cc[t] = conteo en seq[:t]
    fe = list(datos.fecha)
    for nombre in cfg.get("periodos", ["semana", "mes"]):              # periodo natural actual / anterior
        if nombre == "semana":
            clave = (dia - np.asarray(datos.dow)) // 7
        else:
            clave = np.array([int(f[:4]) * 12 + int(f[5:7]) for f in fe])
        nv = np.r_[True, clave[1:] != clave[:-1]]
        ini = np.maximum.accumulate(np.where(nv, ar, 0))
        starts = ar[nv]; pi = np.searchsorted(starts, ini) - 1
        ini_prev = np.where(pi >= 0, starts[np.maximum(pi, 0)], ini)
        for lo, hi in ((ini, ar), (ini_prev, ini)):
            c = Cc[hi] - Cc[lo]; m = ((hi - lo) / K)[:, None]
            dens.append((c - m) / np.sqrt(m + 1.0))
    D = np.stack(dens, axis=2) if dens else np.zeros((n, K, 0))
    return tabs, D


def ajustar_newton(X, y, wts, lam, b0=None, iters=20):
    """MLE ponderado + L2 (prior N(0,1/lam)) por Newton amortiguado. X: (N,K,d) float32."""
    N, _, d = X.shape
    rows = np.arange(N)
    Xf = X.reshape(-1, d)
    Xy = X[rows, y].astype(np.float64).T @ wts
    b = np.zeros(d) if b0 is None or len(b0) != d else b0.copy()

    def valor(b):
        z = (Xf @ b.astype(np.float32)).reshape(N, K).astype(np.float64)
        zm = z.max(1, keepdims=True); e = np.exp(z - zm); S = e.sum(1)
        return -(wts * (z[rows, y] - np.log(S) - zm[:, 0])).sum() + 0.5 * lam * b @ b, e / S[:, None]

    f, p = valor(b)
    for _ in range(iters):
        pw = (p * wts[:, None]).astype(np.float32)
        M = np.einsum("nk,nkd->nd", p.astype(np.float32), X).astype(np.float64)
        g = (pw.reshape(-1) @ Xf).astype(np.float64) - Xy + lam * b
        Hs = ((Xf * pw.reshape(-1, 1)).T @ Xf).astype(np.float64) - (M * wts[:, None]).T @ M + lam * np.eye(d)
        paso = np.linalg.solve(Hs, g)
        t = 1.0
        while True:
            nb = b - t * paso
            nf, npp = valor(nb)
            if nf <= f + 1e-9 or t < 1e-3:
                break
            t *= 0.5
        mejora = f - nf
        b, f, p = nb, nf, npp
        if mejora < 1e-9 * N or np.abs(t * paso).max() < 1e-5:
            break
    return b


class Modelo:
    nombre = "intradia_v2"

    def __init__(self, R=100, lam=1.0, tau=1500, inicio=100, ventana=4500, **cfg):
        self.R, self.lam, self.tau, self.inicio, self.cfg = R, lam, tau, inicio, cfg
        self.ventana = ventana

    def predecir(self, datos, desde):
        seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); n = len(seq)
        tabs, D = construir(datos, self.cfg)
        d = sum(sz - 1 for _, sz in tabs) + D.shape[2]
        a0 = self.inicio
        X = np.zeros((n - a0, K, d), np.float32)
        o = 0
        for ix, sz in tabs:
            ix = ix[a0:]
            r, c = np.nonzero(ix)
            X[r, c, o + ix[r, c] - 1] = 1.0
            o += sz - 1
        X[:, :, o:] = D[a0:]
        del D, tabs
        h = hashlib.sha1(repr((type(self).__name__, self.R, self.lam, self.tau, a0, self.ventana,
                               sorted((k_, repr(v_)) for k_, v_ in self.cfg.items()))).encode())
        h.update(np.asarray(datos.hora).tobytes()); h.update(np.asarray(datos.dow).tobytes())
        h.update(repr(list(datos.fecha)).encode())
        out = np.empty((n - desde, K)); beta = None; pos = 0
        for T in range(desde, n, self.R):
            h.update(seq[pos:T].tobytes()); h.update(dia[pos:T].tobytes()); pos = T
            clave = h.copy().hexdigest()
            if clave in _CACHE:
                beta = _CACHE[clave]
            else:
                a1 = a0 if self.ventana is None else max(a0, T - self.ventana)
                w = np.exp(-(T - 1 - np.arange(a1, T)) / self.tau) if self.tau else np.ones(T - a1)
                beta = ajustar_newton(X[a1 - a0:T - a0], seq[a1:T], w, self.lam, beta)
                _CACHE[clave] = beta
            b = min(T + self.R, n)
            z = (X[T - a0:b - a0].reshape(-1, d) @ beta.astype(np.float32)).reshape(b - T, K).astype(np.float64)
            z -= z.max(1, keepdims=True)
            p = np.exp(z); out[T - desde:b - desde] = p / p.sum(1, keepdims=True)
        self.beta = beta
        return out
