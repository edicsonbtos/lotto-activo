# -*- coding: utf-8 -*-
"""Reconstruye por sorteo el pronóstico de ag12 en sombra (lo que producción congeló y no expone por sorteo)
a partir de: congelado del ensamble (/api/mesa, bajado en mesa/<offset>.json), historial de LA anterior a
cada sorteo (hist_ext.txt hasta 2026-10-07 h4 + ganadores de la mesa) y RD (fresco_rd.csv + rd_scrape.txt +
/api/rdint 'ultimos'). Comprueba que reproduce /api/sombra y /api/sombra_decision. Solo lectura.
Salida: reg.json (una fila por sorteo con puestos y mbits de cada modelo)."""
import json, math, os, sys, glob
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "herramientas", "modelos", "ag12"))
sys.path.insert(0, os.path.join(RAIZ, "herramientas", "modelos"))
from comun import IDX, K, POS, PAGO
import experimentos as EX
import sombra as SOM
import exposicion as EXP

AG = os.path.join(RAIZ, "herramientas", "exploracion", "ag12_2026_2026-10-07")

# ---------- mesa (congelados del vivo)
mesa = {}
for fn in glob.glob(os.path.join(AQUI, "mesa", "*.json")):
    m = json.load(open(fn, encoding="utf-8"))
    if m.get("winner") is None:
        continue
    mesa[(m["fecha"], m["hora"])] = m
print("mesa:", len(mesa), min(mesa), max(mesa))

# ---------- historial LA
hist = []
for ln in open(os.path.join(AG, "hist_ext.txt"), encoding="utf-8"):
    p = ln.split()
    if len(p) == 3 and p[2] in IDX:
        hist.append((p[0], int(p[1]), IDX[p[2]]))
hist.sort(key=lambda r: (r[0], r[1]))
ult = (hist[-1][0], hist[-1][1])
# coherencia hist_ext vs mesa en el solape
dif = [(k, hist_v, mesa[k]["winner"]) for (f, h, hist_v) in hist for k in [(f, h)] if k in mesa and mesa[k]["winner"] != hist_v]
solape = sum(1 for (f, h, v) in hist if (f, h) in mesa)
print("solape hist_ext/mesa:", solape, "discrepancias:", dif[:5])
extra = sorted((k, m["winner"]) for k, m in mesa.items() if k > ult)
hist += [(f, h, v) for (f, h), v in extra]
# huecos tras hist_ext
from datetime import date, timedelta
d0 = date.fromisoformat(ult[0]); faltan = []
for k in range(0, 9):
    f = (d0 + timedelta(days=k)).isoformat()
    for h in range(12):
        if ult < (f, h) <= max(mesa) and (f, h) not in mesa:
            faltan.append((f, h))
print("huecos tras hist_ext (sin ganador en mesa):", faltan)
idx_hist = {(f, h): i for i, (f, h, v) in enumerate(hist)}

# ---------- RD
rd = {}
for ln in open(os.path.join(AG, "fresco_rd.csv"), encoding="utf-8").read().splitlines()[1:]:
    f, h, c = ln.split(","); rd[(f, int(h))] = c
for ln in open(os.path.join(AQUI, "rd_scrape.txt"), encoding="utf-8"):
    f, h, c = ln.split(); rd[(f, int(h))] = c
for f, h, c in json.load(open(os.path.join(AQUI, "rdint.json"), encoding="utf-8"))["ultimos"]:
    rd[(f, int(h))] = c
print("RD slots:", len(rd), min(rd), max(rd))

# multiplicadores de la corrección de las 8:00 (encendida 2026-10-06): p_vivo ∝ p_sin8 · m8
def m8(f):
    return EXP.aplicar_8am([1.0] * K, f, 0)

def norm(p):
    s = sum(p); return [x / s for x in p]

def puesto(p, w):
    return sorted(range(K), key=lambda i: (-p[i], i)).index(w) + 1

FX5 = {1: 2, 2: 2, 3: 2, 4: 1, 5: 1}
FX15 = {**{1: 3, 2: 3, 3: 3, 4: 2, 5: 2}, **{r: 1 for r in range(6, 16)}}
def f5(r): return FX5.get(r, 0)
def f15(r): return FX15.get(r, 0)

