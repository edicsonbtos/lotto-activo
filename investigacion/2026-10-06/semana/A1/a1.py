"""A1: validación día por día del efecto mié-vie. Uso: python a1.py <SP>"""
import sys, numpy as np
from datetime import date
from itertools import combinations
sys.path.insert(0, "/home/user/lotto-activo/herramientas"); import lotto_eval as LE
S = sys.argv[1]
D = LE.cargar(S + "/hist_0605.txt"); FD = np.array(D.fecha)
z = np.load(S + "/prod_0605.npz", allow_pickle=True); P, t, y, f, h = z["P"], z["t"], z["y"], z["f"], z["h"].astype(int)
n = len(y); ar = np.arange(n)
o = np.argsort(-P, 1, kind="stable"); rk = np.argmax(o == y[:, None], 1)
srt = np.take_along_axis(P, o, 1)
in15 = (rk < 15).astype(float); m15 = srt[:, :15].sum(1)
in5 = (rk < 5).astype(float); m5 = srt[:, :5].sum(1)
mb = 1000 * np.log2(38 * P[ar, y])
fich = np.array([2, 2, 2, 1, 1]); ret = np.where(rk < 5, 30 * fich[np.minimum(rk, 4)], 0) / 8 - 1
dow = np.array([date.fromisoformat(d).weekday() for d in f]); MVF = np.isin(dow, [2, 3, 4])
NOM = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
fu, dn = np.unique(f, return_inverse=True)            # jornada de cada sorteo
cnt_hist = {d: c for d, c in zip(*np.unique(FD, return_counts=True))}
FER = {"2026-01-01", "2026-02-16", "2026-02-17", "2026-04-02", "2026-04-03", "2026-04-19", "2026-05-01",
       "2026-06-24", "2026-07-05", "2026-07-24"}
RNG = np.random.default_rng(12345); B = 4000

def boot_days(m, fn, B=B):
    """fn(idx de sorteos) -> escalar; bootstrap por jornada."""
    ds = np.unique(dn[m]); grupos = [ar[m & (dn == d)] for d in ds] if False else None
    idx = ar[m]; dd = dn[m]; u, inv = np.unique(dd, return_inverse=True)
    orden = np.argsort(inv, kind="stable"); idx = idx[orden]; inv = inv[orden]
    cortes = np.r_[0, np.cumsum(np.bincount(inv))]
    out = []
    for _ in range(B):
        s = RNG.integers(0, len(u), len(u))
        sel = np.concatenate([idx[cortes[k]:cortes[k + 1]] for k in s])
        out.append(fn(sel))
    return np.percentile(out, [2.5, 97.5])

def agg_day(m, a, b):
    """suma por jornada de a y b para sorteos en m -> arrays alineados por jornada."""
    u = np.unique(dn[m]); A = np.bincount(dn[m], a[m], minlength=len(fu))[u]; Bb = np.bincount(dn[m], b[m], minlength=len(fu))[u]
    return A, Bb

def ci_ratio(m, a, b):
    A, Bb = agg_day(m, a, b); k = len(A); s = RNG.integers(0, k, (B, k))
    r = A[s].sum(1) / Bb[s].sum(1); return np.percentile(r, [2.5, 97.5])

def ci_mean(m, a):
    A, N = agg_day(m, a, np.ones(n)); k = len(A); s = RNG.integers(0, k, (B, k))
    r = A[s].sum(1) / N[s].sum(1); return np.percentile(r, [2.5, 97.5])

def zval(m):
    return (in15[m].sum() - m15[m].sum()) / np.sqrt((m15[m] * (1 - m15[m])).sum())

def fila(lab, m):
    oe = in15[m].sum() / m15[m].sum(); c = ci_ratio(m, in15, m15)
    o5 = in5[m].sum() / m5[m].sum()
    cm = ci_mean(m, mb); cr = ci_mean(m, ret)
    return (f"{lab:10} n={m.sum():5d} jorn={len(np.unique(dn[m])):3d} | Top-15 O/E {oe:.3f} [{c[0]:.2f};{c[1]:.2f}] z{zval(m):+5.1f}"
            f" | mbits {mb[m].mean():+6.0f} [{cm[0]:+.0f};{cm[1]:+.0f}] | Top-5 {in5[m].mean()*100:4.1f}% (O/E {o5:.2f})"
            f" | ret T5 {ret[m].mean()*100:+6.1f}% [{cr[0]*100:+.0f};{cr[1]*100:+.0f}]")

TR = {"dev": t < 9357, "2026": f >= "2026-01-01", "vivo": f >= "2026-09-15"}
print("=== 1. Día por día ===")
for nt, mt in TR.items():
    print(f"--- tramo {nt} ---")
    for k in range(7):
        print(fila(NOM[k], mt & (dow == k)))
    print(fila("mié-vie", mt & MVF)); print(fila("sáb-mar", mt & ~MVF)); print(fila("TOTAL", mt))

