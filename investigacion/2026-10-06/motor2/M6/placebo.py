import sys, os, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
z = np.load(os.path.join(A.SP, "m6_rasgos.npz")); M, DF = z["M"], z["DF"]
m = np.where(A.TRAMOS["AJUSTE"])[0]; y = A.Y; P = A.PROD; rng = np.random.default_rng(0)
dias = np.unique(A.F[m]); mx = []
Mm = M[:, m]; DFm = DF[:, m]; qq = (Mm * P[m][None]).sum(2)
for r in range(40):
    # placebo: cada fila recibe el ganador de la misma hora de otra jornada de AJUSTE (permutación de jornadas)
    perm = dict(zip(dias, rng.permutation(dias))); idx = {(f, h): i for i, f, h in zip(m, A.F[m], A.H[m])}
    yp = np.array([y[idx.get((perm[f], h), i)] for i, f, h in zip(m, A.F[m], A.H[m])])
    hit = Mm[:, np.arange(len(m)), yp]
    O = (hit * DFm).sum(1); E = (qq * DFm).sum(1); V = (qq * (1 - qq) * DFm).sum(1)
    zz = (O - E) / np.sqrt(np.maximum(V, 1e-9)); mx.append(np.abs(zz).max())
print("max|z| nulo (40 permutaciones de jornadas): mediana %.2f, p90 %.2f, p95 %.2f, max %.2f" % (np.median(mx), *np.quantile(mx, [.9, .95]), max(mx)))
