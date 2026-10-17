# -*- coding: utf-8 -*-
"""¿El operador esquiva otros números "de los más jugados"? (PREREGISTRO.md, misma carpeta)

Uso:  python investigacion/2026-10-15/mas_jugado/mas_jugado.py
Solo desarrollo [2000, 9357): dev-A [2000, 5688) elige, dev-B [5688, 9357) confirma. No lee el tramo de prueba.
"""
import json, os, sys
from datetime import date, timedelta
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE  # noqa: E402

W, MITAD, CORTE = 2000, 5688, 9357
K = 38; B = 4000; SEM = 20261015; NH = 10
SAL = []


def log(s=""):
    print(s, flush=True); SAL.append(s)


# ------------------------------------------------------------------ datos (desarrollo, fechas corregidas)
D = LE.cargar(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "historial.txt"))
_c = np.load(os.path.join(RAIZ, "herramientas", "exploracion", "calor_cache.npz"))
P = LE.normalizar(_c["P"]); Y = _c["y"].astype(int)
assert len(Y) == CORTE - W and (D.seq[W:CORTE] == Y).all()
N = len(Y)
cor = json.load(open(os.path.join(RAIZ, "herramientas", "correccion_historial_2026-09-29.json"), encoding="utf-8"))
mapa = {}
for c in cor["cambios"]:
    a = c["antes"].split(); b = c["despues"].split()
    mapa.setdefault((a[0], int(a[1]), a[2]), []).append(b[0])
FECHA = []; ncor = 0
for t in range(W, CORTE):
    k = (D.fecha[t], int(D.hora[t]), LE.POS[D.seq[t]])
    if k in mapa and mapa[k]:
        FECHA.append(mapa[k].pop(0)); ncor += 1
    else:
        FECHA.append(D.fecha[t])
FILA = np.arange(W, CORTE)
IA = FILA < MITAD; IB = ~IA
HORA = D.hora[W:CORTE].astype(int) + 8                      # 8..19
H12 = (HORA - 1) % 12 + 1
FD = [date.fromisoformat(f) for f in FECHA]
DIA = np.array([d.day for d in FD])
_u, JOR = np.unique(np.array(FECHA), return_inverse=True)   # jornada para el bootstrap
PREV = D.seq[W - 1:CORTE - 1]                               # último ganador (sorteo anterior)
assert (D.seq[W:CORTE][:-1] == PREV[1:]).all()

CODIGOS = LE.POS                                            # índice -> código
TERM = np.array([int(c) % 10 for c in CODIGOS])             # "0" y "00" terminan en 0


def idx(num):
    s = str(int(num))
    return LE.IDX.get(s) if 0 <= int(num) <= 36 else None


def rev(n):
    """Número leído al revés (10->1, 12->21); None si no cambia o se sale de 0..36."""
    s = str(int(n))
    if len(s) < 2:
        return None
    r = int(s[::-1])
    return r if r != n and 0 <= r <= 36 else None


INV_PAR = {1: 10, 10: 1, 2: 20, 20: 2, 3: 30, 30: 3, 12: 21, 21: 12, 13: 31, 31: 13, 23: 32, 32: 23}
FEST = [(1, 1), (4, 19), (5, 1), (6, 24), (7, 5), (7, 24), (10, 12), (12, 24), (12, 25), (12, 31)]


def festivo_proximo(d):
    """Número del día festivo si d está 1..3 días antes de uno."""
    for k in (1, 2, 3):
        e = d + timedelta(days=k)
        if (e.month, e.day) in FEST:
            return e.day
    return None


def dia_pago(d):
    ult = ((d.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)).day
    return d.day in (15, 16, 1) or d.day == ult


def cerca_pago(d):
    return d.day in (12, 13, 14, 15, 16, 17, 18, 27, 28, 29, 30, 31, 1, 2, 3)


# ------------------------------------------------------------------ conjuntos (máscara N x 38)
EXCL = np.zeros((N, K), bool)
for i in range(N):
    for v in (DIA[i], DIA[i] + 1, H12[i]):
        j = idx(v)
        if j is not None:
            EXCL[i, j] = True


