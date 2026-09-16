"""Línea base: azar puro (1/38 para todos)."""
import numpy as np

class Modelo:
    nombre = "uniforme"
    def predecir(self, datos, desde):
        return np.full((len(datos) - desde, 38), 1 / 38)
