# -*- coding: utf-8 -*-
"""Ronda 3 (PREREGISTRO_ronda3.md): ¿el operador esquiva el número de la fecha y el de la hora?

Uso:  python herramientas/exploracion/top15_70/ronda3.py   -> ronda3.json, salida_ronda3.txt
"""
import contextlib, csv, io, json, os, runpy
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path(os.path.join(AQUI, "top15_70.py"))
LE = G["LE"]; K = 38; SEMILLA = 20261001; B = 4000
Q = 100 * 0.05 / 2 / 2           # IC 99,17 % (Bonferroni 3 pruebas por juego)
SAL = []; RES = {}


def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)


def reloj12(h24):
    return (h24 - 1) % 12 + 1


def oe_boot(o, e, dias):
    u, g = np.unique(dias, return_inverse=True)
    so = np.bincount(g, o); se = np.bincount(g, e)
    rng = np.random.default_rng(SEMILLA); idx = rng.integers(0, len(u), (B, len(u)))
    bs = so[idx].sum(1) / se[idx].sum(1)
    return float(o.sum() / e.sum()), [float(np.percentile(bs, Q)), float(np.percentile(bs, 100 - Q))]


def probar(nombre, filas, prob, maxnum):
    """filas: [(fecha, hora24, numero_ganador)]; prob(i, numero) -> esperado. Devuelve dict por prueba."""
    out = {}
    for prueba in ("S0", "S10"):
        o = []; e = []; d = []
        for i, (f, h24, gan) in enumerate(filas):
            dia = int(f[8:10])
            if prueba == "S10" and dia < 10:
                continue
            n = sum(int(ch) for ch in str(dia))
            if not (1 <= n <= maxnum):
                continue
            o.append(float(gan == n)); e.append(prob(i, n)); d.append(f)
        o = np.array(o); e = np.array(e)
        r, ic = oe_boot(o, e, np.array(d))
        rep = r < 1 and ic[1] < 1
        out[prueba] = dict(n=len(o), obs=int(o.sum()), esp=round(float(e.sum()), 1), oe=r, ic99_17=ic,
                           veredicto="SE REPLICA" if rep else "NO")
        log(f"  {nombre} {prueba}: n={len(o)} obs {int(o.sum())} esp {e.sum():.1f} O/E {r:.3f} "
            f"[IC99,17 {ic[0]:.2f}; {ic[1]:.2f}] => {out[prueba]['veredicto']}")
    return out


# ------------------------------------------------------------------ 1. RD Internacional (dev de RD, modelo B1)
log("1. RD Internacional, desarrollo de RD 2024-03-01..2025-06-30 (esperado = modelo B1 de RD)")
c = np.load(os.path.join(RAIZ, "verificacion", "hilo9", "datos", "cache_todo.npz"))
s = c["tramo"] == "dev"
P1 = c["P1"][s].astype(float); P1 /= P1.sum(1, keepdims=True)
filas_rd = [(str(f), int(h) + 8, int(y)) for f, h, y in zip(c["fecha"][s], c["hora"][s], c["y"][s])]
# y está en el índice de LE.POS: pasar a número (0 y 00 no cuentan)
num_de = {i: (int(p) if p not in ("0", "00") else -1) for i, p in enumerate(LE.POS)}
filas_rd = [(f, h, num_de[y]) for f, h, y in filas_rd]
RES["RD"] = probar("RD", filas_rd, lambda i, n: P1[i, LE.IDX[str(n)]], 36)

# ------------------------------------------------------------------ 2. LARD (juego 3 de la API oficial)
log("\n2. LARD (Lotto Activo RD), API oficial 2025-07-01..2026-09-22 (esperado = frecuencia en LARD)")
filas_lard = []
with io.open(os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["juego"] == "3" and r["codigo"] not in ("0", "00"):
            filas_lard.append((r["fecha"], int(r["hora"][:2]), int(r["codigo"])))
        elif r["juego"] == "3":
            filas_lard.append((r["fecha"], int(r["hora"][:2]), -1))
n_l = len(filas_lard)
frec_l = {n: sum(1 for x in filas_lard if x[2] == n) / n_l for n in range(1, 37)}
RES["LARD"] = probar("LARD", filas_lard, lambda i, n: frec_l[n], 36)


# ------------------------------------------------------------------ 3. otras loterías
def leer(nombre):
    out = []
    with io.open(os.path.join(RAIZ, "datos_multiloteria", nombre + ".csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                out.append((r["fecha"], int(r["hora"][:2]), int(r["numero"]) if r["numero"] != "00" else -1))
            except ValueError:
                pass
    return out


log("\n3. Otros operadores, 2026-04-13..09-13 (esperado = frecuencia en cada lotería; descriptivo)")
for nom, maxn in (("lagranjita", 36), ("selvaplus", 99), ("guacharoactivo", 75)):
    fl = leer(nom); nn = len(fl)
    fr = {n: sum(1 for x in fl if x[2] == n) / nn for n in range(1, maxn + 1)}
    RES[nom] = probar(nom, fl, lambda i, n, fr=fr: fr[n], 36)

open(os.path.join(AQUI, "salida_ronda5_replica.txt"), "w", encoding="utf-8").write(chr(10).join(SAL))
