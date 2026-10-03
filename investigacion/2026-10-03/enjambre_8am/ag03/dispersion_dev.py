# -*- coding: utf-8 -*-
"""ag03 — ¿el primer sorteo está SUB-disperso (más parejo que el azar)? Por hora, en cal+dev; simulación con la
restricción conocida 'no repite en el día' para ver si eso solo lo explica."""
import numpy as np
from scipy import stats
from comun import *
pre = (tramo == "cal") | (tramo == "dev")
for era, cond in (("9:00 (hasta 2024-11-27)", fecha <= "2024-11-27"), ("8:00 (dev)", fecha >= "2024-11-28")):
    print("era", era)
    for h in range(12):
        F = np.where(pre & cond & (hora == h))[0]
        if len(F) < 100: continue
        c = np.bincount(seq[F], minlength=38); chi = stats.chisquare(c).statistic
        print(f"  hora {h:2d} n={len(F)} chi2={chi:5.1f} P(chi2<=obs)={stats.chi2.cdf(chi,37):.3f}"
              f"{'  <- primer' if prim[F].mean() > .9 else ''}")
# chi2 por hora sobre todo pre-prueba (mezcla eras): ranking del primer sorteo entre las 12 horas
