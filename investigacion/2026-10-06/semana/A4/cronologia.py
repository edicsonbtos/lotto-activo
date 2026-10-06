#!/usr/bin/env python3
# A4 — cronología y cambio de régimen del efecto día de la semana (ver PREREGISTRO.md)
# Uso: python3 cronologia.py <SP>   (SP = carpeta con prod_0605.npz)
import sys, numpy as np
from datetime import date, timedelta
S = sys.argv[1]
z = np.load(S + "/prod_0605.npz", allow_pickle=True)
P, t, y, f, h = z["P"], z["t"], z["y"], z["f"], z["h"].astype(int)
o = np.argsort(-P, 1, kind="stable"); rk = np.argmax(o == y[:, None], 1)
in15 = (rk < 15).astype(float); m15 = np.take_along_axis(P, o[:, :15], 1).sum(1)
r = in15 - m15; V = m15 * (1 - m15)
fd = np.array([date.fromisoformat(d) for d in f])
dow = np.array([d.weekday() for d in fd]); dom_ = np.array([d.day for d in fd])
mes = np.array([d[:7] for d in f])
tri = np.array([f"{d.year}-T{(d.month-1)//3+1}" for d in fd])
sem = np.array([f"{d.year}-S{(d.month-1)//6+1}" for d in fd])
lunes = np.array([(d - timedelta(days=d.weekday())).isoformat() for d in fd])  # semana ISO (clave = su lunes)
NM = "lun mar mié jue vie sáb dom".split()
MVF = np.isin(dow, [2, 3, 4]); DOM = dow == 6
rng = np.random.default_rng(20261006)
DEV = t < 9357; A26 = f >= "2026-01-01"

def delta(m, A):
    """Diferencia estratificada por hora (A − no A) dentro de m, en unidades de O/E."""
    num = 0.0; wt = 0
    for hh in range(12):
        a = m & A & (h == hh); b = m & ~A & (h == hh)
        if a.sum() == 0 or b.sum() == 0: continue
        n = a.sum() + b.sum(); num += n * (r[a].mean() - r[b].mean()); wt += n
    return num / wt / m15[m].mean() if wt else np.nan

def oe(m): return in15[m].sum() / m15[m].sum() if m.sum() else np.nan

# ---- agregados por jornada (para bootstrap y permutaciones) ----
fu, di = np.unique(f, return_inverse=True)
nd = len(fu)
dO = np.bincount(di, in15, nd); dE = np.bincount(di, m15, nd); dV = np.bincount(di, V, nd); dN = np.bincount(di)
d_date = np.array([date.fromisoformat(x) for x in fu]); d_dow = np.array([x.weekday() for x in d_date])
d_dom = np.array([x.day for x in d_date]); d_mes = np.array([x[:7] for x in fu])
d_lun = np.array([(x - timedelta(days=x.weekday())).isoformat() for x in d_date])
d_tri = np.array([f"{x.year}-T{(x.month-1)//3+1}" for x in d_date]); d_sem = np.array([f"{x.year}-S{(x.month-1)//6+1}" for x in d_date])
d_dev = np.array([x < "2025-12-20" for x in fu]); d_26 = np.array([x >= "2026-01-01" for x in fu])

def boot_ci(dm, lab, B=1000):
    """IC95 bootstrap por jornadas del contraste (O/E grupo − O/E resto) con O/E por jornada agregada."""
    idx = np.where(dm)[0]; g = lab[idx]; out = []
    for _ in range(B):
        s = rng.choice(len(idx), len(idx)); ii = idx[s]; gg = g[s]
        a = dO[ii][gg].sum() / dE[ii][gg].sum(); b = dO[ii][~gg].sum() / dE[ii][~gg].sum(); out.append(a - b)
    return np.percentile(out, [2.5, 97.5])

L = []
def pr(*a):
    s = " ".join(str(x) for x in a); print(s); L.append(s)

def barra(v, esc=0.02):
    if np.isnan(v): return ""
    n = int(round(abs(v) / esc)); n = min(n, 20)
    return (" " * (20 - n) + "#" * n + "|" + " " * 20) if v < 0 else (" " * 20 + "|" + "#" * n)

