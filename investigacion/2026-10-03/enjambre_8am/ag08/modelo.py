# ag08 — logit condicional especializado en el primer sorteo, apilado sobre P_aj.
# Uso: python modelo.py            (solo dev: OOF anidado, ablación, coeficientes)
#      python modelo.py --prueba C1 [C2]   (mide UNA vez los candidatos congelados en prueba y vivo)
import os, sys, json, numpy as np
from scipy.optimize import minimize
os.environ.setdefault("OMP_NUM_THREADS", "1")
AQUI = os.path.dirname(os.path.abspath(__file__))
z = np.load(os.path.join(AQUI, "..", "base8.npz"), allow_pickle=True)
S, H, DI, F, tr, ep, PAJ = z["seq"], z["hora"], z["dia"], z["fecha"], z["tramo"], z["es_primero"], z["P_aj"]
n = len(S)
LAMS = [1, 3, 10, 30, 100, 300, 1000]
rng = np.random.default_rng(8)

# ---------- rasgos ----------
filas_dia = {}
for t in range(n): filas_dia.setdefault(int(DI[t]), []).append(t)
first = {d: v[0] for d, v in filas_dia.items()}
BINS_S = [(1, 6), (7, 12), (13, 18), (19, 24), (25, 36), (37, 48), (49, 72), (73, 108)]
BINS_D = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 6), (7, 10)]
NOM = ([f"A_ayer_pos{j+1}" for j in range(12)] + [f"B_anteayer_pos{j+1}" for j in range(12)] +
       [f"C_primero_hace{k}" for k in range(3, 11)] + [f"D_hueco_sorteos_{a}-{b}" for a, b in BINS_S] +
       [f"E_hueco_dias_{a}-{b}" for a, b in BINS_D] + ["F_n_1d", "F_n_3d", "F_n_7d"])
P0 = len(NOM)
NOM_ALL = NOM + ["G8x" + s for s in NOM]
BLOQ = np.array([s.split("_")[0] for s in NOM])

def rasgos(t):
    d = int(DI[t]); x = np.zeros((38, P0)); c = 0
    for k in (1, 2):
        for j, tt in enumerate(filas_dia.get(d - k, [])[:12]): x[S[tt], c + j] = 1
        c += 12
    for k in range(3, 11):
        if d - k in first: x[S[first[d - k]], c] = 1
        c += 1
    last = np.full(38, -1)
    for tt in range(max(0, t - 400), t): last[S[tt]] = tt
    for a in range(38):
        if last[a] < 0: continue
        g = t - last[a]; gd = d - DI[last[a]]
        for i, (lo, hi) in enumerate(BINS_S):
            if lo <= g <= hi: x[a, c + i] = 1
        for i, (lo, hi) in enumerate(BINS_D):
            if lo <= gd <= hi: x[a, c + len(BINS_S) + i] = 1
    c += len(BINS_S) + len(BINS_D)
    for i, k in enumerate((1, 3, 7)):
        for tt in range(max(0, t - 120), t):
            if d - k <= DI[tt] <= d - 1: x[S[tt], c + i] += 1
    return x

ROWS = np.where(ep & (tr != "cal"))[0]
X0 = np.stack([rasgos(t) for t in ROWS])                     # (N,38,P0)
ERA8 = (H[ROWS] == 0).astype(float)
XF = np.concatenate([X0, X0 * ERA8[:, None, None]], axis=2)  # shared + era-8:00 difference
Y = S[ROWS]; LP = np.log(PAJ[ROWS]); TR = tr[ROWS]; FE = F[ROWS]

def ajustar(X, lp, y, lam):
    p = X.shape[2]
    def f(b):
        s = lp + X @ b; s -= s.max(1, keepdims=True)
        e = np.exp(s); Z = e.sum(1); q = e / Z[:, None]
        ll = s[np.arange(len(y)), y] - np.log(Z)
        g = X[np.arange(len(y)), y] - np.einsum("na,nap->np", q, X)
        return -ll.sum() + lam * b @ b, -g.sum(0) + 2 * lam * b
    return minimize(f, np.zeros(p), jac=True, method="L-BFGS-B").x

def predecir(X, lp, b):
    s = lp + X @ b; s -= s.max(1, keepdims=True); e = np.exp(s); return e / e.sum(1, keepdims=True)

def ll_bits(q, y): return np.log2(q[np.arange(len(y)), y])

def rolling(idx, nb):
    bl = np.array_split(idx, nb); return [(np.concatenate(bl[:k]), bl[k]) for k in range(1, nb)]

def elegir_lam(X, lp, y, idx):
    best = None
    for lam in LAMS:
        tot = 0.0
        for a, b in rolling(idx, 5):
            beta = ajustar(X[a], lp[a], y[a], lam)
            tot += ll_bits(predecir(X[b], lp[b], beta), y[b]).sum()
        if best is None or tot > best[1]: best = (lam, tot)
    return best[0]

def boot(v, B=10000):
    m = v.mean(); bs = v[rng.integers(0, len(v), (B, len(v)))].mean(1)
    return 1000 * m, 1000 * np.percentile(bs, 2.5), 1000 * np.percentile(bs, 97.5), (bs <= 0).mean()

def topk(Pm, y, k): return int((np.argsort(-Pm, 1)[:, :k] == y[:, None]).any(1).sum())

