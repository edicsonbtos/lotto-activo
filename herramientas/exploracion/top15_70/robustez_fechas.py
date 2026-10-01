# -*- coding: utf-8 -*-
"""Robustez pedida por la auditoría: A1 (día del mes) y A2 (hora 12 h) con las FECHAS CORREGIDAS
(herramientas/correccion_historial_2026-09-29.json), aplicadas en memoria; el historial congelado no se toca.
Uso: python herramientas/exploracion/top15_70/robustez_fechas.py -> salida_robustez_fechas.txt"""
import contextlib, io, json, os, runpy
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path(os.path.join(AQUI, "top15_70.py"))
LE = G["LE"]; D = G["D"]; W, CORTE = G["W"], G["CORTE"]
Y, PE, IA, IB, HORA = G["Y"], G["PE"], G["IA"], G["IB"], G["HORA"]
cor = json.load(open(os.path.join(RAIZ, "herramientas", "correccion_historial_2026-09-29.json"), encoding="utf-8"))
mapa = {}
for c in cor["cambios"]:
    a = c["antes"].split(); b = c["despues"].split()
    mapa.setdefault((a[0], int(a[1]), a[2]), []).append(b[0])
fechas = []; n_cor = 0
for t in range(W, CORTE):
    k = (D.fecha[t], int(D.hora[t]), LE.POS[D.seq[t]])
    if k in mapa and mapa[k]:
        fechas.append(mapa[k].pop(0)); n_cor += 1
    else:
        fechas.append(D.fecha[t])
SAL = [f"filas de desarrollo con fecha corregida: {n_cor}"]
dm = np.array([int(f[8:10]) for f in fechas]); r12 = (HORA + 8 - 1) % 12 + 1
for nom, num in (("A1_dia_del_mes", dm), ("A2_hora_12h", r12)):
    a = np.array([LE.IDX[str(x)] for x in num])
    o = (Y == a).astype(float); e = PE[np.arange(len(Y)), a]
    for tr, s in (("dev-A", IA), ("dev-B", IB)):
        SAL.append(f"{nom} {tr} (fechas corregidas): obs {int(o[s].sum())} esp {e[s].sum():.1f} O/E {o[s].sum()/e[s].sum():.3f}")
    for sh in (-1, 1, 2):
        if nom.startswith("A1"):
            ok = (dm + sh >= 1) & (dm + sh <= 36)
            b = np.array([LE.IDX[str(x)] if 1 <= x <= 36 else 0 for x in dm + sh])
            o2 = (Y[ok] == b[ok]).sum(); e2 = PE[np.where(ok)[0], b[ok]].sum()
            SAL.append(f"  placebo día{sh:+d} (todo dev, corregido): O/E {o2/e2:.3f}")
print("\n".join(SAL))
open(os.path.join(AQUI, "salida_robustez_fechas.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
