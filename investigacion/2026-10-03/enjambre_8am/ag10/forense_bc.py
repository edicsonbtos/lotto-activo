# ag10 — B (historial vs fuentes externas) y C (patrón en la fuente externa sola + controles)
import os, sys, csv, json, collections
from datetime import date, timedelta
import numpy as np
from scipy.stats import poisson, binom

AQUI = os.path.dirname(os.path.abspath(__file__)); BASE = os.path.dirname(AQUI)
ML = "/home/user/lotto-activo/datos_multiloteria"
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}

# ---------------- historial
hist = {}
for ln in open(os.path.join(BASE, "hist_la.txt"), encoding="utf-8"):
    p = ln.split()
    if len(p) == 3:
        hist.setdefault((p[0], int(p[1])), []).append(p[2])
dup = {k: v for k, v in hist.items() if len(v) > 1}
print("historial: lineas", sum(len(v) for v in hist.values()), "slots", len(hist), "duplicados", len(dup))
bad = [k for k, v in hist.items() if v[0] not in IDX]
print("codigos invalidos", len(bad))
hist = {k: v[0] for k, v in hist.items()}

# ---------------- oficial
def leer_oficial(juego):
    out = {}
    hh0 = None
    for r in csv.DictReader(open(os.path.join(ML, "oficial_multi.csv"))):
        if r["juego"] != juego: continue
        out[(r["fecha"], r["hora"])] = r["codigo"]
    return out
of1 = leer_oficial("1")
of1h = {(f, int(h[:2]) - 8): c for (f, h), c in of1.items()}
print("oficial juego1 slots", len(of1h), min(f for f, _ in of1h), max(f for f, _ in of1h))
codes_of = collections.Counter(of1h.values()); print("codigos oficiales distintos", len(codes_of), "00 aparece", codes_of.get("00", 0), "0 aparece", codes_of.get("0", 0))

lo, hi = "2025-07-01", "2026-09-22"
hs = {k: v for k, v in hist.items() if lo <= k[0] <= hi}
solo_h = sorted(set(hs) - set(of1h)); solo_o = sorted(set(of1h) - set(hs))
diff = sorted(k for k in set(hs) & set(of1h) if hs[k] != of1h[k])
print(f"\n[B1] historial vs oficial {lo}..{hi}: comunes {len(set(hs)&set(of1h))}, solo historial {len(solo_h)}, solo oficial {len(solo_o)}, valores distintos {len(diff)}")
print("  solo historial:", solo_h[:20]); print("  solo oficial:", solo_o[:20]); print("  distintos:", [(k, hs[k], of1h[k]) for k in diff[:30]])

def primeros(d):
    pr = {}
    for (f, h), c in sorted(d.items()):
        pr.setdefault(f, (h, c))
    return pr
ph, po = primeros(hs), primeros(of1h)
dif_pr = [f for f in ph if f in po and ph[f] != po[f]]
print("  primeros sorteos distintos (hora o código):", len(dif_pr), dif_pr[:20])

def pares_rep(pr):
    """{fecha: (repite?, hora)} para días con ayer presente y misma hora del primero."""
    out = {}
    for f, (h, c) in pr.items():
        y = (date.fromisoformat(f) - timedelta(days=1)).isoformat()
        if y in pr and pr[y][0] == h:
            out[f] = c == pr[y][1]
    return out
rh, ro = pares_rep(ph), pares_rep(po)
print(f"  repeticiones primero-ayer: historial {sum(rh.values())}/{len(rh)}, oficial {sum(ro.values())}/{len(ro)}")
print("  días con repetición en OFICIAL y no en historial:", [f for f in ro if ro[f] and not rh.get(f, False)])
print("  días con repetición en historial y no en oficial:", [f for f in rh if rh[f] and not ro.get(f, False)])
print("  días-par en oficial y no en historial:", [f for f in ro if f not in rh])
print("  días-par en historial y no en oficial:", [f for f in rh if f not in ro])

# ---------------- LH+TZ (lottoactivo.csv) — número 0..36, el 0 no distingue Delfín/Ballena
lh = {}
for r in csv.DictReader(open(os.path.join(ML, "lottoactivo.csv"))):
    lh[(r["fecha"], int(r["hora"][:2]) - 8)] = (r["numero"], r["animal"])
