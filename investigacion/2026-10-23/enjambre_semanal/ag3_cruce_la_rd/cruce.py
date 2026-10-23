# -*- coding: utf-8 -*-
"""ag3: repelencias cruzadas LA h:00 / RD h:30. Ver PREREGISTRO.md."""
import sys, os, csv, ast, re, unicodedata, json
import numpy as np
from collections import defaultdict
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas")); sys.path.insert(0, os.path.join(RAIZ, "investigacion/2026-10-22/bateria"))
import lotto_eval as LE
from rasgos import POSR, RUEDA, IDX, NUM
rng = np.random.default_rng(20261023)
ZB = 2.576
INV_R = {k: IDX[c] for k, c in enumerate(RUEDA)}   # posición rueda -> índice
def vec(i): r = POSR[i]; return {INV_R[(r + 1) % 38], INV_R[(r - 1) % 38]}
def opuesto(i): return INV_R[(POSR[i] + 19) % 38]
def num_idx(n): return IDX[str(n)]
def h12(h): return 12 if h % 12 == 0 else h % 12

# ---- datos
D = LE.cargar(os.path.join(RAIZ, "verificacion/hilo9/datos/historial.txt"))
c = np.load(os.path.join(RAIZ, "verificacion/hilo9/datos/calor_cache.npz")); P = c["P"] / c["P"].sum(1, keepdims=True); y = c["y"]
T0 = 2000; assert (D.seq[T0:T0 + len(y)] == y).all()
src = open(os.path.join(RAIZ, "rdint_vivo.py"), encoding="utf-8").read()
NOMBRE = ast.literal_eval(re.search(r"^NOMBRE = (\{.*?\})", src, re.S | re.M).group(1))
norm = lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().lower().strip()
inv = {norm(v): k for k, v in NOMBRE.items()}
RD = {}; mal = 0
for r in csv.DictReader(open(os.path.join(RAIZ, "datos_multiloteria/rdint_hist.csv"), encoding="utf-8")):
    k = inv.get(norm(r["animal"]))
    if k is None: mal += 1; continue
    RD[(r["fecha"], int(r["hora"][:2]) - 8)] = IDX[k]
print("RD sin mapear:", mal, " RD sorteos:", len(RD))
LA = {(D.fecha[t], int(D.hora[t])): int(D.seq[t]) for t in range(len(D.seq))}
OF = {1: {}, 2: {}}
for r in csv.DictReader(open(os.path.join(RAIZ, "datos_multiloteria/oficial_multi.csv"))):
    if r["juego"] in ("1", "2") and r["codigo"] in IDX and "2025-07-01" <= r["fecha"] <= "2025-12-17":
        OF[int(r["juego"])][(r["fecha"], int(r["hora"][:2]) - 8)] = IDX[r["codigo"]]
print("oficial LA/RD 2025-07..12-17:", len(OF[1]), len(OF[2]))

def dia_mes(f): return int(f[8:10])
# ---- resumen
def resumen(reg):
    """reg: lista (dia, obs, esp, var)."""
    o = sum(r[1] for r in reg); e = sum(r[2] for r in reg); v = sum(r[3] for r in reg)
    return o, e, (o / e if e > 0 else float("nan")), ((o - e) / np.sqrt(v) if v > 0 else float("nan"))
def boot(reg, B=2000):
    por = defaultdict(lambda: [0.0, 0.0])
    for r in reg: por[r[0]][0] += r[1]; por[r[0]][1] += r[2]
    a = np.array(list(por.values())); n = len(a); out = []
    for _ in range(B):
        s = a[rng.integers(0, n, n)].sum(0); out.append(s[0] / s[1])
    return np.percentile(out, [2.5, 97.5])
