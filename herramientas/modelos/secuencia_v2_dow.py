"""secuencia_final: copia de logit_final + (a) conteos del candidato en bandas de retraso [38,200) y [200,700)
(ciclo de largo plazo: exceso reciente favorece, exceso hace 200-700 sorteos penaliza), (b) indicadores
"misma columna que el anterior" y "columna 3 tras columna 3" (evitación). Config elegida en desarrollo.
Otras opciones del código (dif_lags, colpar, dowbal, kernel...) quedan desactivadas.


Logit condicional suavizado: softmax sobre los 38 candidatos con pesos compartidos,
MLE penalizada (L2 + penalización de diferencias entre categorías vecinas, estilo P-spline)
resuelta por Newton con Hessiano exacto.

Causalidad: la fila t usa solo seq[:t] y el calendario (dia) del propio sorteo t.

Bloques de features por candidato (tablas categóricas completas, sin referencia; la
invariancia del softmax la resuelve el L2 pequeño):
  gap   retraso exacto g=1..G1 + tramos + "nunca"            (suavizado a lo largo de g)
  hoy   si salió hoy: k jugados hoy (1..11) x veces hoy (1, 2+)  (suavizado en k)
  dias  si no salió hoy y su última salida fue hace dd<=dm días: dd x k (0..11)
        (suavizado en k y en dd)
  g2    penúltimo retraso 1..G2max + tramos                  (suavizado)
  cnt   conteos en ventanas (z-score bajo azar), densas
Reajuste cada R sorteos con datos[:T]; ponderación exponencial con vida media tau.
Memoización de ajustes por huella del pasado (pura función de datos[:T], sin fuga).
"""
import hashlib
import numpy as np

K = 38
_CACHE = {}


def _estado(datos):
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia)
    n = len(seq); ar = np.arange(n)
    oh = np.zeros((n, K), np.float32); oh[ar, seq] = 1
    C = np.vstack([np.zeros((1, K), np.float32), np.cumsum(oh, axis=0)])
    nuevo = np.r_[True, dia[1:] != dia[:-1]]
    didx = np.cumsum(nuevo) - 1
    ini = np.maximum.accumulate(np.where(nuevo, ar, 0))
    k = ar - ini
    G = np.empty((n, K), np.int64); G2 = np.empty((n, K), np.int64); DD = np.empty((n, K), np.int64)
    last = np.full(K, -10**6); prev = np.full(K, -10**6); lastd = np.full(K, -10**6)
    for t in range(n):
        G[t] = t - last; G2[t] = last - prev; DD[t] = didx[t] - lastd
        v = seq[t]; prev[v] = last[v]; last[v] = t; lastd[v] = didx[t]
    hoy = (C[ar] - C[ini]).astype(np.int64)
    return seq, ar, C, k, G, G2, DD, hoy


def _tabla_orden(V, exactos, tramos, valido=None):
    """Categorías: V=1..exactos, luego tramos [a,b), luego resto (>= último).  Cadena ordenada."""
    idx = np.clip(V, 1, exactos) - 1
    idx = np.where(V > exactos, exactos, idx)  # provisional
    nb = exactos
    for a, b in zip(tramos[:-1], tramos[1:]):
        idx = np.where((V >= a) & (V < b), nb, idx); nb += 1
    idx = np.where(V >= tramos[-1], nb, idx); nb += 1
    cadena = list(range(nb))
    if valido is not None:
        idx = np.where(valido, idx + 1, 0); cadena = [c + 1 for c in cadena]; nb += 1
    return idx, nb, [cadena]


