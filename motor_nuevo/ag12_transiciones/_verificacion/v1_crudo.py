# -*- coding: utf-8 -*-
"""Auditoría: cálculo crudo independiente de O/E de transiciones repetidas. No usa rasgos12."""
import os, sys
import numpy as np
AQ = os.path.dirname(os.path.abspath(__file__)); AG = os.path.dirname(AQ); MN = os.path.dirname(AG)
sys.path.insert(0, MN); sys.path.insert(0, AG)
import arnes as A
D = A.datos().prefijo(A.CORTE)
seq = np.asarray(D.seq); dia = np.asarray(D.dia); hora = np.asarray(D.hora)
fechas = sorted(set(D.fecha)); jidx = {f: i for i, f in enumerate(fechas)}
jn = np.array([jidx[f] for f in D.fecha])          # jornada por fecha (independiente de np.unique)
n = len(seq)
Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True)
assert np.all(y == seq[A.W:A.CORTE])
# último día en que a->b ocurrió dentro del día, lista completa
hist = {}
def masks(t):
    """máscaras (38,) de candidatos b con s1->b hace [1], [2,7], [8,30] jornadas; y i->s1 idem."""
    s1 = seq[t-1]; d = jn[t]
    M = np.zeros((6, 38), bool)
    for (a, b), L in hist.items():
        for jd in L:
            age = d - jd
            for v, (lo, hi) in enumerate([(1, 1), (2, 7), (8, 30)]):
                if lo <= age <= hi:
                    if a == s1: M[v, b] = True
                    if b == s1: M[3 + v, a] = True
    return M
rows = []  # (t, M) para t con s1 del mismo día
for t in range(n):
    if t >= 300 and t >= 1 and jn[t-1] == jn[t]:
        rows.append((t, masks(t)))
    if t >= 1 and jn[t-1] == jn[t]:
        hist.setdefault((seq[t-1], seq[t]), []).append(jn[t])
    # poda >30 jornadas
    if t % 200 == 0:
        for k in list(hist):
            hist[k] = [j for j in hist[k] if jn[t] - j <= 31]
            if not hist[k]: del hist[k]
np.savez_compressed(os.path.join(AQ, "mascaras.npz"), t=np.array([r[0] for r in rows]),
                    M=np.array([r[1] for r in rows]))
nombres = ["s1->i 1d", "s1->i 2-7", "s1->i 8-30", "i->s1 1d", "i->s1 2-7", "i->s1 8-30"]
def oe(sel, base):
    out = []
    for v in range(6):
        o = e = 0.0
        for t, M in sel:
            m = M[v].copy(); m[seq[t-1]] = False
            if not m.any(): continue
            o += m[seq[t]]
            if base == "unif": e += m.sum() / 37.0     # uniforme sin repetir s1 (en la práctica s1 casi nunca repite? se mide abajo)
            elif base == "unif38": e += m.sum() / 38.0
            else: e += Pens[t - A.W][m].sum()
        out.append(f"{nombres[v]:12s} O {int(o):5d} E {e:8.1f} O/E {o/e:5.3f} z {(o-e)/np.sqrt(e):+6.2f}")
    return "\n".join(out)
dev = [r for r in rows if r[0] >= A.W]; pre = [r for r in rows if r[0] < A.W]
rep_s1 = np.mean([seq[t] == seq[t-1] for t, _ in rows])
print("filas intradía: pre", len(pre), "dev", len(dev), "· tasa s1 repetido:", round(rep_s1, 4), "(1/38 =", round(1/38, 4), ")")
print("== DEV [2000,9357) vs ENSAMBLE ==\n" + oe(dev, "ens"))
print("== DEV [2000,9357) vs UNIFORME 1/38 ==\n" + oe(dev, "unif38"))
print("== PRE [300,2000) vs UNIFORME 1/38 (no entró en ajuste ni sondeo) ==\n" + oe(pre, "unif38"))
# dev por mitades y por posición en el día / 11 vs 12 sorteos
cnt = {f: 0 for f in fechas}
for f in D.fecha: cnt[f] += 1
d11 = [r for r in dev if cnt[D.fecha[r[0]]] == 11]; d12 = [r for r in dev if cnt[D.fecha[r[0]]] == 12]
print("== DEV días de 11 sorteos vs ENSAMBLE ==\n" + oe(d11, "ens"))
print("== DEV días de 12 sorteos vs ENSAMBLE ==\n" + oe(d12, "ens"))
h = len(dev) // 2
print("== DEV 1a mitad ==\n" + oe(dev[:h], "ens")); print("== DEV 2a mitad ==\n" + oe(dev[h:], "ens"))
