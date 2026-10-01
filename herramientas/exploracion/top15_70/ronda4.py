# -*- coding: utf-8 -*-
"""Ronda 4 (PREREGISTRO_ronda4.md): números de "La Pirámide de Hoy".
Uso: python herramientas/exploracion/top15_70/ronda4.py -> ronda4.json, salida_ronda4.txt"""
import contextlib, io, json, os, runpy
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path(os.path.join(AQUI, "top15_70.py"))
LE = G["LE"]; SEMILLA = 20261001; B = 4000; Q = 100 * 0.05 / 4 / 2     # IC 98,75 %
SAL = []; RES = {}


def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)


def piramide(fecha):
    """fecha 'AAAA-MM-DD' -> filas de dígitos (8, 7, ..., 2)."""
    a, m, d = fecha.split("-")
    filas = [[int(c) for c in d + m + a]]
    while len(filas[-1]) > 2:
        f = filas[-1]; filas.append([(f[i] + f[i + 1]) % 10 for i in range(len(f) - 1)])
    return filas


def candidatos(fecha, variante):
    filas = piramide(fecha); dia = int(fecha[8:10])
    if variante == "PIR-punta":
        nums = {10 * filas[-1][0] + filas[-1][1]}
    else:
        nums = {10 * f[i] + f[i + 1] for f in filas if len(f) in (4, 3, 2) for i in range(len(f) - 1)}
    return sorted(n for n in nums if 1 <= n <= 36 and n not in (dia, dia + 1))


def oe(fechas, y_num, prob, dias):
    """y_num: número ganador (-1 para 0/00); prob(i, n): esperado."""
    out = {}
    for v in ("PIR-punta", "PIR-pares"):
        o = []; e = []; dd = []
        for i, f in enumerate(fechas):
            for n in candidatos(f, v):
                o.append(float(y_num[i] == n)); e.append(prob(i, n)); dd.append(dias[i])
        o = np.array(o); e = np.array(e); dd = np.array(dd)
        u, g = np.unique(dd, return_inverse=True)
        so = np.bincount(g, o); se = np.bincount(g, e)
        rng = np.random.default_rng(SEMILLA); idx = rng.integers(0, len(u), (B, len(u)))
        bs = so[idx].sum(1) / se[idx].sum(1)
        out[v] = dict(n_candidatos=len(o), obs=int(o.sum()), esp=round(float(e.sum()), 1), oe=float(o.sum() / e.sum()),
                      ic98_75=[float(np.percentile(bs, Q)), float(np.percentile(bs, 100 - Q))])
    return out


num_de = np.array([int(p) if p not in ("0", "00") else -1 for p in LE.POS])
Y, PE, IA, IB, FECHA, DIA = (G[k] for k in ("Y", "PE", "IA", "IB", "FECHA", "DIA"))
F = np.array(FECHA)
for nom, sel in (("LA_devA", IA), ("LA_devB", IB)):
    ii = np.where(sel)[0]
    RES[nom] = oe(list(F[ii]), num_de[Y[ii]], lambda i, n, ii=ii: PE[ii[i], LE.IDX[str(n)]], DIA[ii])
c = np.load(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "cache_todo.npz"))
s = c["tramo"] == "dev"
P1 = c["P1"][s].astype(float); P1 /= P1.sum(1, keepdims=True)
RES["RD_dev"] = oe([str(f) for f in c["fecha"][s]], num_de[c["y"][s]], lambda i, n: P1[i, LE.IDX[str(n)]],
                   c["dia"][s])
for v in ("PIR-punta", "PIR-pares"):
    a, b, r = RES["LA_devA"][v], RES["LA_devB"][v], RES["RD_dev"][v]
    pasa = a["oe"] < 1 and b["oe"] < 1 and r["oe"] < 1 and b["ic98_75"][1] < 1 and r["ic98_75"][1] < 1
    RES["veredicto_" + v] = "PASA" if pasa else "NO PASA"
    for nom, x in (("LA dev-A", a), ("LA dev-B", b), ("RD dev", r)):
        log(f"  {v} {nom}: candidatos {x['n_candidatos']} obs {x['obs']} esp {x['esp']} O/E {x['oe']:.3f} "
            f"[IC98,75 {x['ic98_75'][0]:.2f}; {x['ic98_75'][1]:.2f}]")
    log(f"  => {v}: {RES['veredicto_' + v]}")
log("  ejemplo 2026-10-01:", piramide("2026-10-01"), candidatos("2026-10-01", "PIR-punta"), candidatos("2026-10-01", "PIR-pares"))
with io.open(os.path.join(AQUI, "ronda4.json"), "w", encoding="utf-8") as fh:
    json.dump(RES, fh, ensure_ascii=False, indent=1)
with io.open(os.path.join(AQUI, "salida_ronda4.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(SAL) + "\n")
