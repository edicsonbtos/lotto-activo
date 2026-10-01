# -*- coding: utf-8 -*-
"""10 planes para subir el Top-15 de Lotto Activo (PREREGISTRO.md, misma carpeta).

Uso:  python herramientas/exploracion/top15_70/top15_70.py
Escribe resultados.json y salida.txt en esta carpeta. Solo lee datos congelados del desarrollo
(verificacion/hilo9/datos) y datos_multiloteria/. No toca producción ni el tramo de prueba (>= 9357).

Tramos: dev-A = filas [2000, 5688) para ajustar y elegir; dev-B = filas [5688, 9357) para medir una vez.
"""
import csv, io, json, math, os, sys, time
from datetime import date
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
sys.path.insert(0, os.path.join(RAIZ, "herramientas", "modelos", "ag12"))
import lotto_eval as LE  # noqa: E402

K = 38
W, MITAD, CORTE = 2000, 5688, 9357
SEMILLA = 20261001
B_BOOT = 4000
FECHA_RD_FIN = "2025-12-15"        # desde aquí las fechas de LA están corridas: sin RD
F15P = np.array([3, 3, 3, 2, 2] + [1] * 10, float)   # ponderado 23 fichas
SAL = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); SAL.append(s)


# --------------------------------------------------------------------------- datos
D = LE.cargar(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "historial.txt"))
_c = np.load(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "calor_cache.npz"))
PE = LE.normalizar(_c["P"]); Y = _c["y"].astype(int)
assert (D.seq[W:CORTE] == Y).all()
N = len(Y)
FILA = np.arange(W, CORTE)
HORA = D.hora[W:CORTE]; DIA = D.dia[W:CORTE]; FECHA = D.fecha[W:CORTE]
IA = FILA < MITAD; IB = ~IA

ANIMALES = {
    "DELFIN": "0", "BALLENA": "00", "CARNERO": "1", "TORO": "2", "CIEMPIES": "3", "ALACRAN": "4", "LEON": "5",
    "RANA": "6", "PERICO": "7", "RATON": "8", "AGUILA": "9", "TIGRE": "10", "GATO": "11", "CABALLO": "12",
    "MONO": "13", "PALOMA": "14", "ZORRO": "15", "OSO": "16", "PAVO": "17", "BURRO": "18", "CHIVO": "19",
    "COCHINO": "20", "GALLO": "21", "CAMELLO": "22", "CEBRA": "23", "IGUANA": "24", "GALLINA": "25", "VACA": "26",
    "PERRO": "27", "ZAMURO": "28", "ELEFANTE": "29", "CAIMAN": "30", "LAPA": "31", "ARDILLA": "32",
    "PESCADO": "33", "VENADO": "34", "JIRAFA": "35", "CULEBRA": "36"}


def sin_acentos(t):
    import re, unicodedata
    return re.sub(r"[^A-Z]", "", unicodedata.normalize("NFD", (t or "").upper()))


