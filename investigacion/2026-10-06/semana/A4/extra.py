#!/usr/bin/env python3
# A4 — comprobaciones adicionales (escritas DESPUÉS de ver salida.txt; exploratorias):
#  (a) C1/C2 por hora; (b) reciclaje crudo SIN motor por trimestre; (c) "ya salió esta semana" crudo por día;
#  (d) p-valores clave con más permutaciones.
import sys, numpy as np
from datetime import date, timedelta
sys.path.insert(0, "/home/user/lotto-activo/herramientas"); import lotto_eval as LE
S = sys.argv[1]
D = LE.cargar(S + "/hist_0605.txt"); YS = np.asarray(D.seq); FD = np.array(D.fecha)
z = np.load(S + "/prod_0605.npz", allow_pickle=True); P, t, y, f, h = z["P"], z["t"], z["y"], z["f"], z["h"].astype(int)
o = np.argsort(-P, 1, kind="stable"); rk = np.argmax(o == y[:, None], 1)
in15 = (rk < 15).astype(float); m15 = np.take_along_axis(P, o[:, :15], 1).sum(1); r = in15 - m15
fd = np.array([date.fromisoformat(d) for d in f]); dow = np.array([d.weekday() for d in fd])
tri = np.array([f"{d.year}-T{(d.month-1)//3+1}" for d in fd])
MVF = np.isin(dow, [2, 3, 4]); DOM = dow == 6; A26 = f >= "2026-01-01"; EPI = (f >= "2024-07-01") & (f < "2025-08-01")
rng = np.random.default_rng(7)
L = []
def pr(*a):
    s = " ".join(str(x) for x in a); print(s); L.append(s)

pr("(a) Contraste por hora (O/E grupo − O/E resto, contra el motor)")
pr("hora  " + " ".join(f"{8+k:>6}" for k in range(12)))
for lab, m, G in (("C1 2026", A26, MVF), ("C1 dev", t < 9357, MVF), ("C2 epis", EPI, DOM), ("C2 2026", A26, DOM)):
    v = []
    for k in range(12):
        a = m & G & (h == k); b = m & ~G & (h == k)
        v.append(in15[a].sum() / m15[a].sum() - in15[b].sum() / m15[b].sum() if a.sum() and b.sum() else np.nan)
    pr(f"{lab:7} " + " ".join(f"{x:+6.2f}" for x in v))

# (b) reciclaje crudo: ganador ∈ {salió ayer o anteayer} \ {ya salió hoy}; esperado uniforme sin repetir hoy
fu = np.unique(FD); di = {d: i for i, d in enumerate(fu)}; dn = np.array([di[x] for x in FD])
day_sets = {}
for i in range(len(YS)): day_sets.setdefault(dn[i], []).append(YS[i])
recR = np.zeros(len(t)); recE = np.zeros(len(t)); wkR = np.zeros(len(t)); wkE = np.zeros(len(t))
lun_of = {d: (date.fromisoformat(d) - timedelta(days=date.fromisoformat(d).weekday())).isoformat() for d in fu}
for i, T in enumerate(t):
    d = dn[T]
    # sorteos de hoy anteriores a T
    j = T - 1; hs = set()
    while j >= 0 and dn[j] == d: hs.add(YS[j]); j -= 1
    prev = set(day_sets.get(d - 1, [])) | set(day_sets.get(d - 2, []))
    cand = prev - hs; libre = 38 - len(hs)
    recR[i] = y[i] in cand; recE[i] = len(cand) / libre
    # ya salió esta semana ISO (días anteriores de la misma semana)
    wk = set(); dd = d - 1
    while dd >= 0 and lun_of[fu[dd]] == lun_of[fu[d]]: wk |= set(day_sets.get(dd, [])); dd -= 1
    c2 = wk - hs; wkR[i] = y[i] in c2; wkE[i] = len(c2) / libre
Pc = np.array([P[i, list(set(day_sets.get(dn[t[i]] - 1, [])) | set(day_sets.get(dn[t[i]] - 2, [])))].sum() for i in range(len(t))])
pr(""); pr("(b) Reciclaje (ganador salió ayer o anteayer y no hoy): O/E CRUDO contra uniforme-sin-repetir y O/E contra el motor")
pr(f"{'trim':8} {'crudo mié-vie':>14} {'crudo resto':>12} {'crudo dom':>10} | {'motor mié-vie':>14} {'motor resto':>12} {'motor dom':>10}")
for q in sorted(set(tri)):
    m = tri == q
    if m.sum() < 200: continue
    c = lambda g: recR[m & g].sum() / recE[m & g].sum()
    mo = lambda g: recR[m & g].sum() / Pc[m & g].sum()
    pr(f"{q:8} {c(MVF):14.2f} {c(~MVF):12.2f} {c(DOM):10.2f} | {mo(MVF):14.2f} {mo(~MVF):12.2f} {mo(DOM):10.2f}")
pr(""); pr("(c) 'Ya salió esta semana (lun..ayer)' O/E crudo contra uniforme-sin-repetir, por día (martes..domingo)")
NM = "lun mar mié jue vie sáb dom".split()
for lab, m in (("dev", t < 9357), ("2026", A26)):
    pr(f"{lab:5} " + " ".join(f"{NM[k]} {wkR[m&(dow==k)].sum()/wkE[m&(dow==k)].sum():.2f}" for k in range(1, 7)))

# (d) más permutaciones: peor bloque de 3 días consecutivos en 2026, barajando días dentro de semana ISO
fu2, di2 = np.unique(f, return_inverse=True); nd = len(fu2)
dO = np.bincount(di2, in15, nd); dE = np.bincount(di2, m15, nd)
d_dow = np.array([date.fromisoformat(x).weekday() for x in fu2]); d_lun = np.array([lun_of[x] for x in fu2])
d26 = np.array([x >= "2026-01-01" for x in fu2])
idx = np.where(d26)[0]; bl = [idx[d_lun[idx] == b] for b in np.unique(d_lun[idx])]
def worst3(lab):
    best = 9
    for s in range(7):
        g = np.isin(lab, [(s + i) % 7 for i in range(3)])
        best = min(best, dO[idx][g].sum() / dE[idx][g].sum() - dO[idx][~g].sum() / dE[idx][~g].sum())
    return best
obs = worst3(d_dow[idx]); pos = {v: k for k, v in enumerate(idx)}
NP = 20000; cnt = 0; lab0 = d_dow.copy()
for _ in range(NP):
    lab = lab0.copy()
    for ii in bl: lab[ii] = lab0[rng.permutation(ii)]
    cnt += worst3(lab[idx]) <= obs
pr(""); pr(f"(d) 2026, peor bloque de 3 días: {obs:+.3f}; p_perm con {NP} permutaciones dentro de semana = {(cnt+1)/(NP+1):.5f}")
open(sys.argv[2], "w").write("\n".join(L) + "\n")
