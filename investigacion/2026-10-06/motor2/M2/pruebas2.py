# -*- coding: utf-8 -*-
"""M2 v2: el SE bootstrap falla con conteos minúsculos (O=0 => SE≈0 => z falsos, p.ej. G_lw M6). Se pasa a la otra vía
pre-registrada: p por PERMUTACIÓN de jornadas para cada test + BH-FDR q=0,10.
- Grupos de calendario (pago, quincena, vq, ini, fin, fer, lw): residuo MÁS ALLÁ del día de la semana. E se reescala por
  el O/E de su día de la semana en el tramo (mbits: se resta la media día×hora) y las etiquetas se barajan DENTRO del
  mismo día de la semana. Así 'viernes de quincena' se compara con los otros viernes.
- Grupos de día de la semana (finde, vie, mvf) y la interacción tarde×mvf: sin ajuste por día; etiquetas barajadas entre
  todos los días (es lo ya conocido; se reporta como control)."""
import numpy as np, json
import comun as C
rng = np.random.default_rng(7)
B = 2000
METS = list(C.CATS_ALL) + ["M2_mbits"]
CAL = ["G_pago", "G_q15", "G_q30", "G_vq", "G_ini", "G_fin", "G_fer", "G_lw"]
SEM = ["G_finde", "G_vie", "G_mvf", "G_tarde_mvf"]
ATRd = {g: np.array([C.ATR[f][g] for f in C.UF]) for g in C.GRUPOS}
DOWd = np.array([__import__("datetime").date.fromisoformat(f).weekday() for f in C.UF])

def tramo(tr):
    m = C.A.TRAMOS[tr]; idx = np.where(m)[0]; d = C.DAYID[idx]; t = C.TARDE[idx].astype(int); nd = len(C.UF)
    dow = C.DOW[idx]; AG = {}; AGs = {}
    for k, M in C.CATS_ALL.items():
        o = M[idx, C.Y[idx]].astype(float); e = (C.PROD[idx] * M[idx]).sum(1)
        es = e.copy()
        for w in range(7):
            q = dow == w
            if q.any(): es[q] *= o[q].sum() / e[q].sum()
        for E_, dst in ((e, AG), (es, AGs)):
            O = np.zeros((nd, 2)); E = np.zeros((nd, 2)); np.add.at(O, (d, t), o); np.add.at(E, (d, t), E_); dst[k] = (O, E)
    mb = C.MB[idx]; mbs = mb.copy()
    for w in range(7):
        for h in range(12):
            q = (dow == w) & (C.H[idx] == h)
            if q.any(): mbs[q] -= mb[q].mean()
    for v, dst in ((C.MBc[idx], AG), (mbs, AGs)):
        O = np.zeros((nd, 2)); E = np.zeros((nd, 2)); np.add.at(O, (d, t), v); np.add.at(E, (d, t), 1.0); dst["M2_mbits"] = (O, E)
    dias = np.zeros(nd, bool); dias[np.unique(d)] = True
    return AG, AGs, dias

def lr(O, E, sel, met, cols=(0, 1)):
    o = O[sel][:, list(cols)].sum(); e = E[sel][:, list(cols)].sum()
    return o / e if met == "M2_mbits" else np.log((o + 0.5) / (e + 0.5))

def efecto(AG, met, gd, dias, inter=False):
    O, E = AG[met]
    if inter:
        a = lr(O, E, dias & gd, met, (1,)) - lr(O, E, dias & gd, met, (0,))
        b = lr(O, E, dias & ~gd, met, (1,)) - lr(O, E, dias & ~gd, met, (0,))
        return a - b
    return lr(O, E, dias & gd, met) - lr(O, E, dias & ~gd, met)

def familia(AG, AGs, dias, A):
    r = {}
    for g in CAL:
        for met in METS: r[(g, met)] = efecto(AGs, met, A[g], dias)
    for g in SEM:
        for met in METS:
            r[(g, met)] = efecto(AG, met, A["G_mvf"], dias, True) if g == "G_tarde_mvf" else efecto(AG, met, A[g], dias)
    return r

res = {}
for tr in ("AJUSTE", "ELECCION"):
    AG, AGs, dias = tramo(tr); obs = familia(AG, AGs, dias, ATRd); idd = np.where(dias)[0]
    perms = {k: [] for k in obs}
    for b in range(B):
        A1 = {}; pw = idd.copy()                       # dentro del día de la semana
        for w in range(7):
            q = idd[DOWd[idd] == w]; pw[DOWd[idd] == w] = rng.permutation(q)
        pa = rng.permutation(idd)                      # entre todos los días
        for g in C.GRUPOS:
            v = ATRd[g].copy(); v[idd] = ATRd[g][pw if g in CAL else pa]; A1[g] = v
        for k, x in familia(AG, AGs, dias, A1).items(): perms[k].append(x)
    pv = {k: (1 + np.sum(np.abs(np.array(perms[k])) >= abs(obs[k]) - 1e-12)) / (B + 1) for k in obs}
    p1 = {k: (1 + np.sum(np.sign(obs[k]) * np.array(perms[k]) >= abs(obs[k]) - 1e-12)) / (B + 1) for k in obs}
    sd = {k: np.std(perms[k]) for k in obs}
    res[tr] = dict(obs=obs, pv=pv, p1=p1, sd=sd)

aj, el = res["AJUSTE"], res["ELECCION"]
claves = list(aj["obs"]); fam = {"CAL": [k for k in claves if k[0] in CAL], "SEM": [k for k in claves if k[0] in SEM]}
pasa = set()
for nom, ks in fam.items():
    p = np.array([aj["pv"][k] for k in ks]); o = np.argsort(p); m = len(p); thr = 0.10 * np.arange(1, m + 1) / m
    ok = np.where(p[o] <= thr)[0]
    if len(ok): pasa |= {ks[j] for j in o[: ok.max() + 1]}
print("p por permutación de jornadas (B=2000); BH-FDR q=0,10 por familia (CAL: 8x6=48 tests, SEM: 4x6=24)")
print(f"{'grupo':12} {'métrica':9} {'AJ':>9} {'z*':>6} {'p':>6} FDR | {'EL':>9} {'z*':>6} {'p1':>6}")
filas = []
for k in claves:
    f = (lambda x: f"{np.exp(x):.3f}x") if k[1] != "M2_mbits" else (lambda x: f"{x:+.1f}mb")
    conf = k in pasa and np.sign(el["obs"][k]) == np.sign(aj["obs"][k]) and el["p1"][k] < 0.05
    pel = el["p1"][k] if np.sign(el["obs"][k]) == np.sign(aj["obs"][k]) else 1 - el["p1"][k]
    filas.append(dict(g=k[0], met=k[1], aj=aj["obs"][k], p=aj["pv"][k], fdr=k in pasa, el=el["obs"][k], p1_el=pel, conf=bool(conf)))
    print(f"{k[0]:12} {k[1]:9} {f(aj['obs'][k]):>9} {aj['obs'][k]/aj['sd'][k]:+6.2f} {aj['pv'][k]:6.4f} {'SÍ' if k in pasa else '  '} | "
          f"{f(el['obs'][k]):>9} {el['obs'][k]/el['sd'][k]:+6.2f} {pel:6.4f} {'CONFIRMA' if conf else ''}")
json.dump(filas, open("pruebas2.json", "w"), indent=1, default=float)
