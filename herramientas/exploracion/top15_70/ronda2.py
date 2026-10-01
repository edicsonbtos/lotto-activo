# -*- coding: utf-8 -*-
"""Ronda 2 (PREREGISTRO_ronda2.md). Reutiliza las matrices de la ronda 1 corriendo top15_70.py en memoria.

Uso:  python herramientas/exploracion/top15_70/ronda2.py   -> ronda2.json, salida_ronda2.txt
"""
import contextlib, io, json, os, runpy
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path(os.path.join(AQUI, "top15_70.py"))
LE = G["LE"]; K = 38
Y, PE, P4, P6 = G["Y"], G["PE"], G["P4"], G["P6"]
IA, IB, DIA, HORA, FECHA = G["IA"], G["IB"], G["DIA"], G["HORA"], G["FECHA"]
boot, quitar, regla_rd, orden_de, pos_de = G["boot"], G["quitar"], G["regla_rd"], G["orden_de"], G["pos_de"]
ORD_B1 = G["ORD_B1"]
SEMILLA = 20261001
SAL = []; RES = {}


def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)


def boot_oe(o, e, dias, q, B=4000):
    u, g = np.unique(dias, return_inverse=True)
    so = np.bincount(g, o); se = np.bincount(g, e)
    rng = np.random.default_rng(SEMILLA); idx = rng.integers(0, len(u), (B, len(u)))
    bs = so[idx].sum(1) / se[idx].sum(1)
    return float(o.sum() / e.sum()), [float(np.percentile(bs, q)), float(np.percentile(bs, 100 - q))]


# ------------------------------------------------------------------ familia A
log("FAMILIA A — ¿el operador evita lo que más se juega?")
dia_mes = np.array([int(f[8:10]) for f in FECHA])
reloj12 = np.array([(h + 8 - 1) % 12 + 1 for h in HORA])       # 8..12, 1..7
cand = {"A1_dia_del_mes": np.array([LE.IDX[str(d)] for d in dia_mes]),
        "A2_hora_12h": np.array([LE.IDX[str(c)] for c in reloj12])}
for nom, a in cand.items():
    o = (Y == a).astype(float); e = PE[np.arange(len(Y)), a]
    oeA, icA = boot_oe(o[IA], e[IA], DIA[IA], 2.5)
    oeB, icB = boot_oe(o[IB], e[IB], DIA[IB], 100 * 0.05 / 3 / 2)     # IC 99,17 %
    pasa = oeA < 1 and oeB < 1 and icB[1] < 1
    RES[nom] = dict(devA=dict(oe=oeA, ic95=icA, obs=int(o[IA].sum()), esp=float(e[IA].sum())),
                    devB=dict(oe=oeB, ic99_17=icB, obs=int(o[IB].sum()), esp=float(e[IB].sum())),
                    veredicto="PASA" if pasa else "NO PASA")
    log(f"  {nom}: dev-A O/E {oeA:.3f} [{icA[0]:.2f}; {icA[1]:.2f}] (obs {int(o[IA].sum())}, esp {e[IA].sum():.1f})"
        f"  dev-B O/E {oeB:.3f} [IC99,17 {icB[0]:.2f}; {icB[1]:.2f}] (obs {int(o[IB].sum())}, esp {e[IB].sum():.1f})"
        f"  => {RES[nom]['veredicto']}")
    if pasa:
        o2 = quitar(ORD_B1, [{int(x)} for x in a])
        hB = (pos_de(o2[IB], Y[IB]) < 15).astype(float) - (pos_de(ORD_B1[IB], Y[IB]) < 15)
        RES[nom]["dif_top15_devB"] = boot(hB, DIA[IB])
        log(f"    sacarlo del Top-15 en dev-B: {100*hB.mean():+.2f} pp")

fA = np.bincount(Y[IA], minlength=K) / IA.sum(); fB = np.bincount(Y[IB], minlength=K) / IB.sum()


def spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


rho = spearman(fA, fB)
rng = np.random.default_rng(SEMILLA)
perm = np.array([spearman(fA, rng.permutation(fB)) for _ in range(20000)])
p = float(np.mean(perm >= rho))
RES["A3_popularidad_estable"] = dict(rho=rho, p_perm=p, veredicto="PASA" if rho > 0 and p < 0.0167 else "NO PASA",
                                     frec_devA=fA.tolist(), frec_devB=fB.tolist())
