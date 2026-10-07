# -*- coding: utf-8 -*-
"""Calcula, SIN reajustar nada, las probabilidades del ensamble_v2 (walk-forward) y de ag12 V1/V0 (parametros congelados
en c4a2b17, lambda=30) para las filas posteriores a la 2.a ciega (>=12511 = 2026-09-16 8:00 .. 2026-10-07).
Reproduce ademas las ultimas filas viejas (control de reproducibilidad contra P_*_reciente.npy)."""
import os, sys, subprocess, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
WT = os.path.join(os.path.dirname(RAIZ), "lotto-activo-motor"); MN = os.path.join(WT, "motor_nuevo")
REC = os.path.join(MN, "reciente")
sys.path.insert(0, os.path.join(WT, "herramientas")); sys.path.insert(0, os.path.join(MN, "ag12_transiciones"))
import lotto_eval as LE
import importlib.util
EXT = os.path.join(AQUI, "hist_ext.txt")
with open(EXT, "w", encoding="utf-8") as o:
    o.write(open(os.path.join(RAIZ, "hist" "orial.txt"), encoding="utf-8").read())
    o.write(open(os.path.join(AQUI, "fresco_la.txt"), encoding="utf-8").read())
D = LE.cargar(EXT); n = len(D); print("filas", n, D.fecha[-1])
assert n == 12511 + 249
DESDE = 9357
m = LE.cargar_modelo(os.path.join(WT, "herramientas", "modelos", "ensamble_v2.py"))
Pens = LE.normalizar(m.predecir(D, DESDE)); np.save(os.path.join(AQUI, "P_ens_fresco.npy"), Pens)
spec = importlib.util.spec_from_file_location("modelo_cand", os.path.join(MN, "ag12_transiciones", "modelo.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
for v in ("V1", "V0"):
    a = mod.Modelo(v); a.P_ens = Pens
    np.save(os.path.join(AQUI, f"P_ag12_{v}_fresco.npy"), LE.normalizar(a.predecir(D, DESDE)))
old = np.load(os.path.join(REC, "P_ens_reciente.npy"))[DESDE - 9357:]
print("control ens viejas: max|dif|", np.abs(Pens[:len(old)] - old).max())
for v in ("V1", "V0"):
    oa = np.load(os.path.join(REC, f"P_ag12_{v}.npy"))[DESDE - 9357:]
    print("control ag12", v, "max|dif|", np.abs(np.load(os.path.join(AQUI, f"P_ag12_{v}_fresco.npy"))[:len(oa)] - oa).max())
