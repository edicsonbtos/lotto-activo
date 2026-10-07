"""C3: análisis de la batería sobre la submuestra (4 meses de AJUSTE: 2025-08/10/12, 2026-02; los 4 de ELECCION).
UMBRALES OPERATIVOS (fijados al escribir este script, ANTES de ver ningún resultado de las variantes):
 (a) placebo PASA si, en los dos tramos, Δ mbits(S2 placebo vs PROD) tiene IC90 superior < 0 y además
     Δ_placebo ≤ Δ_sin_información + 10 mbits (sin información = frecuencia con olvido de las etiquetas de entrenamiento).
 (b) retraso PASA si la caída Δ_base − Δ_gap (S2 solo, submuestra entera) ≤ 50 % de Δ_base (y si Δ_base ≤ 0, si la
     caída ≤ 5 mbits).
 (c) semillas PASA si la DE entre las 5 semillas de Δ mbits y de Δ Top-15 es < ½ de la semiamplitud del IC90 por
     jornadas (la semilla pesa menos que el muestreo), en cada tramo.
 (d) rasgo de ruido PASA si su ganancia es < 1 % del total y |Δ_ruido − Δ_base| ≤ max(2 mbits, 2·DE semillas).
 (e) fuga: lo decide fuga_t2.py (P[t] idéntico en los 3 cortes).
 (f) bootstrap: lo da bootstrap.py; PASA si el IC90 del Δ mbits de ELECCION de la mezcla w = 0,75 es > 0
     (S2 solo se reporta).
"""
import sys, json, glob, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/ciego/T2")
import eval_s2 as E
from correr import MESES
A = E.A; SP = A.SP + "/T2"
z = np.load(A.SP + "/motor0_S2.npz"); BASE = z["P"]
SUB = np.zeros(len(A.T), bool)
for m in MESES: SUB[np.char.startswith(A.F.astype(str), m)] = True
TR = ("AJUSTE", "ELECCION")

def cargar(var):
    P = BASE.copy(); imp = None; nm = None; FR = BASE.copy()
    for mes in MESES:
        o = np.load(f"{SP}/{var}_{mes}.npz"); ip = o["filas"] - A.T[0]
        P[ip] = o["P"]; FR[ip] = o["freq"][None, :]
        imp = o["imp"] if imp is None else imp + o["imp"]; nm = [str(x) for x in o["nm"]]
    return P, imp, nm, FR

def met(P, tr):
    o = E.resumen(P, "", tr, sel=SUB); om = E.resumen(E.mezcla(P, 0.75), "", tr, sel=SUB)
    hw = (o["dmb_ic"][1] - o["dmb_ic"][0]) / 2; hw15 = (o["d15_ic"][1] - o["d15_ic"][0]) / 2
    return dict(dmb=o["dmb"], dmb_ic=o["dmb_ic"], hw=hw, d15=o["d15"], d15_ic=o["d15_ic"], hw15=hw15, top15=o["top15"],
                top15_prod=o["top15_ref"], mix_dmb=om["dmb"], mix_dmb_ic=om["dmb_ic"], mix_d15=om["d15"], n=o["n"], dias=o["dias"])

def pareado(P1, P0, tr):
    """Δ mbits de P1 contra P0 (no contra PROD) e IC90 por jornadas, en la submuestra del tramo."""
    idx = np.where(A.TRAMOS[tr] & SUB)[0]; y = A.Y[idx]; a = E.norm(P1); b = E.norm(P0)
    v = 1000 * np.log2(a[idx, y] / b[idx, y]); return v.mean(), E.ic90_dias(v, idx)

R = {}; L = []
def p(s): print(s); L.append(s)
def f(x): return f"{x:+.1f}"
def fic(ic): return f"[{ic[0]:+.1f}; {ic[1]:+.1f}]"
p(f"Submuestra: {MESES}; filas AJUSTE {int((SUB & A.TRAMOS['AJUSTE']).sum())}, ELECCION {int((SUB & A.TRAMOS['ELECCION']).sum())}")
base = {tr: met(BASE, tr) for tr in TR}; R["base"] = base
for tr in TR:
    b = base[tr]; p(f"BASE (congelado, semilla 7) {tr}: Δ mbits {f(b['dmb'])} {fic(b['dmb_ic'])} | Top-15 {b['top15']:.1f} (PROD {b['top15_prod']:.1f}) Δ {b['d15']:+.2f} pp {fic(b['d15_ic'])} | mezcla Δ {f(b['mix_dmb'])}")
# (a) placebo
Ppl, imp_pl, _, FR = cargar("placebo")
R["placebo"] = {}; ok_a = True
for tr in TR:
    m = met(Ppl, tr); si = met(FR, tr); un = met(np.full_like(BASE, 1 / 38), tr)
    R["placebo"][tr] = dict(placebo=m, sin_info=si, uniforme=un)
    c = (m["dmb_ic"][1] < 0) and (m["dmb"] <= si["dmb"] + 10); ok_a &= c
    p(f"(a) PLACEBO {tr}: Δ mbits {f(m['dmb'])} {fic(m['dmb_ic'])} (real {f(base[tr]['dmb'])}) | sin información {f(si['dmb'])} | uniforme {f(un['dmb'])} "
      f"| Top-15 {m['top15']:.1f} Δ {m['d15']:+.2f} pp | mezcla Δ {f(m['mix_dmb'])} -> {'PASA' if c else 'FALLA'}")
