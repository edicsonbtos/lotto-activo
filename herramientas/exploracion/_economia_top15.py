# -*- coding: utf-8 -*-
"""Tarea C: economía del top-N.
Hit rate walk-forward del ensamble en DESARROLLO [2000, 9357) para top-1/3/5/15,
con IC95 de Wilson y EV a pago 30x con apuesta igual repartida (equilibrio N/30).
Solo lee modelos; no los toca."""
import os, sys
import numpy as np

RUTA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERR = os.path.join(RUTA, "herramientas")
sys.path.insert(0, HERR)
import lotto_eval as LE

PAGO = 30
datos = LE.cargar(os.path.join(RUTA, "historial.txt"))
modelo = LE.cargar_modelo(os.path.join(HERR, "modelos", "ensamble_v2.py"))
print("calculando matriz walk-forward de ensamble_v2 sobre", len(datos), "sorteos...")
M = modelo.predecir(datos, LE.W)          # (n-W, 38)
y = datos.seq[LE.W:]

dev = slice(0, LE.CORTE_FIJO - LE.W)      # desarrollo: filas W..CORTE_FIJO
P, Y = M[dev], y[dev]
n = len(Y)
print(f"desarrollo n={n}")

R = np.argsort(-P, axis=1)

def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, c - h, c + h

print(f"\n{'top-N':<7}{'aciertos':<10}{'tasa':<9}{'IC95 bajo':<11}{'IC95 alto':<11}{'equilibrio N/30':<17}{'EV@30x':<9}{'EV IC bajo':<11}")
for k in (1, 3, 5, 15):
    hits = sum(1 for i in range(n) if Y[i] in R[i, :k])
    p, lo, hi = wilson(hits, n)
    ev = (PAGO * hits - k * n) / (k * n)      # apuesta 1 en cada uno de los k
    ev_lo = (PAGO * lo - k) / k
    ev_hi = (PAGO * hi - k) / k
    print(f"{k:<7}{hits:<10}{p*100:<9.2f}{lo*100:<11.2f}{hi*100:<11.2f}{k/PAGO*100:<17.1f}{ev*100:<9.1f}{ev_lo*100:<11.1f}")

# mismo cálculo pero sobre el tablero REAL de 37 (el bin 00 es fantasma):
# penaliza los tops que incluyen el bin 1 ("00") — esos aciertos nunca pagan.
R37 = R.copy()
tiene00 = R37[:, :15] == 1
print(f"\nbin 00 (fantasma) dentro del top-15 en desarrollo: {tiene00.any(1).sum()} de {n} sorteos "
      f"({tiene00.any(1).mean()*100:.1f}%)")

# concentración del top-15 actual (probabilidad acumulada)
pm = P[:, R[:, :15]].sum(1)
print(f"masa de probabilidad del top-15: media {pm.mean()*100:.1f}%  "
      f"min {pm.min()*100:.1f}%  max {pm.max()*100:.1f}%")

# Kelly 1/4 para top-3 y top-15 con p = límite inferior IC95
p3, lo3, _ = wilson(sum(1 for i in range(n) if Y[i] in R[i, :3]), n)
p15, lo15, _ = wilson(sum(1 for i in range(n) if Y[i] in R[i, :15]), n)
for k, lo in ((3, lo3), (15, lo15)):
    B = (PAGO - k) / k
    f = max(0.0, (B * lo - (1 - lo)) / B) * 0.25
    print(f"Kelly 1/4 top-{k}: p(IC bajo)={lo*100:.2f}%  fracción de banca={f*100:.2f}%")
