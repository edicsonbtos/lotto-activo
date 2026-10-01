# -*- coding: utf-8 -*-
"""Elige la variante SOLO en desarrollo [2000, 9357). Salida: dev_resultados.json"""
import json, os
import numpy as np
import comun as C
import sub
D = sub.datos("dev"); y = np.asarray(D.seq); dias = np.asarray(D.dia)
a, b = C.LE.W, C.LE.CORTE_FIJO
yy = y[a:b]; dd = dias[a:b]; mitad = (b - a) // 2
res = {}; met = {}
for g, cl in C.GRUPOS.items():
    L = C.cargar_L("dev", cl)
    P, hist = C.combinar(L, y[C.ARRANQUE:], a, devolver_w=True, **C.COMB[g])
    met[g] = C.por_sorteo(P, yy)
    res[g] = {"pesos_finales": [round(float(x), 3) for x in hist[-1][1]]}
for g in C.GRUPOS:
    m, mb = met[g], met["base"]
    d = m["mb"] - mb["mb"]
    r = res[g]
    r["mbits"] = round(float(m["mb"].mean()), 2)
    r["delta"] = [round(x, 2) for x in C.boot_dif(d, dd)]
    r["mitad1"] = [round(x, 2) for x in C.boot_dif(d[:mitad], dd[:mitad])]
    r["mitad2"] = [round(x, 2) for x in C.boot_dif(d[mitad:], dd[mitad:])]
    for k in ("t5", "t15", "r5", "r15", "r15p"):
        r[k] = round(float(m[k].mean()) * 100, 2)
    r["delta_r5_pp"] = [round(x * 100, 2) for x in C.boot_dif(m["r5"] - mb["r5"], dd)]
    r["pasa_barra"] = bool(g != "base" and r["delta"][0] >= 3 and r["delta"][1] > 0 and r["mitad1"][0] > 0 and r["mitad2"][0] > 0)
    print(g, json.dumps(r, ensure_ascii=False))
cand = max((g for g in C.GRUPOS if g != "base"), key=lambda g: res[g]["delta"][0])
res["elegida"] = cand
print("ELEGIDA (mayor delta en desarrollo):", cand, "pasa barra:", res[cand]["pasa_barra"])
json.dump(res, open(os.path.join(C.AQUI, "dev_resultados.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
