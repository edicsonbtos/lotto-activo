# -*- coding: utf-8 -*-
"""Test directo sobre el ENSAMBLE: penalizacion anti-repeticion en el bloque
actual (T=12250..n), walk-forward. Multiplicadores estimados SOLO con datos < T.
Compara Top-1/3/5 y mbits con y sin penalizacion. NO modifica archivos.
"""
import json, os, sys
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

K, HORAS = 38, 12
datos = LE.cargar()
n = len(datos)
seq, hora = datos.seq, datos.hora
pj = json.load(open(os.path.join(RAIZ, "pesos_ensamble.json"), encoding="utf-8"))
w_ens = np.array(pj["pesos"])
T = pj["frontera"]

# multiplicadores SOLO con datos < T
rep = float(np.sum(seq[1:T] == seq[:T - 1]))
m1 = (rep / (T - 1)) * K
sameh = float(np.sum(seq[HORAS:T] == seq[:T - HORAS]))
m2 = (sameh / (T - HORAS)) * K
print(f"n={n} bloque T={T}  m1={m1:.3f} m2={m2:.3f}  (estimados con sorteos <{T})")

logs = []
for nombre in pj["base"]:
    sub = LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", nombre + ".py"))
    P = LE.normalizar(sub.predecir(datos, T))
    logs.append(np.log(np.clip(P, 1e-9, None)))
    print(f"  {nombre} ok", flush=True)
L = np.stack(logs, axis=1)
L -= np.log(np.exp(L).sum(2, keepdims=True))
z = np.einsum("nmk,m->nk", L, w_ens)
z -= z.max(1, keepdims=True)
P = np.exp(z); P /= P.sum(1, keepdims=True)

y = seq[T:]
def penal(P, m1v, m2v):
    Q = P.copy()
    for j in range(P.shape[0]):
        t = T + j
        Q[j, seq[t - 1]] *= m1v
        if t >= HORAS:
            Q[j, seq[t - HORAS]] *= m2v
    return LE.normalizar(Q)

b = LE.metricas(P, y)
print(f"\nENSAMBLE bloque actual (n={len(y)}): Top1 {b['top1']['tasa']*100:.2f}%  Top3 {b['top3']['tasa']*100:.2f}%  "
      f"Top5 {b['top5']['tasa']*100:.2f}%  {b['logver']['bits_por_sorteo']*1000:+.2f} mbits")
for m1v, m2v, etq in [(m1, 1.0, "solo m1"), (1.0, m2, "solo m2"), (m1, m2, "m1 x m2")]:
    mb = LE.metricas(penal(P, m1v, m2v), y)
    print(f"  +{etq:<8}: Top1 {mb['top1']['tasa']*100:.2f}%  Top3 {mb['top3']['tasa']*100:.2f}%  "
          f"Top5 {mb['top5']['tasa']*100:.2f}%  {mb['logver']['bits_por_sorteo']*1000:+.2f} mbits")
print("\nOJO: 241 sorteos = muestra pequena; una diferencia <2pp es ruido.")