RD = {}   # (fecha, h) -> idx
with io.open(os.path.join(RAIZ, "datos_multiloteria", "rdint_hist.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        cod = ANIMALES.get(sin_acentos(r["animal"]))
        if cod is None or r["fecha"] >= FECHA_RD_FIN:
            continue
        RD[(r["fecha"], int(r["hora"][:2]) - 8)] = LE.IDX[cod]


def rd_hoy(i):
    """{j: animal} de RD de hoy a las (h-j):30, j >= 1, para la fila i de dev."""
    f, h = FECHA[i], int(HORA[i])
    return {j: RD[(f, h - j)] for j in range(1, h + 1) if (f, h - j) in RD}


RDP = np.array([rd_hoy(i).get(1, -1) for i in range(N)])   # RD (h-1):30


# --------------------------------------------------------------------------- utilidades
def orden_de(S):
    return LE.rankings(S)     # desempate aleatorio fijo


def quitar(orden, excl):
    """Saca los animales de excl (lista de conjuntos por fila) y deja que suban los de abajo."""
    out = orden.copy()
    for i, ex in enumerate(excl):
        if ex:
            o = orden[i]
            m = np.isin(o, list(ex))
            out[i] = np.concatenate([o[~m], o[m]])
    return out


def regla_rd(orden):
    return quitar(orden, [{a} if a >= 0 else set() for a in RDP])


def pos_de(orden, y):
    return np.argmax(orden == y[:, None], axis=1)


def medidas(orden, sel, P=None):
    y = Y[sel]; pos = pos_de(orden[sel], y)
    t15 = (pos < 15).astype(float)
    r15 = (30 * t15 - 15) / 15
    w = np.zeros(K); w[:15] = F15P
    r15p = (30 * w[pos] - w.sum()) / w.sum()
    out = dict(t15=t15, r15=r15, r15p=r15p, pos=pos)
    if P is not None:
        Pn = LE.normalizar(P[sel]); out["mb"] = np.log2(Pn[np.arange(len(y)), y] * K) * 1000
    return out


def boot(v, dias, B=B_BOOT, semilla=SEMILLA):
    u, g = np.unique(dias, return_inverse=True)
    s = np.bincount(g, v); c = np.bincount(g)
    rng = np.random.default_rng(semilla); idx = rng.integers(0, len(u), (B, len(u)))
    bs = s[idx].sum(1) / c[idx].sum(1)
    return dict(media=float(v.mean()), ic95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                ic99_5=[float(np.percentile(bs, 0.25)), float(np.percentile(bs, 99.75))],
                p_unilateral=float(np.mean(bs <= 0)))


def resumen(nombre, orden, comp, sel=IB, P=None, Pcomp=None):
    a = medidas(orden, sel, P); b = medidas(comp, sel, Pcomp)
    d = DIA[sel]
    r = dict(plan=nombre, n=int(sel.sum()),
             top15=boot(a["t15"], d), top15_comp=float(b["t15"].mean()),
             dif_top15=boot(a["t15"] - b["t15"], d),
             ret_plano=boot(a["r15"], d), ret_ponderado=boot(a["r15p"], d),
             ret_plano_comp=float(b["r15"].mean()), ret_ponderado_comp=float(b["r15p"].mean()))
    if P is not None:
        r["mbits"] = float(a["mb"].mean())
        r["dif_mbits_vs_B0"] = boot(a["mb"] - medidas(ORD_B0, sel, PE)["mb"], d)
    mej = r["dif_top15"]["media"] > 0 and r["dif_top15"]["p_unilateral"] < 0.005
    if P is not None:
        mej = mej and r["dif_mbits_vs_B0"]["media"] > 0
    obj = r["top15"]["media"] >= 0.70 and r["top15"]["ic95"][0] >= 0.65
    r["veredicto"] = "OBJETIVO 70 %" if obj else ("MEJORA" if mej else "NO PASA")
    log(f"  {nombre}: Top-15 {100*r['top15']['media']:.2f} % [IC95 {100*r['top15']['ic95'][0]:.1f}; "
        f"{100*r['top15']['ic95'][1]:.1f}]  comparador {100*r['top15_comp']:.2f} %  "
        f"dif {100*r['dif_top15']['media']:+.2f} pp [{100*r['dif_top15']['ic95'][0]:+.2f}; "
        f"{100*r['dif_top15']['ic95'][1]:+.2f}] p={r['dif_top15']['p_unilateral']:.4f}")
    log(f"     retorno/ficha plano {100*r['ret_plano']['media']:+.1f} % (comp {100*r['ret_plano_comp']:+.1f} %), "
        f"ponderado {100*r['ret_ponderado']['media']:+.1f} % (comp {100*r['ret_ponderado_comp']:+.1f} %)"
        + (f"  mbits {r['mbits']:.1f} (dif vs B0 {r['dif_mbits_vs_B0']['media']:+.1f} "
           f"[{r['dif_mbits_vs_B0']['ic95'][0]:+.1f}; {r['dif_mbits_vs_B0']['ic95'][1]:+.1f}])" if P is not None else "")
        + f"  => {r['veredicto']}")
    return r


# --------------------------------------------------------------------------- comparadores
ORD_B0 = orden_de(PE)
ORD_B1 = regla_rd(ORD_B0)
RES = {"tramos": {"devA": [D.fecha[W], D.fecha[MITAD - 1], int(IA.sum())],
                  "devB": [D.fecha[MITAD], D.fecha[CORTE - 1], int(IB.sum())]}}
log("dev-A", RES["tramos"]["devA"], " dev-B", RES["tramos"]["devB"])
log("Comparadores en dev-B:")
mb0 = medidas(ORD_B0, IB, PE); mb1 = medidas(ORD_B1, IB)
RES["B0"] = dict(top15=boot(mb0["t15"], DIA[IB]), mbits=float(mb0["mb"].mean()),
                 ret_plano=float(mb0["r15"].mean()), ret_ponderado=float(mb0["r15p"].mean()))
RES["B1"] = dict(top15=boot(mb1["t15"], DIA[IB]), ret_plano=float(mb1["r15"].mean()),
                 ret_ponderado=float(mb1["r15p"].mean()))
log(f"  B0 ensamble: Top-15 {100*RES['B0']['top15']['media']:.2f} %  mbits {RES['B0']['mbits']:.1f}  "
    f"plano {100*RES['B0']['ret_plano']:+.1f} %  ponderado {100*RES['B0']['ret_ponderado']:+.1f} %")
log(f"  B1 ensamble + regla RD: Top-15 {100*RES['B1']['top15']['media']:.2f} %  "
    f"plano {100*RES['B1']['ret_plano']:+.1f} %  ponderado {100*RES['B1']['ret_ponderado']:+.1f} %")

# --------------------------------------------------------------------------- historia por fila
seq = D.seq; dia_all = D.dia; hora_all = D.hora


def hoy_la(t):
    s = []; j = t - 1
    while j >= 0 and dia_all[j] == dia_all[t]:
        s.append(int(seq[j])); j -= 1
    return s


HOY = [hoy_la(t) for t in FILA]

# --------------------------------------------------------------------------- PLAN 1
log("\nPLAN 1  exclusión dura de lo que ya salió hoy en LA (+ regla RD)")
ORD_P1 = regla_rd(quitar(ORD_B0, [set(h) for h in HOY]))
RES["P1"] = resumen("P1", ORD_P1, ORD_B1)

# --------------------------------------------------------------------------- PLAN 2
log("\nPLAN 2  exclusión cruzada RD completa (desfases elegidos en dev-A)")
RDH = [rd_hoy(i) for i in range(N)]
oe = {}
for j in range(1, 12):
    o = e = 0
    for i in np.where(IA)[0]:
        if j in RDH[i]:
            o += Y[i] == RDH[i][j]; e += 1 / K
    oe[j] = (int(o), round(e, 1), float(o / e) if e else None)
DESF = sorted({1} | {j for j, (o, e, r) in oe.items() if r is not None and r < 0.80})
log("  O/E dev-A por desfase j (LA h:00 = RD (h-j):30):",
    {j: (v[0], v[1], round(v[2], 3) if v[2] else None) for j, v in oe.items()})
log("  desfases excluidos:", DESF)
ORD_P2 = quitar(ORD_B0, [{RDH[i][j] for j in DESF if j in RDH[i]} for i in range(N)])
RES["P2"] = resumen("P2", ORD_P2, ORD_B1); RES["P2"]["oe_devA"] = oe; RES["P2"]["desfases"] = DESF


# --------------------------------------------------------------------------- logit condicional (P3, P6)
def ajustar_logit(X, off, y, lam, idx):
    """max sum log softmax(off + X·w)[y] - lam·|w|^2 sobre las filas idx. X (n,38,F)."""
    from scipy.optimize import minimize
    Xi = X[idx].astype(np.float64); oi = off[idx]; yi = y[idx]; n = len(yi)

    def f(w):
        z = oi + Xi @ w; z = z - z.max(1, keepdims=True)
        lse = np.log(np.exp(z).sum(1)); p = np.exp(z - lse[:, None])
        ll = z[np.arange(n), yi] - lse
        g = Xi[np.arange(n), yi].sum(0) - np.einsum("nk,nkf->f", p, Xi)
        return -(ll.sum() - lam * w @ w), -(g - 2 * lam * w)
    r = minimize(f, np.zeros(X.shape[2]), jac=True, method="L-BFGS-B")
    return r.x


def aplicar_logit(X, off, w):
    z = off + X @ w; z -= z.max(1, keepdims=True); p = np.exp(z)
    return p / p.sum(1, keepdims=True)


LOGPE = np.log(PE)

# --------------------------------------------------------------------------- PLAN 3
log("\nPLAN 3  corriente combinada LA+RD con rechazo (m_k, k=1..24, + hoy LA / hoy RD)")
# chorro: (fecha, minuto, animal); LA h:00 -> 60h, RD h:30 -> 60h+30
ev = [(D.fecha[t], 60 * int(hora_all[t]), int(seq[t])) for t in range(len(seq))]
ev += [(f, 60 * h + 30, a) for (f, h), a in RD.items()]
ev.sort()
pos_ev = {(f, m): i for i, (f, m, a) in enumerate(ev)}
X3 = np.zeros((N, K, 26), np.float32)
for i in range(N):
    t = FILA[i]; f = D.fecha[t]; m = 60 * int(hora_all[t]); e = pos_ev[(f, m)]
    for k in range(1, 25):
        if e - k >= 0:
            X3[i, ev[e - k][2], k - 1] = 1
    for a in HOY[i]:
        X3[i, a, 24] = 1
    for a in RDH[i].values():
        X3[i, a, 25] = 1
w3 = ajustar_logit(X3, LOGPE, Y, 10.0, np.where(IA)[0])
log("  multiplicadores exp(w) k=1..24:", [round(float(np.exp(v)), 2) for v in w3[:24]],
    " hoyLA", round(float(np.exp(w3[24])), 2), " hoyRD", round(float(np.exp(w3[25])), 2))
P3 = aplicar_logit(X3, LOGPE, w3)
ORD_P3 = orden_de(P3)
RES["P3"] = resumen("P3", ORD_P3, ORD_B1, P=P3); RES["P3"]["mult"] = [float(np.exp(v)) for v in w3]

# --------------------------------------------------------------------------- variables para árboles
log("\nVariables para P4-P6 ...")
import rasgos12 as R12  # noqa: E402
X12 = R12.construir(D, W)[0][:N]                                  # (N,38,33)
FEAT = []; nombres = []


def add(nombre, M):
    FEAT.append(np.asarray(M, np.float32)); nombres.append(nombre)


ult = np.full(K, -10**6); penult = np.full(K, -10**6); ultdia = np.full(K, -10**6)
G1 = np.zeros((N, K)); G2 = np.zeros((N, K)); GD = np.zeros((N, K))
for t in range(len(seq)):
    if t >= W and t < CORTE:
        i = t - W
        G1[i] = np.minimum(t - ult, 500); G2[i] = np.minimum(t - penult, 1000)
        GD[i] = np.minimum(dia_all[t] - ultdia, 60)
    a = seq[t]; penult[a] = ult[a]; ult[a] = t; ultdia[a] = dia_all[t]
cum = np.zeros((len(seq) + 1, K)); cum[1:] = np.cumsum(np.eye(K)[seq], 0)
CNT = {v: np.array([cum[t] - cum[max(0, t - v)] for t in FILA]) for v in (12, 36, 120, 456)}
LAG = np.zeros((N, K, 12), np.float32)
for i, t in enumerate(FILA):
    for k in range(1, 13):
        LAG[i, seq[t - k], k - 1] = 1
RDL = np.zeros((N, K, 11), np.float32); NRD = np.zeros((N, K)); NRDY = np.zeros((N, K)); NLAY = np.zeros((N, K))
RDG = np.zeros((N, K))
rd_por_dia = {}
for (f, h), a in RD.items():
    rd_por_dia.setdefault(f, []).append(a)
la_por_dia = {}
for t in range(len(seq)):
    la_por_dia.setdefault(D.fecha[t], []).append(int(seq[t]))
from datetime import timedelta  # noqa: E402
# hueco RD en sorteos de RD: índice de evento RD
rd_ev = sorted(RD.items())
rd_pos = {k: i for i, (k, a) in enumerate(rd_ev)}
ultrd = np.full(K, -10**6); j_rd = 0
for i in range(N):
    f, h = FECHA[i], int(HORA[i])
    for j, a in RDH[i].items():
        RDL[i, a, j - 1] = 1; NRD[i, a] += 1
    ay = (date.fromisoformat(f) - timedelta(days=1)).isoformat()
    for a in rd_por_dia.get(ay, []):
        NRDY[i, a] += 1
    for a in la_por_dia.get(ay, []):
        NLAY[i, a] += 1
    # RD anteriores a (f, h-1:30) inclusive
    while j_rd < len(rd_ev) and (rd_ev[j_rd][0][0] < f or (rd_ev[j_rd][0][0] == f and rd_ev[j_rd][0][1] <= h - 1)):
        ultrd[rd_ev[j_rd][1]] = j_rd; j_rd += 1
    RDG[i] = np.minimum(j_rd - ultrd, 500)
NHOY = np.zeros((N, K))
for i in range(N):
    for a in HOY[i]:
        NHOY[i, a] += 1
rank_e = np.argsort(ORD_B0, axis=1)
add("ens_logp", LOGPE); add("ens_rank", rank_e); add("gap1", G1); add("gap2", G2); add("gapdias", GD)
add("veces_hoy", NHOY)
for v in (12, 36, 120, 456):
    add(f"cnt{v}", CNT[v])
for k in range(12):
    add(f"lag{k+1}", LAG[:, :, k])
for j in range(11):
    add(f"rd_h-{j+1}", RDL[:, :, j])
add("rd_veces_hoy", NRD); add("rd_veces_ayer", NRDY); add("la_veces_ayer", NLAY); add("rd_hueco", RDG)
add("hora", np.repeat(HORA[:, None], K, 1)); add("k_hoy", np.repeat(np.array([len(h) for h in HOY])[:, None], K, 1))
add("hay_rd", np.repeat((RDP >= 0)[:, None], K, 1))
for f_ in range(X12.shape[2]):
    add("ag12_" + R12.NOMBRES[f_], X12[:, :, f_])
XF = np.stack(FEAT, axis=2)            # (N,38,F)
log(f"  {XF.shape[2]} variables")

import lightgbm as lgb  # noqa: E402
ia = np.where(IA)[0]
corte_val = ia[int(0.8 * len(ia))]
while DIA[corte_val] == DIA[corte_val - 1]:
    corte_val += 1
itr = ia[ia < corte_val]; iva = ia[ia >= corte_val]
LOGIT_E = np.log(PE) - np.log1p(-PE)


def plano(idx):
    return XF[idx].reshape(-1, XF.shape[2]), (np.arange(K)[None, :] == Y[idx][:, None]).reshape(-1).astype(int)


# --------------------------------------------------------------------------- PLAN 4
log("\nPLAN 4  LightGBM binario sobre el ensamble (init_score)")
Xtr, ytr = plano(itr); Xva, yva = plano(iva)
prm = dict(objective="binary", learning_rate=0.03, num_leaves=31, min_data_in_leaf=200, feature_fraction=0.8,
           bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0, seed=SEMILLA, verbose=-1, num_threads=4,
           deterministic=True, force_col_wise=True)
dtr = lgb.Dataset(Xtr, ytr, init_score=LOGIT_E[itr].reshape(-1), feature_name=nombres)
dva = lgb.Dataset(Xva, yva, init_score=LOGIT_E[iva].reshape(-1), reference=dtr)
m4 = lgb.train(prm, dtr, 3000, valid_sets=[dva], callbacks=[lgb.early_stopping(100, verbose=False)])
log(f"  rondas elegidas: {m4.best_iteration}")
raw4 = m4.predict(XF.reshape(-1, XF.shape[2]), raw_score=True, num_iteration=m4.best_iteration).reshape(N, K) + LOGIT_E
P4 = 1 / (1 + np.exp(-raw4)); P4 /= P4.sum(1, keepdims=True)
ORD_P4 = orden_de(P4)
imp = sorted(zip(m4.feature_importance("gain"), nombres), reverse=True)[:12]
log("  importancia (ganancia):", [(n_, round(float(g), 1)) for g, n_ in imp])
RES["P4"] = resumen("P4", ORD_P4, ORD_B1, P=P4); RES["P4"]["rondas"] = int(m4.best_iteration)
RES["P4"]["importancia"] = [(n_, float(g)) for g, n_ in imp]

# --------------------------------------------------------------------------- PLAN 5
log("\nPLAN 5  LightGBM LambdaRank truncado en 15 sobre el ensamble")
prm5 = dict(objective="lambdarank", learning_rate=0.03, num_leaves=31, min_data_in_leaf=200, feature_fraction=0.8,
            bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0, seed=SEMILLA, verbose=-1, num_threads=4,
            deterministic=True, force_col_wise=True, lambdarank_truncation_level=15, eval_at=[15],
            metric="ndcg")
d5 = lgb.Dataset(Xtr, ytr, group=[K] * len(itr), init_score=LOGPE[itr].reshape(-1), feature_name=nombres)
d5v = lgb.Dataset(Xva, yva, group=[K] * len(iva), init_score=LOGPE[iva].reshape(-1), reference=d5)
m5 = lgb.train(prm5, d5, 3000, valid_sets=[d5v], callbacks=[lgb.early_stopping(100, verbose=False)])
log(f"  rondas elegidas: {m5.best_iteration}")
s5 = m5.predict(XF.reshape(-1, XF.shape[2]), raw_score=True, num_iteration=m5.best_iteration).reshape(N, K) + LOGPE
from scipy.optimize import minimize_scalar  # noqa: E402


def nll_T(T, idx):
    z = s5[idx] / T; z = z - z.max(1, keepdims=True)
    return -(z[np.arange(len(idx)), Y[idx]] - np.log(np.exp(z).sum(1))).mean()


T5 = minimize_scalar(lambda T: nll_T(T, iva), bounds=(0.05, 20), method="bounded").x
z5 = s5 / T5; z5 -= z5.max(1, keepdims=True); P5 = np.exp(z5); P5 /= P5.sum(1, keepdims=True)
log(f"  temperatura {T5:.3f}")
ORD_P5 = orden_de(s5)
RES["P5"] = resumen("P5", ORD_P5, ORD_B1, P=P5); RES["P5"]["rondas"] = int(m5.best_iteration); RES["P5"]["T"] = T5

# --------------------------------------------------------------------------- PLAN 6
log("\nPLAN 6  ag12 re-ajustado solo en dev-A (+ RD h-1, h-2), lambda 30")
X6 = np.concatenate([X12, RDL[:, :, :2]], axis=2)
w6 = ajustar_logit(X6, LOGPE, Y, 30.0, ia)
P6 = aplicar_logit(X6, LOGPE, w6)
ORD_P6 = orden_de(P6)
log("  pesos RD h-1, h-2 -> multiplicador", round(float(np.exp(w6[-2])), 3), round(float(np.exp(w6[-1])), 3))
RES["P6"] = resumen("P6", ORD_P6, ORD_B1, P=P6); RES["P6"]["w"] = [float(v) for v in w6]

# --------------------------------------------------------------------------- PLAN 7
log("\nPLAN 7  jugar solo las horas buenas (elegidas en dev-A)")
ma = medidas(ORD_B1, IA); mbB = medidas(ORD_B1, IB)
por_hora_A = {}
for h in range(12):
    s = HORA[IA] == h
    por_hora_A[h + 8] = (int(s.sum()), float(ma["t15"][s].mean()) if s.sum() else None)
elegidas = [h for h, (n_, r) in por_hora_A.items() if n_ >= 150 and r is not None and r >= 0.56]
log("  dev-A por hora (n, Top-15 B1):", {h: (n_, round(100 * r, 1) if r else None) for h, (n_, r) in por_hora_A.items()})
log("  horas elegidas:", elegidas)
hB = HORA[IB] + 8
sel = np.isin(hB, elegidas)
r7 = dict(horas=elegidas, por_hora_devA=por_hora_A)
if sel.any():
    v = mbB["t15"]; d = DIA[IB]
    # diferencia elegidas - resto, por jornada (bootstrap de jornadas sobre el contraste)
    u, g = np.unique(d, return_inverse=True)
    rng = np.random.default_rng(SEMILLA); idx = rng.integers(0, len(u), (B_BOOT, len(u)))
    s1 = np.bincount(g, v * sel, minlength=len(u)); c1 = np.bincount(g, sel.astype(float), minlength=len(u))
    s0 = np.bincount(g, v * ~sel, minlength=len(u)); c0 = np.bincount(g, (~sel).astype(float), minlength=len(u))
    bs = s1[idx].sum(1) / c1[idx].sum(1) - s0[idx].sum(1) / c0[idx].sum(1)
    dif = float(v[sel].mean() - v[~sel].mean())
    r7.update(n=int(sel.sum()), top15=boot(v[sel], d[sel]), resto=float(v[~sel].mean()), dif=dif,
              dif_ic95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
              p_unilateral=float(np.mean(bs <= 0)),
              ret_plano=float(mbB["r15"][sel].mean()), ret_ponderado=float(mbB["r15p"][sel].mean()))
    obj = r7["top15"]["media"] >= 0.70 and r7["top15"]["ic95"][0] >= 0.65
    r7["veredicto"] = "OBJETIVO 70 %" if obj else ("MEJORA" if dif > 0 and r7["p_unilateral"] < 0.005 else "NO PASA")
    log(f"  dev-B horas elegidas: Top-15 {100*v[sel].mean():.2f} % (n={sel.sum()}) "
        f"[IC95 {100*r7['top15']['ic95'][0]:.1f}; {100*r7['top15']['ic95'][1]:.1f}]  resto {100*v[~sel].mean():.2f} %  "
        f"dif {100*dif:+.2f} pp [{100*r7['dif_ic95'][0]:+.2f}; {100*r7['dif_ic95'][1]:+.2f}] p={r7['p_unilateral']:.4f}"
        f"  plano {100*r7['ret_plano']:+.1f} %  ponderado {100*r7['ret_ponderado']:+.1f} %  => {r7['veredicto']}")
else:
    r7["veredicto"] = "NO PASA (ninguna hora cumple en dev-A)"
    log("  ninguna hora cumple en dev-A => NO PASA")
s8 = hB == 8
r7["ocho_am_replica_debil"] = dict(n=int(s8.sum()), top15=boot(mbB["t15"][s8], DIA[IB][s8]),
                                   ret_plano=float(mbB["r15"][s8].mean()), ret_ponderado=float(mbB["r15p"][s8].mean()))
log(f"  8:00 en dev-B (réplica débil, ya mirada): Top-15 {100*mbB['t15'][s8].mean():.2f} % (n={s8.sum()}) "
    f"[IC95 {100*r7['ocho_am_replica_debil']['top15']['ic95'][0]:.1f}; {100*r7['ocho_am_replica_debil']['top15']['ic95'][1]:.1f}]")
r7["por_hora_devB"] = {int(h + 8): float(mbB["t15"][HORA[IB] == h].mean()) for h in range(12)}
RES["P7"] = r7

# --------------------------------------------------------------------------- PLAN 8
log("\nPLAN 8  reencuadre: Top-15 en dos sorteos seguidos (h, h+1)")
iB = np.where(IB)[0]
pb = pos_de(ORD_B1[iB], Y[iB]) < 15
pares = [(k, k + 1) for k in range(len(iB) - 1)   # mismo día y hora siguiente (auditoría: sin huecos)
         if DIA[iB[k]] == DIA[iB[k + 1]] and HORA[iB[k + 1]] == HORA[iB[k]] + 1]
alguno = np.array([pb[a] or pb[b] for a, b in pares], float)
ambos = np.array([pb[a] and pb[b] for a, b in pares], float)
dpar = np.array([DIA[iB[a]] for a, b in pares])
ret_par = (30 * (pb[[a for a, b in pares]].astype(float) + pb[[b for a, b in pares]]) - 30) / 30
r8 = dict(pares=len(pares), al_menos_uno=boot(alguno, dpar), los_dos=boot(ambos, dpar), ret_ficha=boot(ret_par, dpar),
          azar_al_menos_uno=1 - (23 / 38) ** 2, azar_los_dos=(15 / 38) ** 2)
r8["veredicto"] = ("REENCUADRE (no es mejora por sorteo): " +
                   ("llega al 70 %" if r8["al_menos_uno"]["media"] >= 0.70 else "no llega al 70 %"))
log(f"  al menos uno de los dos: {100*alguno.mean():.2f} % [IC95 {100*r8['al_menos_uno']['ic95'][0]:.1f}; "
    f"{100*r8['al_menos_uno']['ic95'][1]:.1f}] (azar {100*r8['azar_al_menos_uno']:.1f} %)  cuesta 30 fichas, "
    f"retorno/ficha {100*ret_par.mean():+.1f} %")
log(f"  los dos (dupleta del Top-15): {100*ambos.mean():.2f} % (azar {100*r8['azar_los_dos']:.1f} %)  => {r8['veredicto']}")
RES["P8"] = r8

# --------------------------------------------------------------------------- PLAN 9
log("\nPLAN 9  Top-N necesario para el 70 %")
posA = pos_de(ORD_B1[IA], Y[IA]); posB = pos_de(ORD_B1[IB], Y[IB])
curvaA = {n_: float(np.mean(posA < n_)) for n_ in range(15, 31)}
Nst = min(n_ for n_, r in curvaA.items() if r >= 0.70)
hit = (posB < Nst).astype(float)
wN = np.array([3, 3, 3, 2, 2] + [1] * (Nst - 5), float); wpos = np.zeros(K); wpos[:Nst] = wN
r9 = dict(N=Nst, curva_devA=curvaA, top=boot(hit, DIA[IB]),
          ret_plano=boot((30 * hit - Nst) / Nst, DIA[IB]),
          ret_ponderado=boot((30 * wpos[posB] - wN.sum()) / wN.sum(), DIA[IB]), azar=Nst / K,
          curva_devB={n_: float(np.mean(posB < n_)) for n_ in range(15, 31)})
ic = r9["ret_plano"]["ic95"]   # auditoría: el veredicto en plata mira el IC, no solo la media
r9["veredicto"] = ("Top-%d llega al 70 %% " % Nst) + ("y gana (IC95 > 0)" if ic[0] > 0 else
                   ("y PIERDE (IC95 < 0)" if ic[1] < 0 else "pero el retorno plano no se distingue de 0"))
log(f"  N* = {Nst} (dev-A {100*curvaA[Nst]:.1f} %) => {r9['veredicto']}.  dev-B: Top-{Nst} {100*hit.mean():.2f} % "
    f"[IC95 {100*r9['top']['ic95'][0]:.1f}; {100*r9['top']['ic95'][1]:.1f}] (azar {100*Nst/K:.1f} %)  "
    f"retorno/ficha plano {100*r9['ret_plano']['media']:+.1f} % [{100*r9['ret_plano']['ic95'][0]:+.1f}; "
    f"{100*r9['ret_plano']['ic95'][1]:+.1f}], ponderado {100*r9['ret_ponderado']['media']:+.1f} %")
log("  curva dev-B Top-N:", {n_: round(100 * r, 1) for n_, r in r9["curva_devB"].items()})
RES["P9"] = r9

# --------------------------------------------------------------------------- PLAN 10
log("\nPLAN 10  otras loterías como fuente (2026-04-13..09-13; réplica débil)")


def leer_csv(nombre):
    out = {}
    with io.open(os.path.join(RAIZ, "datos_multiloteria", nombre + ".csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                out[(r["fecha"], int(r["hora"][:2]) - 8)] = int(r["numero"]) if r["numero"] not in ("00",) else -2
            except ValueError:
                pass
    return out


LA10 = leer_csv("lottoactivo"); FUENTES = {
    "granjita_h-1": (leer_csv("lagranjita"), 1), "selvaplus_h-1:15": (leer_csv("selvaplus"), 1),
    "guacharo_h-1": (leer_csv("guacharoactivo"), 1), "granjita_h_simultaneo": (leer_csv("lagranjita"), 0),
    "rdint_h-1:30_control": (leer_csv("lottoactivordint"), 1)}
frec = np.bincount([v for v in LA10.values() if 1 <= v <= 36], minlength=37)[1:] / sum(1 for v in LA10.values())
r10 = {}
for nom, (src, lag) in FUENTES.items():
    o = e = 0; dias = []; ov = []
    for (f, h), a in LA10.items():
        x = src.get((f, h - lag))
        if h - lag < 0 or x is None or not (1 <= x <= 36):
            continue
        hitv = float(a == x); o += hitv; e += frec[x - 1]; dias.append(f); ov.append((hitv, frec[x - 1]))
    ov = np.array(ov); u, g = np.unique(dias, return_inverse=True)
    so = np.bincount(g, ov[:, 0]); se = np.bincount(g, ov[:, 1])
    rng = np.random.default_rng(SEMILLA); idx = rng.integers(0, len(u), (B_BOOT, len(u)))
    bs = so[idx].sum(1) / se[idx].sum(1)
    ic = [float(np.percentile(bs, 0.25)), float(np.percentile(bs, 99.75))]
    oe_ = o / e
    pasa = (oe_ < 0.80 or oe_ > 1.20) and not (ic[0] <= 1 <= ic[1])
    r10[nom] = dict(n=len(ov), obs=int(o), esp=round(float(e), 1), oe=float(oe_), ic99_5=ic,
                    veredicto=("control" if "control" in nom else ("descriptivo" if "simult" in nom else
                                                                   ("PASA" if pasa else "NO PASA"))))
    log(f"  {nom}: n={len(ov)} obs {int(o)} esp {e:.1f} O/E {oe_:.3f} [IC99,5 {ic[0]:.2f}; {ic[1]:.2f}] => {r10[nom]['veredicto']}")
RES["P10"] = r10

if __name__ == "__main__":   # las rondas 2-4 importan este script con runpy: que no reescriban las salidas
  with io.open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8") as fh:
    json.dump(RES, fh, ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
  with io.open(os.path.join(AQUI, "salida.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(SAL) + "\n")