# ================= 1. serie mensual y trimestral =================
pr("=" * 110); pr("1. SERIE MENSUAL: Top-15 O/E contra el motor por día de semana; C1 = mié-vie − resto, C2 = dom − resto")
pr("   (C1, C2 estratificados por hora, en unidades de O/E; barra de C1: cada # = 0,02)")
pr(f"{'mes':8} {'n':>4} " + " ".join(f"{x:>5}" for x in NM) + f" {'tot':>5} {'C1':>6} {'C2':>6}   barra C1 (−|+)")
meses = sorted(set(mes)); C1m = {}; C2m = {}
for mm in meses:
    m = mes == mm
    row = [oe(m & (dow == k)) for k in range(7)]
    c1 = delta(m, MVF); c2 = delta(m, DOM); C1m[mm] = c1; C2m[mm] = c2
    pr(f"{mm:8} {m.sum():4d} " + " ".join(f"{v:5.2f}" for v in row) + f" {oe(m):5.2f} {c1:+6.2f} {c2:+6.2f}   {barra(c1)}")

pr(""); pr("1b. SERIE TRIMESTRAL con IC95 por bloques de jornada (bootstrap de días) para C1 y C2 (crudos, sin estratificar el IC)")
pr(f"{'trim':8} {'días':>4} " + " ".join(f"{x:>5}" for x in NM) + f" {'tot':>5} {'C1':>6} {'IC95 C1':>15} {'C2':>6} {'IC95 C2':>15}")
TR = sorted(set(tri)); C1t = {}
for q in TR:
    m = tri == q; dm = d_tri == q
    row = [oe(m & (dow == k)) for k in range(7)]
    c1 = delta(m, MVF); c2 = delta(m, DOM); C1t[q] = c1
    i1 = boot_ci(dm, np.isin(d_dow, [2, 3, 4]), 600); i2 = boot_ci(dm, d_dow == 6, 600)
    pr(f"{q:8} {dm.sum():4d} " + " ".join(f"{v:5.2f}" for v in row) + f" {oe(m):5.2f} {c1:+6.2f} [{i1[0]:+.2f};{i1[1]:+.2f}] {c2:+6.2f} [{i2[0]:+.2f};{i2[1]:+.2f}]")

# ================= 2. punto de cambio =================
pr(""); pr("=" * 110); pr("2. PUNTO DE CAMBIO (semanas ISO; C por semana = media r grupo − media r resto, /m̄15)")
mbar = m15.mean()
W = sorted(set(lunes))
def serie_sem(G):
    c = []
    for w in W:
        m = lunes == w; a = m & G; b = m & ~G
        c.append((r[a].mean() - r[b].mean()) / mbar if a.sum() and b.sum() else np.nan)
    return np.array(c)
Wm = np.array([w[:7] for w in W])
def cambio(c, wm, nperm=2000):
    ok = ~np.isnan(c); c = c[ok]; wm = wm[ok]
    cortes = [mm for mm in sorted(set(wm)) if (wm < mm).sum() >= 17 and (wm >= mm).sum() >= 17]
    pos = [np.argmax(wm >= mm) for mm in cortes]
    def stat(x):
        n = len(x); cs = np.cumsum(x); tot = cs[-1]; out = []
        for p in pos:
            m1 = cs[p - 1] / p; m2 = (tot - cs[p - 1]) / (n - p)
            s2 = (((x[:p] - m1) ** 2).sum() + ((x[p:] - m2) ** 2).sum()) / (n - 2)
            out.append((m2 - m1) / np.sqrt(s2 * (1 / p + 1 / (n - p))))
        return np.array(out)
    tk = stat(c); mx = np.abs(tk).max()
    null = np.array([np.abs(stat(rng.permutation(c))).max() for _ in range(nperm)])
    p = (1 + (null >= mx).sum()) / (nperm + 1)
    return cortes, tk, p, c, wm
res = {}
for nombre, G in (("C1 mié-vie", MVF), ("C2 domingo", DOM)):
    c = serie_sem(G); cortes, tk, p, cc, wm = cambio(c, Wm)
    k = np.argmax(np.abs(tk)); best = cortes[k]
    plaus = [cortes[i] for i in range(len(cortes)) if abs(tk[i]) >= abs(tk[k]) - 1]
    antes = cc[wm < best].mean(); despues = cc[wm >= best].mean()
    res[nombre] = (best, p, cc, wm)
    pr(f"{nombre}: corte óptimo {best} |t| = {abs(tk[k]):.2f}, p_perm (orden de semanas, 2000) = {p:.4f}; media antes {antes:+.3f}, después {despues:+.3f}")
    pr(f"   rango plausible (|t| ≥ máx − 1): {plaus[0]} .. {plaus[-1]}")
    pr("   perfil t por corte: " + " ".join(f"{cortes[i][2:]}:{tk[i]:+.1f}" for i in range(len(cortes))))
    # CUSUM mensual
    cus = np.cumsum(cc - cc.mean()); s = "   CUSUM (fin de mes): "
    s += " ".join(f"{mm[2:]}:{cus[np.where(wm == mm)[0][-1]]:+.1f}" for mm in sorted(set(wm)))
    pr(s)
