# -*- coding: utf-8 -*-
"""ag2: reinicio semanal / compensacion tras pago (ver PREREGISTRO.md). Uso: python analizar.py -> salida.txt, resultado.json"""
import os, sys, json, math
from collections import defaultdict
from datetime import date, timedelta
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

SAL = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)

W, CORTE = 2000, 9357
FIN, CORTE_AB = "2025-12-14", "2025-02-03"      # A: fecha <= CORTE_AB
B, SEM = 2000, 20261023
ALPHA_Z = 2.64
D = LE.cargar(os.path.join(RAIZ, "verificacion/hilo9/datos/historial.txt"))
c = np.load(os.path.join(RAIZ, "verificacion/hilo9/datos/calor_cache.npz"))
P = LE.normalizar(c["P"]); Y = c["y"].astype(int)
assert (D.seq[W:CORTE] == Y).all()

# ---- datos publicados U_d
PUB = defaultdict(dict)
for ln in open(os.path.join(RAIZ, "investigacion/2026-10-15/pronosticadores/datos/publicados.jsonl"), encoding="utf-8"):
    r = json.loads(ln)
    if "error" in r["datos"]: continue
    for juego, v in r["datos"].items():
        if v.get("fecha_pagina") and v["fecha_pagina"] != r["fecha"]: continue
        s = {LE.IDX[n] for n in v["nums"] if n in LE.IDX}
        if s: PUB[("RD" if "RD" in juego else "LA", r["fecha"])][r["fuente"]] = s
def U(f):
    p = PUB.get(("LA", f));  return set().union(*p.values()) if p else None

# ---- filas validas
ts = [t for t in range(W, CORTE) if D.fecha[t] <= FIN]
dia_filas = defaultdict(list)
for t in range(W, CORTE):
    dia_filas[int(D.dia[t])].append(t)
rows = []   # dict por sorteo
for t in ts:
    i = t - W; d = int(D.dia[t]); f = D.fecha[t]
    prior = {int(D.seq[u]) for u in dia_filas[d] if u < t}
    rows.append(dict(t=t, i=i, d=d, f=f, h=int(D.hora[t]), dow=int(D.dow[t]), y=int(Y[i]), prior=prior,
                     half=0 if f <= CORTE_AB else 1, dom=int(f[8:10])))
log(f"sorteos validos {len(rows)}; dev-A {sum(r['half']==0 for r in rows)} dev-B {sum(r['half']==1 for r in rows)}; dias {len({r['d'] for r in rows})}")

# ---- contraste MH con bootstrap por jornada
def contrasta(recs, rng, nombre, g1="g1", g0="g0"):
    """recs: lista (dia, hora, grupo 1/0, O, E). RR = (1)/(0) estratificado por hora."""
    if not recs: log(f"  {nombre}: sin datos"); return None
    a = np.array(recs, float); dias = np.unique(a[:, 0]); ix = np.searchsorted(dias, a[:, 0])
    T = np.zeros((len(dias), 12, 2, 2))
    np.add.at(T, (ix, a[:, 1].astype(int), a[:, 2].astype(int), 0), a[:, 3])
    np.add.at(T, (ix, a[:, 1].astype(int), a[:, 2].astype(int), 1), a[:, 4])
    def rr(S):                        # S: (...,12,2,2); grupo 1 y 0
        O1, E1, O0, E0 = S[..., 1, 0], S[..., 1, 1], S[..., 0, 0], S[..., 0, 1]
        tot = E1 + E0; ok = tot > 0
        num = np.where(ok, O1 * E0 / np.where(ok, tot, 1), 0).sum(-1); den = np.where(ok, O0 * E1 / np.where(ok, tot, 1), 0).sum(-1)
        return num / den
    S0 = T.sum(0); est = rr(S0)
    w = rng.multinomial(len(dias), np.ones(len(dias)) / len(dias), size=B)
    bs = rr(np.einsum("bd,dhgk->bhgk", w, T))
    bs = bs[np.isfinite(bs) & (bs > 0)]
    se = np.log(bs).std()
    z = math.log(est) / se if est > 0 else float("nan")
    o1, e1, o0, e0 = S0[:, 1, 0].sum(), S0[:, 1, 1].sum(), S0[:, 0, 0].sum(), S0[:, 0, 1].sum()
    return dict(RR=float(est), ic=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], z=float(z),
                oe1=float(o1 / e1), O1=float(o1), E1=float(e1), oe0=float(o0 / e0), O0=float(o0), E0=float(e0), dias=int(len(dias)))
def fmt(r):
    if r is None: return "sin datos"
    return (f"RR {r['RR']:.3f} [{r['ic'][0]:.2f};{r['ic'][1]:.2f}] z {r['z']:+.2f} | g1 O/E {r['oe1']:.3f} (O {r['O1']:.0f}/E {r['E1']:.1f}) "
            f"g0 O/E {r['oe0']:.3f} (O {r['O0']:.0f}/E {r['E0']:.1f})")