# ---------- 2. permutación entre jornadas ----------
SUBS3 = list(combinations(range(7), 3)); CONS = [((i) % 7, (i + 1) % 7, (i + 2) % 7) for i in range(7)]
SUBS13 = [c for r in (1, 2, 3) for c in combinations(range(7), r)]
def M(subs):
    X = np.zeros((len(subs), 7))
    for i, c in enumerate(subs): X[i, list(c)] = 1
    return X
X3, XC, X13 = M(SUBS3), M(CONS), M(SUBS13)

def perm_test(mt, NP=20000, etiqueta=""):
    u = np.unique(dn[mt]); O = np.bincount(dn[mt], in15[mt], minlength=len(fu))[u]
    E = np.bincount(dn[mt], m15[mt], minlength=len(fu))[u]; V = np.bincount(dn[mt], (m15 * (1 - m15))[mt], minlength=len(fu))[u]
    lab = np.array([date.fromisoformat(fu[d]).weekday() for d in u])
    def stats(lb):
        Od = np.bincount(lb, O, 7); Ed = np.bincount(lb, E, 7); Vd = np.bincount(lb, V, 7)
        s1 = ((XC @ Od) / (XC @ Ed)).min(); s2 = ((X3 @ Od) / (X3 @ Ed)).min()
        s3 = (((Od - Ed) ** 2) / Vd).sum(); s4 = np.abs((X13 @ Od - X13 @ Ed) / np.sqrt(X13 @ Vd)).max()
        jmin = int(np.argmin((X3 @ Od) / (X3 @ Ed)))
        return np.array([s1, s2, s3, s4]), jmin
    obs, jmin = stats(lab)
    rng = np.random.default_rng(7); cnt = np.zeros(4); nul = []
    for _ in range(NP):
        st, _ = stats(rng.permutation(lab)); nul.append(st)
    nul = np.array(nul)
    p = [(nul[:, 0] <= obs[0]).mean(), (nul[:, 1] <= obs[1]).mean(), (nul[:, 2] >= obs[2]).mean(), (nul[:, 3] >= obs[3]).mean()]
    print(f"{etiqueta}: jornadas={len(u)}; peor 3-subconjunto = {'-'.join(NOM[i] for i in SUBS3[jmin])}")
    print(f"  S1 peor bloque consecutivo O/E {obs[0]:.3f}  p={p[0]:.4f}  (nulo: mediana {np.median(nul[:,0]):.3f}, 1% {np.percentile(nul[:,0],1):.3f})")
    print(f"  S2 peor 3-subconjunto     O/E {obs[1]:.3f}  p={p[1]:.4f}  (nulo: mediana {np.median(nul[:,1]):.3f}, 1% {np.percentile(nul[:,1],1):.3f})")
    print(f"  S3 chi2 7 días            {obs[2]:.1f}   p={p[2]:.4f}  (nulo: mediana {np.median(nul[:,2]):.1f}, 99% {np.percentile(nul[:,2],99):.1f})")
    print(f"  S4 max|z| 63 subconj.     {obs[3]:.2f}   p={p[3]:.4f}  (nulo: mediana {np.median(nul[:,3]):.2f}, 99% {np.percentile(nul[:,3],99):.2f})")
    return p

print("\n=== 2. Permutación de etiquetas de día entre jornadas (20.000) ===")
p26 = perm_test(TR["2026"], etiqueta="2026")
pdev = perm_test(TR["dev"], etiqueta="dev (control: ¿hay estructura por día en otra era?)")

# ---------- 3. estabilidad mensual ----------
print("\n=== 3. Por mes de 2026: Top-15 O/E mié-vie vs resto ===")
dirs = 0; nm = 0
for mes in range(1, 11):
    mm = np.array([x.startswith(f"2026-{mes:02d}") for x in f])
    a = mm & MVF; b = mm & ~MVF
    if a.sum() == 0: continue
    oa = in15[a].sum() / m15[a].sum(); ob = in15[b].sum() / m15[b].sum(); nm += 1; dirs += oa < ob
    print(f"  2026-{mes:02d}: mié-vie {oa:.3f} (jorn {len(np.unique(dn[a])):2d})  resto {ob:.3f} (jorn {len(np.unique(dn[b])):2d})  dif {oa-ob:+.3f}")
print(f"  meses con mié-vie < resto: {dirs}/{nm}")
for lab, mt in (("dev por mes", TR["dev"]),):
    meses = sorted(set(x[:7] for x in f[mt])); dd = 0
    for ms in meses:
        mm = np.array([x.startswith(ms) for x in f]) & mt; a = mm & MVF; b = mm & ~MVF
        dd += (in15[a].sum() / m15[a].sum()) < (in15[b].sum() / m15[b].sum())
    print(f"  control {lab}: meses con mié-vie < resto: {dd}/{len(meses)}")

