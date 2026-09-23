# -*- coding: utf-8 -*-
"""Control 1 del hilo 7: heterogeneidad por semestre de B1 (caché rdint/cache_todo.npz).
Criterio en herramientas/resultados/hilo7_controles.md (fijado antes de correr).
Uso: python herramientas/exploracion/controles_rd1.py
"""
import numpy as np
from scipy import stats
import controles_rd_comun as C

SEM = [("2024a", "2024-03-01", "2024-07-01"), ("2024b", "2024-07-01", "2025-01-01"),
       ("2025a", "2025-01-01", "2025-07-01"), ("2025b", "2025-07-01", "2026-01-01"),
       ("2026a", "2026-01-01", "2026-07-01"), ("2026b", "2026-07-01", "2026-09-14")]


def boot_se(v, dia, rng, nboot=2000):
    _, g = np.unique(dia, return_inverse=True)
    S = np.bincount(g, weights=v); Cn = np.bincount(g).astype(float); nd = len(S)
    idx = rng.integers(0, nd, size=(nboot, nd))
    b = S[idx].sum(1) / Cn[idx].sum(1)
    return float(v.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5)), float(b.std())


def main():
    d = C.cargar_cache(); rng = np.random.default_rng(101)
    y, dia, fecha = d["y"], d["dia"], d["fecha"]
    dm = C.delta(d["P1"], d["P0"], y)
    _, r3, r5 = C.CM.apuestas(d["P1"], y)
    metr = [("Δ mbits B1−B0", dm, 1.0), ("Top-3 plano, % por ficha", r3, 100.0),
            ("Top-5 escalonado, % por ficha", r5, 100.0)]
    sel = [(fecha >= a) & (fecha < b) for _, a, b in SEM]
    print("semestre | sorteos | dias")
    for (s, _, _), m in zip(SEM, sel):
        print(s, int(m.sum()), len(np.unique(dia[m])))
    for nombre, v, esc in metr:
        v = v * esc
        R = [boot_se(v[m], dia[m], rng) for m in sel]
        mu = np.array([r[0] for r in R]); se = np.array([r[3] for r in R]); w = 1 / se ** 2
        mp = (w * mu).sum() / w.sum(); Q = (w * (mu - mp) ** 2).sum(); pQ = stats.chi2.sf(Q, len(mu) - 1)
        I2 = max(0.0, (Q - (len(mu) - 1)) / Q) if Q > 0 else 0.0
        # 2025b contra el resto
        i = 3; resto = np.zeros(len(y), bool)
        for j, m in enumerate(sel):
            if j != i:
                resto |= m
        mr = boot_se(v[resto], dia[resto], rng)
        z = (mu[i] - mr[0]) / np.sqrt(se[i] ** 2 + mr[3] ** 2); pz = 2 * stats.norm.sf(abs(z))
        # tendencia: WLS de mu sobre indice
        x = np.arange(len(mu)); X = np.c_[np.ones_like(x), x]
        cov = np.linalg.inv(X.T @ (w[:, None] * X)); beta = cov @ X.T @ (w * mu)
        zt = beta[1] / np.sqrt(cov[1, 1]); pt = 2 * stats.norm.sf(abs(zt))
        print("\n## %s" % nombre)
        for (s, _, _), r in zip(SEM, R):
            print("%s  %+.2f [%+.2f, %+.2f]  ee %.2f" % (s, r[0], r[1], r[2], r[3]))
        print("resto (sin 2025b) %+.2f [%+.2f, %+.2f]" % mr[:3])
        print("media ponderada %+.2f; Cochran Q=%.2f gl=%d p=%.4f I2=%.0f%%" % (mp, Q, len(mu) - 1, pQ, 100 * I2))
        print("2025b vs resto: z=%+.2f p=%.4f" % (z, pz))
        print("tendencia: pendiente %+.2f por semestre (ee %.2f) z=%+.2f p=%.4f" % (beta[1], np.sqrt(cov[1, 1]), zt, pt))


if __name__ == "__main__":
    main()