def veredicto(rA, rB, rT, dir_=None):
    if None in (rA, rB, rT): return False
    ok = (np.sign(rA['z']) == np.sign(rB['z']) == np.sign(rT['z']) and abs(rA['z']) >= 2 and abs(rB['z']) >= 2 and abs(rT['z']) >= ALPHA_Z)
    if dir_ == "<": ok = ok and rT['RR'] < 1
    return bool(ok)
def correr(nombre, recs_por_mitad, dir_=None):
    rng = np.random.default_rng(SEM)
    rA = contrasta(recs_por_mitad[0], rng, nombre); rB = contrasta(recs_por_mitad[1], rng, nombre)
    rT = contrasta(recs_por_mitad[0] + recs_por_mitad[1], rng, nombre)
    log(f"\n[{nombre}]"); log("  dev-A:", fmt(rA)); log("  dev-B:", fmt(rB)); log("  total:", fmt(rT))
    p = veredicto(rA, rB, rT, dir_); log(f"  veredicto: {'PASA' if p else 'NO PASA'}")
    RES[nombre] = dict(A=rA, B=rB, T=rT, pasa=p); return p
RES = {}

# ---- R1: F1 (ya salio hoy) y F2 (numero = fecha) por posicion en la semana
def pos(dow): return 1 if dow >= 4 else (0 if dow <= 1 else None)   # fin=1 (vie-dom), inicio=0 (lun-mar)
def pos3(dow): return 0 if dow <= 1 else (1 if dow <= 3 else 2)
def feat(r, tipo):
    if tipo == "F1":
        if not r["prior"]: return None
        m = list(r["prior"])
    else:
        m = [LE.IDX[str(x)] for x in (r["dom"], r["dom"] + 1) if x <= 36]
    return float(r["y"] in m), float(P[r["i"], m].sum())
for tipo, nom in (("F1", "R1a_ya_salio_hoy"), ("F2", "R1b_numero_fecha")):
    recs = [[], []]
    for r in rows:
        g = pos(r["dow"]); x = feat(r, tipo)
        if g is None or x is None: continue
        recs[r["half"]].append((r["d"], r["h"], g, x[0], x[1]))
    correr(f"{nom} fin(vie-dom) vs inicio(lun-mar)", recs)
    # descriptivo: tres posiciones y cada dia de semana
    log(f"  descriptivo {tipo}: O/E por posicion (inicio/mitad/fin) y por dia lun..dom, total / A / B")
    for lab, sel in (("total", lambda r: True), ("A", lambda r: r["half"] == 0), ("B", lambda r: r["half"] == 1)):
        oe = lambda f_: (lambda l: (sum(x[0] for x in l) / sum(x[1] for x in l), sum(x[1] for x in l)) if l and sum(x[1] for x in l) > 0 else (float('nan'), 0))(
            [x for r in rows if sel(r) and f_(r) and (x := feat(r, tipo))])
        p3 = [oe(lambda r, k=k: pos3(r["dow"]) == k) for k in range(3)]
        dw = [oe(lambda r, k=k: r["dow"] == k) for k in range(7)]
        log(f"   {lab:5s} pos: " + " ".join(f"{o:.2f}(E{e:.0f})" for o, e in p3) + " | dow: " + " ".join(f"{o:.2f}" for o, e in dw))

# ---- R2a: tras pago del sorteo inmediatamente anterior
recs = [[], []]
for r in rows:
    Ud = U(r["f"])
    if Ud is None or not r["prior"]: continue
    t = r["t"]
    if t - 1 < W or D.dia[t - 1] != r["d"]: continue
    a = np.fromiter(Ud, int)
    paid = int(int(D.seq[t - 1]) in Ud)
    recs[r["half"]].append((r["d"], r["h"], paid, float(r["y"] in Ud), float(P[r["i"], a].sum())))
correr("R2a_tras_pago_sorteo_anterior (g1=pago, g0=no pago)", recs, dir_="<")

# ---- R2b: perdida ayer (>=2 pagos en d-1 con 12 sorteos)
por_dia = {}
for d, lst in dia_filas.items():
    f = D.fecha[lst[0]]
    por_dia[d] = (f, lst)
recs = [[], []]
for r in rows:
    d1 = r["d"] - 1
    if d1 not in por_dia: continue
    f1, lst = por_dia[d1]
    if len(lst) < 12 or U(f1) is None: continue
    Ud = U(r["f"])
    if Ud is None: continue
    n_pag = sum(int(D.seq[u]) in U(f1) for u in lst)
    a = np.fromiter(Ud, int)
    recs[r["half"]].append((r["d"], r["h"], int(n_pag >= 2), float(r["y"] in Ud), float(P[r["i"], a].sum())))
