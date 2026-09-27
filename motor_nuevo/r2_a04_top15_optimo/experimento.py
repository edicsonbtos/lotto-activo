# -*- coding: utf-8 -*-
"""r2_a04_top15_optimo: ¿se puede armar un Top-15 mejor que los 15 de mayor P de ag12 V1?

Uso (desde cualquier carpeta):
    set PYTHONIOENCODING=utf-8 && python motor_nuevo/r2_a04_top15_optimo/experimento.py
Solo filas [2000, 9357). Prerregistro: PREREGISTRO.md. Salida: resultados.json + consola.
"""
import json, os, sys, time
import numpy as np
from scipy.optimize import minimize

AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI)
sys.path.insert(0, MN); sys.path.insert(0, os.path.join(MN, "ag12_transiciones"))
import arnes as A  # noqa
import importlib.util as _iu
_sp = _iu.spec_from_file_location("exp_ag02", os.path.join(MN, "ag02_residuo_boost", "experimento.py"))
E2 = _iu.module_from_spec(_sp); _sp.loader.exec_module(E2)
import rasgos12 as R  # noqa

LAM, K, SEMILLA_RANK = 30.0, 38, 12345
PSEUDO = 20.0
t0 = time.time()
D = A.datos().prefijo(A.CORTE)
Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True)
LPE = np.log(np.clip(Pens, 1e-12, None))
P_ref = np.load(os.path.join(MN, "ag12_transiciones", "P_V1.npy"))
P_ref = P_ref / P_ref.sum(1, keepdims=True)
X, _ = R.construir(D, A.W); X = X.astype(np.float64)
dia = np.asarray(D.dia[A.W:A.CORTE]); blo = E2.bloques_jornada(dia)
n = len(y); h = n // 2; NB = blo.max() + 1
res = {}


def fmt(t):
    return f"{t[0]:+.4f} [{t[1]:+.4f} ; {t[2]:+.4f}]"


def top15(P):
    return (A.puestos(P, y) <= 15).astype(float)


def comparar_top15(Pc, Pr, mask=None):
    m = np.ones(n, bool) if mask is None else mask
    d = top15(Pc)[m] - top15(Pr)[m]
    dd = dia[m]; hh = len(d) // 2
    return {"top15_cand": float(top15(Pc)[m].mean()), "top15_ref": float(top15(Pr)[m].mean()),
            "delta": A.ic_bloques(d, dd), "mitad1": A.ic_bloques(d[:hh], dd[:hh]),
            "mitad2": A.ic_bloques(d[hh:], dd[hh:]),
            "cambios_por_sorteo": float(np.mean(np.sum(rank_set(Pc)[m] != rank_set(Pr)[m], 1) / 2))}


def rank_set(P):
    o = A.LE.rankings(A._norm(P), SEMILLA_RANK)[:, :15]
    S = np.zeros(P.shape, bool); S[np.arange(len(P))[:, None], o] = True
    return S


def mbits_vs(Pc, Pr, mask=None):
    m = np.ones(n, bool) if mask is None else mask
    d = A.mbits_fila(Pc, y)[m] - A.mbits_fila(Pr, y)[m]
    return A.ic_bloques(d, dia[m])


# ------------------------------------------------------------------ diagnósticos
print("== Diagnósticos de ag12 V1 (P_V1) ==")
orden = A.LE.rankings(P_ref, SEMILLA_RANK)
Psorted = np.take_along_axis(P_ref, orden, 1)
pos = A.puestos(P_ref, y)
esp15 = Psorted[:, :15].sum(1); obs15 = (pos <= 15).astype(float)
res["D1"] = {"top15_esperado": A.ic_bloques(esp15, dia), "top15_observado": A.ic_bloques(obs15, dia),
             "obs_menos_esp": A.ic_bloques(obs15 - esp15, dia)}
print("D1 Top-15 esperado", fmt(res["D1"]["top15_esperado"]), "observado", fmt(res["D1"]["top15_observado"]),
      "obs-esp", fmt(res["D1"]["obs_menos_esp"]))
O = np.bincount(pos - 1, minlength=K).astype(float); E = Psorted.sum(0)
res["D2_por_puesto"] = [{"puesto": r + 1, "obs": int(O[r]), "esp": float(E[r]), "O_E": float(O[r] / E[r]),
                         "z": float((O[r] - E[r]) / np.sqrt(E[r] * (1 - E[r] / n)))} for r in range(K)]
