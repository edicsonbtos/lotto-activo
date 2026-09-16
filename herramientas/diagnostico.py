#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnóstico rápido de aleatoriedad del histórico (segundos).

Muestra si el sorteo se comporta como azar puro o tiene estructura explotable:
uniformidad, efecto de la hora, repetición según retraso, animales distintos por
jornada y tasa base real de la tripleta (día natural y ventana de 12 sorteos).
Compara el primer y el último tercio para ver si el mecanismo cambia.
"""
import os, sys
from math import comb
from collections import defaultdict
import numpy as np
from scipy.stats import chisquare, chi2_contingency

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lotto_eval as LE

K = 38


def bloque(seq, dia, titulo):
    n = len(seq)
    print(f"\n--- {titulo}: {n} sorteos ---")
    print(f"Uniformidad (chi2): p = {chisquare(np.bincount(seq, minlength=K)).pvalue:.3f}  (p < 0,01 = algunos animales salen más)")
    last = np.full(K, -1); hit = np.zeros(61); tot = np.zeros(61)
    for t, v in enumerate(seq):
        if t > 0:
            g = np.where(last >= 0, np.minimum(t - last, 60), 60)
            np.add.at(tot, g, 1); hit[g[v]] += 1
        last[v] = t
    tramos = [(1, 1), (2, 3), (4, 8), (9, 12), (13, 20), (21, 30), (31, 45), (46, 59)]
    txt = "  ".join(f"{a}-{b}: {hit[a:b+1].sum()/tot[a:b+1].sum()*K:.2f}x" for a, b in tramos)
    print(f"Probabilidad relativa según sorteos desde que salió (1,00x = azar):\n  {txt}")
    g = defaultdict(list)
    for t in range(n):
        g[dia[t]].append(seq[t])
    D = np.array([len(set(v)) for v in g.values() if len(v) == 12])
    if len(D):
        print(f"Distintos por jornada de 12: {D.mean():.2f}  (azar con repetición: 10,41; sin repetir: 12)")
        print(f"Tripleta al azar, día natural: {np.mean([comb(x, 3) for x in D]) / comb(K, 3) * 100:.2f}%  (umbral 45x: 2,22%)")
    Dw = np.array([len(set(seq[t:t + 12])) for t in range(0, n - 12)])
    print(f"Tripleta al azar, ventana de 12 sorteos: {np.mean([comb(int(x), 3) for x in Dw]) / comb(K, 3) * 100:.2f}%")


def main():
    d = LE.cargar()
    s, dia = np.asarray(d.seq), np.asarray(d.dia)
    print(f"Histórico: {len(s)} sorteos, {d.fecha[0]} a {d.fecha[-1]}")
    T = np.zeros((12, K))
    for h, v in zip(d.hora, s):
        T[h, v] += 1
    print(f"¿La hora influye en qué animal sale? p = {chi2_contingency(T[1:]).pvalue:.3f}  (p > 0,05 = no)")
    bloque(s, dia, "Todo el histórico")
    n = len(s); a = n // 3
    bloque(s[:a], dia[:a], "Primer tercio")
    bloque(s[-a:], dia[-a:], "Último tercio (lo más reciente)")
    print("\nLectura: valores de 1-1 muy por debajo de 1,00x y más de 11 distintos por jornada indican que el "
          "operador evita repetir animales. Esa es la estructura que usan los modelos.")


if __name__ == "__main__":
    main()