# dos cortes para C2: ¿termina el domingo malo y vuelve? -> episodio
pr("")
pr("2b. Segmentación con DOS cortes (episodio: entra y sale), búsqueda exhaustiva por meses, p por permutación de semanas")
def dos_cortes(c, wm, nperm=500):
    ok = ~np.isnan(c); c = c[ok]; wm = wm[ok]; ms = sorted(set(wm)); pos = [np.argmax(wm >= mm) for mm in ms]
    def stat(x):
        best = (0, None); n = len(x); cs = np.concatenate([[0], np.cumsum(x)]); cs2 = np.concatenate([[0], np.cumsum(x * x)])
        tot = cs[-1]; tot2 = cs2[-1]; sst = tot2 - tot ** 2 / n
        for i in range(len(pos)):
            for j in range(i + 1, len(pos)):
                a, b = pos[i], pos[j]
                if b - a < 13 or n - (b - a) < 13: continue
                ni = b - a; si = cs[b] - cs[a]; so = tot - si; no = n - ni
                ssb = si ** 2 / ni + so ** 2 / no - tot ** 2 / n
                F = ssb / ((sst - ssb) / (n - 2))
                if F > best[0]: best = (F, (ms[i], ms[j], si / ni, so / no))
        return best
    obs = stat(c); null = np.array([stat(rng.permutation(c))[0] for _ in range(nperm)])
    return obs, (1 + (null >= obs[0]).sum()) / (nperm + 1)
for nombre in res:
    _, _, cc, wm = res[nombre]
    (F, (a, b, mi, mo)), p = dos_cortes(cc, wm)
    pr(f"{nombre}: episodio {a} .. (antes de) {b}: media dentro {mi:+.3f}, fuera {mo:+.3f}, F = {F:.1f}, p_perm = {p:.3f}")