def construir(datos, cfg):
    seq, ar, C, k, G, G2, DD, hoy = _estado(datos)
    n = len(seq)
    kk = np.broadcast_to(k[:, None], (n, K))
    salio = hoy > 0
    bloques = []   # (nombre, idx(n,K), tamaño, cadenas, fuerza_suavizado)

    G1 = cfg.get("G1", 40)
    tr = cfg.get("tramos", [G1 + 1, 51, 61, 81, 101, 151, 10**5])
    nunca = G >= 10**5
    idx, nb, cad = _tabla_orden(G, G1, tr, valido=None)
    idx = np.where(nunca, nb, idx); nb += 1   # "nunca" fuera de la cadena
    bloques.append(("gap", idx, nb, cad, cfg.get("s_gap", 50.0)))

    if cfg.get("hoy", True):
        vh = np.minimum(hoy, 2)
        km = np.minimum(kk, 11)
        idx = np.where(salio, (km - 1) * 2 + vh, 0)
        cad = [[1 + 2 * j for j in range(11)], [2 + 2 * j for j in range(1, 11)]]
        bloques.append(("hoy", idx, 23, cad, cfg.get("s_hoy", 50.0)))

    if cfg.get("dias", True):
        dm = cfg.get("ddmax", 4)
        km = np.minimum(kk, 11)
        idx = np.where(~salio & (DD <= dm), (np.minimum(DD, dm) - 1) * 12 + km + 1, 0)
        cad = [[1 + d * 12 + j for j in range(12)] for d in range(dm)]
        cad += [[1 + d * 12 + j for d in range(dm)] for j in range(12)]
        bloques.append(("dias", idx, dm * 12 + 1, cad, cfg.get("s_dias", 50.0)))

    if cfg.get("g2", True):
        g2m = cfg.get("G2max", 30)
        valido = (G2 > 0) & (G2 < 10**5)
        idx, nb, cad = _tabla_orden(np.minimum(G2, 10**5 - 1), g2m, [g2m + 1, 46, 61, 91, 10**5 - 1], valido)
        bloques.append(("g2", idx, nb, cad, cfg.get("s_g2", 50.0)))

    if cfg.get("cuota", False):
        # candidatos que salieron el día d-dd (y no hoy): cuántos animales de ese día ya salieron hoy
        dia = np.asarray(datos.dia)
        nuevo = np.r_[True, dia[1:] != dia[:-1]]
        inis = np.r_[np.flatnonzero(nuevo), n]
        pos = np.cumsum(nuevo) - 1                    # índice del día de cada t
        cm = cfg.get("cuota_max", 5)
        kfull = cfg.get("cuota_kfull", False)
        kg = np.minimum(kk, 11) if kfull else np.array([0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3])[np.minimum(kk, 11)]
        ng = 12 if kfull else 4
        for dd_ in cfg.get("cuota_dd", [1]):
            p0 = pos - dd_
            ok = p0 >= 0
            a0 = inis[np.maximum(p0, 0)]; a1 = inis[np.maximum(p0, 0) + 1]
            dset = ((C[a1] - C[a0]) > 0) & ok[:, None]
            cnt = (dset & salio).sum(1)
            idx = np.where(dset & ~salio, 1 + np.minimum(cnt, cm)[:, None] * ng + kg, 0)
            cad = [[1 + c * ng + g for c in range(cm + 1)] for g in range(ng)]
            if kfull:
                cad += [[1 + c * ng + g for g in range(ng)] for c in range(cm + 1)]
            bloques.append((f"cuota{dd_}", idx, 1 + (cm + 1) * ng, cad, cfg.get("s_cuota", 50.0)))

    if cfg.get("clases", None):
        # cuota por clase de "días desde la última salida" al comenzar el día:
        # para un candidato de la clase c que no ha salido hoy, cuántos de su clase ya salieron hoy
        dia = np.asarray(datos.dia)
        nuevo = np.r_[True, dia[1:] != dia[:-1]]
        ini = np.maximum.accumulate(np.where(nuevo, ar, 0))
        DDs = DD[ini]                                  # (n, K) clase fijada al inicio del día
        bordes = cfg["clases"]                         # p.ej. [1,2,3,4,6,10]
        cl = np.searchsorted(np.array(bordes), np.minimum(DDs, 10**4), side="right") - 1   # -1 = nunca/0
        nc = len(bordes)
        cm = cfg.get("cuota_max", 5)
        kg = np.array([0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3])[np.minimum(kk, 11)]
        cnt = np.zeros((n, K), np.int64)
        for c in range(nc):
            cc = ((cl == c) & salio).sum(1)
            cnt = np.where(cl == c, cc[:, None], cnt)
        valid = (cl >= 0) & ~salio
        idx = np.where(valid, 1 + (np.maximum(cl, 0) * (cm + 1) + np.minimum(cnt, cm)) * 4 + kg, 0)
        cad = [[1 + (c * (cm + 1) + u) * 4 + g for u in range(cm + 1)] for c in range(nc) for g in range(4)]
        bloques.append(("clases", idx, 1 + nc * (cm + 1) * 4, cad, cfg.get("s_cuota", 50.0)))

    if cfg.get("rango", False):
        # posición del candidato ordenado por retraso (0 = el que más tiempo lleva sin salir)
        rk = np.argsort(np.argsort(-G, axis=1, kind="stable"), axis=1, kind="stable")
        bloques.append(("rango", rk, K, [list(range(K))], cfg.get("s_rango", 50.0)))

    # ---- bloques secuenciales (familia secuencia_) ----
    dens_extra = []
    oh_seq = np.zeros((n, K), np.float32); oh_seq[ar, seq] = 1
    NUMV = np.array([0, 0] + list(range(1, 37)))
    DV = np.array([0, 37] + list(range(1, 37)))
    COL = np.where(np.arange(K) < 2, 3, (NUMV - 1) % 3)
    prev1 = np.r_[0, seq[:-1]]; okp = (ar > 0)[:, None]
    for lagk in cfg.get("dif_lags", []):
        pv = np.r_[np.zeros(lagk, np.int64), seq[:-lagk]]; ok = (ar >= lagk)[:, None]
        idx = np.where(ok, 1 + (DV[None, :] - DV[pv][:, None]) % K, 0)
        cad = [list(range(1, K + 1)) + [1]]          # cadena circular
        bloques.append((f"dif{lagk}", idx, K + 1, cad, cfg.get("s_dif", 50.0)))
    if cfg.get("colpar", False):
        idx = np.where(okp, 1 + COL[prev1][:, None] * 4 + COL[None, :], 0)
        bloques.append(("colpar", idx, 17, [], 0.0))
    if cfg.get("mismacol", False):
        idx = np.where(okp, 1 + ((COL[prev1][:, None] == COL[None, :]) & (COL[None, :] < 3)), 0)
        bloques.append(("mismacol", idx, 3, [], 0.0))
    for lagk in cfg.get("col22_lags", []):
        pv = np.r_[np.zeros(lagk, np.int64), seq[:-lagk]]; ok = (ar >= lagk)[:, None]
        idx = np.where(ok, 1 + ((COL[pv][:, None] == 2) & (COL[None, :] == 2)), 0)
        bloques.append((f"col22l{lagk}", idx, 3, [], 0.0))
    if cfg.get("dowbal", None):
        # conteo del candidato en el mismo día de semana en las ultimas S semanas (z bajo azar)
        S = cfg["dowbal"]
        dow = np.asarray(datos.dow)
        acc = np.zeros((n, K), np.float32)
        for dw in range(7):
            ix = np.flatnonzero(dow == dw)
            if len(ix) == 0: continue
            cs = np.vstack([np.zeros((1, K), np.float32), np.cumsum(oh_seq[ix], axis=0)])
            # para cada sorteo t de este dow: conteos de sorteos anteriores de ese dow dentro de S*12 sorteos del dow
            j = np.arange(len(ix)); lo = np.maximum(j - S * 12, 0)
            acc[ix] = cs[j] - cs[lo]
        # antes de t dentro del mismo día se incluyen sorteos de hoy (ya contados en 'hoy'); se aceptan
        w_ = np.minimum(np.searchsorted(np.r_[0], 0) * 0 + S * 12, 10**9)
        dens_extra.append(((acc - S * 12 / K) / np.sqrt(S * 12 / K)).astype(np.float64))
    if cfg.get("horabal", None):
        S = cfg["horabal"]; hora = np.asarray(datos.hora)
        acc = np.zeros((n, K), np.float32)
        for hh in range(12):
            ix = np.flatnonzero(hora == hh)
            if len(ix) == 0: continue
            cs = np.vstack([np.zeros((1, K), np.float32), np.cumsum(oh_seq[ix], axis=0)])
            j = np.arange(len(ix)); lo = np.maximum(j - S, 0)
            acc[ix] = cs[j] - cs[lo]
        dens_extra.append(((acc - S / K) / np.sqrt(S / K)).astype(np.float64))
    for (a_, b_) in cfg.get("bandas", []):
        lo = np.maximum(ar - b_, 0); hi = np.maximum(ar - a_, 0)
        w_ = b_ - a_
        dens_extra.append(((C[hi] - C[lo]) - w_ / K) / np.sqrt(w_ / K))
    ker = cfg.get("kernel", None)     # (inicio, ancho, nbandas, suavizado)
    if ker:
        a0, bw, nbk, sk = ker
        for j in range(nbk):
            a_ = a0 + j * bw; b_ = a_ + bw
            lo = np.maximum(ar - b_, 0); hi = np.maximum(ar - a_, 0)
            dens_extra.append(((C[hi] - C[lo]) - bw / K) / np.sqrt(bw / K))
    if cfg.get("mismacol2", False):
        idx = np.where(okp, 1 + ((COL[prev1][:, None] == 2) & (COL[None, :] == 2)), 0)
        bloques.append(("col22", idx, 3, [], 0.0))

    dens = []; nombres_d = []
    for w in cfg.get("ventanas", [12, 24, 38, 76, 152]):
        lo = np.maximum(ar - w, 0)
        dens.append((C[ar] - C[lo] - w / K) / np.sqrt(w / K)); nombres_d.append(f"cnt{w}")

    for de in dens_extra:
        dens.append(de); nombres_d.append("extra")
    # penalización y estructura por bloques (one-hot como índices, densas aparte)
    d = sum(b[2] for b in bloques) + len(dens)
    Pen = np.zeros((d, d)); nombres = []; off = 0; idxs = []
    for nm, idx, sz, cadenas, s in bloques:
        for c in cadenas:
            for i, j in zip(c[:-1], c[1:]):
                a, b = off + i, off + j
                Pen[a, a] += s; Pen[b, b] += s; Pen[a, b] -= s; Pen[b, a] -= s
        nombres += [f"{nm}[{i}]" for i in range(sz)]
        idxs.append((off, sz, idx.astype(np.int32)))
        off += sz
    if ker:
        base_k = off + len(dens) - len(dens_extra) + (len(dens_extra) - ker[2])
        for j in range(ker[2] - 1):
            a, b = base_k + j, base_k + j + 1
            Pen[a, a] += ker[3]; Pen[b, b] += ker[3]; Pen[a, b] -= ker[3]; Pen[b, a] -= ker[3]
    D = (np.stack([np.asarray(c, np.float64) for c in dens], axis=2) if dens
         else np.zeros((n, K, 0)))
    nombres += nombres_d
    return (idxs, D, off), Pen, nombres


