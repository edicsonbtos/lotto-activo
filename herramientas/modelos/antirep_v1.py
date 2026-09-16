# -*- coding: utf-8 -*-
"""Anti-repeticion: frecuencia por hora suavizada x penalizadores empiricos.

Dos sesgos medidos en el historial (2026-09-14, consejo de exploracion):
  * repeticion inmediata y[t] == y[t-1]:              0.74% vs 2.63% de azar
  * mismo animal a la misma hora del dia anterior:    2.21% vs 2.63% de azar
    (y[t] == y[t-12] con 12 sorteos/dia)

Modelo: p_t(i) prop. frecuencia_hora(i; datos<t, suavizado global s)
        * m1^[i == y[t-1]] * m2^[i == y[t-12]]
Los multiplicadores m1, m2 = tasa_empirica / (1/K) se reajustan cada R sorteos
usando SOLO sorteos < t (walk-forward estricto), con suavizado de Laplace.
"""
import numpy as np

K = 38
HORAS = 12


class Modelo:
    nombre = "antirep_v1"

    def __init__(self, R=250, s=80.0, suav_mult=200.0, quema=500):
        self.R = R                  # cadencia de reajuste de multiplicadores
        self.s = s                  # suavizado de la frecuencia por hora
        self.suav_mult = suav_mult  # pseudo-observaciones de los multiplicadores
        self.quema = quema          # minimo de historial antes de activar penalizadores

    def _mult(self, seq, t):
        """Multiplicadores estimados SOLO con seq[:t]."""
        if t < self.quema:
            return 1.0, 1.0
        a0 = self.suav_mult
        rep = float(np.sum(seq[1:t] == seq[:t - 1]))
        r1 = (rep + a0 / K) / (t - 1 + a0)
        m1 = float(np.clip(r1 * K, 0.05, 3.0))
        if t > HORAS + 100:
            sameh = float(np.sum(seq[HORAS:t] == seq[:t - HORAS]))
            r2 = (sameh + a0 / K) / (t - HORAS + a0)
            m2 = float(np.clip(r2 * K, 0.05, 3.0))
        else:
            m2 = 1.0
        return m1, m2

    def predecir(self, datos, desde):
        seq = np.asarray(datos.seq)
        hora = np.asarray(datos.hora)
        n = len(seq)
        out = np.empty((n - desde, K))
        gc = np.zeros(K)                 # conteo global
        hc = np.zeros((HORAS, K))        # conteo por hora
        m1 = m2 = 1.0
        prox_T = None
        for t in range(n):
            if t >= desde:
                if prox_T is None or t >= prox_T:
                    m1, m2 = self._mult(seq, t)
                    prox_T = t + self.R
                g = gc.sum()
                prior = gc / g if g > 0 else np.full(K, 1.0 / K)
                p = hc[hora[t]] + self.s * prior
                p = p / p.sum()
                p[seq[t - 1]] *= m1
                if t >= HORAS:
                    p[seq[t - HORAS]] *= m2
                out[t - desde] = p / p.sum()
            gc[seq[t]] += 1.0
            hc[hora[t], seq[t]] += 1.0
        return out