def construir(fn):
    M = np.zeros((N, K), bool)
    for i in range(N):
        for v in fn(i):
            if v is None:
                continue
            j = idx(v)
            if j is not None:
                M[i, j] = True
    return M


def por_terminal(dig_fn, sin=None):
    M = np.zeros((N, K), bool)
    for i in range(N):
        M[i] = TERM == dig_fn(i)
        if sin is not None:
            M[i, sin(i)] = False
    return M


HIP = {
    "M1_dia_invertido": construir(lambda i: [rev(DIA[i])]),
    "M2_terminal_dia": por_terminal(lambda i: DIA[i] % 10),
    "M3_terminal_hora": por_terminal(lambda i: H12[i] % 10),
    "M4_hora_invertida": construir(lambda i: [rev(H12[i]) if H12[i] >= 10 else (H12[i] * 10 if H12[i] <= 3 else None)]),
    "M5_invertido_ultimo": construir(lambda i: [INV_PAR.get(int(CODIGOS[PREV[i]])) if CODIGOS[PREV[i]] != "00" else None]),
    "M6_terminal_ultimo": por_terminal(lambda i: TERM[PREV[i]], sin=lambda i: PREV[i]),
    "M7_suma_fecha": construir(lambda i: [sum(int(ch) for ch in FD[i].strftime("%d%m%Y"))]),
    "M8_vispera_festiva": construir(lambda i: [festivo_proximo(FD[i])]),
    "M9_quincena_15_30": construir(lambda i: [15, 30] if cerca_pago(FD[i]) else []),
}
HIP = {k: (M & ~EXCL) for k, M in HIP.items()}
PAGO = np.array([dia_pago(d) for d in FD])
D0 = construir(lambda i: [DIA[i]])


def placebo(M):
    return np.roll(M, 7, axis=1) & ~EXCL


# ------------------------------------------------------------------ medidas
def por_jornada(o, e, s):
    return np.bincount(JOR[s], o[s], minlength=len(_u)), np.bincount(JOR[s], e[s], minlength=len(_u))


def boot_oe(o, e, s, rng_seed=SEM):
    so, se = por_jornada(o, e, s)
    keep = se > 0
    so, se = so[keep], se[keep]
    idxb = np.random.default_rng(rng_seed).integers(0, len(so), (B, len(so)))
    bs = so[idxb].sum(1) / se[idxb].sum(1)
    oe = so.sum() / se.sum()
    return dict(O=int(round(so.sum())), E=float(se.sum()), OE=float(oe),
                ic95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                ic99=[float(np.percentile(bs, 0.5)), float(np.percentile(bs, 99.5))],
                p_menor1=float((np.sum(bs >= 1) + 1) / (B + 1)))


def oe_mascara(M, s):
    o = M[np.arange(N), Y].astype(float); e = (P * M).sum(1)
    return o, e, s & M.any(1)


def por_hora(M, s):
    o, e, ss = oe_mascara(M, s)
    return {int(h): round(float(o[ss & (HORA == h)].sum() / max(e[ss & (HORA == h)].sum(), 1e-9)), 2) for h in range(8, 20)}


def heterogeneidad(M, s):
    o, e, ss = oe_mascara(M, s)
    chi = 0.0
    for h in range(8, 20):
        q = ss & (HORA == h)
        O, E = o[q].sum(), e[q].sum()
        if E > 0:
            chi += (O - E) ** 2 / E
    return float(chi)   # ~ chi2 con 12 g.l. si O/E = 1 en todas las horas (descriptivo)


