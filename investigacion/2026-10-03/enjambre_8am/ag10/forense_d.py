# ag10 — D: re-derivar 0,272 y 1,736 en dev y comprobar que P_aj no tiene fuga
import os, numpy as np
from scipy.optimize import minimize
from scipy.stats import chi2, poisson
AQUI = os.path.dirname(os.path.abspath(__file__)); BASE = os.path.dirname(AQUI)
Z = np.load(os.path.join(BASE, "base8.npz"), allow_pickle=True)
S, H, DI, F, P, PA, EP, TR = (Z[k] for k in ("seq", "hora", "dia", "fecha", "P", "P_aj", "es_primero", "tramo"))
n = len(S)
first = {}
for t in range(n): first.setdefault(int(DI[t]), t)

# --- 1. fuga estructural: reconstruir P_aj desde P con índices explícitos y comprobar tp < t
fug = 0; maxdiff = 0.0; filas = []
for d, t in first.items():
    if TR[t] == "cal": continue
    m = np.ones(38); src = {}
    for k, mult in {1: 0.272, 3: 1.736}.items():
        tp = first.get(d - k)
        if tp is not None and H[tp] == H[t]:
            if not (tp < t and F[tp] < F[t] and DI[tp] == d - k): fug += 1
            m[S[tp]] *= mult; src[k] = tp
    q = P[t] * m; q /= q.sum()
    maxdiff = max(maxdiff, np.abs(q - PA[t]).max())
    filas.append((t, src))
# filas no-primeras: P_aj == P
noprim = (~EP) & (TR != "cal")
print(f"[D1] filas primer sorteo con motor: {len(filas)}; referencias a sorteos no anteriores: {fug}; "
      f"max|P_aj recalculado - P_aj base8| = {maxdiff:.2e}; filas no-primeras con P_aj != P: {int((np.abs(PA[noprim]-P[noprim]).max(1)>1e-12).sum())}")
# prueba de barajado: cambiar seq de la fila t no altera P_aj[t] (más allá de P, que es walk-forward)
cambios = 0
for t, src in filas:
    S3 = S.copy(); S3[t] = (S[t] + 7) % 38
    m1 = np.ones(38); m2 = np.ones(38)
    for k, mult in {1: 0.272, 3: 1.736}.items():
        if k in src: m1[S[src[k]]] *= mult; m2[S3[src[k]]] *= mult
    cambios += not np.allclose(m1, m2)
print(f"     cambiar el ganador de la propia fila t altera su multiplicador en {cambios} filas (debe ser 0)")

# --- 2. re-derivación en dev: q ∝ P·exp(b1·[ayer] + b3·[hace 3])
def diseño(tramo):
    X1, X3, Y, PP = [], [], [], []
    for t, src in filas:
        if TR[t] != tramo: continue
        x1 = np.zeros(38); x3 = np.zeros(38)
        if 1 in src: x1[S[src[1]]] = 1
        if 3 in src: x3[S[src[3]]] = 1
        X1.append(x1); X3.append(x3); Y.append(S[t]); PP.append(P[t])
    return np.array(X1), np.array(X3), np.array(Y), np.array(PP)
X1, X3, Y, PP = diseño("dev")
def nll(b, lam, X1=X1, X3=X3, Y=Y, PP=PP):
    lg = np.log(PP) + b[0] * X1 + b[1] * X3
    lg -= lg.max(1, keepdims=True)
    lq = lg - np.log(np.exp(lg).sum(1, keepdims=True))
    return -lq[np.arange(len(Y)), Y].sum() + lam * (b ** 2).sum()
print(f"\n[D2] dev: n={len(Y)} filas; con primero de ayer: {int(X1.sum())}, con primero de hace 3: {int(X3.sum())}")
for nombre, lam in (("sin L2", 0.0), ("L2 λ=0,5 (½·b²)", 0.5), ("L2 λ=1 (1·b²)", 1.0)):
    r = minimize(nll, np.zeros(2), args=(lam,), method="BFGS")
    print(f"     {nombre:16s} m1 = {np.exp(r.x[0]):.3f}   m3 = {np.exp(r.x[1]):.3f}")
# conteos O/E en dev (para un factor cada uno)
for k, X in ((1, X1), (3, X3)):
    O = int(X[np.arange(len(Y)), Y].sum()); E = (PP * X).sum()
    print(f"     k={k}: dev O={O} E(motor)={E:.2f} O/E={O/E:.3f}  (O+0,5)/(E+0,5)={(O+.5)/(E+.5):.3f}")
# por era en dev
for era, hh in (("9:00", 1), ("8:00", 0)):
    idx = [i for i, (t, src) in enumerate([f for f in filas if TR[f[0]] == "dev"]) if H[t] == hh]
    for k, X in ((1, X1), (3, X3)):
        O = int(X[idx][np.arange(len(idx)), Y[idx]].sum()); E = (PP[idx] * X[idx]).sum()
        print(f"     era {era} k={k}: O={O} E={E:.2f} O/E={O/E:.2f}")
# ¿qué darían los multiplicadores si se hubieran ajustado con prueba? (para ver que producción NO usó prueba)
X1p, X3p, Yp, PPp = diseño("prueba")
r = minimize(lambda b: nll(b, 1.0, X1p, X3p, Yp, PPp), np.zeros(2), method="BFGS")
print(f"     (contraste) ajustado SOLO en prueba con λ=1: m1={np.exp(r.x[0]):.3f} m3={np.exp(r.x[1]):.3f}")
X1a = np.r_[X1, X1p]; X3a = np.r_[X3, X3p]; Ya = np.r_[Y, Yp]; PPa = np.r_[PP, PPp]
r = minimize(lambda b: nll(b, 1.0, X1a, X3a, Ya, PPa), np.zeros(2), method="BFGS")
print(f"     (contraste) ajustado en dev+prueba con λ=1: m1={np.exp(r.x[0]):.3f} m3={np.exp(r.x[1]):.3f}")

# --- 3. mbits de P_aj vs P por tramo (re-cálculo independiente)
print("\n[D3] mbits por primer sorteo P_aj vs P")
for tr in ("dev", "prueba", "vivo"):
    ts = np.array([t for t, _ in filas if TR[t] == tr])
    g = 1000 * np.log2(PA[ts, S[ts]] / P[ts, S[ts]])
    dias = DI[ts]; boots = []
    rb = np.random.default_rng(1)
    for _ in range(2000):
        b = rb.integers(0, len(g), len(g)); boots.append(g[b].mean())
    print(f"     {tr:6s} n={len(ts)} {g.mean():+6.1f} [{np.percentile(boots,2.5):+.1f}; {np.percentile(boots,97.5):+.1f}]")
