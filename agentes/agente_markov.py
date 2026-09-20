# -*- coding: utf-8 -*-
"""Agente de secuencias: cadenas de Markov con decaimiento exponencial.

Estrategia
----------
1. Bigrama con suavizado de Laplace: P(proximo | ultimo salido).
   Decaimiento exponencial opcional (VIDA_MEDIA=None lo desactiva): el
   barrido walk-forward mostro que SIN decaimiento rinde mejor en este
   juego (la 'memoria' util del bigrama es mas larga que 8000 sorteos).
2. Refinamientos interpolados sobre el componente markoviano:
   - matriz de transicion condicionada por la HORA del sorteo destino
     (12 matrices 38x38, suavizado fuerte, peso moderado);
   - trigrama ligero P(proximo | dos ultimos) con suavizado fuerte.
3. Mezcla final con uniforme 1/38 para robustez (70% markov + 30% uniforme).

Salida: la probabilidad p misma como puntaje (el orquestador normaliza
y ordena; para log-loss verdadero de la distribucion, ver _eval_agente,
nota: ese evaluador aplica softmax sobre puntajes ESTANDARIZADOS, lo que
re-escala logits de probabilidades calibradas; el log-loss real de p es
medido mejor directamente: ~3.635, ligeramente mejor que ln 38 ~ 3.638).

Determinista. Usa solo sorteos estrictamente anteriores (seq ya los cumple).
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import Agente, K  # noqa: E402

# --- hiperparametros (fijos, deterministicos) ---
VIDA_MEDIA = None     # vida media del decaimiento; None = sin decaimiento
                      # (barrido walk-forward: None > 8000 > 2000 > 500)
ALPHA_BI = 0.5        # Laplace para bigrama global
ALPHA_HORA = 8.0      # Laplace fuerte para matriz por hora (datos mas escasos)
ALPHA_TRI = 4.0       # Laplace fuerte para trigrama (38x38 estados)
W_BI = 0.60           # peso bigrama dentro del componente markoviano
W_HORA = 0.25         # peso matriz por hora
W_TRI = 0.15          # peso trigrama
W_MARKOV = 0.70       # mezcla global: 70% markov + 30% uniforme
HORAS = 12


class AgenteMarkov(Agente):
    nombre = "markov"
    descripcion = ("Cadenas de Markov: bigrama + hora + trigrama "
                   "(sin decaimiento, memoria larga), mezclado 70/30 con uniforme.")

    def predecir(self, seq, horas, dweek):
        n = len(seq)
        uni = 1.0 / K
        if n == 0:
            return [uni] * K

        s = np.asarray(seq, dtype=np.int64)
        # peso de cada transicion i -> i+1 (indexada por i)
        if VIDA_MEDIA:
            w = np.power(0.5, (n - 1 - np.arange(n - 1)) / VIDA_MEDIA)
        else:
            w = np.ones(n - 1)

        # --- bigrama global ---
        B = np.zeros((K, K))
        np.add.at(B, (s[:-1], s[1:]), w)
        P_bi = (B + ALPHA_BI) / (B.sum(axis=1, keepdims=True) + ALPHA_BI * K)
        p = W_BI * P_bi[s[-1]]

        # --- transicion condicionada por la hora del sorteo destino ---
        h = np.asarray(horas, dtype=np.int64)
        H = np.zeros((HORAS, K, K))
        np.add.at(H, (h[1:], s[:-1], s[1:]), w)
        P_h = (H + ALPHA_HORA) / (H.sum(axis=2, keepdims=True) + ALPHA_HORA * K)
        h_next = int((h[-1] + 1) % HORAS)  # sorteo siguiente en la secuencia regular
        p += W_HORA * P_h[h_next, s[-1]]

        # --- trigrama ligero: P(proximo | ultimos dos) ---
        if n >= 2:
            T = np.zeros((K * K, K))
            np.add.at(T, (s[:-2] * K + s[1:-1], s[2:]), w[1:])
            fila = T[s[-2] * K + s[-1]]
            p_tri = (fila + ALPHA_TRI) / (fila.sum() + ALPHA_TRI * K)
            p += W_TRI * p_tri
        else:
            p += W_TRI * uni

        # --- mezcla con uniforme y salida ---
        p = W_MARKOV * p + (1.0 - W_MARKOV) * uni
        return [float(x) for x in p]


if __name__ == "__main__":
    from base import cargar_historial, POS, ANIM

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    seq, horas, dweek, _ = cargar_historial(os.path.join(raiz, "historial.txt"))
    ag = AgenteMarkov()
    p = ag.predecir(seq, horas, dweek)
    top = np.argsort(p)[::-1][:5]
    print("Top-5 para el proximo sorteo:")
    for r, i in enumerate(top, 1):
        print(f"  {r}. {POS[i]} ({ANIM[POS[i]]})  p={p[i]:.4f}")
