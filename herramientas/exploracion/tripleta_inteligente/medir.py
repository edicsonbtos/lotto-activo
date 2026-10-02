# -*- coding: utf-8 -*-
"""Tripleta inteligente (PREREGISTRO.md). Solo desarrollo: inicios 2000..9345 del historial congelado.
Uso: python herramientas/exploracion/tripleta_inteligente/medir.py -> resultados.json, salida.txt"""
import io, json, os, sys, time
from itertools import combinations
from math import comb
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE  # noqa: E402
import tripleta_ventana as TV  # noqa: E402

K = 38; V = 12; PAGO = 45; CORTE = 9357; MITAD = 5688; SEM = 20261002; B = 3000
SAL = []; RES = {}


def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)


D = LE.cargar(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "historial.txt")).prefijo(CORTE)
t0 = time.time()
X, Y, _ = TV.construir(D)
FIN = CORTE - V + 1                                  # último inicio 9345
P = TV.Modelo().predecir(X, Y, LE.W, FIN)            # (FIN-W, 38)
log(f"modelo listo en {time.time()-t0:.0f}s; inicios {LE.W}..{FIN-1}")
ini = np.arange(LE.W, FIN)
seq = np.asarray(D.seq); hora = np.asarray(D.hora)[ini]; dia = np.asarray(D.dia)[ini]
fecha = [D.fecha[t] for t in ini]
SALE = [set(seq[t:t + V].tolist()) for t in ini]
base = np.array([comb(len(s), 3) / comb(K, 3) for s in SALE])
orden = np.argsort(-P, axis=1, kind="stable")
IA = ini < MITAD; IB = ~IA


def jugar(combos_de):
    """combos_de(i) -> lista de tripletas. Devuelve (aciertos por ventana, fichas por ventana)."""
    h = np.zeros(len(ini)); f = np.zeros(len(ini))
    for i in range(len(ini)):
        cs = combos_de(i); f[i] = len(cs)
        h[i] = sum(1 for c in cs if all(a in SALE[i] for a in c))
    return h, f


def boot(num, den, sel):
    u, g = np.unique(dia[sel], return_inverse=True)
    sn = np.bincount(g, num[sel]); sd = np.bincount(g, den[sel])
    rng = np.random.default_rng(SEM); i = rng.integers(0, len(u), (B, len(u)))
    bs = sn[i].sum(1) / sd[i].sum(1)
    return float(num[sel].sum() / den[sel].sum()), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def ev(h, f, sel):
    r, ic = boot(PAGO * h - f, f, sel)
    return r, ic


def estr_topk(k):
    return lambda i: [tuple(c) for c in combinations(orden[i, :k].tolist(), 3)]


ESTR = {"A_123_456": lambda i: [tuple(orden[i, :3]), tuple(orden[i, 3:6])],
        "B_123_124": lambda i: [tuple(orden[i, :3]), (orden[i, 0], orden[i, 1], orden[i, 3])]}
for k in (3, 4, 5, 6):
    ESTR[f"C{k}_todas_de_top{k}"] = estr_topk(k)
J = {n: jugar(fn) for n, fn in ESTR.items()}

log("\nReferencia: P(sale en 12) por puesto 1..6 en dev:",
    [round(float(np.mean([orden[i, r] in SALE[i] for i in range(len(ini))])), 3) for r in range(6)],
    " base por animal", round(float(np.mean([len(s) for s in SALE]) / K), 3))
log(f"Tasa de una tripleta al azar: {100*base.mean():.2f} % (umbral con 45x: 2,22 %); "
    f"lo que se queda la casa al azar: {100*(1-45*base.mean()):.1f} %")

# ---------------- Q2 cobertura
log("\nQ2  cuántas combinaciones (EV por ficha, % de ventanas que cobran algo)")
RES["Q2"] = {}
for n, (h, f) in J.items():
    row = {}
    for tr, sel in (("devA", IA), ("devB", IB)):
        r, ic = ev(h, f, sel)
        row[tr] = dict(ev=r, ic95=ic, tasa=float(h[sel].sum() / f[sel].sum()), cobra=float(np.mean(h[sel] > 0)),
                       fichas=int(f[sel][0]))
    RES["Q2"][n] = row
    a, b = row["devA"], row["devB"]
    log(f"  {n:<18} {a['fichas']:2d} fichas | dev-A EV {100*a['ev']:+6.1f} %  cobra {100*a['cobra']:5.1f} % | "
        f"dev-B EV {100*b['ev']:+6.1f} % [{100*b['ic95'][0]:+.0f}; {100*b['ic95'][1]:+.0f}]  "
        f"acierto/tripleta {100*b['tasa']:.2f} %  cobra {100*b['cobra']:5.1f} %")
mejor = max(RES["Q2"], key=lambda n: RES["Q2"][n]["devA"]["ev"])
hA, fA = J["A_123_456"]; hM, fM = J[mejor]
d_ev = (PAGO * hM - fM) / fM - (PAGO * hA - fA) / fA
r, ic = boot(d_ev, np.ones(len(ini)), IB)
RES["Q2_eleccion"] = dict(elegida_en_devA=mejor, dif_ev_vs_A_devB=r, ic95=ic,
                          veredicto="MEJORA" if (mejor != "A_123_456" and ic[0] > 0) else
                          ("es la misma A" if mejor == "A_123_456" else "no se distingue"))
