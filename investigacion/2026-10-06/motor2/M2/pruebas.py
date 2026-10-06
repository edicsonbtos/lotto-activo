# -*- coding: utf-8 -*-
"""M2: residuo de calendario contra PROD. AJUSTE (FDR + permutación de jornadas) -> ELECCION (confirmación)."""
import numpy as np, json, sys
from scipy.stats import norm
import comun as C
rng = np.random.default_rng(20261006)
METS = list(C.CATS_ALL) + ["M2_mbits"]
GR = [g for g in C.GRUPOS if g != "G_mvf"] + ["G_mvf", "G_tarde_mvf"]

def stat(O, E, g_d, met, dias):
    """O,E: (nd,2). g_d: bool por día. dias: días del tramo. -> (est, se_delta)."""
    def lr(dsel, col):   # log O/E (o media para mbits) y residuos por día para delta
        o = O[dsel][:, col].sum(1) if isinstance(col, list) else O[dsel][:, col]
        e = E[dsel][:, col].sum(1) if isinstance(col, list) else E[dsel][:, col]
        if met == "M2_mbits":
            r = o.sum() / e.sum(); return r, ((o - r * e) ** 2).sum() / e.sum() ** 2
        r = o.sum() / e.sum(); return np.log(r), ((o - r * e) ** 2).sum() / max(o.sum(), 1e-9) ** 2
    if g_d is None:   # interacción tarde-mvf: mvf en dias
        mv = C._MVF_D
        a1, v1 = lr(dias & mv, 1); a0, v0 = lr(dias & mv, 0); b1, w1 = lr(dias & ~mv, 1); b0, w0 = lr(dias & ~mv, 0)
        return (a1 - a0) - (b1 - b0), np.sqrt(v1 + v0 + w1 + w0)   # (aprox: ignora covarianza dentro del día)
    a, va = lr(dias & g_d, [0, 1]); b, vb = lr(dias & ~g_d, [0, 1])
    return a - b, np.sqrt(va + vb)

def familia(AG, dias, attr_d):
    res = {}
    for g in GR:
        for met in METS:
            if g == "G_tarde_mvf":
                C._MVF_D = attr_d["G_mvf"]; e, s = stat(*AG[met], None, met, dias)
            else:
                e, s = stat(*AG[met], attr_d[g], met, dias)
            res[(g, met)] = (e, s)
    return res

def boot_se(AG, dias, attr_d, g, met, B=2000):
    """SE por bootstrap de jornadas (estratificado por grupo/complemento)."""
    O, E = AG[met]; idx = np.where(dias)[0]; vals = []
    gd = attr_d["G_mvf"] if g == "G_tarde_mvf" else attr_d[g]
    i1 = idx[gd[idx]]; i0 = idx[~gd[idx]]
    for _ in range(B):
        s = np.r_[rng.choice(i1, len(i1)), rng.choice(i0, len(i0))]
        Ob = np.zeros_like(O); Eb = np.zeros_like(E); np.add.at(Ob, s, O[s]); np.add.at(Eb, s, E[s])
        dd = np.zeros(len(dias), bool); dd[s] = True
        if g == "G_tarde_mvf":
            C._MVF_D = gd; vals.append(stat(Ob, Eb, None, met, dd)[0])
        else:
            vals.append(stat(Ob, Eb, gd, met, dd)[0])
    return np.std(vals, ddof=1)

ATRd = {g: np.array([C.ATR[f][g] for f in C.UF]) for g in C.GRUPOS}
salida = {}
for tr in ("AJUSTE", "ELECCION"):
    m = C.A.TRAMOS[tr]; AG = C.agregados(m); dias = np.zeros(len(C.UF), bool); dias[np.unique(C.DAYID[m])] = True
    R = familia(AG, dias, ATRd)
    salida[tr] = dict(AG=AG, dias=dias, R=R)

# --- AJUSTE: SE bootstrap, p, FDR ---
AG, dias, R = salida["AJUSTE"]["AG"], salida["AJUSTE"]["dias"], salida["AJUSTE"]["R"]
claves = list(R); Z = {}; P = {}
for k in claves:
    se = boot_se(AG, dias, ATRd, *k, B=1000); Z[k] = R[k][0] / se; P[k] = 2 * norm.sf(abs(Z[k]))
pv = np.array([P[k] for k in claves]); o = np.argsort(pv); mtests = len(pv)
bh = np.zeros(mtests, bool); thr = 0.10 * np.arange(1, mtests + 1) / mtests
ok = np.where(pv[o] <= thr)[0]
if len(ok): bh[o[: ok.max() + 1]] = True
# permutación de jornadas: barajar los atributos de calendario entre los días de AJUSTE (z delta)
zd_obs = max(abs(R[k][0] / R[k][1]) for k in claves)
idd = np.where(dias)[0]; mx = []
for b in range(1000):
    perm = rng.permutation(idd); A2 = {g: v.copy() for g, v in ATRd.items()}
    for g in A2: A2[g][idd] = ATRd[g][perm]
    Rb = familia(AG, dias, A2); mx.append(max(abs(v[0] / v[1]) for v in Rb.values()))
mx = np.array(mx); p_fam = (1 + (mx >= zd_obs).sum()) / (1 + len(mx))
# ELECCION: p una cola en la dirección de AJUSTE
AGe, diase, Re = salida["ELECCION"]["AG"], salida["ELECCION"]["dias"], salida["ELECCION"]["R"]
print(f"tests {mtests}; max|z| delta AJUSTE {zd_obs:.2f}; p familiar (permutación) {p_fam:.3f}; pasan FDR: {bh.sum()}")
print(f"{'grupo':12} {'métrica':10} {'AJ efecto':>9} {'z':>6} {'p':>7} FDR | {'EL efecto':>9} {'z':>6}")
filas = []
for j, k in enumerate(claves):
    ze = Re[k][0] / boot_se(AGe, diase, ATRd, *k, B=400) if (bh[j] or abs(Z[k]) > 2) else Re[k][0] / Re[k][1]
    conf = bh[j] and np.sign(Re[k][0]) == np.sign(R[k][0]) and norm.sf(abs(ze)) < 0.05
    ef = (lambda x: f"{np.exp(x):.3f}x") if k[1] != "M2_mbits" else (lambda x: f"{x:+.1f}mb")
    filas.append(dict(g=k[0], met=k[1], aj=R[k][0], z=Z[k], p=P[k], fdr=bool(bh[j]), el=Re[k][0], ze=ze, conf=bool(conf)))
    print(f"{k[0]:12} {k[1]:10} {ef(R[k][0]):>9} {Z[k]:+6.2f} {P[k]:7.4f} {'SÍ' if bh[j] else '  '} | {ef(Re[k][0]):>9} {ze:+6.2f} {'CONFIRMA' if conf else ''}")
json.dump(dict(p_fam=p_fam, zmax=zd_obs, filas=filas), open("pruebas.json", "w"), indent=1, default=float)