log(f"  A3_popularidad_estable: Spearman dev-A vs dev-B rho = {rho:+.3f}, p = {p:.4f} => "
    f"{RES['A3_popularidad_estable']['veredicto']}")
log(f"     frecuencias dev-B: min {100*fB.min():.2f} %  max {100*fB.max():.2f} %  (uniforme {100/K:.2f} %)")

# ------------------------------------------------------------------ familia B
log("\nFAMILIA B — P4 + P6 juntos (descriptivo: dev-B ya se vio en la ronda 1)")
Pc = np.sqrt(P4 * P6); Pc /= Pc.sum(1, keepdims=True)
Oc = regla_rd(orden_de(Pc))
hc = (pos_de(Oc[IB], Y[IB]) < 15).astype(float); h1 = (pos_de(ORD_B1[IB], Y[IB]) < 15).astype(float)
mbc = np.log2(Pc[IB][np.arange(IB.sum()), Y[IB]] * K) * 1000
mb0 = np.log2(PE[IB][np.arange(IB.sum()), Y[IB]] * K) * 1000
RES["B_comb"] = dict(top15=boot(hc, DIA[IB]), dif_vs_B1=boot(hc - h1, DIA[IB]), mbits=float(mbc.mean()),
                     dif_mbits_vs_B0=boot(mbc - mb0, DIA[IB]), veredicto="descriptivo (contaminado)")
log(f"  B-comb: Top-15 {100*hc.mean():.2f} % (B1 {100*h1.mean():.2f} %, dif {100*(hc-h1).mean():+.2f} pp "
    f"[{100*RES['B_comb']['dif_vs_B1']['ic95'][0]:+.2f}; {100*RES['B_comb']['dif_vs_B1']['ic95'][1]:+.2f}])  "
    f"mbits {mbc.mean():.1f} (dif vs B0 {(mbc-mb0).mean():+.1f})")
m15 = np.sort(Pc[IB], 1)[:, ::-1][:, :15].sum(1)
log(f"  masa Top-15 que el modelo se da: media {100*m15.mean():.1f} %, máx {100*m15.max():.1f} %, "
    f"sorteos con ≥ 70 %: {int((m15 >= .7).sum())}")

# ------------------------------------------------------------------ familia C
log("\nFAMILIA C — Top-22 escalonado 3-3-3-2-2-1×17 (30 fichas), desglose del plan 9 (B1)")
posB = pos_de(ORD_B1[IB], Y[IB])
w = np.zeros(K); w[:22] = [3, 3, 3, 2, 2] + [1] * 17
neto = 30 * w[posB] - w.sum()
gana = (neto > 0).astype(float); empata = (neto == 0).astype(float); pierde = (neto < 0).astype(float)
RES["C_top22"] = dict(no_pierde=boot(gana + empata, DIA[IB]), gana=float(gana.mean()), recupera=float(empata.mean()),
                      pierde=float(pierde.mean()), ret_ficha=boot(neto / w.sum(), DIA[IB]))
log(f"  no pierde {100*(gana+empata).mean():.1f} % [IC95 {100*RES['C_top22']['no_pierde']['ic95'][0]:.1f}; "
    f"{100*RES['C_top22']['no_pierde']['ic95'][1]:.1f}] = gana {100*gana.mean():.1f} % + recupera lo apostado "
    f"{100*empata.mean():.1f} %;  pierde todo {100*pierde.mean():.1f} %;  retorno/ficha "
    f"{100*RES['C_top22']['ret_ficha']['media']:+.1f} % [{100*RES['C_top22']['ret_ficha']['ic95'][0]:+.1f}; "
    f"{100*RES['C_top22']['ret_ficha']['ic95'][1]:+.1f}]")

with io.open(os.path.join(AQUI, "ronda2.json"), "w", encoding="utf-8") as fh:
    json.dump(RES, fh, ensure_ascii=False, indent=1)
with io.open(os.path.join(AQUI, "salida_ronda2.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(SAL) + "\n")
