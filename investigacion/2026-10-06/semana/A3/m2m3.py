from comun import *
from collections import Counter
print("M2 · Top-15 O/E por hora (2026 y dev). ratio MVF/SM [IC95 días]")
for era, me in (("2026", A26), ("dev", DEV)):
    print(f"== {era} ==")
    for lab, hs in [(f"{8+k}:00", [k]) for k in range(12)] + [("mañana 8-13", range(0, 6)), ("tarde 14-19", range(6, 12)), ("todas", range(12))]:
        mh = me & np.isin(h, list(hs)); a = mh & MVF; b = mh & ~MVF
        r, lo, hi = boot_ratio(IN15[a].astype(float), M15[a], IN15[b].astype(float), M15[b], dayid[a], dayid[b], B=1000)
        oa = IN15[a].sum() / M15[a].sum(); ob = IN15[b].sum() / M15[b].sum()
        rep_a = HOYB[rows, y][a].mean() * 100; rep_b = HOYB[rows, y][b].mean() * 100
        print(f"  {lab:12} MVF {oa:.2f}  SM {ob:.2f}  ratio {r:.2f} [{lo:.2f}; {hi:.2f}]   %repite-hoy MVF {rep_a:4.1f} SM {rep_b:4.1f}")
# z mañana vs tarde (2026), bootstrap del log-ratio
rng = np.random.default_rng(5)
me = A26; days = np.unique(dayid[me])
def lr(sel_days):
    out = []
    for hs in (range(0, 6), range(6, 12)):
        m = np.isin(dayid, sel_days) & me & np.isin(h, list(hs))
        a = m & MVF; b = m & ~MVF
        out.append(np.log((IN15[a].sum()/M15[a].sum())/(IN15[b].sum()/M15[b].sum())))
    return out[0] - out[1]
d0 = lr(days); bs = []
dv = {d: i for i, d in enumerate(days)}
oh = [np.flatnonzero(dayid == d) for d in days]
# bootstrap rápido por días con pesos
Wm = np.zeros(len(t))
for _ in range(1000):
    c = np.bincount(rng.integers(0, len(days), len(days)), minlength=len(days)).astype(float)
    w = np.zeros(len(t)); w[np.isin(dayid, days)] = c[np.searchsorted(days, dayid[np.isin(dayid, days)])]
    vals = []
    for hs in (range(0, 6), range(6, 12)):
        m = me & np.isin(h, list(hs)); a = m & MVF; b = m & ~MVF
        vals.append(np.log(((w*IN15)[a].sum()/(w*M15)[a].sum())/((w*IN15)[b].sum()/(w*M15)[b].sum())))
    bs.append(vals[0] - vals[1])
print(f"\n2026 log-ratio mañana − tarde = {d0:+.3f}, z = {d0/np.std(bs):+.2f}")

print("\nM3 · Concentración por día (solo días completos de 12 sorteos)")
def dias_stats(me):
    res = {}
    for g, gm in (("MVF", MVF), ("SM", ~MVF)):
        sel = me & gm; ids = np.unique(dayid[sel]); R = []; Ent = []; Rexp = []; Dist = []
        for d in ids:
            ix = np.flatnonzero((dayid == d) & sel)
            if len(ix) != 12: continue
            w = y[ix]; c = np.array(list(Counter(w).values()))
            Dist.append(len(c)); R.append(12 - len(c)); p_ = c / 12; Ent.append(-(p_ * np.log2(p_)).sum())
            Rexp.append((P[ix] * HOYB[ix]).sum())
        res[g] = (np.array(R), np.array(Rexp), np.array(Ent), np.array(Dist))
    return res
for era, me in (("dev", DEV), ("2026", A26)):
    r = dias_stats(me)
    for g in ("MVF", "SM"):
        R, Re, En, Di = r[g]; se = R.std() / np.sqrt(len(R))
        print(f"  {era:4} {g:3}: días {len(R)}  repeticiones/día {R.mean():.2f} ±{se:.2f} (motor {Re.mean():.2f}; azar 1.60)  distintos {Di.mean():.2f}  entropía {En.mean():.3f} bits  días con ≥3 rep {np.mean(R>=3)*100:.0f}%")

print("\nRepeticiones/día por día de la semana y trimestre (obs/motor)")
dn = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
for lab, lo, hi in (("2024", "2024-03-01", "2024-12-31"), ("2025-S1", "2025-01-01", "2025-06-30"), ("2025-S2", "2025-07-01", "2025-12-31"),
                    ("26-T1", "2026-01-01", "2026-03-31"), ("26-T2", "2026-04-01", "2026-06-30"), ("26-T3", "2026-07-01", "2026-10-05")):
    me = (f >= lo) & (f <= hi); s = f"  {lab:8}"
    for k in range(7):
        m = me & (dow == k); s += f" {dn[k]} {HOYB[rows,y][m].sum()/ (P*HOYB)[m].sum().sum():.2f}"
    print(s)

print("\nGanancia del motor sobre el uniforme (mbits/sorteo) [IC95 días]")
LL = np.log2(P[rows, y] * K) * 1000
for era, me in (("dev", DEV), ("2026", A26)):
    for g, gm in (("MVF", MVF), ("SM", ~MVF)):
        m = me & gm; u, inv = np.unique(dayid[m], return_inverse=True); s = np.bincount(inv, LL[m]); c = np.bincount(inv)
        bs = []
        for _ in range(2000):
            i = rng.integers(0, len(s), len(s)); bs.append(s[i].sum() / c[i].sum())
        print(f"  {era:4} {g:3}: {LL[m].mean():+6.1f} [{np.percentile(bs,2.5):+.1f}; {np.percentile(bs,97.5):+.1f}]   Top-15 {IN15[m].mean()*100:.1f}% (azar 39.5)")
