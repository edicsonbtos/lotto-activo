"""Ganancia de M2/M6 sobre la JUGADA EN VIVO (Top-5 de PROD con la regla de cambio RD (h-1):30). Exploratorio."""
import sys, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
SP = A.SP
rdD = A.LE.cargar("/home/user/lotto-activo/rdint_historial.txt")
rd = {(f, int(h)): int(s) for f, h, s in zip(rdD.fecha, rdD.hora, rdD.seq)}
M = {"PROD": A.PROD, "M6": np.load(SP + "/motor2_M6.npz")["P"], "M2": np.load(SP + "/motor2_M2.npz")["P"]}
lp = np.log(A.PROD); comb = np.exp(np.log(M["M6"]) + np.log(M["M2"]) - lp); M["M2+M6 (expl.)"] = comb / comb.sum(1, keepdims=True)
FI = np.array([2, 2, 2, 1, 1])
def top5(P, i, cambio):
    o = list(np.argsort(-P[i], kind="stable")[:6])
    r = rd.get((A.F[i], int(A.H[i]) - 1), -1) if A.H[i] >= 1 else -1
    if cambio and r in o[:5]: o.remove(r)
    return o[:5]
for tr in ("AJUSTE", "ELECCION", "PRUEBA26"):
    idx = np.where(A.TRAMOS[tr] & np.array([A.H[i] == 0 or (A.F[i], int(A.H[i]) - 1) in rd for i in range(len(A.T))]))[0]
    print(f"== {tr} (n={len(idx)}, con RD disponible) ==")
    for nm, P in M.items():
        for cambio in ((True,) if nm != "PROD" else (False, True)):
            g = []; h = 0
            for i in idx:
                o = top5(P, i, cambio); y = A.Y[i]
                if y in o: g.append(30 * FI[o.index(y)]); h += 1
                else: g.append(0)
            g = np.array(g) / 8 - 1
            ds = A.F[idx]; u, inv = np.unique(ds, return_inverse=True); per = np.bincount(inv, g); cnt = np.bincount(inv)
            se = np.sqrt(((per - g.mean() * cnt) ** 2).sum() * len(u) / (len(u) - 1)) / len(g)
            print(f"   {nm:14} {'+cambio' if cambio else 'sin cambio':10} Top-5 {h/len(idx)*100:5.1f}%  retorno {g.mean()*100:+6.1f}% [IC90 {100*(g.mean()-1.645*se):+.0f};{100*(g.mean()+1.645*se):+.0f}]")
