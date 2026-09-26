# -*- coding: utf-8 -*-
"""Auditoría: (a) rasgos12.transiciones == máscaras independientes; (b) pesos congelados V0 aplicados
sobre base uniforme en [300,2000) (fuera de ajuste y de sondeo) frente a dev; (c) look-ahead por hora/dia."""
import os, sys, json
import numpy as np
AQ = os.path.dirname(os.path.abspath(__file__)); AG = os.path.dirname(AQ); MN = os.path.dirname(AG)
sys.path.insert(0, MN); sys.path.insert(0, AG)
import arnes as A, rasgos12 as R
D = A.datos().prefijo(A.CORTE); seq = np.asarray(D.seq); n = len(seq)
T = R.transiciones(D, 300)                        # (n-300, 38, 6)
z = np.load(os.path.join(AQ, "mascaras.npz")); tt, M = z["t"], z["M"]
B = (T[tt - 300] > 0).transpose(0, 2, 1)          # (m, 6, 38)
print("(a) filas intradía con rasgo != máscara independiente:", int((B != M).any(axis=(1, 2)).sum()), "de", len(tt))
# filas no intradía deben ser 0
mask_intra = np.zeros(n - 300, bool); mask_intra[tt - 300] = True
print("    filas primer-sorteo con rasgo != 0:", int((T[~mask_intra] != 0).any(axis=(1, 2)).sum()))
w0 = np.array(json.load(open(os.path.join(AG, "parametros_V0.json"), encoding="utf-8"))["w"])[27:]
w1 = np.array(json.load(open(os.path.join(AG, "parametros_V1.json"), encoding="utf-8"))["w"])[27:]
def dmb(Tsub, y, w, cols=slice(None)):
    ww = np.zeros(6); ww[cols] = w[cols]
    zz = Tsub @ ww; zz -= zz.max(1, keepdims=True); Q = np.exp(zz); Q /= Q.sum(1, keepdims=True)
    return 1000 * np.log2(Q[np.arange(len(y)), y] * 38)
dia = np.asarray(D.dia)
for nombre, lo, hi in [("PRE [300,2000)", 300, 2000), ("DEV [2000,9357)", 2000, A.CORTE)]:
    Ts = T[lo - 300:hi - 300].astype(float); y = seq[lo:hi]; dd = dia[lo:hi]
    for etq, w, cols in [("V0 6 pesos", w0, slice(None)), ("V0 solo T1-T3", w0, slice(0, 3)), ("V0 solo R1-R3", w0, slice(3, 6)),
                         ("V1 pesos trans.", w1, slice(None))]:
        m, a, b = A.ic_bloques(dmb(Ts, y, w, cols), dd)
        print(f"(b) {nombre:16s} {etq:16s} Δmbits vs uniforme {m:+6.2f} [{a:+.2f}, {b:+.2f}]")
# (c) look-ahead por calendario: cambiar hora/dia/seq futuros no debe cambiar filas <= c
rng = np.random.default_rng(1)
base = R.construir(D.prefijo(3000), 2000)[0]
for c in (2300, 2600, 2900):
    s2 = np.array(D.seq[:3000]).copy(); s2[c:] = rng.integers(0, 38, 3000 - c)
    h2 = np.array(D.hora[:3000]).copy(); h2[c:] = rng.integers(0, 12, 3000 - c)
    d2 = np.array(D.dia[:3000]).copy(); d2[c:] = d2[c:] + rng.integers(0, 3, 3000 - c).cumsum()
    Dx = type(D)(s2, h2, np.array(D.dow[:3000]), d2, list(D.fecha[:3000]))
    alt = R.construir(Dx, 2000)[0]
    print(f"(c) corte {c}: max|Δ| filas < c (seq+hora+dia futuros alterados):", float(np.abs(base[:c - 2000] - alt[:c - 2000]).max()))
# (c2) solo seq futura (desde c) alterada: filas <= c idénticas (fila c usa seq[:c])
for c in (2300, 2600, 2900):
    s2 = np.array(D.seq[:3000]).copy(); s2[c:] = rng.integers(0, 38, 3000 - c)
    Dx = type(D)(s2, np.array(D.hora[:3000]), np.array(D.dow[:3000]), np.array(D.dia[:3000]), list(D.fecha[:3000]))
    alt = R.construir(Dx, 2000)[0]
    print(f"(c2) corte {c}: max|Δ| filas <= c (solo seq futura):", float(np.abs(base[:c - 2000 + 1] - alt[:c - 2000 + 1]).max()))