correr("R2b_perdida_ayer>=2 pagos (g1=perdida ayer)", recs, dir_="<")
npag = [sum(int(D.seq[u]) in U(D.fecha[lst[0]]) for u in lst) for d, (f, lst) in por_dia.items() if D.fecha[lst[0]] <= FIN and len(lst) == 12 and U(D.fecha[lst[0]]) is not None]
log("  distribucion de pagos por dia (0,1,2,3,4+):", [int(sum(1 for x in npag if x == k)) for k in range(4)] + [int(sum(1 for x in npag if x >= 4))])

# ---- R3: lunes vs resto, permutacion dentro de semana
top5 = np.argsort(-P, axis=1)[:, :5]
def r3(metrica, nombre, dir_):
    # por dia: O, E
    od = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        if metrica == "top5":
            m = top5[r["i"]]; o, e = float(r["y"] in m), float(P[r["i"], m].sum())
        else:
            x = feat(r, "F1")
            if x is None: continue
            o, e = x
        od[r["f"]][0] += o; od[r["f"]][1] += e
    semanas = defaultdict(dict)
    for f, v in od.items():
        dt = date.fromisoformat(f); lun = dt - timedelta(days=dt.weekday())
        semanas[lun.isoformat()][dt.weekday()] = v
    comp = sorted(k for k, v in semanas.items() if len(v) == 7)
    A = np.array([[semanas[k][j] for j in range(7)] for k in comp])        # sem x 7 x (O,E)
    half = np.array([0 if k <= CORTE_AB else 1 for k in comp])
    rng = np.random.default_rng(SEM)
    def stat(Ar, js):
        O = Ar[:, :, 0]; E = Ar[:, :, 1]; n = len(Ar); ar = np.arange(n)
        if js.ndim == 1: js = js[None, :]
        o1 = O[ar, js].sum(1); e1 = E[ar, js].sum(1)
        return o1 / e1 - (O.sum() - o1) / (E.sum() - e1)
    out = {}
    for lab, sel in (("total", np.ones(len(comp), bool)), ("A", half == 0), ("B", half == 1)):
        Ar = A[sel]; n = len(Ar)
        obs = stat(Ar, np.zeros(n, int))[0]
        js = rng.integers(0, 7, (20000, n)); nul = stat(Ar, js)
        p = (1 + (np.abs(nul) >= abs(obs)).sum()) / (20001)
        out[lab] = dict(T=float(obs), p=float(p), sem=int(n), oe_lun=float(Ar[:, 0, 0].sum() / Ar[:, 0, 1].sum()),
                        oe_resto=float((Ar[:, 1:, 0].sum()) / Ar[:, 1:, 1].sum()))
    log(f"\n[{nombre}] (semanas completas: {len(comp)})")
    for lab in ("A", "B", "total"):
        o = out[lab]; log(f"  {lab:5s} sem {o['sem']:3d} O/E lunes {o['oe_lun']:.3f} resto {o['oe_resto']:.3f} T {o['T']:+.3f} p_perm {o['p']:.4f}")
    sg = lambda lab: np.sign(out[lab]["T"])
    pasa = (sg("A") == sg("B") == sg("total") and out["A"]["p"] <= .05 and out["B"]["p"] <= .05 and out["total"]["p"] <= .05 / 6
            and ((dir_ == "<" and out["total"]["T"] < 0) or (dir_ == ">" and out["total"]["T"] > 0)))
    log(f"  veredicto: {'PASA' if pasa else 'NO PASA'}")
    out["pasa"] = bool(pasa); RES[nombre] = out
    # descriptivo: serie semanal y autocorrelacion
    ser = A[:, :, 0].sum(1) / A[:, :, 1].sum(1)
    ac = float(np.corrcoef(ser[:-1], ser[1:])[0, 1]); log(f"  descriptivo: O/E semanal media {ser.mean():.3f} sd {ser.std():.3f} (sd esperada Poisson ~{np.mean(1/np.sqrt(A[:,:,1].sum(1))):.3f}), autocorr lag1 {ac:+.3f}")
    out["oe_sem_sd"] = float(ser.std()); out["autocorr"] = ac
r3("top5", "R3a_top5_lunes_vs_resto", "<")
r3("F1", "R3b_ya_salio_hoy_lunes_vs_resto", ">")

log("\n=== Resumen familia (Bonferroni m=6, |z|>=2,64) ===")
for k, v in RES.items():
    log(f"  {k}: {'PASA' if v['pasa'] else 'NO PASA'}")
open(os.path.join(AQUI, "salida.txt"), "w", encoding="utf-8").write("\n".join(SAL))
json.dump(RES, open(os.path.join(AQUI, "resultado.json"), "w"), indent=1, default=float)