def norm(c): return "0" if c in ("0", "00") else c
lo2, hi2 = min(f for f, _ in lh), max(f for f, _ in lh)
hs2 = {k: v for k, v in hist.items() if lo2 <= k[0] <= hi2}
d2 = sorted(k for k in set(hs2) & set(lh) if norm(hs2[k]) != lh[k][0])
print(f"\n[B2] historial vs lottoactivo.csv (LH+TZ) {lo2}..{hi2}: comunes {len(set(hs2)&set(lh))}, solo hist {len(set(hs2)-set(lh))}, solo LH {len(set(lh)-set(hs2))}, distintos {len(d2)} {d2[:10]}")
print("  solo LH:", sorted(set(lh) - set(hs2))[:10], " solo hist:", sorted(set(hs2) - set(lh))[:10])
lhn = {k: v[0] for k, v in lh.items()}
rl = pares_rep(primeros(lhn)); rh2 = pares_rep(primeros({k: norm(v) for k, v in hs2.items()}))
print(f"  repeticiones primero-ayer: LH {sum(rl.values())}/{len(rl)}, historial (mismo tramo) {sum(rh2.values())}/{len(rh2)}")
# oficial vs LH en solape
d3 = sorted(k for k in set(of1h) & set(lh) if norm(of1h[k]) != lh[k][0])
print(f"  oficial vs LH: comunes {len(set(of1h)&set(lh))}, distintos {len(d3)}")

# ---------------- C: patrón en fuentes externas solas
def resumen_patron(nombre, d, K=38, nh=None):
    pr = primeros(d)
    rp = pares_rep(pr)
    N = len(rp); k = sum(rp.values()); E = N / K
    # control: misma hora de ayer en las demás horas (no primeras)
    firsts = {(f, h) for f, (h, _) in pr.items()}
    kc = Nc = 0
    for (f, h), c in d.items():
        if (f, h) in firsts: continue
        y = (date.fromisoformat(f) - timedelta(days=1)).isoformat()
        if (y, h) in d:
            Nc += 1; kc += c == d[(y, h)]
    # hace 3 días
    k3 = N3 = 0
    for f, (h, c) in pr.items():
        y = (date.fromisoformat(f) - timedelta(days=3)).isoformat()
        if y in pr and pr[y][0] == h:
            N3 += 1; k3 += c == pr[y][1]
    print(f"  {nombre:34s} primero=primero ayer {k:3d}/{N:4d} (azar {E:5.1f}) O/E {k/E:4.2f} P(<=k)={poisson.cdf(k,E):.2g} | "
          f"demás horas misma hora ayer {kc}/{Nc} O/E {kc/(Nc/K):4.2f} | primero hace 3 días {k3}/{N3} O/E {k3/(N3/K):4.2f} P(>=k)={poisson.sf(k3-1,N3/K):.2g}")
    return k, N
print("\n[C] patrón crudo contra azar 1/38 (sin motor)")
resumen_patron("LA oficial (juego 1) 2025-07..09-22", of1h)
resumen_patron("LA historial mismo tramo", hs)
resumen_patron("LA LH+TZ 2026-04..09", lhn, K=37)
of2 = leer_oficial("2"); of2h = {(f, int(h[:2]) - 8): c for (f, h), c in of2.items()}
of3 = leer_oficial("3"); of3h = {(f, int(h[:2]) - 8): c for (f, h), c in of3.items()}
resumen_patron("RD Int oficial (juego 2)", of2h)
resumen_patron("LARD oficial (juego 3)", of3h)
rd = {}
NOMB = {}
for r in csv.DictReader(open(os.path.join(ML, "rdint_hist.csv"))):
    rd[(r["fecha"], int(r["hora"][:2]) - 8)] = r["animal"]
resumen_patron("RD Int rdint_hist 2023-09..", rd)
for nombre in ("lottoactivordint", "lagranjita", "guacharoactivo", "selvaplus"):
    dd = {}
    for r in csv.DictReader(open(os.path.join(ML, nombre + ".csv"))):
        dd[(r["fecha"], int(r["hora"][:2]))] = r["numero"]
    Kt = int(r["n_tablero"])
    resumen_patron(f"{nombre} (K={Kt}) 2026-04..", dd, K=Kt)

# LA oficial por subtramo (dev = hasta 2025-12-19, prueba = 2025-12-20..)
print("\n[C2] LA oficial por tramo")
resumen_patron("oficial 2025-07-01..2025-12-19 (dev)", {k: v for k, v in of1h.items() if k[0] <= "2025-12-19"})
resumen_patron("oficial 2025-12-20..2026-09-14 (prueba)", {k: v for k, v in of1h.items() if "2025-12-19" <= k[0] <= "2026-09-14"})
