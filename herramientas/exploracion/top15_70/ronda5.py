# -*- coding: utf-8 -*-
"""Ronda 5 (PREREGISTRO_ronda5.md): otros números de fecha/hora que el operador podría esquivar."""
import contextlib, io, json, os, runpy, datetime
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path(os.path.join(AQUI, "top15_70.py"))
LE = G["LE"]; Y, PE = G["Y"], G["PE"]
IA, IB, DIA, HORA, FECHA = G["IA"], G["IB"], G["DIA"], G["HORA"], G["FECHA"]
boot, quitar, pos_de, ORD_B1 = G["boot"], G["quitar"], G["pos_de"], G["ORD_B1"]
SEM = 20261001
def boot_oe(o, e, dias, q, B=4000):
    u, g = np.unique(dias, return_inverse=True)
    so = np.bincount(g, o); se = np.bincount(g, e)
    idx = np.random.default_rng(SEM).integers(0, len(u), (B, len(u)))
    bs = so[idx].sum(1) / se[idx].sum(1)
    return float(o.sum() / e.sum()), [float(np.percentile(bs, q)), float(np.percentile(bs, 100 - q))]
d = np.array([int(f[8:10]) for f in FECHA]); m = np.array([int(f[5:7]) for f in FECHA])
yy = np.array([int(f[2:4]) for f in FECHA])
wd = np.array([datetime.date.fromisoformat(f).isoweekday() for f in FECHA])
h12 = np.array([(h + 8 - 1) % 12 + 1 for h in HORA])
ds = np.array([sum(map(int, str(x))) for x in d])
C = {"C1_mes": m, "C2_semana": wd, "C3_dia+mes": d + m, "C4_suma_digitos": ds,
     "C5_n_sorteo": HORA - 7, "C6_dia+hora12": d + h12, "C7_anio": yy, "C8_espejo": 38 - d}
out = {}; S = []
def log(s): print(s, flush=True); S.append(s)
for nom, v in C.items():
    res = {}
    for desp in (0, 1, -1):
        w = v + desp
        ok = np.array([str(int(x)) in LE.IDX for x in w])
        a = np.array([LE.IDX[str(int(x))] if k else 0 for x, k in zip(w, ok)])
        o = ((Y == a) & ok).astype(float); e = np.where(ok, PE[np.arange(len(Y)), a], 0.0)
        A = IA & ok; B = IB & ok
        if desp == 0:
            oa, ia = boot_oe(o[A], e[A], DIA[A], 2.5); ob, ib = boot_oe(o[B], e[B], DIA[B], 100*0.05/8/2)
            res["dev-A"] = (oa, ia); res["dev-B"] = (ob, ib)
            pasa = oa < 1 and ob < 1 and ib[1] < 1
            res["pasa"] = pasa
            log(f"{nom}: n(A,B)=({A.sum()},{B.sum()}) dev-A O/E {oa:.3f} [{ia[0]:.2f};{ia[1]:.2f}]  dev-B {ob:.3f} [IC99,4 {ib[0]:.2f};{ib[1]:.2f}] => {'PASA' if pasa else 'NO PASA'}")
        else:
            ob, _ = boot_oe(o[B], e[B], DIA[B], 2.5)
            res[f"placebo{desp:+d}"] = ob
    log("   placebos dev-B: " + ", ".join(f"{k} {res[k]:.2f}" for k in res if k.startswith("pl")))
    out[nom] = {k: (v if not isinstance(v, np.bool_) else bool(v)) for k, v in res.items()}
json.dump(out, open(os.path.join(AQUI, "ronda5.json"), "w"), default=float, indent=1)
open(os.path.join(AQUI, "salida_ronda5.txt"), "w", encoding="utf-8").write("\n".join(S))
