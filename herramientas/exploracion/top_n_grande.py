# -*- coding: utf-8 -*-
"""¿Rinde jugar muchos animales (Top-15 a Top-23) a 10 $ cada uno?

Lee la misma matriz walk-forward de DESARROLLO que estrategia_top5.py
(calor_cache.npz; si no existe, la calcula una vez). NO toca el tramo de prueba.
Imprime, para cada Top-N plano: tasa de acierto, el equilibrio N/30, la ganancia
por sorteo a 10 $/animal con IC95 por bloques de jornada, y cómo le va a una
banca de 300 $ jugando todos los sorteos durante un mes.

Uso:  python herramientas/exploracion/top_n_grande.py
"""
import os
import runpy
import sys
import io
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
# Reutiliza la carga de estrategia_top5.py (caché o cálculo) sin repetir su salida.
_so = sys.stdout; sys.stdout = io.StringIO()
try:
    g = runpy.run_path(os.path.join(AQUI, "estrategia_top5.py"))
finally:
    sys.stdout = _so
P, H, puesto, n = g["P"], g["H"], g["puesto"], g["n"]
PAGO, FICHA = 30, 10
BLK = 12

print(f"desarrollo walk-forward: n = {n} sorteos (a {FICHA} $ por animal)\n")
print(f"{'Top':<6}{'apuesta':>8}{'acierta':>9}{'necesita':>10}{'gana/sorteo':>13}   IC95 (bloques de jornada)")
rng = np.random.default_rng(1)
nb = n // BLK
idx = rng.integers(0, nb, (2000, nb))
for N in (5, 15, 18, 20, 23, 25):
    gan = np.where(puesto <= N, PAGO * FICHA - N * FICHA, -N * FICHA).astype(float)
    pb = gan[:nb * BLK].reshape(nb, BLK).mean(1)
    lo, hi = np.percentile(pb[idx].mean(1), [2.5, 97.5])
    print(f"{N:<6}{N*FICHA:>7}${(puesto <= N).mean()*100:>8.1f}%{N/30*100:>9.1f}%{gan.mean():>+12.1f}$   [{lo:+.1f}, {hi:+.1f}]")

print("\nTop-23 a 10 $ (230 $ por sorteo), banca 300 $, 12 sorteos al día, 30 días reales seguidos:")
gan = np.where(puesto <= 23, 70.0, -230.0)
L = 12 * 30
finales, quiebras = [], 0
for ini in range(0, n - L, 12):
    b = 300.0
    for x in gan[ini:ini + L]:
        if b < 230:
            quiebras += 1
            break
        b += x
    finales.append(b)
f = np.array(finales)
print(f"  meses simulados: {len(f)}")
print(f"  se quedó sin plata para seguir: {quiebras/len(f)*100:.0f} % de los meses")
print(f"  banca final típica (mediana): {np.median(f):.0f} $ · 1 de cada 10 termina por encima de {np.percentile(f, 90):.0f} $")
dias = gan[:n // 12 * 12].reshape(-1, 12).sum(1)
print(f"  días en ganancia: {(dias > 0).mean()*100:.0f} % · día típico {np.median(dias):+.0f} $ · peor día {dias.min():+.0f} $")
