# ag10 — control RD Int (rdint_hist.csv, 2023-09..) por periodo: primero=primero de ayer, contra azar 1/38
import csv
from datetime import date, timedelta
from scipy.stats import poisson
d = {}
for r in csv.DictReader(open("/home/user/lotto-activo/datos_multiloteria/rdint_hist.csv")):
    d[(r["fecha"], r["hora"])] = r["animal"]
pr = {}
for (f, h), a in sorted(d.items()): pr.setdefault(f, (h, a))
per = [("2023-09..2024-11-27", "2023-09-01", "2024-11-27"), ("2024-11-28..2025-06-30", "2024-11-28", "2025-06-30"),
       ("2025-07-01..2026-09", "2025-07-01", "2026-12-31")]
for nom, a, b in per:
    k = N = 0; horas = set()
    for f, (h, an) in pr.items():
        if not (a <= f <= b): continue
        y = (date.fromisoformat(f) - timedelta(days=1)).isoformat()
        if y in pr and pr[y][0] == h:
            N += 1; k += an == pr[y][1]; horas.add(h)
    print(f"RD {nom}: {k}/{N} azar {N/38:.1f} O/E {k/(N/38):.2f} P(<=k)={poisson.cdf(k, N/38):.2g} horas primer sorteo {sorted(horas)}")
