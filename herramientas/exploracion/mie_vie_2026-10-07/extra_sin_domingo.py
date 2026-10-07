# -*- coding: utf-8 -*-
"""Sensibilidad POST-HOC (no preregistrada): el 'resto' incluye el domingo, que arrastra. Sin domingo + omnibus 7 dias."""
import runpy, os, sys, io, contextlib
AQUI = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.path.join(AQUI, "mie_vie.py"))
import numpy as np
bits, hora, dow, inv, nd, rng = g["bits"], g["hora"], g["dow"], g["inv"], g["nd"], g["rng"]
h15, h5 = g["h15"], g["h5"]
def dif(v, A, B, w=None):
    num = ww = 0
    for h in range(12):
        a = A & (hora == h); b = B & (hora == h)
        if a.sum() and b.sum():
            if w is None: d = v[a].mean() - v[b].mean()
            else: d = (v[a]*w[a]).sum()/w[a].sum() - (v[b]*w[b]).sum()/w[b].sum()
            num += a.sum() * d; ww += a.sum()
    return num / ww
def ic(v, A, B, Bt=2000):
    est = dif(v, A, B); o = []
    for _ in range(Bt):
        w = np.bincount(rng.integers(0, nd, nd), minlength=nd)[inv].astype(float); o.append(dif(v, A, B, w))
    return est, np.percentile(o, 2.5), np.percentile(o, 97.5)
MV = np.isin(dow, [2, 3, 4]); OTR = np.isin(dow, [0, 1, 5]); MIE = dow == 2; OT2 = np.isin(dow, [0, 1, 3, 4, 5])
for nom, v, k in (("mbits", bits, 1), ("Top5 pp", h5, 100), ("Top15 pp", h15, 100)):
    for t, A, B in (("mie-vie vs lun,mar,sab (sin dom)", MV, OTR), ("mie vs lun,mar,jue,vie,sab", MIE, OT2)):
        e, l, h = ic(v, A, B); print(f"{nom:9s} {t:36s} {k*e:+7.2f} [{k*l:+.2f}; {k*h:+.2f}]")
# omnibus: varianza entre dias de la semana de mbits, permutacion dentro de semana
from datetime import date, timedelta
fecha = g["fecha"]; ud = g["ud"]; dia = g["dia"]
fe = {}
for f, d in zip(fecha, dia): fe[d] = f
sem = np.array([date.fromisoformat(fe[d]).toordinal() - date.fromisoformat(fe[d]).weekday() for d in ud])
grp = {}
for i, s in enumerate(sem): grp.setdefault(s, []).append(i)
gl = [np.array(x) for x in grp.values()]
dow_d = g["dow_d"].copy()
def stat(dd, excl_dom):
    m = dd[inv]; keep = np.ones(len(bits), bool) if not excl_dom else (m != 6)
    mu = [bits[keep & (m == k)].mean() for k in range(7) if (not excl_dom or k != 6)]
    return np.var(mu)
for ex in (False, True):
    s0 = stat(dow_d, ex); c = 0; B = 3000
    for _ in range(B):
        dd = dow_d.copy()
        for gi in gl: dd[gi] = dd[rng.permutation(gi)]
        c += stat(dd, ex) >= s0
    print(f"omnibus 7 dias {'SIN domingo' if ex else 'con domingo'}: var entre medias {s0:.1f}  p perm = {(c+1)/(B+1):.4f}")
