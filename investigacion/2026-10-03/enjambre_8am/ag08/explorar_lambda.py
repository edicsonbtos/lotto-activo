# Exploración descriptiva en dev (no anidada): OOF rolling-origin con lambda FIJO, por subconjunto de rasgos.
import sys; sys.argv = ["x"]
from modelo import *
def oof_fijo(cols, lam):
    q = np.full((len(Y), 38), np.nan); X = XF[:, :, cols]
    for a, b in rolling(DEV, 6):
        q[b] = predecir(X[b], LP[b], ajustar(X[a], LP[a], Y[a], lam))
    m = ~np.isnan(q[:, 0]); g = ll_bits(q[m], Y[m]) - ll_bits(np.exp(LP[m]), Y[m])
    pf = [1000 * (ll_bits(q[b], Y[b]) - ll_bits(np.exp(LP[b]), Y[b])).mean() for _, b in rolling(DEV, 6)]
    return boot(g, 2000), pf
def sub(bloques, era=True):
    keep = [i for i in range(P0) if BLOQ[i] in bloques]
    return np.array(keep + ([P0 + i for i in keep] if era else []))
SUBS = {"C1": np.arange(2 * P0), "C1_sin_era": np.arange(P0), "F": sub("F", False), "E": sub("E", False),
        "DEF": sub("DEF", False), "AB": sub("AB", False), "C": sub("C", False)}
for nm, cols in SUBS.items():
    for lam in [10, 100, 1000, 3000, 10000]:
        r, pf = oof_fijo(cols, lam)
        print(f"{nm:11s} lam={lam:6d}: {r[0]:+6.1f} [{r[1]:+6.1f}; {r[2]:+6.1f}]  pliegues " + " ".join(f"{x:+.0f}" for x in pf), flush=True)