bs = [tuple(np.load(f"{SP}/placebo_{mes}.npz")["bs"]) for mes in MESES]; p(f"    árboles del placebo por mes (N, R): {bs}")
R["placebo"]["PASA"] = bool(ok_a)
# (b) retraso
Pg, _, _, _ = cargar("gap1"); R["gap1"] = {}
allidx = SUB & (A.TRAMOS["AJUSTE"] | A.TRAMOS["ELECCION"])
def dmb_all(P):
    idx = np.where(allidx)[0]; y = A.Y[idx]; return (1000 * np.log2(E.norm(P)[idx, y] / A.PROD[idx, y])).mean()
for tr in TR:
    m = met(Pg, tr); d, ic = pareado(Pg, BASE, tr); R["gap1"][tr] = dict(m, vs_base=d, vs_base_ic=ic)
    p(f"(b) RETRASO 1 mes {tr}: Δ mbits {f(m['dmb'])} {fic(m['dmb_ic'])} (real {f(base[tr]['dmb'])}); gap − base {f(d)} {fic(ic)} | Top-15 Δ {m['d15']:+.2f} pp (real {base[tr]['d15']:+.2f}) | mezcla Δ {f(m['mix_dmb'])} (real {f(base[tr]['mix_dmb'])})")
db, dg = dmb_all(BASE), dmb_all(Pg); caida = db - dg
ok_b = (caida <= 0.5 * db) if db > 0 else (caida <= 5)
p(f"    submuestra entera: Δ base {f(db)}, Δ gap {f(dg)}, caída {f(caida)} mbits ({100*caida/db:.0f} % de Δ base) -> {'PASA' if ok_b else 'FALLA'}")
R["gap1"]["caida"] = caida; R["gap1"]["PASA"] = bool(ok_b)
# (c) semillas
Ps = {"7": BASE}; imps = {}
for s in ("s1", "s2", "s3", "s4"): Ps[s[1:]], imps[s], nms, _ = cargar(s)
R["semillas"] = {}; ok_c = True; sd_tr = {}
for tr in TR:
    ms = {k: met(P, tr) for k, P in Ps.items()}
    v = np.array([m["dmb"] for m in ms.values()]); v15 = np.array([m["d15"] for m in ms.values()]); vm = np.array([m["mix_dmb"] for m in ms.values()])
    sd, sd15 = v.std(ddof=1), v15.std(ddof=1); sd_tr[tr] = sd
    c = (sd < 0.5 * base[tr]["hw"]) and (sd15 < 0.5 * base[tr]["hw15"]); ok_c &= c
    R["semillas"][tr] = dict(dmb=v.tolist(), d15=v15.tolist(), mix=vm.tolist(), sd=sd, sd15=sd15, top15=[m["top15"] for m in ms.values()])
    p(f"(c) SEMILLAS {tr} (7,1,2,3,4): Δ mbits {[round(x,1) for x in v]} media {v.mean():+.1f} DE {sd:.2f} (½ semiamplitud IC {0.5*base[tr]['hw']:.1f}) | "
      f"Top-15 {[round(m['top15'],1) for m in ms.values()]} Δ pp {[round(x,2) for x in v15]} DE {sd15:.2f} (½ semiampl. {0.5*base[tr]['hw15']:.2f}) | "
      f"mezcla Δ {[round(x,1) for x in vm]} -> {'PASA' if c else 'FALLA'}")
Pmean = np.mean([E.norm(P) for P in Ps.values()], 0)
for tr in TR:
    m = met(Pmean, tr); p(f"    bagging de las 5 semillas (media de P) {tr}: Δ mbits {f(m['dmb'])} {fic(m['dmb_ic'])}, Δ Top-15 {m['d15']:+.2f} pp")
R["semillas"]["PASA"] = bool(ok_c)
# (d) ruido
Pr, imp_r, nm_r, _ = cargar("ruido"); share = imp_r / imp_r.sum(); j = nm_r.index("ruido_gauss")
rank = int((share > share[j]).sum()) + 1
R["ruido"] = dict(share=float(share[j]), rank=rank, nfeat=len(nm_r)); ok_d = share[j] < 0.01
for tr in TR:
    m = met(Pr, tr); d, ic = pareado(Pr, BASE, tr); R["ruido"][tr] = dict(m, vs_base=d, vs_base_ic=ic)
    lim = max(2.0, 2 * sd_tr[tr]); c = abs(m["dmb"] - base[tr]["dmb"]) <= lim; ok_d &= c
    p(f"(d) RUIDO {tr}: Δ mbits {f(m['dmb'])} (base {f(base[tr]['dmb'])}); ruido − base {f(d)} {fic(ic)} (límite ±{lim:.1f}) | Top-15 Δ {m['d15']:+.2f} pp (base {base[tr]['d15']:+.2f})")
orden = np.argsort(-share)
p(f"    ganancia del rasgo de ruido: {100*share[j]:.2f} % del total, puesto {rank} de {len(nm_r)}; mediana de los rasgos {100*np.median(share):.2f} %; "
  f"top-5: {[(nm_r[k], round(100*share[k],1)) for k in orden[:5]]}; últimos 5: {[(nm_r[k], round(100*share[k],2)) for k in orden[-5:]]} -> {'PASA' if ok_d else 'FALLA'}")
R["ruido"]["PASA"] = bool(ok_d)
json.dump(R, open("/home/user/lotto-activo/investigacion/2026-10-06/ciego/T2/resultados.json", "w"), indent=1, default=float)