RES = {"filas_fecha_corregida": ncor, "N": int(N), "nA": int(IA.sum()), "nB": int(IB.sum())}
log(f"Desarrollo: {N} sorteos ({FECHA[0]}..{FECHA[-1]}); dev-A {IA.sum()}, dev-B {IB.sum()}; filas con fecha corregida {ncor}")
log("Criterio: dev-A O/E<1 con p<0,05 Y dev-B O/E<1 con p<0,005 (Bonferroni 10)\n")
PASAN = []
for nom, M in HIP.items():
    o, e, ss = oe_mascara(M, np.ones(N, bool))
    a = boot_oe(o, e, ss & IA); b = boot_oe(o, e, ss & IB)
    op, ep, sp = oe_mascara(placebo(M), np.ones(N, bool))
    pl = boot_oe(op, ep, sp & IB)
    pasa = a["OE"] < 1 and a["p_menor1"] < 0.05 and b["OE"] < 1 and b["p_menor1"] < 0.005
    RES[nom] = dict(sorteos_validos_A=int((ss & IA).sum()), sorteos_validos_B=int((ss & IB).sum()),
                    tam_medio=float(M[ss].sum(1).mean()), devA=a, devB=b, placebo_devB=pl,
                    por_hora_devA=por_hora(M, IA), por_hora_devB=por_hora(M, IB),
                    chi2_horas_devB=heterogeneidad(M, IB), PASA=bool(pasa))
    if pasa:
        PASAN.append(nom)
    log(f"{nom}: válidos A/B {(ss & IA).sum()}/{(ss & IB).sum()}, tamaño medio {M[ss].sum(1).mean():.2f}")
    log(f"   dev-A O/E {a['OE']:.3f} [{a['ic95'][0]:.2f}; {a['ic95'][1]:.2f}] (O {a['O']}, E {a['E']:.1f}, p {a['p_menor1']:.3f})")
    log(f"   dev-B O/E {b['OE']:.3f} [IC99 {b['ic99'][0]:.2f}; {b['ic99'][1]:.2f}] (O {b['O']}, E {b['E']:.1f}, p {b['p_menor1']:.4f})"
        f"   placebo+7 dev-B {pl['OE']:.2f}   chi2 horas dev-B {RES[nom]['chi2_horas_devB']:.1f}  => {'PASA' if pasa else 'NO PASA'}")

# M10: razón de O/E del animal D0 en días de pago vs el resto
o, e, ss = oe_mascara(D0, np.ones(N, bool))


def razon(s, seed=SEM):
    sp, ep_ = por_jornada(o, e, s & PAGO); sr, er = por_jornada(o, e, s & ~PAGO)
    dias = np.where((ep_ + er) > 0)[0]
    sp, ep_, sr, er = sp[dias], ep_[dias], sr[dias], er[dias]
    R0 = (sp.sum() / ep_.sum()) / (sr.sum() / er.sum())
    ib = np.random.default_rng(seed).integers(0, len(dias), (B, len(dias)))
    rb = (sp[ib].sum(1) / np.maximum(ep_[ib].sum(1), 1e-9)) / (sr[ib].sum(1) / er[ib].sum(1))
    return dict(R=float(R0), OE_pago=float(sp.sum() / ep_.sum()), OE_resto=float(sr.sum() / er.sum()),
                O_pago=int(sp.sum()), E_pago=float(ep_.sum()), O_resto=int(sr.sum()), E_resto=float(er.sum()),
                ic95=[float(np.percentile(rb, 2.5)), float(np.percentile(rb, 97.5))],
                ic99=[float(np.percentile(rb, 0.5)), float(np.percentile(rb, 99.5))],
                p_menor1=float((np.sum(rb >= 1) + 1) / (B + 1)))


a = razon(ss & IA); b = razon(ss & IB)
pasa = a["R"] < 1 and a["p_menor1"] < 0.05 and b["R"] < 1 and b["p_menor1"] < 0.005
RES["M10_pago_x_fecha"] = dict(devA=a, devB=b, PASA=bool(pasa))
if pasa:
    PASAN.append("M10_pago_x_fecha")
log("M10_pago_x_fecha (animal D0, días de pago vs resto):")
for t, r in (("dev-A", a), ("dev-B", b)):
    log(f"   {t}: O/E pago {r['OE_pago']:.2f} (O {r['O_pago']}, E {r['E_pago']:.1f}) vs resto {r['OE_resto']:.2f} "
        f"(O {r['O_resto']}, E {r['E_resto']:.1f}); R {r['R']:.2f} [IC95 {r['ic95'][0]:.2f}; {r['ic95'][1]:.2f}] p {r['p_menor1']:.3f}")
