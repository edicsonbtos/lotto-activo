# -*- coding: utf-8 -*-
"""ag1: ciclo semanal (S1..S5). Uso: python semanal.py dev | rd  (ver PREREGISTRO.md)"""
import sys, os, csv, json, ast, re, unicodedata
from datetime import date, timedelta
from collections import defaultdict
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE
rng = np.random.default_rng(20261023)
R = 2000
modo = sys.argv[1] if len(sys.argv) > 1 else "dev"

def cargar_juego():
    """-> filas ordenadas [(fecha, slot, codigo)], indices de desarrollo, funcion P(fila)"""
    if modo == "dev":
        D = LE.cargar(os.path.join(RAIZ, "verificacion/hilo9/datos/historial.txt"))
        c = np.load(os.path.join(RAIZ, "verificacion/hilo9/datos/calor_cache.npz"))
        P = c["P"]; P = P / P.sum(1, keepdims=True); y = c["y"]
        assert (D.seq[2000:2000 + len(y)] == y).all()
        filas = [(D.fecha[t], int(D.hora[t]), int(D.seq[t])) for t in range(9357)]
        dev = list(range(2000, 9357))
        return filas, dev, (lambda t, vistos: P[t - 2000])
    sys.path.insert(0, RAIZ)
    sys.path.insert(0, os.path.join(RAIZ, "investigacion/2026-10-22/bateria")); from rasgos import IDX
    src = open(os.path.join(RAIZ, "rdint_vivo.py"), encoding="utf-8").read()
    NOMBRE = ast.literal_eval(re.search(r"^NOMBRE = (\{.*?\})", src, re.S | re.M).group(1))
    norm = lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().lower().strip()
    inv = {norm(v): k for k, v in NOMBRE.items()}
    rows = []
    for r in csv.DictReader(open(os.path.join(RAIZ, "datos_multiloteria/rdint_hist.csv"), encoding="utf-8")):
        c = inv.get(norm(r["animal"]))
        if c is None: continue
        rows.append((r["fecha"], int(r["hora"][:2]) - 7, IDX[c]))   # 08:30 -> slot 1
    rows.sort()
    dev = [i for i, f in enumerate(rows) if "2024-03-01" <= f[0] <= "2025-06-30"]
    def pf(t, vistos):
        p = np.ones(38)
        for c in vistos: p[c] = 0
        return p / p.sum()
    return rows, dev, pf

filas, dev, pfun = cargar_juego()
n = len(filas)
fe = [date.fromisoformat(f[0]) for f in filas]
por_dia = defaultdict(dict)
for (f, s, c) in filas: por_dia[f][s] = c

def semana_id(d, inicio):   # inicio 'L' o 'D'
    dd = d + timedelta(days=1) if inicio == "D" else d
    a = dd.isocalendar(); return (a[0], a[1])
def pos_dia(d, inicio):
    return d.weekday() + 1 if inicio == "L" else (d.weekday() + 1) % 7 + 1

# recorrido cronologico: vistos del dia y de la semana (antes de cada fila)
vistos_dia = [None] * n; vistos_sem = {"L": [None] * n, "D": [None] * n}
cur_d = None; sd = set(); sw = {}
for t in range(n):
    if filas[t][0] != cur_d: cur_d = filas[t][0]; sd = set()
    vistos_dia[t] = frozenset(sd)
    for ini in "LD":
        wid = semana_id(fe[t], ini)
        if sw.get((ini, "id")) != wid and ini == "L": pass
    sd.add(filas[t][2])
for ini in "LD":
    cur = None; s = set()
    for t in range(n):
        wid = semana_id(fe[t], ini)
        if wid != cur: cur = wid; s = set()
        vistos_sem[ini][t] = frozenset(s); s.add(filas[t][2])

def dato(d, s):
    return por_dia.get(d.isoformat(), {}).get(s)

# ----- construir registros por hipotesis: (dia_idx, hora, obs, e, v, pos)
reg = defaultdict(list)
for t in dev:
    f, s, c = filas[t]; d = fe[t]
    p = pfun(t, vistos_dia[t])
    def add(k, mask, pos=0):
        e = float(p[list(mask)].sum()) if len(mask) else 0.0
        reg[k].append((f, s, float(c in mask), e, e * (1 - e), pos))
    for k, lag in (("S1", 7), ("S2", 14)):
        x = dato(d - timedelta(days=lag), s)
        if x is not None: add(k, {x})
    dd = por_dia.get((d - timedelta(days=7)).isoformat())
    if dd: add("S3", set(dd.values()))
    for k, ini in (("S4a", "L"), ("S4b", "D")):
        libres = set(range(38)) - vistos_sem[ini][t]
        add(k, libres, pos_dia(d, ini))