def dif_ci(m, etiqueta):
    a = m & MVF; b = m & ~MVF
    oa = in15[a].sum() / m15[a].sum(); ob = in15[b].sum() / m15[b].sum()
    u = np.unique(dn[m]); O = np.bincount(dn[m], in15[m], minlength=len(fu))[u]; E = np.bincount(dn[m], m15[m], minlength=len(fu))[u]
    w = np.array([date.fromisoformat(fu[d]).weekday() in (2, 3, 4) for d in u])
    ia, ib = np.flatnonzero(w), np.flatnonzero(~w); r = []
    for _ in range(B):
        sa = RNG.choice(ia, len(ia)); sb = RNG.choice(ib, len(ib))
        r.append(O[sa].sum() / E[sa].sum() - O[sb].sum() / E[sb].sum())
    c = np.percentile(r, [2.5, 97.5]); c90 = np.percentile(r, [5, 95])
    print(f"  {etiqueta:38} mié-vie {oa:.3f} ({len(ia)} jorn) resto {ob:.3f} ({len(ib)} jorn) dif {oa-ob:+.3f} IC95 [{c[0]:+.3f};{c[1]:+.3f}] IC90 [{c90[0]:+.3f};{c90[1]:+.3f}]")
    return oa, c

print("\n=== 3b. Vivo (f >= 2026-09-15) ===")
dif_ci(TR["vivo"], "vivo")

# ---------- 4. robustez ----------
print("\n=== 4. Robustez (2026) ===")
m26 = TR["2026"]
incom = np.array([cnt_hist.get(x, 0) < 12 for x in f]); fer = np.isin(f, list(FER))
print(f"  jornadas 2026 incompletas (<12 en historial): {len(set(f[m26 & incom]))}  {sorted(set(f[m26 & incom]))}")
print(f"  feriados excluidos presentes en 2026: {sorted(set(f[m26 & fer]))} (de ellos mié-vie: {sorted(set(f[m26 & fer & MVF]))})")
dif_ci(m26, "2026 todo")
dif_ci(m26 & ~incom, "2026 sin incompletas")
dif_ci(m26 & ~incom & ~fer, "2026 sin incompletas ni feriados")
dif_ci(TR["dev"], "dev (control)")
# dev sin domingos
dif_ci(TR["dev"] & (dow != 6), "dev sin domingos")
dif_ci(m26 & (dow != 6), "2026 sin domingos")
print("  Por hora (2026, sin incompletas ni feriados): O/E mié-vie vs resto")
mr = m26 & ~incom & ~fer; nh = 0; num = 0; den = 0
hs = []
for hh in range(12):
    a = mr & MVF & (h == hh); b = mr & ~MVF & (h == hh)
    oa = in15[a].sum() / m15[a].sum(); ob = in15[b].sum() / m15[b].sum(); nh += oa < ob
    w = m15[mr & (h == hh)].sum(); num += w * (oa - ob); den += w; hs.append(oa - ob)
    print(f"    {8+hh:2d}:00  mié-vie {oa:.3f}  resto {ob:.3f}  dif {oa-ob:+.3f}")
print(f"  horas con mié-vie < resto: {nh}/12; diferencia estratificada por hora (ponderada por E): {num/den:+.3f}")
# IC de la diferencia estratificada por hora, bootstrap por jornada
u = np.unique(dn[mr]); w = np.array([date.fromisoformat(fu[d]).weekday() in (2, 3, 4) for d in u])
Oh = np.zeros((len(u), 12)); Eh = np.zeros((len(u), 12)); pos = {d: i for i, d in enumerate(u)}
for i in ar[mr]: Oh[pos[dn[i]], h[i]] += in15[i]; Eh[pos[dn[i]], h[i]] += m15[i]
ia, ib = np.flatnonzero(w), np.flatnonzero(~w); WH = Eh.sum(0) / Eh.sum(); r = []
for _ in range(B):
    sa = RNG.choice(ia, len(ia)); sb = RNG.choice(ib, len(ib))
    r.append((WH * (Oh[sa].sum(0) / Eh[sa].sum(0) - Oh[sb].sum(0) / Eh[sb].sum(0))).sum())
print(f"  IC95 diferencia estratificada: [{np.percentile(r,2.5):+.3f};{np.percentile(r,97.5):+.3f}]")
# por mitad de la jornada
for lab, hm in (("mañana 8-13", h < 6), ("tarde 14-19", h >= 6)):
    dif_ci(mr & hm, f"2026 limpio {lab}")
# Permutación también sobre el subconjunto limpio
print()
perm_test(mr, NP=20000, etiqueta="2026 limpio (sin incompletas ni feriados)")
# Calidad de la máscara del motor por día (¿el motor es más o menos seguro mié-vie?)
print("\n  Masa media del Top-15 del motor por día (2026 / dev):")
print("   " + "  ".join(f"{NOM[k]} {m15[m26&(dow==k)].mean():.3f}/{m15[TR['dev']&(dow==k)].mean():.3f}" for k in range(7)))
