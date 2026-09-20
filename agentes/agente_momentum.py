# -*- coding: utf-8 -*-
"""Agente momentum / frecuencia dinamica (memoria lenta a dos escalas).

Base  : conteos con decaimiento exponencial (EMA) a DOS vidas medias:
        hl=40 (corto plazo, "calientes" ahora) y hl=160 (medio plazo).
        score = W1*log(freq40) + W2*log(freq160), con W1 > W2 para que lo
        reciente pese mas. En escala log para que sea aditivo y comparable
        con los demas terminos. Documentado en
        herramientas/modelos/intradia_v2.py (vida media ~40 y ~160 a favor).

Aditivos suaves (documentados, no reajustados walk-forward):
  (a) efecto hora del dia: frecuencia condicionada por la hora del sorteo a
      predecir, con suavizado fuerte hacia la global (ALFA_HORA pseudo-
      observaciones); peso bajo W_HORA.
  (b) efecto dia de la semana: igual que (a) pero por dweek, con suavizado
      aun mas fuerte (ALFA_DOW) y peso menor W_DOW.
  (c) contra-peso anti-recencia: resta fija en escala log a los animales que
      salieron en los ultimos 1-2 sorteos (PEN_1, PEN_2), para no perseguir
      lo reciente de forma ingenua (la repeticion inmediata es ~0.74% vs
      2.63% de azar; ver exploracion 2026-09-14 en agente_antirep.py).

Determinista, numpy, O(T) por llamada en C (bincount). Sin estado interno:
misma entrada -> misma salida siempre.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import Agente, K  # noqa: E402

HORAS = 12      # sorteos por dia: 8AM=0 ... 7PM=11
DIAS = 7

# Vidas medias de las dos EMA (en sorteos)
HL_CORTO = 40.0
HL_LARGO = 160.0
# Pesos de las dos escalas (lo reciente pesa mas)
W1 = 1.0
W2 = 0.5

# (a)/(b) condicionales con suavizado hacia la global
ALFA_HORA = 80.0    # pseudo-observaciones del prior global en frecuencia por hora
ALFA_DOW = 200.0    # suavizado mas fuerte aun (menos datos por celda)
W_HORA = 0.15
W_DOW = 0.08

# (c) contra-peso anti-recencia (en unidades de log-puntaje)
PEN_1 = 0.20   # animal del sorteo inmediato anterior y[t-1]
PEN_2 = 0.08   # animal de hace dos sorteos y[t-2]

EPS = 1e-12


class AgenteMomentum(Agente):
    nombre = "momentum"
    descripcion = ("Momentum a dos escalas: EMA(40)+EMA(160) en log-frecuencia, "
                   "+ hora/dia suavizados, - castigo suave por salir en los "
                   "ultimos 1-2 sorteos")

    # ------------------------------------------------------------------
    def predecir(self, seq, horas, dweek):
        t = len(seq)
        if t == 0:
            return [1.0] * K

        s = np.asarray(seq, dtype=np.int64)

        # ---- EMAs a dos escalas, normalizadas a frecuencia relativa
        d1 = 0.5 ** (1.0 / HL_CORTO)
        d2 = 0.5 ** (1.0 / HL_LARGO)
        edad = np.arange(t - 1, -1, -1, dtype=np.float64)  # 0 = sorteo mas reciente
        e1 = np.bincount(s, weights=d1 ** edad, minlength=K)
        e2 = np.bincount(s, weights=d2 ** edad, minlength=K)
        f1 = e1 / e1.sum()
        f2 = e2 / e2.sum()

        score = W1 * np.log(f1 + EPS) + W2 * np.log(f2 + EPS)

        # ---- (a) hora del sorteo a predecir (la siguiente en el ciclo)
        h_sig = 0 if horas[-1] == HORAS - 1 else horas[-1] + 1
        h = np.asarray(horas, dtype=np.int64)
        m_h = h == h_sig
        n_h = int(m_h.sum())
        cnt_h = np.bincount(s[m_h], minlength=K)
        cond_h = (cnt_h + ALFA_HORA * f2) / (n_h + ALFA_HORA)
        score = score + W_HORA * np.log((cond_h + EPS) / (f2 + EPS))

        # ---- (b) dia de la semana del sorteo a predecir
        dw_sig = dweek[-1] if horas[-1] != HORAS - 1 else (dweek[-1] + 1) % DIAS
        dw = np.asarray(dweek, dtype=np.int64)
        m_d = dw == dw_sig
        n_d = int(m_d.sum())
        cnt_d = np.bincount(s[m_d], minlength=K)
        cond_d = (cnt_d + ALFA_DOW * f2) / (n_d + ALFA_DOW)
        score = score + W_DOW * np.log((cond_d + EPS) / (f2 + EPS))

        # ---- (c) contra-peso anti-recencia
        score[s[-1]] -= PEN_1
        if t >= 2:
            score[s[-2]] -= PEN_2

        return [float(x) for x in score]


# Instancia por defecto usada por el orquestador
agente = AgenteMomentum()