def informe(nombre, reg, esperado_bajo=True, extra=""):
    dias = sorted({r[0] for r in reg}); corte = dias[len(dias) // 2]
    A = resumen([r for r in reg if r[0] < corte]); B = resumen([r for r in reg if r[0] >= corte]); T = resumen(reg)
    ic = boot(reg)
    pasa = (np.sign(A[3]) == np.sign(B[3]) and abs(A[3]) >= 2 and abs(B[3]) >= 2 and abs(T[3]) >= ZB)
    print(f"{nombre:34s} n={len(reg):5d} obs {T[0]:5.0f} esp {T[1]:7.1f} O/E {T[2]:.3f} [{ic[0]:.2f};{ic[1]:.2f}] z {T[3]:+.2f} | A {A[2]:.3f} ({A[3]:+.2f}) B {B[2]:.3f} ({B[3]:+.2f}) {'PASA' if pasa else 'no'} {extra}")
    return dict(n=len(reg), obs=T[0], esp=T[1], oe=T[2], ic=list(map(float, ic)), z=T[3], zA=A[3], zB=B[3], oeA=A[2], oeB=B[2], pasa=bool(pasa))

# ---- objetivo LA (ensamble)
def la_filas(masker, excl_rd=False, cond=None):
    reg = []
    for i in range(len(y)):
        t = T0 + i; f = D.fecha[t]; j = int(D.hora[t])
        if f == "2025-12-17" or j < 1: continue
        rd = RD.get((f, j - 1))
        if rd is None: continue
        if cond is not None and not cond(f, j): continue
        m = masker(f, j, rd)
        if m is None: continue
        p = P[i].copy()
        if excl_rd: p[rd] = 0; p = p / p.sum()
        e = p[m].sum(); reg.append((int(D.dia[t]), float(y[i] in m), e, e * (1 - e)))
    return reg
res = {}
print("\n== Objetivo LA, base ensamble ==")
res["C1"] = informe("C1 vecinos rueda de RD(h-1):30", la_filas(lambda f, j, rd: list(vec(rd))))
res["C1_sens"] = informe("C1 sens (RD anim=0 en base)", la_filas(lambda f, j, rd: list(vec(rd)), excl_rd=True))
res["C4"] = informe("C4 numero (h-1) 12h", la_filas(lambda f, j, rd: [num_idx(h12(8 + j - 1))]))
res["C4_plac_h+1"] = informe("  placebo numero h+1", la_filas(lambda f, j, rd: [num_idx(h12(8 + j + 1))]))
res["C4_propia"] = informe("  ref: numero propia hora", la_filas(lambda f, j, rd: [num_idx(h12(8 + j))]))
res["C5"] = informe("C5 opuesto d19 de RD(h-1):30", la_filas(lambda f, j, rd: [opuesto(rd)]))
res["C5_sens"] = informe("C5 sens (RD anim=0)", la_filas(lambda f, j, rd: [opuesto(rd)], excl_rd=True))

# C3 LA
g1, g0 = [], []
for i in range(len(y)):
    t = T0 + i; f = D.fecha[t]; j = int(D.hora[t]); d = dia_mes(f)
    if f == "2025-12-17" or j < 1 or d > 31 or (f, j - 1) not in RD: continue
    n = num_idx(d); e = P[i][n]
    hoy = any(RD.get((f, k)) == n for k in range(0, j))
    (g1 if hoy else g0).append((int(D.dia[t]), float(y[i] == n), e, e * (1 - e)))
def c3(g1, g0, nombre):
    o0, e0, r0, _ = resumen(g0); o1 = sum(r[1] for r in g1); e1 = sum(r[2] for r in g1); v1 = sum(r[3] for r in g1)
    E1 = r0 * e1; z = (o1 - E1) / np.sqrt(r0 * v1) if v1 > 0 else float("nan")
    dias = sorted({r[0] for r in g1 + g0}); corte = dias[len(dias) // 2]
    zs = []
    for sel in (lambda r: r[0] < corte, lambda r: r[0] >= corte):
        a = [r for r in g1 if sel(r)]; oo = sum(r[1] for r in a); ee = r0 * sum(r[2] for r in a); vv = r0 * sum(r[3] for r in a)
        zs.append((oo, ee, (oo - ee) / np.sqrt(vv) if vv > 0 else float("nan")))
    pot = e1 >= 30
    pasa = pot and np.sign(zs[0][2]) == np.sign(zs[1][2]) and abs(zs[0][2]) >= 2 and abs(zs[1][2]) >= 2 and abs(z) >= ZB
    print(f"{nombre:34s} G1: n={len(g1)} obs {o1:.0f} esp(base G0 r0={r0:.3f}) {E1:.1f} (sinAjuste {e1:.1f}) O/E_G1 {o1/e1:.3f} z {z:+.2f} | A {zs[0][0]:.0f}/{zs[0][1]:.1f} z{zs[0][2]:+.2f} B {zs[1][0]:.0f}/{zs[1][1]:.1f} z{zs[1][2]:+.2f} potencia(e1>=30) {pot} {'PASA' if pasa else 'no'}")
    return dict(n1=len(g1), o1=o1, E1=E1, e1=e1, r0=r0, z=z, zA=zs[0][2], zB=zs[1][2], pasa=bool(pasa))
print("\n== C3 LA ==")
res["C3"] = c3(g1, g0, "C3 LA dia-mes | RD ya lo saco hoy")

# ---- objetivo RD (uniforme, no salidos hoy, sin LA h:00)
def rd_filas(RDd, LAd, masker, f0, f1, cond=None, incl_j0=True):
    reg = []
    fechas = sorted({k[0] for k in RDd if f0 <= k[0] <= f1})
    for f in fechas:
        vistos = set()
        for j in range(0, 12):
            if (f, j) not in RDd: continue
            r = RDd[(f, j)]
            la = LAd.get((f, j))
            if la is None: vistos.add(r); continue
            libres = [k for k in range(38) if k not in vistos and k != la]
            if r in libres and (cond is None or cond(f, j)):
                m = masker(f, j, la, vistos)
                if m is not None:
                    e = sum(1 for k in libres if k in m) / len(libres)
                    reg.append((f, float(r in m), e, e * (1 - e)))
            vistos.add(r)
    return reg
def rd_dia(RDd, LAd, f0, f1):
    """descriptivo: día del mes en RD."""
    return rd_filas(RDd, LAd, lambda f, j, la, v: {num_idx(dia_mes(f))} if dia_mes(f) <= 31 else None, f0, f1)
def informe_rd(nombre, reg):
    """fechas ya son strings; informe usa corte por orden -> mapear a ordinal."""
    reg2 = [(int(r[0].replace("-", "")), *r[1:]) for r in reg]
    return informe(nombre, reg2)
def bloque_rd(RDd, LAd, f0, f1, etiqueta):
    print(f"\n== Objetivo RD ({etiqueta} {f0}..{f1}), base uniforme ==")
    o = {}
    o["C2"] = informe_rd("C2 vecinos rueda de LA h:00", rd_filas(RDd, LAd, lambda f, j, la, v: vec(la), f0, f1))
    o["C4r"] = informe_rd("C4r numero (h-1) 12h (RD h:30)", rd_filas(RDd, LAd, lambda f, j, la, v: {num_idx(h12(8 + j - 1))} if j >= 1 else None, f0, f1))
    o["C4r_propia"] = informe_rd("  ref: numero hora propia", rd_filas(RDd, LAd, lambda f, j, la, v: {num_idx(h12(8 + j))}, f0, f1))
    o["C5r"] = informe_rd("C5r opuesto d19 de LA h:00", rd_filas(RDd, LAd, lambda f, j, la, v: {opuesto(la)}, f0, f1))
    o["RD_dia_mes"] = informe_rd("desc: RD dia del mes", rd_dia(RDd, LAd, f0, f1))
    # C3r
    g1, g0 = [], []
    for r in rd_filas(RDd, LAd, lambda f, j, la, v: {num_idx(dia_mes(f))}, f0, f1):
        pass
    for f in sorted({k[0] for k in RDd if f0 <= k[0] <= f1}):
        vistos = set(); n = num_idx(dia_mes(f))
        for j in range(12):
            if (f, j) not in RDd: continue
            r = RDd[(f, j)]; la = LAd.get((f, j))
            if la is not None and j >= 1:
                libres = [k for k in range(38) if k not in vistos and k != la]
                if r in libres and n in libres:
                    e = 1 / len(libres); hoy = any(LAd.get((f, k)) == n for k in range(0, j + 1))
                    (g1 if hoy else g0).append((int(f.replace("-", "")), float(r == n), e, e * (1 - e)))
            vistos.add(r)
    o["C3r"] = c3(g1, g0, "C3r RD dia-mes | LA ya lo saco")
    return o
LAd_all = {k: v for k, v in LA.items() if k[0] != "2025-12-17"}
res["RD_dev"] = bloque_rd(RD, LA, "2024-03-01", "2025-06-30", "desarrollo")
res["RD_oficial"] = bloque_rd(OF[2], OF[1], "2025-07-01", "2025-12-17", "oficial")
json.dump(res, open(os.path.join(os.path.dirname(__file__), "resultado.json"), "w"), indent=1, default=float)
