# -*- coding: utf-8 -*-
"""Test: ¿la penalizacion anti-repeticion MEJORA a un modelo base fuerte?
Multiplicadores m1 (repeticion inmediata) y m2 (misma hora ayer) estimados
SOLO con el calentamiento [0,W) -> cero fuga. Se aplican sobre hazard_actual
y se comparan metricas en DESARROLLO (nunca se toca la prueba ciega).
"""
import os, sys
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

K, HORAS = 38, 12
datos = LE.cargar()
n = len(datos)
w, corte = LE.particion(n)
seq, hora = datos.seq, datos.hora

# ---- multiplicadores SOLO con calentamiento ----
rep = float(np.sum(seq[1:w] == seq[:w - 1]))
m1 = (rep / (w - 1)) * K
sameh = float(np.sum(seq[HORAS:w] == seq[:w - HORAS]))
m2 = (sameh / (w - HORAS)) * K
print(f"multiplicadores (solo warmup <{w}): m1(rep)={m1:.3f}  m2(misma hora ayer)={m2:.3f}")

def penalizar(P, m1v, m2v, offset):
    """P filas corresponden a sorteos offset..n-1 (global)."""
    Q = P.copy()
    for j in range(P.shape[0]):
        t = offset + j
        Q[j, seq[t - 1]] *= m1v
        if t >= HORAS:
            Q[j, seq[t - HORAS]] *= m2v
    return LE.normalizar(Q)

for nombre in ("hazard_actual",):
    sub = LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", nombre + ".py"))
    P = LE.normalizar(sub.predecir(datos, w))
    y = seq[w:]
    nd = corte - w
    base = LE.metricas(P[:nd], y[:nd])
    print(f"\n== {nombre} DESARROLLO (n={nd}) ==")
    print(f"  sin penalizar : Top1 {base['top1']['tasa']*100:.2f}%  Top3 {base['top3']['tasa']*100:.2f}%  "
          f"Top5 {base['top5']['tasa']*100:.2f}%  {base['logver']['bits_por_sorteo']*1000:+.2f} mbits")
    for m1v, m2v, etq in [(m1, 1.0, "solo m1"), (1.0, m2, "solo m2"), (m1, m2, "m1 x m2")]:
        Q = penalizar(P, m1v, m2v, w)
        mb = LE.metricas(Q[:nd], y[:nd])
        print(f"  {etq:<12}: Top1 {mb['top1']['tasa']*100:.2f}%  Top3 {mb['top3']['tasa']*100:.2f}%  "
              f"Top5 {mb['top5']['tasa']*100:.2f}%  {mb['logver']['bits_por_sorteo']*1000:+.2f} mbits")
