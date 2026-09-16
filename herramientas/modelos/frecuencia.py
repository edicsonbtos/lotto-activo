"""Línea base: frecuencia histórica con suavizado de Dirichlet."""
import numpy as np

class Modelo:
    nombre = "frecuencia (Dirichlet a=50)"
    def __init__(self, alfa=50.0):
        self.alfa = alfa
    def predecir(self, datos, desde):
        seq = datos.seq; n = len(seq)
        c = np.bincount(seq[:desde], minlength=38).astype(float)
        out = np.empty((n - desde, 38))
        for t in range(desde, n):
            out[t - desde] = c + self.alfa
            c[seq[t]] += 1
        return out
