"""A2 exploratorio (POST-HOC, no pre-registrado): el control 'repetición en el mismo día' por día de semana.
Uso: python3 explora.py <SP>"""
import sys, csv, collections as C
from datetime import date
import numpy as np
sys.argv = sys.argv[:2]
import replica as R
RNG = np.random.default_rng(7)
dn = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

def arr(j, lo, hi):
    N, F = R.filas(j, lo, hi)
    f = np.array([r[0] for r in F]); dw = np.array([r[1] for r in F]); hr = np.array([r[2] for r in F])
    O, E1, Orp, Erp = (np.array([r[k] for r in F], float) for k in (3, 4, 6, 7))
    return N, f, dw, hr, O, E1, Orp, Erp

def perm_p(f, hr, O, E, A_days_fn, nperm=3000, lado="mayor"):
    dias, di = np.unique(f, return_inverse=True)
    dA = A_days_fn(dias); A = dA[di]
    rr = R.rr_mh(None, hr, O, E, A); c = 0
    for _ in range(nperm):
        x = R.rr_mh(None, hr, O, E, RNG.permutation(dA)[di]); c += (x >= rr) if lado == "mayor" else (x <= rr)
    return rr, (c + 1) / (nperm + 1)

mvf = lambda d: np.isin([date.fromisoformat(x).weekday() for x in d], [2, 3, 4])
dom = lambda d: np.array([date.fromisoformat(x).weekday() == 6 for x in d])
print("1) Control: repetición mismo día, RR_MH (grupo vs resto), p unilateral por permutación de jornadas")
for nom, j, lo, hi, g, gn in [("LA dev", "LA", "2024-01-01", "2025-12-31", dom, "dom"), ("LA dev", "LA", "2024-01-01", "2025-12-31", mvf, "mié-vie"),
                              ("LA 2026", "LA", "2026-01-01", "2026-10-05", mvf, "mié-vie"), ("LA 2026", "LA", "2026-01-01", "2026-10-05", dom, "dom"),
                              ("RD dev", "RD", "2024-01-01", "2025-12-31", dom, "dom"), ("RD dev", "RD", "2024-01-01", "2025-12-31", mvf, "mié-vie"),
                              ("RD 2026", "RD", "2026-01-01", "2026-09-22", mvf, "mié-vie"), ("RD 2026", "RD", "2026-01-01", "2026-09-22", dom, "dom"),
                              ("Granjita", "GRANJITA", "2026-04-13", "2026-09-13", mvf, "mié-vie")]:
    N, f, dw, hr, O, E1, Orp, Erp = arr(j, lo, hi)
    rr, p = perm_p(f, hr, Orp, Erp, g)
    print(f"  {nom:9} {gn:8} RR {rr:.2f}  p {p:.4f}")

print("\n2) Repetición mismo día O/E por mes, LA y RD: mié-vie | dom | lun-mar+sáb   (n repeticiones)")
for j, lo, hi in [("LA", "2023-09-01", "2026-10-05"), ("RD", "2023-09-01", "2026-09-22")]:
    N, f, dw, hr, O, E1, Orp, Erp = arr(j, lo, hi)
    mes = np.array([x[:7] for x in f])
    print(" ", j)
    for m in np.unique(mes):
        s = mes == m; a = s & np.isin(dw, [2, 3, 4]); b = s & (dw == 6); c = s & np.isin(dw, [0, 1, 5])
        q = lambda k: f"{Orp[k].sum() / Erp[k].sum():.2f}({int(Orp[k].sum()):2d})"
        print(f"    {m}  {q(a)}  {q(b)}  {q(c)}")

print("\n3) Descomposición del reciclaje (LA, RD, Granjita): solo sorteos cuyo ganador es NUEVO hoy (∉ T);"
      " tasa de S\\T vs |S\\T|/(N-|T|)")