def logits(est, b, sl):
    idxs, D, nt = est
    z = D[sl] @ b[nt:]
    for off, sz, ix in idxs:
        z = z + b[off + ix[sl]]
    return z


def ajustar(est, sl, y, wts, Pen, b0=None, iters=15, tol=1e-8, lin=None):
    idxs, D, nt = est
    Ds = D[sl]; N = Ds.shape[0]; m = Ds.shape[2]; d = nt + m
    ixs = [(off, sz, ix[sl]) for off, sz, ix in idxs]
    Pen = Pen / wts.sum()          # penalización en escala de suma de log-verosimilitud
    lin = np.zeros(Pen.shape[0]) if lin is None else lin / wts.sum()   # término lineal (media a priori)
    wn = wts / wts.sum()
    rows = np.arange(N)
    Xy = np.zeros(d)
    for off, sz, ix in ixs:
        Xy[off:off + sz] = np.bincount(ix[rows, y], weights=wn, minlength=sz)
    Xy[nt:] = wn @ Ds[rows, y]
    # índices planos por fila para M (N x sz)
    flat = [(off, sz, (rows[:, None] * sz + ix).ravel()) for off, sz, ix in ixs]
    b = np.zeros(d) if b0 is None else b0.copy()
    for _ in range(iters):
        z = Ds @ b[nt:]
        for off, sz, ix in ixs:
            z = z + b[off + ix]
        z -= z.max(1, keepdims=True); e = np.exp(z); p = e / e.sum(1, keepdims=True)
        pw = p * wn[:, None]; pwf = pw.ravel()
        g = -Xy + Pen @ b - lin
        for off, sz, ix in ixs:
            g[off:off + sz] += np.bincount(ix.ravel(), weights=pwf, minlength=sz)
        g[nt:] += np.einsum("nk,nkm->m", pw, Ds)
        if np.abs(g).max() < tol:
            break
        H = np.zeros((d, d))
        # término E[x x^T]
        for i, (oa, sa, ia) in enumerate(ixs):
            H[oa:oa + sa, oa:oa + sa] += np.diag(np.bincount(ia.ravel(), weights=pwf, minlength=sa))
            for ob, sb, ib in ixs[i + 1:]:
                blk = np.bincount((ia * sb + ib).ravel(), weights=pwf, minlength=sa * sb).reshape(sa, sb)
                H[oa:oa + sa, ob:ob + sb] += blk; H[ob:ob + sb, oa:oa + sa] += blk.T
            for j in range(m):
                col = np.bincount(ia.ravel(), weights=(pw * Ds[:, :, j]).ravel(), minlength=sa)
                H[oa:oa + sa, nt + j] += col; H[nt + j, oa:oa + sa] += col
        if m:
            Dw = Ds * pw[:, :, None]
            H[nt:, nt:] += np.einsum("nkm,nkl->ml", Dw, Ds)
        # término E[x] E[x]^T
        Mx = np.zeros((N, d))
        for (off, sz, fl) in flat:
            Mx[:, off:off + sz] = np.bincount(fl, weights=p.ravel(), minlength=N * sz).reshape(N, sz)
        Mx[:, nt:] = np.einsum("nk,nkm->nm", p, Ds)
        H -= (Mx * wn[:, None]).T @ Mx
        H += Pen
        b = b - np.linalg.solve(H, g)
    return b


