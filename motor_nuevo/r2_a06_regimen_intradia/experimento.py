# -*- coding: utf-8 -*-
"""r2_a06_regimen_intradia: ¿cambia la fuerza de la evitación de pares / no-repetición según la posición del día,
el fin de semana o los días de 12 sorteos? Reajuste con log P_ens como offset, 5 bloques de jornada (ag02), λ=30.
Uso (raíz del worktree): PYTHONIOENCODING=utf-8 python motor_nuevo/r2_a06_regimen_intradia/experimento.py
Solo filas < 9357. Δ frente a ag12_transiciones/P_V1.npy.
"""
import json, os, sys, time
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI)
sys.path.insert(0, MN); sys.path.insert(0, os.path.join(MN, "ag02_residuo_boost")); sys.path.insert(0, os.path.join(MN, "ag12_transiciones"))
import arnes as A  # noqa
import importlib.util as _iu
_sp = _iu.spec_from_file_location('exp_ag02', os.path.join(MN, 'ag02_residuo_boost', 'experimento.py'))
E2 = _iu.module_from_spec(_sp); _sp.loader.exec_module(E2)
import rasgos12 as R  # noqa
LAM = 30.0; K = 38
t0 = time.time()
out = []
def pr(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); out.append(s)

D = A.datos().prefijo(A.CORTE)
Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True)
LPE = np.log(np.clip(Pens, 1e-12, None))
P_V1 = np.load(os.path.join(MN, "ag12_transiciones", "P_V1.npy"))
X33, extra = R.construir(D, A.W); X33 = X33.astype(np.float64)
n = X33.shape[0]
seq = np.asarray(D.seq); hora = np.asarray(D.hora); diaT = np.asarray(D.dia); dow = np.asarray(D.dow)
dia = diaT[A.W:A.CORTE]; blo = E2.bloques_jornada(dia)
kpos = extra[:, 1].astype(int)

# REPD y régimen (fila t: solo seq[:t] y calendario de t)
REPD = np.zeros((n, K)); D12 = np.zeros(n)
hoy_cnt = np.zeros(K); dia_act = None; hora_ini = None
for t in range(A.CORTE):
    if diaT[t] != dia_act:
        dia_act = diaT[t]; hoy_cnt[:] = 0; hora_ini = hora[t]
    if t >= A.W:
        REPD[t - A.W] = np.log1p(hoy_cnt); D12[t - A.W] = float(hora_ini == 0)
    hoy_cnt[seq[t]] += 1
MED = ((kpos >= 4) & (kpos <= 7)).astype(float); TAR = (kpos >= 8).astype(float)
FDS = (dow[A.W:A.CORTE] >= 5).astype(float)
G = np.concatenate([X33[:, :, 27:33], REPD[:, :, None]], axis=2)       # 7 columnas
GN = R.NUEVOS + ["REPD"]

def inter(ind, tag):
    return G * ind[:, None, None], [f"{g}x{tag}" for g in GN]
Xmed, nmed = inter(MED, "MED"); Xtar, ntar = inter(TAR, "TAR"); Xfds, nfds = inter(FDS, "FDS"); Xd12, nd12 = inter(D12, "D12")
base_n = R.NOMBRES
VAR = {
    "V1_refit_control": (X33, base_n),
    "VR_ablacion_33_REPD": (np.concatenate([X33, REPD[:, :, None]], 2), base_n + ["REPD"]),
    "VA_tramo_dia": (np.concatenate([X33, REPD[:, :, None], Xmed, Xtar], 2), base_n + ["REPD"] + nmed + ntar),
    "VB_fin_de_semana": (np.concatenate([X33, REPD[:, :, None], Xfds], 2), base_n + ["REPD"] + nfds),
    "VC_dias_12": (np.concatenate([X33, REPD[:, :, None], Xd12], 2), base_n + ["REPD"] + nd12),
}
pr(f"n={n}, régimen: MED {MED.mean():.3f} TAR {TAR.mean():.3f} FDS {FDS.mean():.3f} D12 {D12.mean():.3f}; bloques {np.bincount(blo)}")

# ---------------- descriptivo: O/E frente a P_V1 por régimen ----------------
Y = np.zeros((n, K)); Y[np.arange(n), y] = 1
trans_any = (X33[:, :, 27:33].sum(2) > 0); rep_any = REPD > 0
desc = {}
def oe(mask, filas, nombre):
    m = mask & filas[:, None]
    o = Y[m].sum(); e = P_V1[m].sum(); v = (P_V1[m] * (1 - P_V1[m])).sum()
    z = (o - e) / np.sqrt(v) if v > 0 else 0
    desc[nombre] = dict(obs=float(o), esp=float(e), oe=float(o / e) if e else None, z=float(z))
    pr(f"  {nombre:32s} obs {o:6.0f} esp {e:8.1f} O/E {o/e if e else float('nan'):.3f} z {z:+.2f}")
