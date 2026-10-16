# -*- coding: utf-8 -*-
"""EXPLORATORIO (después de la prueba preregistrada): controles para entender el O/E < 1 de los datos.
Uso: python explorar.py -> salida_explorar.txt, explorar.json"""
import contextlib, io, json, os, runpy
from datetime import date, timedelta
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path(os.path.join(AQUI, "analizar.py"))
LE, PUB, medir, piramide, confusores = G["LE"], G["PUB"], G["medir"], G["piramide"], G["confusores"]
P, Y, H, F, DIA, SEL = G["P"], G["Y"], G["H"], G["F"], G["DIA"], G["SEL"]
orig = G["conjunto"]
SAL, RES = [], {}


def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)


def corr(f, k):
    return (date.fromisoformat(f) + timedelta(days=k)).isoformat()


def pares_piramide(fecha):
    a, m, d = fecha.split("-")
    filas = [[int(c) for c in d + m + a]]
    while len(filas[-1]) > 2:
        f = filas[-1]; filas.append([(f[i] + f[i + 1]) % 10 for i in range(len(f) - 1)])
    return {LE.IDX[str(10 * f[i] + f[i + 1])] for f in filas for i in range(len(f) - 1) if 10 * f[i] + f[i + 1] <= 36}


def fecha_derivados(fecha):
    d = int(fecha[8:10]); m = int(fecha[5:7])
    s = {LE.IDX[str(x)] for x in (d - 1, d, d + 1, d + 2, m) if 0 <= x <= 36}
    return s | piramide(fecha) | pares_piramide(fecha)


VARIANTES = {
    "U": lambda j, f, h: orig(j, f, "U"),
    "placebo U(d-7)": lambda j, f, h: orig(j, corr(f, -7), "U"),
    "placebo U(d+7)": lambda j, f, h: orig(j, corr(f, 7), "U"),
    "placebo U(d-14)": lambda j, f, h: orig(j, corr(f, -14), "U"),
    "placebo U(d+14)": lambda j, f, h: orig(j, corr(f, 14), "U"),
    "U sin nada derivado de la fecha ni hora": lambda j, f, h: (orig(j, f, "U") or set()) - fecha_derivados(f) - confusores(f, h) or None,
    "U ∩ derivados de la fecha": lambda j, f, h: (orig(j, f, "U") or set()) & fecha_derivados(f) or None,
    "derivados de la fecha (todos)": lambda j, f, h: fecha_derivados(f),
    "derivados de la fecha fuera de U": lambda j, f, h: fecha_derivados(f) - (orig(j, f, "U") or set()) or None,
}


def correr(nom, P_, Y_, H_, F_, D_, juego="LA", mult=None):
    fn = VARIANTES[nom]
    # recombinar con bootstrap por días común: recalcular directamente
    o = e = 0.0; od = {}; ed = {}
    for h in np.unique(H_):
        s = np.where(H_ == h)[0]
        for t in s:
            A = fn(juego, F_[t], h)
            if not A:
                continue
            a = np.fromiter(A, int)
            od[D_[t]] = od.get(D_[t], 0) + float(Y_[t] in A); ed[D_[t]] = ed.get(D_[t], 0) + float(P_[t, a].sum())
    k = sorted(od); so = np.array([od[x] for x in k]); se = np.array([ed[x] for x in k])
    rng = np.random.default_rng(20261014); idx = rng.integers(0, len(k), (4000, len(k)))
    bs = so[idx].sum(1) / se[idx].sum(1)
    r = dict(obs=int(so.sum()), esp=round(float(se.sum()), 1), oe=round(float(so.sum() / se.sum()), 3),
             ic95=[round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)])
    return r


def mostrar(et, r):
    log(f"  {et}: obs {r['obs']} esp {r['esp']} O/E {r['oe']:.3f} [IC95 {r['ic95'][0]:.2f}; {r['ic95'][1]:.2f}]")


for tramo, s in SEL.items():
    log(f"\n== LA {tramo}")
    for nom in VARIANTES:
        RES[f"{tramo}|{nom}"] = r = correr(nom, P[s], Y[s], H[s], F[s], DIA[s]); mostrar(nom, r)

