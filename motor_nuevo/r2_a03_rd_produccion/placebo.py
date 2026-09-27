# -*- coding: utf-8 -*-
"""Control placebo (no es variante): VA con el RD de la MISMA hora pero de 7 días antes. Debe dar Delta ~ 0."""
import os, sys, json
from datetime import date, timedelta
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import experimento as X
A, E2 = X.A, X.E2
D = A.datos().prefijo(A.CORTE); _, y = A.base()
Pv1 = np.load(os.path.join(X.MN, "ag12_transiciones", "P_V1.npy")); Pv1 /= Pv1.sum(1, keepdims=True)
LV1 = np.log(np.clip(Pv1, 1e-12, None))
rd = X.cargar_rd(D.fecha[-1])
rd7 = {((date.fromisoformat(f) + timedelta(days=7)).isoformat(), h): s for (f, h), s in rd.items()}
Xr = X.rasgos_rd(D, A.W, rd7).astype(np.float64)
blo = E2.bloques_jornada(np.asarray(D.dia[A.W:A.CORTE]))
P, w = E2.cross_fit(lambda tr: E2.ajustar_lineal(Xr[tr], LV1[tr], y[tr], X.LAM),
                    lambda w, te: E2.predecir_lineal(w, Xr[te], LV1[te]), blo)
r = A.evaluar(P, P_ref=Pv1, y=y)
print("placebo RD-7d: Delta", r["delta_mbits"], "mitades", r["delta_mitad1"][0], r["delta_mitad2"][0], "Top-15", r["top15_cand"])
json.dump({"placebo_rd_menos_7d": r}, open(os.path.join(AQUI, "resultados_placebo.json"), "w"), indent=1)
