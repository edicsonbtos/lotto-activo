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
Q = 100 * 0.05 / 3 / 2           # IC 99,17 % (Bonferroni 3 pruebas por juego)
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
    for prueba in ("D0", "D1", "H12"):
        o = []; e = []; d = []
        for i, (f, h24, gan) in enumerate(filas):
            dia = int(f[8:10])
            n = dia if prueba == "D0" else (dia + 1 if prueba == "D1" else reloj12(h24))
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

ver_rd = any(RES["RD"][p]["veredicto"] == "SE REPLICA" for p in ("D0", "D1"))
ver_l = any(RES["LARD"][p]["veredicto"] == "SE REPLICA" for p in ("D0", "D1"))
RES["veredicto_operador"] = "CONFIRMADA" if (ver_rd and ver_l) else "NO CONFIRMADA"
log(f"\nVeredicto 'el operador esquiva la fecha' (D0 o D1 en RD y en LARD): {RES['veredicto_operador']}")

# ------------------------------------------------------------------ 4. LA: corrección por exposición sobre P6
log("\n4. LA: corrección por exposición sobre P6 (descriptivo, contaminado)")
Y, P6, IA, IB, DIA, HORA, FECHA = (G[k] for k in ("Y", "P6", "IA", "IB", "DIA", "HORA", "FECHA"))
N = len(Y)
XE = np.zeros((N, K, 6), np.float32)
for i in range(N):
    d = int(FECHA[i][8:10]); m = int(FECHA[i][5:7]); h12 = reloj12(int(HORA[i]) + 8)
    for j, n in enumerate((d - 1, d, d + 1, d + 2, h12, m)):
        if 1 <= n <= 36:
            XE[i, LE.IDX[str(n)], j] = 1
w = G["ajustar_logit"](XE, np.log(P6), Y, 30.0, np.where(IA)[0])
PX = G["aplicar_logit"](XE, np.log(P6), w)
log("  multiplicadores (dev-A) día-1, día, día+1, día+2, hora12, mes:", [round(float(np.exp(v)), 3) for v in w])
OX = G["regla_rd"](G["orden_de"](PX)); O6 = G["regla_rd"](G["orden_de"](P6))
hx = (G["pos_de"](OX[IB], Y[IB]) < 15).astype(float)
h6 = (G["pos_de"](O6[IB], Y[IB]) < 15).astype(float)
h1 = (G["pos_de"](G["ORD_B1"][IB], Y[IB]) < 15).astype(float)
mbx = np.log2(PX[IB][np.arange(IB.sum()), Y[IB]] * K) * 1000
mb6 = np.log2(P6[IB][np.arange(IB.sum()), Y[IB]] * K) * 1000
mb0 = np.log2(G["PE"][IB][np.arange(IB.sum()), Y[IB]] * K) * 1000
bt = G["boot"]
RES["LA_exposicion"] = dict(mult=[float(np.exp(v)) for v in w], top15=bt(hx, DIA[IB]),
                            dif_vs_P6_regla=bt(hx - h6, DIA[IB]), dif_vs_B1=bt(hx - h1, DIA[IB]),
                            mbits=float(mbx.mean()), dif_mbits_vs_P6=bt(mbx - mb6, DIA[IB]),
                            dif_mbits_vs_B0=bt(mbx - mb0, DIA[IB]), veredicto="descriptivo (contaminado)")
r = RES["LA_exposicion"]
log(f"  dev-B: Top-15 {100*hx.mean():.2f} % (P6+regla {100*h6.mean():.2f} %, B1 {100*h1.mean():.2f} %); "
    f"dif vs P6 {100*r['dif_vs_P6_regla']['media']:+.2f} pp [{100*r['dif_vs_P6_regla']['ic95'][0]:+.2f}; "
    f"{100*r['dif_vs_P6_regla']['ic95'][1]:+.2f}], vs B1 {100*r['dif_vs_B1']['media']:+.2f} pp; "
    f"mbits {mbx.mean():.1f} (vs P6 {r['dif_mbits_vs_P6']['media']:+.1f} [{r['dif_mbits_vs_P6']['ic95'][0]:+.1f}; "
    f"{r['dif_mbits_vs_P6']['ic95'][1]:+.1f}], vs B0 {r['dif_mbits_vs_B0']['media']:+.1f})")
m15 = np.sort(PX[IB], 1)[:, ::-1][:, :15].sum(1)
log(f"  masa Top-15 que se da: media {100*m15.mean():.1f} %, máx {100*m15.max():.1f} %")

with io.open(os.path.join(AQUI, "ronda3.json"), "w", encoding="utf-8") as fh:
    json.dump(RES, fh, ensure_ascii=False, indent=1)
with io.open(os.path.join(AQUI, "salida_ronda3.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(SAL) + "\n")
