# -*- coding: utf-8 -*-
"""Repite ag13 sobre los sorteos en vivo ya jugados (2026-09-26 .. 2026-10-14). EXPLORATORIO, no es la prueba preregistrada:
estos sorteos ya se vieron al armar ag12, la exposición y el factor de pronosticadores (0,862). No cuenta para la decisión.
Reutiliza reconstruir.py (ag12 por sorteo con solo el historial anterior) y experimentos._marcador_ag13 (el mismo código
que correrá en Railway). Solo lectura. Uso: python backtest_ag13.py > salida_backtest_ag13.txt"""
import json, math, os, random, sys
from collections import defaultdict
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "herramientas", "modelos", "ag12"))
sys.path.insert(0, os.path.join(RAIZ, "herramientas", "modelos"))
sys.stdout.reconfigure(encoding="utf-8")
sys.argv = ["reconstruir"]
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):                     # reconstruir.py imprime sus comprobaciones; no las repetimos
    import runpy
    ns = runpy.run_path(os.path.join(AQUI, "reconstruir.py"))
mesa, hist, idx_hist, rd, SOM, EX, EXP, norm, m8 = (ns[k] for k in ("mesa", "hist", "idx_hist", "rd", "SOM", "EX", "EXP", "norm", "m8"))
K, IDX, PAGO = ns["K"], ns["IDX"], ns["PAGO"]

# U del día: lotoven ∪ loteriadehoy, solo Lotto Activo, página de la fecha del día (lo mismo que ag13.conjunto_fuente)
PUB = defaultdict(dict)
for ln in open(os.path.join(AQUI, "..", "pronosticadores", "datos", "publicados.jsonl"), encoding="utf-8"):
    r = json.loads(ln)
    v = r["datos"].get("Lotto Activo") if "error" not in r["datos"] else None
    if v and v.get("fecha_pagina") == r["fecha"]:
        s = {IDX[n] for n in v["nums"] if n in IDX}
        if s:
            PUB[r["fecha"]][r["fuente"]] = s
U = {f: sorted(set().union(*p.values())) for f, p in PUB.items() if set(p) == {"lotoven", "loteriadehoy"}}

res = []
for (f, h), m in sorted(mesa.items()):
    if f < EX.SOMBRA_DESDE or m.get("modelo") != "ensamble_v2" or m.get("vista") != "prob" or (f, h) == ("2026-10-02", 0):
        continue
    pv = [a["prob"] for a in sorted(m["animales"], key=lambda a: a["idx"])]
    ps = norm([pv[i] / m8(f)[i] for i in range(K)]) if (h == 0 and f >= "2026-10-06") else pv
    ag = SOM.corregir(hist[:idx_hist[(f, h)]], f, h, ps)["ag12"]
    reg = {"fecha": f, "hora": h, "salio": m["winner"], "scores": ps, "modelo": "x", "sombra": {"ag12": ag}}
    if f in U:
        reg["pron"] = {"u": U[f]}
    res.append(reg)
print(f"sorteos reconstruidos: {len(res)}; con U (dos fuentes): {sum('pron' in r for r in res)}; días con U: {len(U)}")

EX.AG13_DESDE = "2026-09-26"
FICHAS = [0, 2, 2, 2, 1, 1] + [0] * 33
M = EX._marcador_ag13(res, FICHAS, {k: v for k, v in rd.items()})
print(json.dumps({k: v for k, v in M.items()}, ensure_ascii=False, indent=1))

# ---- plata y puestos, con la regla RD (Top-5 escalonado; Top-15 ponderado), mismos sorteos que M
FX15 = {1: 3, 2: 3, 3: 3, 4: 2, 5: 2, **{k: 1 for k in range(6, 16)}}
mod = EX._modulo_ag13()
filas = []
for r in res:
    if "pron" not in r:
        continue
    f, h, w = r["fecha"], r["hora"], r["salio"]
    q, _ = EX.con_rd(r["sombra"]["ag12"], rd, f, h)
    q_exp, p13, _ = mod.cadena(q, f, h, r["pron"]["u"])
    cod = rd.get((f, h - 1)) if h > 0 else None
    fila = {"f": f}
    for nom, p in (("ensamble", r["scores"]), ("ag12_rd", q), ("ag12_rd_exp", q_exp), ("ag13", p13)):
        o = sorted(range(K), key=lambda i: (-p[i], i))
        o5 = EX.cambiar(o, cod) if cod in IDX else o
        o15 = EX.cambiar15(o, cod) if cod in IDX else o
        fila[nom] = dict(t5=o5.index(w) + 1 <= 5, t15=o15.index(w) + 1 <= 15, pos5=o5.index(w) + 1, pos15=o15.index(w) + 1)
    filas.append(fila)
n = len(filas)
print("\n=== puestos y plata (pago 30, regla RD aplicada), n =", n)
print(f"{'modelo':<14}{'Top-5':>8}{'Top-15':>8}{'neto Top-5 (u)':>16}{'ROI T5':>9}{'neto T15 pond (u)':>19}{'ROI T15':>9}")
for nom in ("ensamble", "ag12_rd", "ag12_rd_exp", "ag13"):
    t5 = sum(x[nom]["t5"] for x in filas); t15 = sum(x[nom]["t15"] for x in filas)
    n5 = sum(30 * {1: 2, 2: 2, 3: 2, 4: 1, 5: 1}.get(x[nom]["pos5"], 0) - 8 for x in filas)
    n15 = sum(30 * FX15.get(x[nom]["pos15"], 0) - 23 for x in filas)
    print(f"{nom:<14}{t5:>8}{t15:>8}{n5:>16}{100 * n5 / (8 * n):>8.1f}%{n15:>19}{100 * n15 / (23 * n):>8.1f}%")

# Δ de plata pareado ag13 − ensamble con IC90 por bootstrap de jornadas
rnd = random.Random(20261015)
def delta5(fs, a, b):
    g = lambda x, k: 30 * {1: 2, 2: 2, 3: 2, 4: 1, 5: 1}.get(x[k]["pos5"], 0) - 8
    return sum(g(x, a) - g(x, b) for x in fs)
def delta15(fs, a, b):
    g = lambda x, k: 30 * FX15.get(x[k]["pos15"], 0) - 23
    return sum(g(x, a) - g(x, b) for x in fs)
J = defaultdict(list)
for x in filas: J[x["f"]].append(x)
J = list(J.values())
for nom, fn in (("Top-5 escalonado (u)", delta5), ("Top-15 ponderado (u)", delta15)):
    est = fn(filas, "ag13", "ensamble"); v = []
    for _ in range(10000):
        s = [x for j in (rnd.choice(J) for _ in J) for x in j]; v.append(fn(s, "ag13", "ensamble"))
    v.sort()
    print(f"Δ ag13 − ensamble, {nom}: {est:+d}  IC90 [{v[500]:+.0f}; {v[9500]:+.0f}]")
