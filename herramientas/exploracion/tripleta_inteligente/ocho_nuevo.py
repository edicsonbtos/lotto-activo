# -*- coding: utf-8 -*-
"""Anexo 6: ¿la regla de las 8:00 cambió de forma? Época nueva 2025-11-01..2026-09-29.
Descubrimiento 2025-11..2026-04, confirmación 2026-05..09. Antes: reentreno/sub.py todo I|S|H (cache).
Uso: python herramientas/exploracion/tripleta_inteligente/ocho_nuevo.py -> salida_ocho_nuevo.txt, ocho_nuevo.json"""
import csv, io, json, os, sys, time
from datetime import date, timedelta
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
RE = os.path.join(RAIZ, "herramientas", "exploracion", "enjambre_2026-09-30", "reentreno"); sys.path.insert(0, RE)
import comun as C  # noqa: E402
LE = C.LE; K = 38; SEM = 20261002; B = 4000; Q = 0.2      # IC 99,6 %
SALIDA = os.path.join(AQUI, "ocho_nuevo.json")
if os.path.exists(SALIDA):
    sys.exit("Ya se corrió (ocho_nuevo.json). No se repite.")
SAL = []; RES = {}
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)
D = LE.cargar(os.path.join(RE, "historial_la.txt")); seq = np.asarray(D.seq); n = len(seq)
LA = {(D.fecha[t], int(D.hora[t])): int(seq[t]) for t in range(n)}
OF = {1: {}, 2: {}, 3: {}}
with io.open(os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["codigo"] in LE.IDX:
            OF[int(r["juego"])][(r["fecha"], int(r["hora"][:2]))] = LE.IDX[r["codigo"]]
# ---- paso 0
comp = [(k, v) for k, v in OF[1].items() if k[1] == 8 and (k[0], 0) in LA]
mal = sum(LA[(k[0], 0)] != v for k, v in comp)
log(f"Paso 0: 8:00 del historial contra la API oficial: {len(comp)} madrugadas, {mal} diferencias")
RES["paso0"] = dict(n=len(comp), diferencias=mal)
if mal > 0.01 * len(comp):
    log("  DATOS NO COINCIDEN: se para."); json.dump(RES, io.open(SALIDA, "w"), indent=1); sys.exit()
def ayer(f):
    return (date.fromisoformat(f) - timedelta(days=1)).isoformat()
fechas = sorted({f for (f, h) in LA if h == 0 and "2025-11-01" <= f <= "2026-09-29"})
desc = [f for f in fechas if f <= "2026-04-30"]; conf = [f for f in fechas if f >= "2026-05-01"]
pdia = {}
for (f, h), a in LA.items():
    pdia.setdefault(f, set()).add(a)
ult = {}
gapd = {}
for t in range(n):
    if D.hora[t] == 0:
        gapd[D.fecha[t]] = {a: (D.dia[t] - ult[a]) if a in ult else 999 for a in range(K)}
    ult[int(seq[t])] = D.dia[t]
def oe(fs, senal, hora=0):
    """senal(f) -> conjunto de animales señalados para el sorteo (f, hora). O/E contra 1/38, IC por jornadas."""
    o = []; e = []
    for f in fs:
        s = senal(f)
        if s is None or (f, hora) not in LA: continue
        o.append(float(LA[(f, hora)] in s)); e.append(len(s) / K)
    o = np.array(o); e = np.array(e)
    if len(o) == 0 or e.sum() == 0: return None
    rng = np.random.default_rng(SEM); i = rng.integers(0, len(o), (B, len(o)))
    bs = o[i].sum(1) / np.maximum(e[i].sum(1), 1e-9)
    return dict(n=len(o), obs=int(o.sum()), esp=round(float(e.sum()), 1), oe=float(o.sum() / e.sum()),
                ic=[float(np.percentile(bs, Q / 2)), float(np.percentile(bs, 100 - Q / 2))])
def S_la(hs):
    return lambda f: {LA[(ayer(f), h)] for h in hs if (ayer(f), h) in LA} or None
def S_of(j, hs):
    return lambda f: {OF[j][(ayer(f), h)] for h in hs if (ayer(f), h) in OF[j]} or None
H = {"H1 LA de anoche (19, 18, 17)": (S_la([11, 10, 9]), 0),
     "H2 RD de anoche (19:30, 18:30)": (S_of(2, [19, 18]), 0),
     "H3 LARD de anoche (21:00, 20:00)": (S_of(3, [21, 20]), 0),
     "H4 animal de las 8:00 de ayer": (S_la([0]), 0),
     "H5 lo de hace 2-3 días": (lambda f: {a for a, g in gapd.get(f, {}).items() if 2 <= g <= 3} or None, 0),
     "H6 número del día": (lambda f: {LE.IDX[str(int(f[8:10]))]}, 0)}
for hh in range(1, 12):
    H[f"H7 'salió ayer' a las {hh+8}:00"] = ((lambda f: pdia.get(ayer(f)) or None), hh)
def veredicto(a, b):
    if a is None or b is None: return "sin datos"
    if not (a["oe"] < 0.80 or a["oe"] > 1.25): return "NO (descubrimiento)"
    mismo = (b["oe"] < 1) == (a["oe"] < 1)
    if mismo and not (b["ic"][0] <= 1 <= b["ic"][1]): return "REAL EN LA ÉPOCA NUEVA"
    return "pista sin confirmar" if mismo else "NO (se invierte)"
log("\nHipótesis (O/E: <1 evita, >1 prefiere)        descubrimiento         confirmación [IC 99,6 %]        veredicto")
for nom, (sen, hora) in H.items():
    fd = desc if hora == 0 else sorted({f for (f, h) in LA if h == hora and "2025-11-01" <= f <= "2026-04-30"})
    fc = conf if hora == 0 else sorted({f for (f, h) in LA if h == hora and "2026-05-01" <= f <= "2026-09-29"})
    a = oe(fd, sen, hora); b = oe(fc, sen, hora); v = veredicto(a, b)
    RES[nom] = dict(descubrimiento=a, confirmacion=b, veredicto=v)
    fa = lambda x: "—" if x is None else f"{x['oe']:.2f} ({x['obs']}/{x['esp']})"
    fb = lambda x: "—" if x is None else f"{x['oe']:.2f} ({x['obs']}/{x['esp']}) [{x['ic'][0]:.2f}; {x['ic'][1]:.2f}]"
    log(f"  {nom:<36} {fa(a):<20} {fb(b):<34} {v}")
# ---- H8: residuo del motor a las 8:00
L = C.cargar_L("todo", ["I", "S", "H"]); P = C.combinar(L, seq[C.ARRANQUE:], LE.W, **C.COMB["base"])
idx = {(D.fecha[t], int(D.hora[t])): t for t in range(n)}
log("\nH8 residuo del motor a las 8:00 (O/E contra lo que esperaba el ensamble)")
for nom, (lo, hi) in (("salió ayer", (1, 1)), ("hace 2-3 días", (2, 3)), ("hace 4+ días", (4, 10**6))):
    out = []
    for fs in (desc, conf):
        o = []; e = []
        for f in fs:
            t = idx[(f, 0)]; g = gapd[f]; sel = [a for a in range(K) if lo <= g[a] <= hi]
            o.append(float(int(seq[t]) in sel)); e.append(float(P[t - LE.W][sel].sum()))
        o = np.array(o); e = np.array(e); rng = np.random.default_rng(SEM); i = rng.integers(0, len(o), (B, len(o)))
        bs = o[i].sum(1) / e[i].sum(1)
        out.append(dict(oe=float(o.sum() / e.sum()), ic=[float(np.percentile(bs, Q / 2)), float(np.percentile(bs, 100 - Q / 2))], obs=int(o.sum()), esp=round(float(e.sum()), 1)))
    v = veredicto(out[0], out[1]); RES[f"H8 {nom}"] = dict(descubrimiento=out[0], confirmacion=out[1], veredicto=v)
    log(f"  {nom:<14} desc {out[0]['oe']:.2f} ({out[0]['obs']}/{out[0]['esp']})  conf {out[1]['oe']:.2f} [{out[1]['ic'][0]:.2f}; {out[1]['ic'][1]:.2f}]  {v}")
# ---- Top-15 de las 8:00 contra el resto, época nueva
pos = {}
for (f, h), t in idx.items():
    if t >= LE.W and "2025-11-01" <= f <= "2026-09-29":
        pos[(f, h)] = int(np.where(np.argsort(-P[t - LE.W], kind="stable") == seq[t])[0][0])
t8 = [p < 15 for (f, h), p in pos.items() if h == 0]; tr = [p < 15 for (f, h), p in pos.items() if h > 0]
log(f"\nTop-15 época nueva: 8:00 {100*np.mean(t8):.1f} % (n={len(t8)})  vs resto de horas {100*np.mean(tr):.1f} % (n={len(tr)})")
for h in range(12):
    x = [p < 15 for (f, hh), p in pos.items() if hh == h]
    log(f"   {h+8:2d}:00  {100*np.mean(x):.1f} %")
RES["top15_8am_vs_resto"] = [float(np.mean(t8)), float(np.mean(tr))]
json.dump(RES, io.open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
io.open(os.path.join(AQUI, "salida_ocho_nuevo.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
with io.open(os.path.join(RAIZ, "herramientas", "registro_final.jsonl"), "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"cuando": time.strftime("%Y-%m-%d %H:%M:%S"), "modelo": "8:00 época nueva (anexo 6), 2025-11..2026-09",
                         "preregistro": "herramientas/exploracion/tripleta_inteligente/PREREGISTRO.md (anexo 6)",
                         "reales": [k for k, v in RES.items() if isinstance(v, dict) and v.get("veredicto") == "REAL EN LA ÉPOCA NUEVA"]},
                        ensure_ascii=False) + "\n")