# vivo
import json as _j
filas = [_j.loads(l) for l in open(os.path.join(AQUI, "datos", "mesa.jsonl"), encoding="utf-8")]
filas = sorted([f for f in filas if f["winner_num"] in LE.IDX and f["fecha"] >= "2026-09-15"
                and all(v is not None for v in f["prob"].values())], key=lambda f: (f["fecha"], f["hora"]))
PM = np.array([[f["prob"][n] for n in LE.POS] for f in filas]); PM /= PM.sum(1, keepdims=True)
YM = np.array([LE.IDX[f["winner_num"]] for f in filas]); HM = np.array([f["hora"] for f in filas])
FM = np.array([f["fecha"] for f in filas]); DM = np.unique(FM, return_inverse=True)[1]
log("\n== LA vivo")
for nom in ("U", "U sin nada derivado de la fecha ni hora", "derivados de la fecha (todos)"):
    RES[f"vivo|{nom}"] = r = correr(nom, PM, YM, HM, FM, DM); mostrar(nom, r)

# por trimestres (dev + conf1)
log("\n== U por trimestre (dev + confirmación 1)")
s_all = SEL["desarrollo"] | SEL["confirmacion1"]
trim = np.array([f[:4] + "T" + str((int(f[5:7]) - 1) // 3 + 1) for f in F])
for q in sorted(set(trim[s_all])):
    s = s_all & (trim == q)
    r = correr("U", P[s], Y[s], H[s], F[s], DIA[s]); r2 = correr("U sin nada derivado de la fecha ni hora", P[s], Y[s], H[s], F[s], DIA[s])
    log(f"  {q}: U O/E {r['oe']:.2f} [{r['ic95'][0]:.2f}; {r['ic95'][1]:.2f}] (obs {r['obs']}, esp {r['esp']})"
        f" | U sin fecha {r2['oe']:.2f} [{r2['ic95'][0]:.2f}; {r2['ic95'][1]:.2f}]")
    RES[f"trim|{q}"] = [r, r2]


# explotar: x ajustado en confirmación 1 (U sin derivados de fecha), aplicado al vivo (único tramo no visto)
def mbits(P_, Y_, H_, F_, D_, nom, x):
    g = []; dd = []
    for t in range(len(Y_)):
        A = VARIANTES[nom]("LA", F_[t], H_[t])
        if not A:
            g.append(0.0); dd.append(D_[t]); continue
        a = np.fromiter(A, int); q = P_[t].copy(); q[a] *= x; q /= q.sum()
        g.append(1000 * np.log2(q[Y_[t]] / P_[t, Y_[t]])); dd.append(D_[t])
    g = np.array(g); dd = np.array(dd)
    u, gi = np.unique(dd, return_inverse=True); sg = np.bincount(gi, g); n = np.bincount(gi)
    rng = np.random.default_rng(20261014); idx = rng.integers(0, len(u), (4000, len(u)))
    b = sg[idx].sum(1) / n[idx].sum(1)
    return round(float(g.mean()), 2), [round(float(np.percentile(b, 2.5)), 2), round(float(np.percentile(b, 97.5)), 2)]


log("\n== Explotar (exploratorio): x de confirmación 1 aplicado al vivo y a la propia confirmación 1")
for nom in ("U", "U sin nada derivado de la fecha ni hora"):
    x = RES[f"confirmacion1|{nom}"]["oe"]
    s = SEL["confirmacion1"]
    m1 = mbits(P[s], Y[s], H[s], F[s], DIA[s], nom, x)
    mv = mbits(PM, YM, HM, FM, DM, nom, x)
    log(f"  {nom}: x={x:.3f}  en conf1 (dentro de muestra) {m1[0]:+.2f} mbits {m1[1]}  | en vivo {mv[0]:+.2f} mbits {mv[1]}")
    RES[f"explotar|{nom}"] = dict(x=x, conf1=m1, vivo=mv)

with io.open(os.path.join(AQUI, "explorar.json"), "w", encoding="utf-8") as fh:
    json.dump(RES, fh, ensure_ascii=False, indent=1)
with io.open(os.path.join(AQUI, "salida_explorar.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(SAL) + "\n")
