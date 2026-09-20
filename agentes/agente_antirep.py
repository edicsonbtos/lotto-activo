# -*- coding: utf-8 -*-
"""Agente anti-repeticion intradia.

Los puntajes devueltos son LOG-PROBABILIDADES (log p, p ya normalizada):
asi `agente.softmax(sc)` devuelve exactamente p y el orden argmax/top-k
es identico al de p. Todas las p > 0 por el suavizado, asi que log es seguro.

Base  : frecuencia por hora del dia (8AM=0 ... 7PM=11) suavizada con un prior
        global, igual que el modelo de referencia herramientas/modelos/antirep_v1.py.

Penalizadores (multiplicadores fijos, documentados; no reajustados walk-forward):
  (a) animales que YA salieron hoy (misma fecha): multiplicador por cada salida
      hoy = 0.70 * 0.92**hoy, siendo hoy = sorteos previos del mismo dia.
      Penaliza mas fuerte cuantas mas veces salio y cuanto mas temprana es la hora
      (pocas salidas hoy -> el castigo por salida es mayor), y una salida temprana
      pesa mas que una reciente, pues queda multiplicada en cada paso.
  (b) animal del sorteo inmediato anterior  y[t-1]        : x 0.30
  (c) animal de la MISMA HORA del dia anterior y[t-12]    : x 0.80

Justificacion empirica (exploracion 2026-09-14):
  * repeticion inmediata y[t]==y[t-1]           : 0.74%  vs 2.63% de azar
  * mismo animal a la misma hora del dia anterior: 2.21% vs 2.63% de azar
  * animales repetidos dentro del mismo dia aparecen claramente menos de lo
    que sugeriria la independencia (anti-clumping intradia del sorteo).

Determinista, solo stdlib, O(T) en una pasada incremental (rapida porque el
evaluador llama predecir() en cada paso y no re-procesa el historial).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base  # noqa: E402

K = base.K
HORAS = 12  # sorteos por dia: 8AM=0 ... 7PM=11

# Penalizadores fijos (documentados, no reajustados)
M_INMEDIATO = 0.30   # (b) y[t-1]
M_MISMA_HORA = 0.80  # (c) y[t-12]
P_SALIDA_HOY = 0.70  # (a) factor geometrico por salida previa hoy
DECAIMENTO_HOY = 0.92  # (a) cada salida adicional hoy castiga un poco menos
SUAV_GLOBAL = 80.0   # pseudo-observaciones del prior global en la frecuencia por hora


class AgenteAntirep(base.Agente):
    nombre = "antirep"
    descripcion = ("Anti-repeticion intradia: frecuencia por hora x penalizadores "
                   "(salio hoy, salio en el sorteo previo, salio a esta hora ayer)")

    def __init__(self):
        self._t = 0
        self._gc = [0.0] * K          # conteo global por animal
        self._hc = [[0.0] * K for _ in range(HORAS)]  # conteo por hora
        self._hoy = [0.0] * K         # salidas del animal en el dia actual
        self._hay_hist = False

    # ------------------------------------------------------------------
    def _puntajes(self, hora_sig):
        g = sum(self._gc)
        prior = [c / g if g > 0 else 1.0 / K for c in self._gc]
        fila = self._hc[hora_sig]
        p = [fila[i] + SUAV_GLOBAL * prior[i] for i in range(K)]
        # (a) penalizar animales que ya salieron hoy
        if self._hay_hist:
            for i in range(K):
                k = self._hoy[i]
                if k > 0:
                    p[i] *= P_SALIDA_HOY * (DECAIMENTO_HOY ** (k - 1))
        # (b) y (c) requieren historial
        return p

    def predecir(self, seq, horas, dweek):
        t = len(seq)
        if t == 0:
            return [1.0] * K

        # Reconstruir estado incrementalmente si se avanzo paso a paso
        # (el evaluador/orquestador llama con seq[:t], seq[:t+1], ...).
        if t < self._t or t - self._t > 1:
            self._reiniciar()
        # Alimentar los sorteos nuevos (desde self._t hasta t-1)
        while self._t < t:
            i = self._t
            if i > 0 and horas[i] == 0 and self._hay_hist:
                self._hoy = [0.0] * K   # cambio de dia
            a = seq[i]
            self._gc[a] += 1.0
            self._hc[horas[i]][a] += 1.0
            self._hoy[a] += 1.0
            self._hay_hist = True
            self._t = i + 1

        hora_sig = 0 if horas[-1] == HORAS - 1 else horas[-1] + 1
        p = self._puntajes(hora_sig)
        if t >= 1:
            p[seq[t - 1]] *= M_INMEDIATO
        if t >= HORAS:
            p[seq[t - HORAS]] *= M_MISMA_HORA
        s = sum(p)
        return [math.log(x / s) for x in p]    # log-probabilidades (p > 0)

    def _reiniciar(self):
        self._t = 0
        self._gc = [0.0] * K
        self._hc = [[0.0] * K for _ in range(HORAS)]
        self._hoy = [0.0] * K
        self._hay_hist = False


# Instancia por defecto usada por el orquestador
agente = AgenteAntirep()
