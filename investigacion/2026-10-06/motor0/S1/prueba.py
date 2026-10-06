# -*- coding: utf-8 -*-
"""S1: UNA mirada a PRUEBA26 (CONTAMINADA: el régimen mié-vie y la regla RD se descubrieron con 2026) con lo congelado:
selector LR calibrada (walk-forward mensual, sin cambios), u = 0,50 elegido en AJUSTE. Registra en registro_prueba26_S1.jsonl."""
import sys, os, json, time
import numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estrategias as E, modelo as Mo
AQUI = os.path.dirname(os.path.abspath(__file__)); L = []; reg = {}
def pr(s): print(s, flush=True); L.append(s)
st_ref, pay_ref = E.ref_top5()
for mot, P in (("PROD", A.PROD), ("M4", E.M4)):
    y = E.Z[f"{mot}__hit"]
    preds = {k: E.PR[f"{mot}__{k}"] for k in ("C0", "C0_vm30d", "C1_masa", "LR", "GBM")}
    pr(f"== {mot} · parte 1 en PRUEBA26 (contaminada)")
    Mo.informe(mot, y, preds, "C0", tramos=("PRUEBA26",), lineas=L)
    m = A.TRAMOS["PRUEBA26"] & E.CON_RD; p = np.nan_to_num(E.PR[f"{mot}__LR"]); sel = p >= 0.50
    mult = np.select([p >= .60, p >= .55, p >= .50], [3, 2, 1], 0)
    sp, pp = E.top15(P); sw, pw = E.top15(P, ponderado=True)
    R = {"REF Top-5 PROD +cambio (todos)": E.metr(st_ref, pay_ref, m), "T15 plano todos": E.metr(sp, pp, m),
         "T15 ponderado todos": E.metr(sw, pw, m), "T15 plano si P̂≥0.50": E.metr(sp * sel, pp * sel, m),
         "T15 ponderado si P̂≥0.50": E.metr(sw * sel, pw * sel, m), "T15 plano graduado": E.metr(sp * mult, pp * mult, m)}
    pr(f"  parte 2 en PRUEBA26 (n={m.sum()}, días={len(set(A.F[m]))})")
    for k, r in R.items(): pr(E.linea(k, r))
    for a_, b_ in (("T15 plano si P̂≥0.50", "T15 plano todos"), ("T15 ponderado si P̂≥0.50", "T15 ponderado todos"), ("T15 plano graduado", "T15 plano todos")):
        (l1, h1), _ = E.pareado(R[a_], R["REF Top-5 PROD +cambio (todos)"]); _, (l2, h2) = E.pareado(R[a_], R[b_])
        pr(f"    pareado {a_:26}: netas/día − REF {R[a_]['neto_dia']-R['REF Top-5 PROD +cambio (todos)']['neto_dia']:+6.2f} [{l1:+.2f};{h1:+.2f}] | ret/ficha − '{b_}' {100*(R[a_]['ret']-R[b_]['ret']):+5.1f} pp [{100*l2:+.1f};{100*h2:+.1f}]")
    reg[mot] = {k: dict(ret=round(100 * v["ret"], 2), neto_dia=round(v["neto_dia"], 2), jugado=round(100 * v["jugado"], 1)) for k, v in R.items()}
open(os.path.join(AQUI, "registro_prueba26_S1.jsonl"), "a").write(json.dumps(dict(cuando=time.strftime("%Y-%m-%d %H:%M:%S"), contaminada=True, congelado="LR calibrada, u=0.50", **reg), ensure_ascii=False) + "\n")
open(os.path.join(AQUI, "salida_prueba26.txt"), "w").write("\n".join(L) + "\n")