log(f"   => {'PASA' if pasa else 'NO PASA'}")


# ------------------------------------------------------------------ ganancia (solo las que pasan)
def mbits_boot(Pn, s):
    d = 1000 * (np.log2(Pn[np.arange(N), Y]) - np.log2(P[np.arange(N), Y]))
    sd = np.bincount(JOR[s], d[s], minlength=len(_u)); cnt = np.bincount(JOR[s], minlength=len(_u))
    k = cnt > 0; sd, cnt = sd[k], cnt[k]
    ib = np.random.default_rng(SEM).integers(0, len(sd), (B, len(sd)))
    bs = sd[ib].sum(1) / cnt[ib].sum(1)
    return float(sd.sum() / cnt.sum()), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def aplicar(Ms, lm):
    L = np.log(P).copy()
    for M, v in zip(Ms, lm):
        L = L + v * M
    L -= L.max(1, keepdims=True); Q = np.exp(L)
    return Q / Q.sum(1, keepdims=True)


def ajustar(Ms, s, it=60):
    lm = np.zeros(len(Ms))
    for _ in range(it):                       # Newton sobre log m (log-verosimilitud cóncava)
        Q = aplicar(Ms, lm)
        g = np.array([(M[np.arange(N), Y][s]).sum() - (Q * M)[s].sum() for M in Ms])
        Hm = np.zeros((len(Ms), len(Ms)))
        for a_ in range(len(Ms)):
            qa = (Q * Ms[a_]).sum(1)
            for b_ in range(len(Ms)):
                qb = (Q * Ms[b_]).sum(1); qab = (Q * (Ms[a_] & Ms[b_])).sum(1)
                Hm[a_, b_] = -(qab - qa * qb)[s].sum()
        paso = np.linalg.solve(Hm - 1e-9 * np.eye(len(Ms)), g)
        lm = lm - paso
        if np.abs(paso).max() < 1e-8:
            break
    return lm


log("\nGanancia (m ajustado en dev-A, medido en dev-B):")
if not PASAN:
    log("   ninguna hipótesis pasa: no se estima ganancia.")
else:
    MS = {k: (HIP[k] if k in HIP else (D0 & PAGO[:, None])) for k in PASAN}
    for k, M in MS.items():
        lm = ajustar([M], IA)
        mb = mbits_boot(aplicar([M], lm), IB)
        RES[k]["m_devA"] = float(np.exp(lm[0])); RES[k]["mbits_devB"] = mb
        log(f"   {k}: m = {np.exp(lm[0]):.3f}; dev-B {mb[0]:+.2f} mbits [{mb[1][0]:+.2f}; {mb[1][1]:+.2f}]")
    if len(MS) > 1:
        lm = ajustar(list(MS.values()), IA)
        mb = mbits_boot(aplicar(list(MS.values()), lm), IB)
        RES["conjunto"] = dict(m=[float(x) for x in np.exp(lm)], mbits_devB=mb)
        log(f"   juntas: m = {[round(float(x), 3) for x in np.exp(lm)]}; dev-B {mb[0]:+.2f} mbits [{mb[1][0]:+.2f}; {mb[1][1]:+.2f}]")

# referencia: la corrección conocida D0/D+1/H12 con el mismo método (descriptivo)
REF = [construir(lambda i: [DIA[i]]), construir(lambda i: [DIA[i] + 1]), construir(lambda i: [H12[i]])]
lm = ajustar(REF, IA); mb = mbits_boot(aplicar(REF, lm), IB)
RES["referencia_D0_D1_H12"] = dict(m=[float(x) for x in np.exp(lm)], mbits_devB=mb)
log(f"   referencia D0/D+1/H12 (ya conocida, mismo método): m = {[round(float(x), 3) for x in np.exp(lm)]}; "
    f"dev-B {mb[0]:+.2f} mbits [{mb[1][0]:+.2f}; {mb[1][1]:+.2f}]")
RES["PASAN"] = PASAN
log(f"\nPASAN: {PASAN if PASAN else 'ninguna'}")
json.dump(RES, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(os.path.join(AQUI, "salida.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