CFG_FINAL = dict(bandas=[[38, 200], [200, 700]], mismacol=True, mismacol2=True, dowbal=8, cuota=True, s_gap=15.0, s_hoy=15.0, s_dias=15.0, s_g2=150.0, s_cuota=15.0, ventanas=[12, 38])


class Modelo:
    nombre = "secuencia_v2_dow (dowbal8 + logit_final + bandas de conteo [38,200)/[200,700) + misma columna tras anterior)"

    def __init__(self, R=250, lam=1.0, inicio=200, tau=3000, tau_r=None, rho=None, **cfg):
        cfg = {**CFG_FINAL, **cfg}
        self.R = R; self.lam = lam; self.inicio = inicio; self.tau = tau; self.cfg = cfg
        self.tau_r = tau_r; self.rho = rho

    def predecir(self, datos, desde):
        seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); n = len(seq)
        est, Pen, self.nombres = construir(datos, self.cfg)
        d = Pen.shape[0]
        Pen = Pen + self.lam * np.eye(d)
        h = hashlib.sha1(repr((type(self).__name__, self.R, self.lam, self.inicio, self.tau, self.tau_r, self.rho,
                               sorted((a, repr(b)) for a, b in self.cfg.items()))).encode())
        out = np.empty((n - desde, K)); beta = None; beta_r = None; pos = 0
        for T in range(desde, n, self.R):
            h.update(seq[pos:T].tobytes()); h.update(dia[pos:T].tobytes()); pos = T
            clave = h.copy().hexdigest()
            if clave in _CACHE:
                beta, beta_r = _CACHE[clave]
            else:
                a = self.inicio; sl = slice(a, T); edad = T - 1 - np.arange(a, T)
                wts = np.ones(T - a) if self.tau is None else np.exp(-edad / self.tau)
                beta = ajustar(est, sl, seq[a:T], wts, Pen, beta)
                if self.tau_r is not None:
                    # segunda escala: ajuste reciente encogido hacia el ajuste de largo plazo
                    wr = np.exp(-edad / self.tau_r)
                    beta_r = ajustar(est, sl, seq[a:T], wr, Pen + self.rho * np.eye(d),
                                     beta if beta_r is None else beta_r, lin=self.rho * beta)
                _CACHE[clave] = (beta, beta_r)
            bu = beta if beta_r is None else beta_r
            b = min(T + self.R, n)
            z = logits(est, bu, slice(T, b))
            z -= z.max(axis=1, keepdims=True)
            p = np.exp(z)
            out[T - desde:b - desde] = p / p.sum(axis=1, keepdims=True)
        self.beta = bu
        return out
