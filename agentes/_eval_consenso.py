# -*- coding: utf-8 -*-
"""Evalua consenso de los 4 agentes walk-forward sobre los ultimos N sorteos."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import K, POS, cargar_historial  # noqa: E402
import orquestador as O  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
seq, horas, dweek, _ = cargar_historial(os.path.join("..", "historial.txt"))
n = len(seq)

t0 = time.time()
hit1 = hit3 = 0
hit1c = hit3c = 0
for t in range(n - N, n):
    hora_sig = (horas[t - 1] + 1) % 12
    tops = O.top15_agentes(seq[:t], horas[:t], dweek[:t], hora_sig)
    # capitan: agente con mejor tasa acumulada en esta corrida (simula marcador)
    real = seq[t]
    # consenso
    votos = O.votos_consenso(tops)
    orden = sorted(range(K), key=lambda i: (-votos[i], i))
    if orden[0] == real:
        hit1c += 1
    if real in orden[:3]:
        hit3c += 1

dt = time.time() - t0
print(f"Consenso 4 agentes, ultimos {N} sorteos:")
print(f"  Top-1: {hit1c / N:.4f}  ({hit1c}/{N})   azar 0.0263")
print(f"  Top-3: {hit3c / N:.4f}  ({hit3c}/{N})   azar 0.0789")
print(f"  tiempo: {dt:.1f}s ({dt / N * 1000:.1f} ms/sorteo)")