log(f"  elegida en dev-A: {mejor}; dev-B frente a A: {100*r:+.1f} pp [{100*ic[0]:+.1f}; {100*ic[1]:+.1f}] => "
    f"{RES['Q2_eleccion']['veredicto']}")

# ---------------- Q1 hora de compra
log("\nQ1  a qué hora comprar (estrategia A; hora del primer sorteo de la ventana)")
RES["Q1"] = {}
evA_h = {}
for hh in range(12):
    row = {}
    for tr, sel in (("devA", IA), ("devB", IB)):
        s = sel & (hora == hh)
        if s.sum() < 30:
            row[tr] = None; continue
        r, ic = ev(hA, fA, s)
        row[tr] = dict(n=int(s.sum()), ev=r, ic95=ic, base=float(base[s].mean()),
                       tasa=float(hA[s].sum() / fA[s].sum()))
    RES["Q1"][hh + 8] = row; evA_h[hh] = row["devA"]["ev"] if row["devA"] else None
    fa = lambda x: "—" if x is None else f"n={x['n']:4d} EV {100*x['ev']:+6.1f} % (azar {100*x['base']:.2f} %, modelo {100*x['tasa']:.2f} %)"
    log(f"  {hh+8:2d}:00  dev-A {fa(row['devA'])} | dev-B {fa(row['devB'])}" +
        (f" [{100*row['devB']['ic95'][0]:+.0f}; {100*row['devB']['ic95'][1]:+.0f}]" if row["devB"] else ""))
mejor_h = max((h for h in evA_h if evA_h[h] is not None and RES["Q1"][h + 8]["devA"]["n"] >= 150),
              key=lambda h: evA_h[h])
RES["Q1_eleccion"] = {}
for nom, hh in (("8:00 (a priori)", 0), (f"{mejor_h+8}:00 (mejor en dev-A)", mejor_h)):
    s = IB & (hora == hh)
    v = np.where(hora == hh, (PAGO * hA - fA) / fA, np.nan)
    rr, ic1 = ev(hA, fA, s); todo, _ = ev(hA, fA, IB)
    # diferencia hora vs cualquier hora, por jornadas
    u, g = np.unique(dia[IB], return_inverse=True)
    x1 = (PAGO * hA - fA)[IB]; f1 = fA[IB]; m1 = (hora[IB] == hh)
    s1 = np.bincount(g, x1 * m1, minlength=len(u)); c1 = np.bincount(g, f1 * m1, minlength=len(u))
    s0 = np.bincount(g, x1, minlength=len(u)); c0 = np.bincount(g, f1, minlength=len(u))
    rng = np.random.default_rng(SEM); i = rng.integers(0, len(u), (B, len(u)))
    bs = s1[i].sum(1) / np.maximum(c1[i].sum(1), 1) - s0[i].sum(1) / c0[i].sum(1)
    dif = rr - todo; icd = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    ver = "MEJORA" if icd[0] > 0 else "no se distingue"
    RES["Q1_eleccion"][nom] = dict(ev_devB=rr, ic95=ic1, ev_cualquier_hora=todo, dif=dif, ic95_dif=icd, veredicto=ver)
    log(f"  {nom}: dev-B EV {100*rr:+.1f} % [{100*ic1[0]:+.0f}; {100*ic1[1]:+.0f}] contra {100*todo:+.1f} % a cualquier hora; "
        f"dif {100*dif:+.1f} pp [{100*icd[0]:+.0f}; {100*icd[1]:+.0f}] => {ver}")

# ---------------- Q3 lista negra
log("\nQ3  lista negra (sin el número del día ni el de mañana)")
def sin_fecha(i):
    d = int(fecha[i][8:10]); neg = {LE.IDX[str(n)] for n in (d, d + 1) if 1 <= n <= 36}
    o = [a for a in orden[i].tolist() if a not in neg]
    return [tuple(o[:3]), tuple(o[3:6])]
hN, fN = jugar(sin_fecha)
cambia = np.array([len({LE.IDX[str(n)] for n in (int(fecha[i][8:10]), int(fecha[i][8:10]) + 1) if 1 <= n <= 36}
                       & set(orden[i, :6].tolist())) > 0 for i in range(len(ini))])
d3 = (PAGO * hN - fN) / fN - (PAGO * hA - fA) / fA
r3, ic3 = boot(d3, np.ones(len(ini)), IB)
RES["Q3"] = dict(ventanas_que_cambian_devB=float(cambia[IB].mean()), dif_ev_devB=r3, ic95=ic3,
                 veredicto="MEJORA" if ic3[0] > 0 else "no se distingue")
log(f"  cambia la tripleta en {100*cambia[IB].mean():.0f} % de las ventanas; dev-B dif EV {100*r3:+.1f} pp "
    f"[{100*ic3[0]:+.1f}; {100*ic3[1]:+.1f}] => {RES['Q3']['veredicto']}")

# ---------------- rachas (para hablar claro)
p = RES["Q2"]["A_123_456"]["devB"]["tasa"]
log(f"\nRachas: con {100*p:.1f} % por tripleta y 2 por día, sin cobrar 15 días seguidos pasa con prob "
    f"{100*(1-p)**30:.0f} %, 30 días {100*(1-p)**60:.0f} %.")
RES["rachas"] = dict(p=p, sin_cobrar_15_dias=(1 - p) ** 30, sin_cobrar_30_dias=(1 - p) ** 60)
with io.open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8") as fh:
    json.dump(RES, fh, ensure_ascii=False, indent=1)
with io.open(os.path.join(AQUI, "salida.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(SAL) + "\n")