reg = []
for (f, h), m in sorted(mesa.items()):
    if f < EX.SOMBRA_DESDE or m.get("modelo") != "ensamble_v2" or m.get("vista") != "prob":
        continue
    pv = [a["prob"] for a in sorted(m["animales"], key=lambda a: a["idx"])]
    rank_vivo = {a["idx"]: a["rank"] for a in m["animales"]}
    orden_vivo = sorted(range(K), key=lambda i: rank_vivo[i])
    if h == 0 and f >= "2026-10-06":
        mm = m8(f); ps = norm([pv[i] / mm[i] for i in range(K)])
    else:
        ps = pv
    n = idx_hist[(f, h)]
    filas = hist[:n]                      # SOLO lo anterior al sorteo
    assert filas[-1][:2] < (f, h)
    ag = SOM.corregir(filas, f, h, ps)["ag12"]
    q, usado = EX.con_rd(ag, rd, f, h)
    w = m["winner"]
    cod = rd.get((f, h - 1)) if h > 0 else None
    def pos15(orden):  # regla RD en Top-15 aplicada a un orden
        o = EX.cambiar15(orden, cod) if cod in IDX else orden
        return o.index(w) + 1
    def pos5(orden):
        o = EX.cambiar(orden, cod) if cod in IDX else orden
        return o.index(w) + 1
    orden_ens = sorted(range(K), key=lambda i: (-ps[i], i))
    orden_ag = sorted(range(K), key=lambda i: (-ag[i], i))
    orden_q = sorted(range(K), key=lambda i: (-q[i], i))
    ex_ens = EXP.aplicar(ps, f, h)
    reg.append(dict(f=f, h=h, w=w, rd_prev=cod,
        r_vivo=rank_vivo[w], r_vivo_rd5=pos5(orden_vivo), r_vivo_rd15=pos15(orden_vivo),
        r_ens=orden_ens.index(w) + 1, r_ens_rd15=pos15(orden_ens),
        r_ag=orden_ag.index(w) + 1, r_ag_rd15=pos15(orden_ag), r_agrd=orden_q.index(w) + 1,
        mb_vivo=1000 * math.log2(pv[w] * K), mb_ens=1000 * math.log2(ps[w] * K),
        mb_ag=1000 * math.log2(ag[w] / sum(ag) * K), mb_agrd=1000 * math.log2(q[w] / sum(q) * K),
        mb_ensexp=(1000 * math.log2(ex_ens[w] * K) if f >= EX.SOMBRA_EXP_DESDE else None),
        r_ensexp=puesto(ex_ens, w), r_agrdexp=puesto(EXP.aplicar(q, f, h), w),
        mb_agrdexp=1000 * math.log2(EXP.aplicar(q, f, h)[w] * K),
        empate_ens=sum(1 for i in range(K) if ps[i] == ps[w]) - 1,
        empate_ag=sum(1 for i in range(K) if ag[i] == ag[w]) - 1))
json.dump(reg, open(os.path.join(AQUI, "reg.json"), "w"), indent=0)

# ---------- comprobación contra /api/sombra y /api/sombra_decision
S = json.load(open(os.path.join(AQUI, "sombra.json"), encoding="utf-8"))["marcador"]
def resumen(rk, mb):
    n = len(reg)
    return dict(n=n, top3=sum(r[rk] <= 3 for r in reg), top5=sum(r[rk] <= 5 for r in reg), top15=sum(r[rk] <= 15 for r in reg),
                mbits=round(sum(r[mb] for r in reg) / n, 1), t5_neto=sum(PAGO * f5(r[rk]) - 8 for r in reg))
for nom, rk, mb in (("ensamble", "r_ens", "mb_ens"), ("ag12", "r_ag", "mb_ag"), ("ag12_rd", "r_agrd", "mb_agrd")):
    print(nom, "reconstruido:", resumen(rk, mb)); print(nom, "producción:  ", {k: S[nom][k] for k in ("n", "top3", "top5", "top15", "mbits", "t5_neto")})
print("vivo (con 8am):", resumen("r_vivo", "mb_vivo"))
dm = [(r["f"], r["mb_ag"] - r["mb_ens"]) for r in reg]
print("dmbits decision:", EX.ic90_jornadas(dm))
print("empates en el puesto del ganador: ens", sum(r["empate_ens"] > 0 for r in reg), "ag12", sum(r["empate_ag"] > 0 for r in reg))