print("D2 puesto: obs / esp (O/E, z)")
for r in range(K):
    q = res["D2_por_puesto"][r]
    print(f"  {q['puesto']:2d}: {q['obs']:4d} / {q['esp']:7.1f}  ({q['O_E']:.3f}, z {q['z']:+.2f})")
chi2 = float(sum(q["z"] ** 2 for q in res["D2_por_puesto"]))
res["D2_chi2_38gl"] = chi2
fr = slice(10, 20)
res["D2_frontera_11_20"] = {"obs": int(O[fr].sum()), "esp": float(E[fr].sum())}
print(f"D2 chi2 (38 gl, aprox) = {chi2:.1f}; frontera 11-20 obs {O[fr].sum():.0f} esp {E[fr].sum():.1f}")
pp = P_ref.ravel(); yy = np.zeros_like(P_ref); yy[np.arange(n), y] = 1; yy = yy.ravel()
qs = np.quantile(pp, np.linspace(0, 1, 11)); qb = np.clip(np.searchsorted(qs, pp, side="right") - 1, 0, 9)
res["D3_deciles"] = [{"decil": d + 1, "p_media": float(pp[qb == d].mean()), "frec": float(yy[qb == d].mean()),
                      "n": int((qb == d).sum())} for d in range(10)]
print("D3 deciles de p: p media -> frecuencia")
for q in res["D3_deciles"]:
    print(f"  {q['decil']:2d}: {q['p_media']*100:.3f}% -> {q['frec']*100:.3f}%  (n {q['n']})")
res["D4_identidad"] = {}
for T in (0.7, 1.5):
    PT = P_ref ** (1 / T); PT /= PT.sum(1, keepdims=True)
    c = comparar_top15(PT, P_ref)
    res["D4_identidad"][f"T={T}"] = {"delta_top15": c["delta"][0], "cambios": c["cambios_por_sorteo"],
                                      "delta_mbits": mbits_vs(PT, P_ref)[0]}
    print(f"D4 temperatura {T}: ΔTop-15 {c['delta'][0]:+.6f} (cambios/sorteo {c['cambios_por_sorteo']:.3f}),"
          f" Δmbits {res['D4_identidad'][f'T={T}']['delta_mbits']:+.2f}")


# ------------------------------------------------------------------ cross-fit anidado de ag12
def fit12(tr):
    return E2.ajustar_lineal(X[tr], LPE[tr], y[tr], LAM)


def pred12(w, te):
    return E2.predecir_lineal(w, X[te], LPE[te])


print("\nReajuste ag12 (control) y cross-fit anidado ...", flush=True)
Pctrl = np.zeros_like(P_ref)
for k in range(NB):
    Pctrl[blo == k] = pred12(fit12(blo != k), blo == k)
res["control_max_dif_P_V1"] = float(np.abs(Pctrl - P_ref).max())
print("control: max |P_reajuste - P_V1| =", res["control_max_dif_P_V1"])
INNER = {}   # INNER[k] = matriz con predicciones de ag12 para filas fuera de k, sin k ni su propio bloque
for k in range(NB):
    Pi = np.full_like(P_ref, np.nan)
    for j in range(NB):
        if j == k:
            continue
        Pi[blo == j] = pred12(fit12((blo != k) & (blo != j)), blo == j)
    INNER[k] = Pi
print(f"  [{time.time()-t0:.0f} s]", flush=True)


# ------------------------------------------------------------------ correcciones
def c_puesto(Pb, idx):
    o = A.LE.rankings(Pb[idx], SEMILLA_RANK)
    ps = np.take_along_axis(Pb[idx], o, 1)
    pz = np.argmax(o == y[idx][:, None], 1)
    Oo = np.bincount(pz, minlength=K).astype(float); Ee = ps.sum(0)
    return (Oo + PSEUDO) / (Ee + PSEUDO)


def ap_puesto(c, Pb):
    o = A.LE.rankings(Pb, SEMILLA_RANK)
    rk = np.empty_like(o); rk[np.arange(len(Pb))[:, None], o] = np.arange(K)[None, :]
    Q = Pb * c[rk]
    return Q / Q.sum(1, keepdims=True)


