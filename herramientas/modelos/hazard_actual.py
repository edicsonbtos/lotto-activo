"""Réplica fiel del modelo de servidor.py (tasa de aparición por tramo de retraso).

Incremental: la fila t usa los conteos de los sorteos 1..t-1, igual que
estado(filas[:t]) en el servidor.
"""
import numpy as np

BINS = [0,1,2,3,4,5,6,8,10,13,17,22,28,36,46,60,80,10**9]
K = 38

def bidx(g):
    return int(np.searchsorted(BINS, g, side="right") - 1)

class Modelo:
    nombre = "hazard_actual (servidor.py)"
    def __init__(self, bins=None, minimo=30):
        self.bins = bins or BINS; self.minimo = minimo
    def predecir(self, datos, desde):
        seq = datos.seq; n = len(seq); nb = len(self.bins)
        edges = np.array(self.bins)
        hit = np.zeros(nb); tot = np.zeros(nb)
        last = np.full(K, -10**7)
        out = np.empty((n - desde, K))
        for t in range(n):
            if t >= desde:
                g = np.where(last >= 0, (t - 1 - last) + 1, 10**6)   # retraso del próximo
                b = np.searchsorted(edges, g, side="right") - 1
                hz = np.where(tot >= self.minimo, hit / np.maximum(tot, 1), 1 / K)
                out[t - desde] = hz[b]
            v = seq[t]
            if t > 0:
                g = np.where(last >= 0, t - last, 10**6)
                b = np.searchsorted(edges, g, side="right") - 1
                np.add.at(tot, b, 1)
                hit[b[v]] += 1
            last[v] = t
        return out
