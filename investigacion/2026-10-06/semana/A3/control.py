from comun import *
import csv
from collections import defaultdict
rng = np.random.default_rng(11)
dn = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
print("Control de selección: Top-15 O/E y repeticiones del día (O/E motor) para las 7 ternas de días consecutivos, 2026")
u, inv = np.unique(dayid[A26], return_inverse=True)
o_d = np.bincount(inv, IN15[A26]); e_d = np.bincount(inv, M15[A26])
r_d = np.bincount(inv, HOYB[rows, y][A26]); re_d = np.bincount(inv, (P * HOYB).sum(1)[A26])
dw_d = np.array([dow[A26][inv == i][0] for i in range(len(u))])
zs = []
for s in range(7):
    tri = [(s + k) % 7 for k in range(3)]; a = np.isin(dw_d, tri)
    # z de la diferencia O/E terna vs resto, bootstrap por días
    def st(ix_a, ix_b): return o_d[ix_a].sum() / e_d[ix_a].sum() - o_d[ix_b].sum() / e_d[ix_b].sum()
    A, B = np.flatnonzero(a), np.flatnonzero(~a); d0 = st(A, B)
    bs = [st(rng.choice(A, len(A)), rng.choice(B, len(B))) for _ in range(1000)]
    zs.append(d0 / np.std(bs))
    print(f"  {'-'.join(dn[k] for k in tri):12} Top-15 O/E {o_d[a].sum()/e_d[a].sum():.2f} vs resto {o_d[~a].sum()/e_d[~a].sum():.2f}  z {zs[-1]:+.1f}  | repeticiones O/E {r_d[a].sum()/re_d[a].sum():.2f} vs resto {r_d[~a].sum()/re_d[~a].sum():.2f}")
from scipy.stats import norm
zm = min(zs); print(f"  min z {zm:.1f}: p unilateral {norm.cdf(zm):.1e}, ×7 = {7*norm.cdf(zm):.1e}")
# permutación de etiquetas de día de semana por SEMANAS (bloque) — preserva la estructura temporal
print("\nPermutación: barajar el día de la semana dentro de cada semana (2000 veces); estadístico = mínimo O/E de las 7 ternas")
wk = (dia_t[A26][np.searchsorted(np.flatnonzero(A26), np.flatnonzero(A26))] if False else None)
dias_u = np.array([dia_t[A26][inv == i][0] for i in range(len(u))]); semana = (dias_u - dw_d) // 7
def min_tri(dw):
    return min(o_d[np.isin(dw, [(s + k) % 7 for k in range(3)])].sum() / e_d[np.isin(dw, [(s + k) % 7 for k in range(3)])].sum() for s in range(7))
obs = min_tri(dw_d); cnt = 0
for _ in range(2000):
    dw = dw_d.copy()
    for w_ in np.unique(semana):
        ix = np.flatnonzero(semana == w_); dw[ix] = rng.permutation(dw[ix])
    cnt += min_tri(dw) <= obs
print(f"  observado {obs:.3f}; p perm = {(cnt+1)/2001:.4f}")

print("\nOtras loterías (sin motor): repeticiones del día por sorteo, MVF vs SM (O/E contra azar puro con su tablero)")
def rep_stats(rows_, nb, nsort, lab):
    by = defaultdict(list)
    for fe, ho, c in rows_: by[fe].append((ho, c))
    res = defaultdict(lambda: [0, 0.0, 0])
    for fe, l in by.items():
        l.sort(); seen = set(); g = "MVF" if date.fromisoformat(fe).weekday() in (2, 3, 4) else "SM"
        era = fe[:4] if fe >= "2026-01-01" else "pre26"
        for k, (ho, c) in enumerate(l):
            res[(era, g)][0] += c in seen; res[(era, g)][1] += len(seen) / nb; res[(era, g)][2] += 1; seen.add(c)
    s = f"  {lab:14}"
    for era in ("pre26", "2026"):
        for g in ("MVF", "SM"):
            if (era, g) in res:
                o, e, nn = res[(era, g)]; s += f" | {era} {g} {o/e:.2f} (n={nn})"
    print(s)
def leer(path, fc, fh, fv, filt=None):
    out = []
    with open(path) as fh_:
        for r in csv.DictReader(fh_):
            if filt and not filt(r): continue
            out.append((r[fc], r[fh], r[fv]))
    return out
B = "/home/user/lotto-activo/datos_multiloteria/"
la = [(D.fecha[T], int(HORA[T]), int(SEQ[T])) for T in range(n) if D.fecha[T] >= "2024-03-01"]
rep_stats(la, 38, 12, "Lotto Activo")
rep_stats([r for r in leer(B + "rdint_hist.csv", "fecha", "hora", "animal") if r[0] >= "2024-03-01"], 38, 12, "RD Internac.")
rep_stats(leer(B + "oficial_multi.csv", "fecha", "hora", "codigo", lambda r: r["juego"] == "3"), 38, 14, "LARD")
rep_stats(leer(B + "lagranjita.csv", "fecha", "hora", "numero"), 37, 12, "La Granjita")
rep_stats(leer(B + "selvaplus.csv", "fecha", "hora", "numero"), 100, 12, "Selva Plus")
rep_stats(leer(B + "guacharoactivo.csv", "fecha", "hora", "numero"), 76, 12, "Guácharo")
