# -*- coding: utf-8 -*-
"""Tarea B apoyo: tasa base de 'top congelado' bajo el modelo sano.
Sobre el desarrollo walk-forward: distribución de longitudes de racha en que
el CONJUNTO del top-3 se mantiene idéntico entre sorteos consecutivos.
Distingue: mismo conjunto / mismo orden exacto."""
import os, sys
import numpy as np

RUTA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERR = os.path.join(RUTA, "herramientas")
sys.path.insert(0, HERR)
import lotto_eval as LE

datos = LE.cargar(os.path.join(RUTA, "historial.txt"))
modelo = LE.cargar_modelo(os.path.join(HERR, "modelos", "ensamble_v2.py"))
print("matriz walk-forward...")
M = modelo.predecir(datos, LE.W)
y = datos.seq[LE.W:]
P = M[: LE.CORTE_FIJO - LE.W]
n = len(P)
R = np.argsort(-P, axis=1)
t3 = [frozenset(r[:3]) for r in R]
o3 = [tuple(r[:3]) for r in R]

def rachas(seq):
    lens = []
    act = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i - 1]:
            act += 1
        else:
            lens.append(act); act = 1
    lens.append(act)
    return np.array(lens)

for nombre, seq in (("mismo conjunto top-3", t3), ("mismo orden exacto top-3", o3)):
    L = rachas(seq)
    print(f"\n{nombre}: {len(L)} rachas en {n} sorteos")
    for k in (2, 3, 4, 5, 6):
        frac = (L >= k).sum() / len(L)
        print(f"  P(racha >= {k} sorteos) = {frac*100:.1f}%   ({(L >= k).sum()} rachas)")

# enriquecido: racha del conjunto CONDICIONADO a ir perdiendo (0 aciertos en la racha)
hits = np.array([y[i] in t3[i] for i in range(n)])
L = rachas(t3)
ini = 0
perdiendo = []
for ln in L:
    seg = hits[ini:ini + ln]
    if not seg.any() and ln >= 2:
        perdiendo.append(ln)
    ini += ln
perdiendo = np.array(perdiendo)
print(f"\nrachas de conjunto estable SIN ningun acierto dentro: {len(perdiendo)}")
for k in (3, 4, 5, 6):
    print(f"  P(racha perdedora >= {k}) = {(perdiendo >= k).mean()*100:.1f}%")

# probabilidad de 0/12 en top-3 (para la tabla del reporte)
h3 = hits.mean()
print(f"\nhit rate top-3 dev = {h3*100:.2f}%   P(0/12)={(1-h3)**12:.4f}   P(0/11)={(1-h3)**11:.4f}")