def f_mezcla(Pb, idx):
    L1 = np.log(np.clip(Pb[idx], 1e-12, None)); L2 = LPE[idx]
    Xm = np.stack([L1, L2], 2)
    r = minimize(E2._perdida, np.zeros(2), args=(Xm, L1, y[idx], 0.0), jac=True, method="L-BFGS-B")
    return r.x    # log P = (1+a)·L1 + b·L2


def ap_mezcla(w, Pb, idx):
    L1 = np.log(np.clip(Pb, 1e-12, None)); L2 = LPE[idx]
    z = (1 + w[0]) * L1 + w[1] * L2; z -= z.max(1, keepdims=True)
    Q = np.exp(z); return Q / Q.sum(1, keepdims=True)


EYE = np.eye(K)


def f_animal(Pb, idx):
    L1 = np.log(np.clip(Pb[idx], 1e-12, None)); m = len(L1)
    Xa = np.broadcast_to(EYE, (m, K, K))
    r = minimize(E2._perdida, np.zeros(K), args=(Xa, L1, y[idx], LAM), jac=True, method="L-BFGS-B",
                 options={"maxiter": 500})
    return r.x


def ap_animal(b, Pb):
    Q = Pb * np.exp(b)[None, :]
    return Q / Q.sum(1, keepdims=True)


VARS = {
    "V1_puesto": (lambda Pb, idx: c_puesto(Pb, idx), lambda m, Pb, idx: ap_puesto(m, Pb)),
    "V2_mezcla_ensamble": (f_mezcla, ap_mezcla),
    "V3_sesgo_animal": (f_animal, lambda m, Pb, idx: ap_animal(m, Pb)),
}

# forward base: ag12 V1 forward (bloque 0 = ensamble)
Pf = np.zeros_like(P_ref); Pf[blo == 0] = Pens[blo == 0]
for k in range(1, NB):
    Pf[blo == k] = pred12(fit12(blo < k), blo == k)

res["variantes"] = {}
for nom, (fit, ap) in VARS.items():
    Pc = np.zeros_like(P_ref); pars = []
    for k in range(NB):
        tr = np.where(blo != k)[0]; te = np.where(blo == k)[0]
        m = fit(INNER[k], tr); pars.append(np.asarray(m).tolist())
        Pc[te] = ap(m, P_ref[te], te)
    Pfw = Pf.copy()
    for k in range(2, NB):
        tr = np.where((blo >= 1) & (blo < k))[0]; te = np.where(blo == k)[0]
        m = fit(Pf, tr)
        Pfw[te] = ap(m, Pf[te], te)
    ev = A.evaluar(Pc, P_ref=P_ref, y=y)
    t15 = comparar_top15(Pc, P_ref)
    mf = blo >= 2
    fw = {"delta_mbits": mbits_vs(Pfw, Pf, mf), "top15": comparar_top15(Pfw, Pf, mf)}
    res["variantes"][nom] = {"evaluar": ev, "top15": t15, "forward_bloques_2a4": fw, "parametros": pars}
    np.save(os.path.join(AQUI, f"P_{nom}.npy"), Pc)
    print(f"\n== {nom} ==")
    print(f"  Δ mbits {fmt(ev['delta_mbits'])} · mitad1 {fmt(ev['delta_mitad1'])} · mitad2 {fmt(ev['delta_mitad2'])}")
    print(f"  Top-15 {t15['top15_cand']*100:.2f}% vs ag12 {t15['top15_ref']*100:.2f}% · Δ {fmt(t15['delta'])}"
          f" · m1 {fmt(t15['mitad1'])} · m2 {fmt(t15['mitad2'])} · animales cambiados/sorteo {t15['cambios_por_sorteo']:.3f}")
    print(f"  Top-5 {ev['top5_cand']*100:.2f}% vs {ev['top5_ens']*100:.2f}% · Top-5 escalonado Δ {fmt(ev['delta_ret_t5'])}")
    print(f"  forward (bloques 2-4, n={int(mf.sum())}): Δ mbits {fmt(fw['delta_mbits'])} · ΔTop-15 {fmt(fw['top15']['delta'])}")
    print(f"  PASA BARRA DEV (mbits): {ev['pasa_barra_dev']}", flush=True)

json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"\n[{time.time()-t0:.0f} s]")
