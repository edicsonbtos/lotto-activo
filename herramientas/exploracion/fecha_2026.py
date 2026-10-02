# -*- coding: utf-8 -*-
"""Replica en 2026 de 'el operador esquiva el numero de la fecha/hora' (PREREGISTRO_fecha_2026.md)."""
import csv, json, os, datetime, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
H12 = {8: 8, 9: 9, 10: 10, 11: 11, 12: 12, 13: 1, 14: 2, 15: 3, 16: 4, 17: 5, 18: 6, 19: 7}
rows = []
for r in csv.DictReader(open(os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv"), encoding="utf-8")):
    if r["juego"] == "1":
        rows.append((r["fecha"], int(r["hora"][:2]), r["codigo"]))
rows.sort()
SHIFTS = [s for s in range(-10, 11) if abs(s) >= 3]


def objetivo(fam, f, h, s):
    d = datetime.date.fromisoformat(f)
    base = {"D0": d.day, "D1": d.day + 1, "H12": H12[h]}[fam] + s
    return str(base) if 0 <= base <= 36 else None


def medir(desde, hasta, etiqueta, B=4000, semilla=20261001):
    R = [x for x in rows if desde <= x[0] <= hasta]
    dias = sorted(set(x[0] for x in R)); di = {d: i for i, d in enumerate(dias)}
    out = {"n": len(R), "dias": len(dias)}
    for fam in ("D0", "D1", "H12"):
        def hits(s):
            v = np.full(len(dias), 0.0); n = np.full(len(dias), 0.0)
            for f, h, c in R:
                o = objetivo(fam, f, h, s)
                if o is None: continue
                n[di[f]] += 1; v[di[f]] += (c == o)
            return v, n
        vo, no = hits(0)
        vp = np.zeros(len(dias)); npl = np.zeros(len(dias))
        for s in SHIFTS:
            v, n = hits(s); vp += v; npl += n
        rng = np.random.default_rng(semilla); idx = rng.integers(0, len(dias), (B, len(dias)))
        # razon = tasa objetivo / tasa placebo, remuestreando jornadas
        ro = vo[idx].sum(1) / np.maximum(no[idx].sum(1), 1); rp = vp[idx].sum(1) / np.maximum(npl[idx].sum(1), 1)
        raz = ro / rp
        R0 = (vo.sum() / no.sum()) / (vp.sum() / npl.sum())
        p = float(np.mean(raz >= 1))
        out[fam] = dict(hits=int(vo.sum()), validos=int(no.sum()), tasa=float(vo.sum() / no.sum()),
                        tasa_placebo=float(vp.sum() / npl.sum()), R=float(R0),
                        ic95=[float(np.percentile(raz, 2.5)), float(np.percentile(raz, 97.5))],
                        p_unilateral=p, PASA=bool(R0 < 0.80 and p < 0.0167))
    print(etiqueta, json.dumps(out, ensure_ascii=False))
    return out


res = {"primario_2026": medir("2026-01-01", "2026-12-31", "2026"),
       "secundario_2025H2": medir("2025-07-01", "2025-12-31", "2025-07..12"),
       "2026_ene_abr": medir("2026-01-01", "2026-04-30", "2026 ene-abr"),
       "2026_may_sep": medir("2026-05-01", "2026-12-31", "2026 may-sep")}
json.dump(res, open(os.path.join(AQUI, "fecha_2026.json"), "w"), indent=1, ensure_ascii=False)
