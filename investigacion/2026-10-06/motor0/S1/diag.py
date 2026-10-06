# -*- coding: utf-8 -*-
"""S1 diagnóstico adversarial (exploratorio, no pre-registrado): ¿de dónde sale la selección en ELECCION?"""
import sys; import numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S1"); import estrategias as E
PR = E.PR; Z = E.Z; DS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
for mot in ("PROD", "M4"):
    p = np.nan_to_num(PR[f"{mot}__LR"]); hit = Z[f"{mot}__hit"]; masa = Z[f"{mot}__masa15"]
    for tr in ("AJUSTE", "ELECCION"):
        m = A.TRAMOS[tr] & E.CON_RD; sel = p >= 0.5
        print(f"== {mot} {tr}: por día de la semana: jugado% / acierto jugados / acierto no jugados / acierto total")
        print("   " + " | ".join(f"{DS[d]} {100*sel[m&(A.DOW==d)].mean():3.0f}% {100*hit[m&(A.DOW==d)&sel].mean() if (m&(A.DOW==d)&sel).any() else np.nan:4.1f}/{100*hit[m&(A.DOW==d)&~sel].mean() if (m&(A.DOW==d)&~sel).any() else np.nan:4.1f}/{100*hit[m&(A.DOW==d)].mean():4.1f}" for d in range(7)))
        # discriminación dentro del día: P̂ menos su media del día
        u, inv = np.unique(A.F, return_inverse=True)
        pd_ = (np.bincount(inv, p * m, len(u)) / np.maximum(np.bincount(inv, m.astype(float), len(u)), 1))[inv]
        pw = p - pd_
        from scipy.stats import spearmanr
        r1 = spearmanr(pw[m], hit[m]).correlation; r2 = spearmanr(pd_[m], hit[m]).correlation
        print(f"   corr(P̂ dentro del día, acierto) {r1:+.3f} | corr(P̂ media del día, acierto) {r2:+.3f}")
        # reglas simples
        st, pay = E.planes_cache[mot] if hasattr(E, "planes_cache") else E.top15(A.PROD if mot == "PROD" else E.M4)
        for nom, s in (("saltar mié-vie", ~np.isin(A.DOW, [2, 3, 4])), ("saltar si π_d>0,15", Z[f"{mot}__pri"] <= .15),
                       ("saltar si q_h>0,2", Z[f"{mot}__q"] <= .2), ("saltar si RD(h−1) en Top-15", Z[f"{mot}__rd_in15"] == 0),
                       ("selector LR P̂≥0,50", sel)):
            r = E.metr(st * s, pay * s, m)
            print(f"   regla {nom:28} ret/ficha {100*r['ret']:+6.1f}% [{100*r['lo']:+4.0f};{100*r['hi']:+4.0f}] jugado {100*r['jugado']:4.1f}% acierto {100*r['acierto']:.1f}%")