# ================= 3. controles =================
pr(""); pr("=" * 110); pr("3. CONTROLES Y CORRECCIÓN POR SELECCIÓN (permutaciones a nivel de jornada)")
tercio = np.where(d_dom <= 10, 0, np.where(d_dom <= 20, 1, 2)); semmes = np.minimum((d_dom - 1) // 7, 4)
def chi2_grupos(dm, lab, G):
    zz = []
    for g in range(G):
        s = dm & (lab == g); zz.append((dO[s].sum() - dE[s].sum()) / np.sqrt(dV[s].sum()))
    return np.array(zz)
def rel_oe(dm, lab, G):
    tot = dO[dm].sum() / dE[dm].sum()
    return np.array([dO[dm & (lab == g)].sum() / dE[dm & (lab == g)].sum() / tot for g in range(G)])
def perm_bloques(dm, lab, bloque):
    """baraja las etiquetas entre los días de cada bloque (semana ISO o mes)."""
    out = lab.copy(); idx = np.where(dm)[0]
    for bk in np.unique(bloque[idx]):
        ii = idx[bloque[idx] == bk]; out[ii] = lab[rng.permutation(ii)]
    return out
def worst3(dm, lab):  # peor bloque circular de 3 días consecutivos de la semana: O/E bloque − O/E resto
    best = (9, None)
    for s in range(7):
        g = np.isin(lab, [(s + i) % 7 for i in range(3)])
        a = dO[dm & g].sum() / dE[dm & g].sum(); b = dO[dm & ~g].sum() / dE[dm & ~g].sum()
        if a - b < best[0]: best = (a - b, s)
    return best
def worstg(dm, lab, G):
    v = rel_oe(dm, lab, G); return v.min(), int(v.argmin())
NP = 2000
for tramo, dm in (("dev 2024-03..2025-12", d_dev), ("2026 ene..5-oct", d_26)):
    pr(f"-- {tramo} ({dm.sum()} jornadas)")
    for nombre, lab, G, bloque, etq in (("día semana", d_dow, 7, d_lun, NM),
                                        ("tercio mes", tercio, 3, d_mes, ["1-10", "11-20", "21-31"]),
                                        ("semana mes", semmes, 5, d_mes, ["1-7", "8-14", "15-21", "22-28", "29-31"])):
        zz = chi2_grupos(dm, lab, G); x2 = (zz ** 2).sum(); ro = rel_oe(dm, lab, G); wg = worstg(dm, lab, G)
        nx = []; nw = []
        for _ in range(NP):
            lp = perm_bloques(dm, lab, bloque); nx.append((chi2_grupos(dm, lp, G) ** 2).sum()); nw.append(worstg(dm, lp, G)[0])
        px = (1 + (np.array(nx) >= x2).sum()) / (NP + 1); pw = (1 + (np.array(nw) <= wg[0]).sum()) / (NP + 1)
        pr(f"   {nombre:11} χ²={x2:5.1f} (gl {G-1}) p_perm={px:.4f} | O/E relativo: " + " ".join(f"{e}:{v:.2f}" for e, v in zip(etq, ro))
           + f" | peor {etq[wg[1]]} {wg[0]:.2f} (z {zz[wg[1]]:+.1f}), p_perm(peor)={pw:.4f}")
    w = worst3(dm, d_dow); nw = []
    for _ in range(NP): nw.append(worst3(dm, perm_bloques(dm, d_dow, d_lun))[0])
    pw = (1 + (np.array(nw) <= w[0]).sum()) / (NP + 1)
    pr(f"   peor bloque de 3 días consecutivos: {NM[w[1]]}-{NM[(w[1]+2)%7]} diferencia {w[0]:+.3f}, p_perm (corrige 7 bloques) = {pw:.4f}")

# ================= 4. rotación por semestre =================
pr(""); pr("=" * 110); pr("4. ROTACIÓN: por semestre, O/E por día (crudo), peor día, peor bloque de 3 días, χ² y p_perm")
SEMS = sorted(set(d_sem)); hit = []; nullhit = []
for s_ in SEMS:
    dm = d_sem == s_
    row = [dO[dm & (d_dow == k)].sum() / dE[dm & (d_dow == k)].sum() for k in range(7)]
    zz = chi2_grupos(dm, d_dow, 7); x2 = (zz ** 2).sum(); w = worst3(dm, d_dow)
    nx = []; nmin = []
    for _ in range(1000):
        lp = perm_bloques(dm, d_dow, d_lun); nx.append((chi2_grupos(dm, lp, 7) ** 2).sum())
        nmin.append(min(dO[dm & (lp == k)].sum() / dE[dm & (lp == k)].sum() for k in range(7)))
    px = (1 + (np.array(nx) >= x2).sum()) / 1001
    k = int(np.argmin(row)); hit.append((s_, NM[k], row[k])); nullhit.append((np.array(nmin) <= 0.85).mean())
    pr(f"{s_} ({dm.sum():3d} d) " + " ".join(f"{NM[i]} {row[i]:.2f}" for i in range(7)) + f" | peor {NM[k]} {row[k]:.2f} | 3d {NM[w[1]]}-{NM[(w[1]+2)%7]} {w[0]:+.2f} | χ² {x2:5.1f} p {px:.3f} | P0(algún día≤0,85) {nullhit[-1]:.2f}")

# ================= 5. tendencia dentro de 2026 =================
pr(""); pr("=" * 110); pr("5. ESTABILIDAD DESPUÉS DEL CORTE de C1")
best, p, cc, wm = res["C1 mié-vie"]
post = wm >= best; x = np.arange(post.sum()); yv = cc[post]
sl = np.polyfit(x, yv, 1)[0]; nul = np.array([np.polyfit(x, rng.permutation(yv), 1)[0] for _ in range(2000)])
pr(f"desde {best}: {post.sum()} semanas, C1 medio {yv.mean():+.3f}; pendiente {sl*52:+.3f}/año, p_perm (2 colas) = {(np.abs(nul) >= abs(sl)).mean():.3f}")
for q in [q for q in TR if q >= best[:4]]:
    pr(f"   {q}: C1 = {C1t[q]:+.3f}")
# mes por mes, cuántos meses tras el corte tienen C1 < 0
mm_post = [mm for mm in meses if mm >= best]
pr(f"   meses con C1 < 0 desde el corte: {sum(C1m[mm] < 0 for mm in mm_post)}/{len(mm_post)};  antes del corte: {sum(C1m[mm] < 0 for mm in meses if mm < best)}/{len([mm for mm in meses if mm < best])}")
# lo mismo para C2 domingo
b2, p2, c2c, w2 = res["C2 domingo"]
pr(f"   C2 domingo: meses con C2 < 0 antes de {b2}: {sum(C2m[mm] < 0 for mm in meses if mm < b2)}/{len([mm for mm in meses if mm < b2])}; desde: {sum(C2m[mm] < 0 for mm in meses if mm >= b2)}/{len([mm for mm in meses if mm >= b2])}")

open(sys.argv[2] if len(sys.argv) > 2 else "salida.txt", "w").write("\n".join(L) + "\n")