pr("== Descriptivo O/E frente a P_V1 (ya calibrado para transiciones; interesa si difiere por régimen) ==")
reg = {"k1_3": (kpos >= 1) & (kpos <= 3), "k4_7": MED > 0, "k8_11": TAR > 0,
       "entre_semana": FDS == 0, "fin_semana": FDS > 0, "dia11": D12 == 0, "dia12": D12 > 0}
for nm, f in reg.items(): oe(trans_any, f, f"trans_any|{nm}")
for nm, f in reg.items(): oe(rep_any, f, f"ya_salio_hoy|{nm}")

# ---------------- modelos ----------------
res = {"descriptivo": desc}
Ps, Pfs = {}, {}
def fitpred(Xc):
    return (lambda tr: E2.ajustar_lineal(Xc[tr], LPE[tr], y[tr], LAM)), (lambda w, te: E2.predecir_lineal(w, Xc[te], LPE[te]))
fmt = lambda t: f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}]"
for nombre, (Xc, nms) in VAR.items():
    f, p = fitpred(Xc)
    P, pars = E2.cross_fit(f, p, blo); Ps[nombre] = P
    Pf = E2.forward(f, p, blo); Pf[blo == 0] = Pens[blo == 0]; Pfs[nombre] = Pf
    r = A.evaluar(P, P_ref=P_V1, y=y)
    Wb = np.array(pars)
    pesos = {nm: [float(v) for v in Wb[:, i]] for i, nm in enumerate(nms) if i >= 27}
    res[nombre] = dict(crossfit_vs_V1=r, pesos_por_pliegue=pesos)
    pr(f"\n== {nombre} ({Xc.shape[2]} var) cross-fit, frente a P_V1 ==")
    pr(f"Δ mbits {fmt(r['delta_mbits'])} · mitad1 {fmt(r['delta_mitad1'])} · mitad2 {fmt(r['delta_mitad2'])} · PASA {r['pasa_barra_dev']}")
    pr(f"Top-3 {r['top3_cand']*100:.2f}% vs {r['top3_ens']*100:.2f}% · Top-5 {r['top5_cand']*100:.2f}% vs {r['top5_ens']*100:.2f}% · "
       f"Top-15 {r['top15_cand']*100:.2f}% vs {r['top15_ens']*100:.2f}% · ret T5 {r['ret_t5_cand']*100:+.2f}% vs {r['ret_t5_ens']*100:+.2f}%")
    for nm, v in pesos.items():
        sg = "mismo signo" if (min(v) > 0 or max(v) < 0) else "cambia"
        pr(f"   {nm:22s} {np.mean(v):+.3f} [{min(v):+.3f}, {max(v):+.3f}] {sg}")
    if nombre == "V1_refit_control":
        dmax = float(np.abs(P - P_V1).max()); res[nombre]["max_dif_P_V1"] = dmax; pr(f"   control: max |P - P_V1| = {dmax:.2e}")

f1 = blo >= 1
for nombre in VAR:
    if nombre == "V1_refit_control": continue
    dcf = A.mbits_fila(Ps[nombre], y) - A.mbits_fila(Ps["VR_ablacion_33_REPD"], y)
    dfw = A.mbits_fila(Pfs[nombre][f1], y[f1]) - A.mbits_fila(Pfs["V1_refit_control"][f1], y[f1])
    dfw1 = A.mbits_fila(Pfs[nombre][f1], y[f1]) - A.mbits_fila(P_V1[f1], y[f1])
    res[nombre]["vs_VR_crossfit"] = A.ic_bloques(dcf, dia)
    res[nombre]["forward_vs_V1forward_b1_4"] = A.ic_bloques(dfw, dia[f1])
    res[nombre]["forward_vs_P_V1_b1_4"] = A.ic_bloques(dfw1, dia[f1])
    pr(f"{nombre:22s} Δ vs VR (cross-fit) {fmt(res[nombre]['vs_VR_crossfit'])} · forward vs V1-forward (b1-4) "
       f"{fmt(res[nombre]['forward_vs_V1forward_b1_4'])} · forward vs P_V1 (b1-4) {fmt(res[nombre]['forward_vs_P_V1_b1_4'])}")
np.save(os.path.join(AQUI, "P_VA.npy"), Ps["VA_tramo_dia"])
json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1)
pr(f"[{time.time()-t0:.0f} s]")
open(os.path.join(AQUI, "salida_experimento.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