for nom, j, lo, hi in [("LA dev", "LA", "2024-01-01", "2025-12-31"), ("LA 2026", "LA", "2026-01-01", "2026-10-05"),
                       ("RD 2026", "RD", "2026-01-01", "2026-09-22"), ("Granjita", "GRANJITA", "2026-04-13", "2026-09-13")]:
    N, f, dw, hr, O, E1, Orp, Erp = arr(j, lo, hi)
    nuevo = Orp == 0
    rr, p = perm_p(f[nuevo], hr[nuevo], O[nuevo], E1[nuevo], mvf, 2000, "menor")
    A = np.isin(dw, [2, 3, 4])
    print(f"  {nom:9} nuevos: O/E mié-vie {O[nuevo & A].sum() / E1[nuevo & A].sum():.3f} | resto {O[nuevo & ~A].sum() / E1[nuevo & ~A].sum():.3f}"
          f"  RR {rr:.3f} p {p:.4f}   | fracción de repeticiones mismo día: mié-vie {Orp[A].mean() * 100:.1f}% resto {Orp[~A].mean() * 100:.1f}%")

print("\n4) LA 2026: distancia (en sorteos) entre la repetición y su aparición anterior en el día; mié-vie vs resto")
G, std = R.leer("LA")
for lab, ks in (("mié-vie", (2, 3, 4)), ("resto", (0, 1, 5, 6))):
    gap = C.Counter()
    for fch in G:
        if not ("2026-01-01" <= fch <= "2026-10-05") or date.fromisoformat(fch).weekday() not in ks: continue
        hs = std(fch); seq = [G[fch].get(h) for h in hs]
        for i, y in enumerate(seq):
            prev = [k for k in range(i) if seq[k] == y]
            if prev and y is not None: gap[i - prev[-1]] += 1
    print(f"  {lab}: {dict(sorted(gap.items()))}")

print("\n5) LA: hist_0605 contra API oficial (juego 1), 2025-07-01..2026-09-22")
H = {}
for ln in open(R.SP + "/hist_0605.txt"):
    p = ln.split()
    if len(p) == 3: H[(p[0], f"{8 + int(p[1]):02d}:00")] = p[2]
ok = tot = 0; rep_of = C.Counter()
OF = C.defaultdict(dict)
for r in csv.DictReader(open(R.DM + "oficial_multi.csv")):
    if r["juego"] == "1":
        OF[r["fecha"]][r["hora"]] = r["codigo"]; tot += 1; ok += H.get((r["fecha"], r["hora"])) == r["codigo"]
print(f"  coinciden {ok}/{tot}")
for lab, ks in (("mié-vie", (2, 3, 4)), ("resto", (0, 1, 5, 6))):
    for per, lo, hi in (("2025-S2", "2025-07-01", "2025-12-31"), ("2026", "2026-01-01", "2026-09-22")):
        nd = nr = 0
        for fch, d in OF.items():
            if lo <= fch <= hi and date.fromisoformat(fch).weekday() in ks:
                v = [d[h] for h in sorted(d)]; nd += 1; nr += len(v) - len(set(v))
        print(f"  oficial LA {per} {lab}: repeticiones mismo día por jornada {nr / nd:.2f} ({nd} jornadas)")

print("\n6) LA 2026 por trimestre: repetición mismo día O/E y reciclaje O/E1, mié-vie | resto")
N, f, dw, hr, O, E1, Orp, Erp = arr("LA", "2026-01-01", "2026-10-05")
A = np.isin(dw, [2, 3, 4])
for lo, hi in (("2026-01-01", "2026-03-31"), ("2026-04-01", "2026-06-30"), ("2026-07-01", "2026-10-05")):
    s = (f >= lo) & (f <= hi)
    print(f"  {lo[:7]}: rep {Orp[s & A].sum() / Erp[s & A].sum():.2f} | {Orp[s & ~A].sum() / Erp[s & ~A].sum():.2f}   "
          f"recic {O[s & A].sum() / E1[s & A].sum():.2f} | {O[s & ~A].sum() / E1[s & ~A].sum():.2f}")
