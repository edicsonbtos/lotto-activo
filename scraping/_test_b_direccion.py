# -*- coding: utf-8 -*-
"""Caracterizacion del z negativo lottoactivo -> lottoactivordint:
¿la anti-coincidencia ocurre solo cuando B sortea DESPUES de A (mecanismo
'evitar lo ya salio hoy') o tambien cuando B sortea antes (lo cual serial
una senal estadistica pura, no explicable por memoria del operador)?
"""
import io
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

RAIZ = core.RAIZ
SALIDA = os.path.join(RAIZ, "datos_multiloteria")


def minutos(hora):
    hh, mm = hora.split(":")
    return int(hh) * 60 + int(mm)


def cargar(slug):
    por_dia = defaultdict(dict)
    with io.open(os.path.join(SALIDA, "%s.csv" % slug), encoding="utf-8") as f:
        next(f)
        for l in f:
            p = l.rstrip("\n").split(",")
            por_dia[p[0]][minutos(p[1])] = int(p[3])
    return por_dia


A = cargar("lottoactivo")
B = cargar("lottoactivordint")
fechas = sorted(set(A) & set(B))

for L in (0, 1):
    for direccion in ("B_despues", "B_antes"):
        n = hits = 0
        for f in fechas:
            for ta, na in A[f].items():
                objetivo = ta + 60 * L
                cand = [tb for tb in B[f] if abs(tb - objetivo) <= 30]
                if not cand:
                    continue
                tb = min(cand, key=lambda t: abs(t - objetivo))
                despues = tb > ta
                if (direccion == "B_despues") != despues:
                    continue
                n += 1
                if na == B[f][tb]:
                    hits += 1
        ph = hits / n if n else 0
        p0 = 1 / 37
        z = (ph - p0) / math.sqrt(p0 * (1 - p0) / n) if n else 0
        print("lag %+dh %-10s n=%4d hits=%3d p_hat=%.4f z=%+.2f"
              % (L, direccion, n, hits, ph, z))
