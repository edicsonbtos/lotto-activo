# -*- coding: utf-8 -*-
"""Calibración del ensamble por hueco del animal (días sin salir), desarrollo LA. O/E por grupo y por mitad."""
import sys, os
import numpy as np
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE
D = LE.cargar(os.path.join(RAIZ, "verificacion/hilo9/datos/historial.txt"))
c = np.load(os.path.join(RAIZ, "verificacion/hilo9/datos/calor_cache.npz"))
P, y = c["P"], c["y"]; P = P / P.sum(1, keepdims=True)
T0 = 2000; n = len(y); dia = D.dia[T0:T0 + n]; corte = np.unique(dia)[len(np.unique(dia)) // 2]
ult = np.full(38, -999)
G = np.zeros((n, 38), int)
for t in range(T0 + n):
    if t >= T0: G[t - T0] = D.dia[t] - ult
    ult[D.seq[t]] = D.dia[t]
# R = ya salió hoy (hueco 0)
grupos = [("ya salió hoy", 0, 0), ("1 día", 1, 1), ("2 días", 2, 2), ("3 días", 3, 3), ("4-5 días", 4, 5), ("6-10 días", 6, 10), (">10 días", 11, 9999)]
print(f"{'grupo':14s}{'masa del modelo':>16s}{'obs':>7s}{'esp':>8s}{'O/E':>7s}{'z':>7s}{'O/E dev-A':>11s}{'O/E dev-B':>11s}")
for et, lo, hi in grupos:
    M = (G >= lo) & (G <= hi)
    e = (P * M).sum(1); o = M[np.arange(n), y].astype(float)
    def oe(s): return o[s].sum() / e[s].sum()
    z = (o.sum() - e.sum()) / np.sqrt((e * (1 - e)).sum())
    print(f"{et:14s}{e.mean():16.1%}{o.sum():7.0f}{e.sum():8.1f}{oe(slice(None)):7.3f}{z:+7.2f}{oe(dia < corte):11.3f}{oe(dia >= corte):11.3f}")