dias = sorted({f[0] for f in filas[i] and [filas[i]] for i in dev}) if False else sorted({filas[i][0] for i in dev})
corte = dias[len(dias) // 2]

def resumen(sel):
    o = sum(r[2] for r in sel); e = sum(r[3] for r in sel); v = sum(r[4] for r in sel)
    return o, e, (o / e if e else float("nan")), ((o - e) / np.sqrt(v) if v else 0.0)
def boot(sel, B=2000):
    por = defaultdict(lambda: [0.0, 0.0])
    for r in sel: por[r[0]][0] += r[2]; por[r[0]][1] += r[3]
    a = np.array(list(por.values())); m = len(a); q = []
    for _ in range(B):
        s = a[rng.integers(0, m, m)].sum(0); q.append(s[0] / s[1])
    return np.percentile(q, [2.5, 97.5])
def tendencia(sel):
    por_h = defaultdict(list)
    for r in sel: por_h[r[1]].append(r)
    num = den = 0.0
    for h, rs in por_h.items():
        pm = np.mean([r[5] for r in rs])
        for r in rs:
            c = r[5] - pm; num += (r[2] - r[3]) * c; den += r[4] * c * c
    return num / np.sqrt(den)

out = {}
UMBRAL = 2.64
def veredicto(a, b, t): return bool(np.sign(a) == np.sign(b) and abs(a) >= 2 and abs(b) >= 2 and abs(t) >= UMBRAL)

print(f"modo={modo}  filas={len(dev)}  corte={corte}")
for k in ("S1", "S2", "S3", "S4a", "S4b"):
    s = reg[k]; A = [r for r in s if r[0] < corte]; B = [r for r in s if r[0] >= corte]
    rA, rB, rT = resumen(A), resumen(B), resumen(s); ic = boot(s)
    if k.startswith("S4"):
        zA, zB, zT = tendencia(A), tendencia(B), tendencia(s)
        terc = {}
        for nom, lo, hi in (("d1-2", 1, 2), ("d3-5", 3, 5), ("d6-7", 6, 7)):
            ss = [r for r in s if lo <= r[5] <= hi]; q = resumen(ss); terc[nom] = dict(n=len(ss), obs=q[0], esp=q[1], OE=q[2], z=q[3])
        out[k] = dict(zA=zA, zB=zB, zT=zT, OE=rT[2], ic=list(ic), tercios=terc, pasa=veredicto(zA, zB, zT))
        print(f"{k}: tendencia z A {zA:+.2f} B {zB:+.2f} T {zT:+.2f}  O/E total {rT[2]:.3f} [{ic[0]:.3f};{ic[1]:.3f}]  PASA={out[k]['pasa']}")
        for nom, v in terc.items(): print(f"    {nom}: n={v['n']} obs={v['obs']:.0f} esp={v['esp']:.1f} O/E={v['OE']:.3f} z={v['z']:+.2f}")
    else:
        out[k] = dict(n=len(s), obs=rT[0], esp=rT[1], OE=rT[2], ic=list(ic), OE_A=rA[2], zA=rA[3], OE_B=rB[2], zB=rB[3], zT=rT[3], pasa=veredicto(rA[3], rB[3], rT[3]))
        print(f"{k}: n={len(s)} obs={rT[0]:.0f} esp={rT[1]:.1f} O/E {rT[2]:.3f} [{ic[0]:.3f};{ic[1]:.3f}] zT {rT[3]:+.2f} | A {rA[2]:.3f} z{rA[3]:+.2f} | B {rB[2]:.3f} z{rB[3]:+.2f}  PASA={out[k]['pasa']}")
# descriptivo por hora de S1 y S2
for k in ("S1", "S2"):
    print(f"  {k} por hora (desc.):", " ".join(f"{h}:{resumen([r for r in reg[k] if r[1]==h])[2]:.2f}" for h in sorted({r[1] for r in reg[k]})))

# ----- S5 cobertura semanal
devset = set(dev); semanas = defaultdict(list)
for t in dev: semanas[semana_id(fe[t], "L")].append(t)
completas = {w for w, ts in semanas.items() if len(ts) == 84}
wlist = sorted(completas); wmed = wlist[len(wlist) // 2]
obs_w = {w: len({filas[t][2] for t in semanas[w]}) for w in wlist}
def sim(plain=False):
    cnt = {w: np.zeros(R) for w in wlist}
    seen_w = np.zeros((R, 38), bool); seen_d = np.zeros((R, 38), bool)
    cur_d = None; cur_w = None
    for t in dev:
        if filas[t][0] != cur_d: cur_d = filas[t][0]; seen_d[:] = False
        w = semana_id(fe[t], "L")
        if w != cur_w:
            if cur_w in cnt: cnt[cur_w] = seen_w.sum(1).astype(float)
            cur_w = w; seen_w[:] = False
        p = pfun(t, vistos_dia[t])
        pr = np.broadcast_to(p, (R, 38)).copy()
        if not plain: pr[seen_d] = 0
        cs = pr.cumsum(1); u = rng.random(R)[:, None] * cs[:, -1:]
        x = np.minimum((cs < u).sum(1), 37)
        seen_d[np.arange(R), x] = True; seen_w[np.arange(R), x] = True
    if cur_w in cnt: cnt[cur_w] = seen_w.sum(1).astype(float)
    return cnt
def z5(ws, cnt):
    o = np.mean([obs_w[w] for w in ws]); sm = np.mean([cnt[w] for w in ws], axis=0)
    return o, sm.mean(), (o - sm.mean()) / sm.std()
for nom, plain in (("S5", False), ("S5_plano(desc.)", True)):
    cnt = sim(plain); wa = [w for w in wlist if w < wmed]; wb = [w for w in wlist if w >= wmed]
    a, b, t = z5(wa, cnt), z5(wb, cnt), z5(wlist, cnt)
    out[nom] = dict(semanas=len(wlist), obs=t[0], sim=t[1], zT=t[2], obsA=a[0], simA=a[1], zA=a[2], obsB=b[0], simB=b[1], zB=b[2],
                    pasa=veredicto(a[2], b[2], t[2]) if not plain else None)
    print(f"{nom}: semanas={len(wlist)} obs {t[0]:.2f} sim {t[1]:.2f} z {t[2]:+.2f} | A {a[0]:.2f} vs {a[1]:.2f} z{a[2]:+.2f} | B {b[0]:.2f} vs {b[1]:.2f} z{b[2]:+.2f}")
json.dump(out, open(os.path.join(AQUI, f"salida_{modo}.json"), "w"), indent=1, default=float)