def columnas(cand):
    if cand == "C1": return np.arange(2 * P0)
    nuevo = [i for i, s in enumerate(NOM) if not (s.startswith("A_") or s == "B_anteayer_pos1"
             or s in ("C_primero_hace3", "C_primero_hace4", "C_primero_hace7"))]
    return np.array(nuevo + [P0 + i for i in nuevo])

DEV = np.where(TR == "dev")[0]

def oof(cols, verbose=True):
    q = np.full((len(Y), 38), np.nan); lams = []
    X = XF[:, :, cols]
    for a, b in rolling(DEV, 6):
        lam = elegir_lam(X, LP, Y, a); lams.append(lam)
        beta = ajustar(X[a], LP[a], Y[a], lam); q[b] = predecir(X[b], LP[b], beta)
    m = ~np.isnan(q[:, 0])
    return q, m, lams

if __name__ == "__main__":
    res = {}
    if "--prueba" not in sys.argv:
        print("filas dev", len(DEV), "rasgos", XF.shape[2])
        for cand in ("C1", "C2"):
            cols = columnas(cand)
            q, m, lams = oof(cols)
            g = ll_bits(q[m], Y[m]) - ll_bits(np.exp(LP[m]), Y[m])
            r = boot(g); print(f"\n{cand} ({len(cols)} rasgos) OOF n={m.sum()} lams={lams}: mbits {r[0]:+.1f} [{r[1]:+.1f}; {r[2]:+.1f}] P(<=0)={r[3]:.3f}")
            res[cand] = dict(oof=r, lams=lams)
            for e, nm in ((0, "9:00"), (1, "8:00")):
                mm = m & (ERA8 == e); ge = ll_bits(q[mm], Y[mm]) - ll_bits(np.exp(LP[mm]), Y[mm]); re = boot(ge)
                print(f"   era {nm} n={mm.sum()}: {re[0]:+.1f} [{re[1]:+.1f}; {re[2]:+.1f}]  Top5 {topk(np.exp(LP[mm]),Y[mm],5)}->{topk(q[mm],Y[mm],5)}  Top15 {topk(np.exp(LP[mm]),Y[mm],15)}->{topk(q[mm],Y[mm],15)}")
                res[cand]["era" + nm] = re
            # por pliegue
            for k, (a, b) in enumerate(rolling(DEV, 6)):
                gb = ll_bits(q[b], Y[b]) - ll_bits(np.exp(LP[b]), Y[b])
                print(f"   pliegue {k+1} {FE[b[0]]}..{FE[b[-1]]}: {1000*gb.mean():+.1f}")
        # ablación (descriptiva): C1 sin cada bloque
        print("\nAblación sobre C1 (OOF mbits, quitando un bloque):")
        for bl in ("A", "B", "C", "D", "E", "F", "G"):
            if bl == "G": cols = np.arange(P0)
            else:
                keep = [i for i in range(P0) if BLOQ[i] != bl]; cols = np.array(keep + [P0 + i for i in keep])
            q, m, lams = oof(cols); g = ll_bits(q[m], Y[m]) - ll_bits(np.exp(LP[m]), Y[m]); r = boot(g, 2000)
            print(f"   sin {bl}: {r[0]:+.1f} [{r[1]:+.1f}; {r[2]:+.1f}] lams={lams}"); res["sin" + bl] = r
        # modelo final en todo dev y coeficientes
        for cand in ("C1", "C2"):
            cols = columnas(cand); X = XF[:, :, cols]
            lam = elegir_lam(X, LP, Y, DEV); beta = ajustar(X[DEV], LP[DEV], Y[DEV], lam)
            nm = [NOM_ALL[i] for i in cols]; o = np.argsort(-np.abs(beta))
            print(f"\n{cand} final: lambda={lam}; 12 coeficientes mayores (multiplicador exp(b)):")
            for i in o[:12]: print(f"   {nm[i]:28s} {beta[i]:+.3f}  x{np.exp(beta[i]):.2f}")
            np.savez(os.path.join(AQUI, f"congelado_{cand}.npz"), beta=beta, cols=cols, lam=lam, nombres=np.array(nm))
            res[cand]["lam_final"] = lam
            res[cand]["top"] = [(nm[i], float(beta[i])) for i in o[:12]]
        json.dump(res, open(os.path.join(AQUI, "res_dev.json"), "w"), indent=1, default=str)
    else:
        for cand in [a for a in sys.argv[1:] if a.startswith("C")]:
            zc = np.load(os.path.join(AQUI, f"congelado_{cand}.npz")); beta, cols = zc["beta"], zc["cols"]
            q = predecir(XF[:, :, cols], LP, beta)
            for t in ("prueba", "vivo"):
                m = TR == t; g = ll_bits(q[m], Y[m]) - ll_bits(np.exp(LP[m]), Y[m]); r = boot(g)
                print(f"{cand} {t} n={m.sum()}: mbits {r[0]:+.1f} [{r[1]:+.1f}; {r[2]:+.1f}] p1={r[3]:.4f}  "
                      f"Top5 {topk(np.exp(LP[m]),Y[m],5)}->{topk(q[m],Y[m],5)}  Top15 {topk(np.exp(LP[m]),Y[m],15)}->{topk(q[m],Y[m],15)}")
