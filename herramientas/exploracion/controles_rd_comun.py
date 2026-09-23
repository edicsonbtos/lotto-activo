# -*- coding: utf-8 -*-
"""Hilo 7, controles: utilidades comunes (solo lectura; no toca produccion).

cache_todo.npz de rdint (P0, P1, y, hora, dia, tramo, fecha) + Lotto Activo por fecha/hora para
rehacer x con otro dia (placebo) o con la hora desplazada (desfase k).
"""
import os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.dirname(AQUI)
RDINT = os.path.join(HERR, "rdint")
sys.path.insert(0, HERR); sys.path.insert(0, RDINT)
import lotto_eval as LE
import datos as DT
import modelo as MB
import correr_modelo as CM

K = LE.K


def cargar_cache():
    z = np.load(os.path.join(RDINT, "cache_todo.npz"))
    P0 = LE.normalizar(z["P0"].astype(np.float64))
    P1 = LE.normalizar(z["P1"].astype(np.float64))
    return dict(P0=P0, P1=P1, y=z["y"].astype(int), hora=z["hora"].astype(int), dia=z["dia"].astype(int),
                tramo=z["tramo"], fecha=z["fecha"])


def la_dict():
    return DT._la_por_fecha()


def construir_X(fechas, horas, la, k=0, fuente=None):
    """x con LA desplazado k horas y/o tomado de la fecha fuente[t] (None = misma fecha).
    Devuelve X (n,38,3) float32 igual que modelo.features y la_h desplazado (n,)."""
    n = len(fechas)
    la_h = np.full(n, -1); la_h1 = np.full(n, -1); la_hoy = np.zeros((n, K), np.int8)
    for t in range(n):
        f = fechas[t] if fuente is None else fuente[t]
        dia = la.get(f, {}) if f is not None else {}
        h = int(horas[t]) + k
        if 0 <= h <= 11:
            la_h[t] = dia.get(h, -1)
        if 1 <= h <= 12:
            la_h1[t] = dia.get(h - 1, -1)
        for hh, s in dia.items():
            if hh <= h:
                la_hoy[t, s] += 1
    return MB.features(la_h, la_h1, la_hoy), la_h


def delta(P1, P0, y):
    return CM.mbits(P1, y) - CM.mbits(P0, y)


def boot(v, dia, rng):
    return CM.boot_media(v, dia, rng)


def boot_razon(num, den, dia, rng, nboot=2000):
    """Razon sum(num)/sum(den) con IC95 por bootstrap de dias."""
    _, g = np.unique(dia, return_inverse=True)
    N = np.bincount(g, weights=num); D = np.bincount(g, weights=den); nd = len(N)
    idx = rng.integers(0, nd, size=(nboot, nd))
    b = N[idx].sum(1) / D[idx].sum(1)
    return float(num.sum() / den.sum()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))
