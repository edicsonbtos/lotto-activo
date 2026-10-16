# -*- coding: utf-8 -*-
"""ANEXO 1 de PREREGISTRO_ag13.md: ag13 sobre la réplica 2026 (filas 9357..12510 del historial). Se corre UNA vez.
Solo lee; escribe salida_2026.txt y resultados_2026.json en esta carpeta. Uso: python probar_2026.py"""
import csv, io, json, os, sys
from collections import defaultdict
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
HERR = os.path.join(RAIZ, "herramientas")
AG = os.path.join(HERR, "exploracion", "ag12_2026_2026-10-07")
sys.path.insert(0, HERR); sys.path.insert(0, os.path.join(HERR, "rdint")); sys.path.insert(0, os.path.join(HERR, "modelos"))
import lotto_eval as LE
from datos import ANIMALES, sin_acentos
import exposicion as EXPO
import ag13 as A13

K, D0, B, SEED = 38, 9357, 4000, 20261015
rng = np.random.default_rng(SEED)
SAL = io.open(os.path.join(AQUI, "salida_2026.txt"), "w", encoding="utf-8")
RES = {}


def pr(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.write(s + "\n"); SAL.flush()


# ---------------------------------------------------------------- datos (idéntico a ag12_2026_2026-10-07/analizar.py)
cambios = {c["antes"]: c["despues"] for c in
           json.load(open(os.path.join(HERR, "correccion_historial_2026-09-29.json"), encoding="utf-8"))["cambios"]}
tocados = {k.split()[0] for k in cambios} | {v.split()[0] for v in cambios.values()}
filas = []
for ln in open(os.path.join(AG, "hist_ext.txt"), encoding="utf-8"):
    p = ln.split()
    if len(p) == 3 and p[2] in LE.IDX:
        filas.append((p[0], int(p[1]), LE.IDX[p[2]], cambios.get(" ".join(p), " ".join(p)).split()[0]))
filas.sort(key=lambda r: (r[0], r[1]))
D = LE.cargar(os.path.join(AG, "hist_ext.txt"))
assert len(filas) == len(D) == 12760
fecha_all = np.array([r[3] for r in filas]); hora_all = np.asarray(D.hora); y_all = np.asarray(D.seq)
excl_all = np.array([(f in tocados) or (g in tocados) for f, g in zip(fecha_all, np.array(D.fecha))])
y, fe, ho, ex = y_all[D0:], fecha_all[D0:], hora_all[D0:], excl_all[D0:]
glob = np.arange(D0, len(D))
Pe = np.load(os.path.join(AG, "P_ens_fresco.npy")).astype(float)
Pa = np.load(os.path.join(AG, "P_ag12_V1_fresco.npy")).astype(float)
assert len(Pe) == len(y) == len(Pa)
norm = lambda P: np.clip(P, 1e-9, None) / np.clip(P, 1e-9, None).sum(-1, keepdims=True)

rd = {}
with io.open(os.path.join(RAIZ, "datos_multiloteria", "rdint_hist.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        c = ANIMALES.get(sin_acentos(r["animal"]))
        if c is not None:
            rd[(r["fecha"], int(r["hora"][:2]) - 8)] = LE.IDX[c]
with io.open(os.path.join(AG, "fresco_rd.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        rd[(r["fecha"], int(r["hora"]))] = LE.IDX[r["codigo"]]
rd1 = np.array([rd.get((f, h - 1), -1) if h > 0 else -1 for f, h in zip(fe, ho)])
rd2 = np.array([rd.get((f, h - 2), -1) if h > 1 else -1 for f, h in zip(fe, ho)])

rep = (~ex) & (glob < 12511) & (fe >= "2026-01-01")
idx = np.where(rep)[0]
pr(f"réplica 2026: {len(idx)} sorteos, {len(set(fe[idx]))} jornadas, {min(fe[idx])}..{max(fe[idx])}")

# ---------------------------------------------------------------- U (lotoven ∪ loteriadehoy, Lotto Activo, fecha de la página)
PUB = defaultdict(dict)
for ruta in (os.path.join(AQUI, "publicados_2026.jsonl"), os.path.join(AQUI, "..", "pronosticadores", "datos", "publicados.jsonl")):
    for ln in open(ruta, encoding="utf-8"):
        r = json.loads(ln)
        if "error" in r["datos"]:
            continue
        v = r["datos"].get("Lotto Activo")
        if v and v.get("fecha_pagina") == r["fecha"]:
            s = {LE.IDX[n] for n in v["nums"] if n in LE.IDX}
            if s:
                PUB[r["fecha"]][r["fuente"]] = s
U = {f: sorted(set().union(*p.values())) for f, p in PUB.items() if set(p) == {"lotoven", "loteriadehoy"}}
con_u = np.array([fe[i] in U for i in idx])
dias = sorted(set(fe[idx])); dias_u = [f for f in dias if f in U]
pr(f"días con U (las dos fuentes): {len(dias_u)} de {len(dias)}; sorteos con U: {int(con_u.sum())} de {len(idx)}")
# ---------------------------------------------------------------- cadena por sorteo
MB = {k: [] for k in ("ens", "ag12_rd", "ag12_rd_exp", "ag13", "ag13_nd")}
ORD = {k: [] for k in MB}
O_E = []          # (jornada, o, e) con U
PLAC = {s: [] for s in (7, -7, 14, -14)}
from datetime import date, timedelta
shift = lambda f, d: (date.fromisoformat(f) + timedelta(days=d)).isoformat()
sub = []
for i in idx:
    f, h, w = fe[i], int(ho[i]), y[i]
    if f not in U:
        continue
    sub.append(i)
    q = (Pa[i] / Pa[i].sum()).copy()
    if rd1[i] >= 0: q[rd1[i]] *= 0.50
    if rd2[i] >= 0: q[rd2[i]] *= 0.75
    qe, p13, nd = A13.cadena(list(q), f, h, U[f])
    ps = norm(Pe[i]); q = q / q.sum()
    for k, p in (("ens", ps), ("ag12_rd", q), ("ag12_rd_exp", np.array(qe)), ("ag13", np.array(p13)), ("ag13_nd", np.array(nd))):
        p = np.asarray(p, float); p = p / p.sum()
        MB[k].append(1000 * np.log2(max(p[w], 1e-12) * K))
        ORD[k].append(np.lexsort((np.arange(K), -p)))
    O_E.append((f, int(w in U[f]), float(sum(qe[j] for j in U[f]))))
    for dd in PLAC:
        g = shift(f, dd)
        if g in U:
            PLAC[dd].append((f, int(w in U[g]), float(sum(qe[j] for j in U[g]))))
sub = np.array(sub)
MB = {k: np.array(v) for k, v in MB.items()}
jid = {f: j for j, f in enumerate(sorted(set(fe[sub])))}
J = np.array([jid[f] for f in fe[sub]]); nJ = len(jid)


def boot_mean(v, mask=None, alpha=(0.05, 0.025)):
    """media de v con IC por bootstrap de jornadas (bloques); mask = filas incluidas."""
    m = np.ones(len(v), bool) if mask is None else mask
    S = np.bincount(J[m], weights=v[m], minlength=nJ); N = np.bincount(J[m], minlength=nJ).astype(float)
    keep = N > 0; S, N = S[keep], N[keep]
    est = S.sum() / N.sum(); jj = len(S)
    sel = rng.integers(0, jj, size=(B, jj))
    bm = S[sel].sum(1) / N[sel].sum(1)
    q = lambda a: float(np.quantile(bm, a))
    return dict(media=round(est, 2), n=int(N.sum()), jornadas=int(jj), ic90=[round(q(.05), 2), round(q(.95), 2)],
                ic95=[round(q(.025), 2), round(q(.975), 2)])


def oe(rows):
    por = defaultdict(lambda: [0, 0.0])
    for f, o, e in rows:
        por[f][0] += o; por[f][1] += e
    fs = sorted(por); Ob = np.array([por[f][0] for f in fs], float); Eb = np.array([por[f][1] for f in fs])
    R = Ob.sum() / Eb.sum(); sel = rng.integers(0, len(fs), size=(B, len(fs)))
    bm = Ob[sel].sum(1) / Eb[sel].sum(1)
    return dict(O=int(Ob.sum()), E=round(float(Eb.sum()), 1), oe=round(float(R), 3),
                ic95=[round(float(np.quantile(bm, .025)), 3), round(float(np.quantile(bm, .975)), 3)], jornadas=len(fs))


def dif(a, b, mask=None):
    return boot_mean(MB[a] - MB[b], mask)


pr("\n=== M1 / M2: Δ mbits por sorteo (IC por bloques de jornada) ===")
trim = {"T1 ene-mar": ("2026-01-01", "2026-03-31"), "T2 abr-jun": ("2026-04-01", "2026-06-30"), "T3 jul-sep16": ("2026-07-01", "2026-09-16")}
for nom, a, b in (("M1  ag13 − ensamble", "ag13", "ens"), ("M2  ag13 − ag12_rd_exp (pronosticadores)", "ag13", "ag12_rd_exp"),
                  ("    ag12_rd_exp − ag12_rd (exposición)", "ag12_rd_exp", "ag12_rd"), ("    ag12_rd − ensamble (ag12 + RD)", "ag12_rd", "ens"),
                  ("    ag13_nd − ag12_rd_exp (diagnóstico)", "ag13_nd", "ag12_rd_exp")):
    r = dif(a, b); RES[nom.strip()] = r
    pr(f"{nom:<46} {r['media']:+7.2f}  IC90 {r['ic90']}  IC95 {r['ic95']}  (n={r['n']}, jornadas={r['jornadas']})")
pr("\nPor trimestre (M1 y M2):")
for t, (a, b) in trim.items():
    m = np.array([a <= f <= b for f in fe[sub]])
    r1, r2 = dif("ag13", "ens", m), dif("ag13", "ag12_rd_exp", m)
    RES["trim " + t] = {"M1": r1, "M2": r2}
    pr(f"  {t:<14} M1 {r1['media']:+7.2f} IC90 {r1['ic90']}   M2 {r2['media']:+7.2f} IC90 {r2['ic90']}  n={r1['n']}")

pr("\n=== M3: O/E de U contra ag12_rd_exp (menos de 1 = el operador los esquiva) ===")
r = oe(O_E); RES["M3"] = r
pr(f"  real:    O/E {r['oe']}  IC95 {r['ic95']}  (O={r['O']}, E={r['E']}, jornadas={r['jornadas']})")
for dd, rows in PLAC.items():
    r = oe(rows); RES[f"placebo {dd:+d}"] = r
    pr(f"  placebo d{dd:+d}: O/E {r['oe']}  IC95 {r['ic95']}  (E={r['E']})")

# ---------------------------------------------------------------- M4: puestos y retorno por ficha con la regla RD
F5 = np.zeros(40); F5[1:6] = [2, 2, 2, 1, 1]
FP = np.zeros(40); FP[1:6] = [3, 3, 3, 2, 2]; FP[6:16] = 1


def pos(orden, w, c, tope):
    o = list(orden)
    if c >= 0 and c in o[:tope]:
        o = [x for x in o[:tope] if x != c] + [o[tope], c] + o[tope + 1:]
    return o.index(w) + 1


pr("\n=== M4: aciertos y retorno por ficha (pago 30, con la regla RD de Top-5 / Top-15), mismos sorteos ===")
w_ = y[sub]
tabla = {}
for k in ("ens", "ag12_rd", "ag12_rd_exp", "ag13"):
    p5 = np.array([pos(ORD[k][j], w_[j], rd1[sub[j]], 5) for j in range(len(sub))])
    p15 = np.array([pos(ORD[k][j], w_[j], rd1[sub[j]], 15) for j in range(len(sub))])
    raw = np.array([ORD[k][j].tolist().index(w_[j]) + 1 for j in range(len(sub))])
    r5 = 100 * (30 * F5[np.minimum(p5, 39)] - F5.sum()) / F5.sum()
    r15 = 100 * (30 * FP[np.minimum(p15, 39)] - FP.sum()) / FP.sum()
    tabla[k] = (r5, r15)
    pr(f"  {k:<12} Top-3 {100 * (raw <= 3).mean():5.2f}%  Top-5 {100 * (raw <= 5).mean():5.2f}%  Top-15 {100 * (raw <= 15).mean():5.2f}%   "
       f"retorno Top-5 esc. {r5.mean():+6.1f} pp/ficha   Top-15 pond. {r15.mean():+6.1f}")
for nom, ia in (("Top-5 escalonado", 0), ("Top-15 ponderado", 1)):
    for a, b in (("ag13", "ens"), ("ag13", "ag12_rd_exp")):
        r = boot_mean(tabla[a][ia] - tabla[b][ia]); RES[f"M4 {nom} {a}-{b}"] = r
        pr(f"  Δ {a} − {b}, {nom}: {r['media']:+6.2f} pp/ficha  IC90 {r['ic90']}  IC95 {r['ic95']}")

# ---------------------------------------------------------------- veredicto con las reglas del anexo
m1, m2, m3 = RES["M1  ag13 − ensamble"], RES["M2  ag13 − ag12_rd_exp (pronosticadores)"], RES["M3"]
t_ok = all(RES["trim " + t]["M1"]["media"] > 0 for t in trim)
t5 = RES["M4 Top-5 escalonado ag13-ens"]["media"]
pr("\n=== VEREDICTO (reglas del anexo, escritas antes) ===")
pron_pasa = m2["ic90"][0] > 0 and m3["ic95"][1] < 1
pron_no = m2["ic90"][1] < 0 or m3["oe"] >= 1
pr("pronosticadores:", "PASA" if pron_pasa else "NO PASA" if pron_no else "NO CONCLUYENTE",
   f"(M2 IC90 inf {m2['ic90'][0]:+.2f}; M3 O/E {m3['oe']} IC95 sup {m3['ic95'][1]})")
ag13_pasa = m1["ic90"][0] > 0 and t5 >= -3 and t_ok
ag13_no = m1["ic90"][1] < 0 or m1["ic90"][0] <= 0
pr("ag13 global:", "PASA" if ag13_pasa else "NO PASA" if ag13_no else "NO CONCLUYENTE",
   f"(M1 IC90 inf {m1['ic90'][0]:+.2f}; Top-5 pp/ficha {t5:+.2f}; tres trimestres >0: {t_ok})")
json.dump(RES, open(os.path.join(AQUI, "resultados_2026.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
