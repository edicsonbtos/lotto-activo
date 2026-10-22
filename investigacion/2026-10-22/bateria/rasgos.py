# -*- coding: utf-8 -*-
"""Rasgos de la batería 2026-10-22 (ver PREREGISTRO.md). Índices 0..37 = ["0","00","1".."36"]."""
import numpy as np
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}
RUEDA = ["0", "28", "9", "26", "30", "11", "7", "20", "32", "17", "5", "22", "34", "15", "3", "24", "36", "13", "1",
         "00", "27", "10", "25", "29", "12", "8", "19", "31", "18", "6", "21", "33", "16", "4", "23", "35", "14", "2"]
POSR = {IDX[c]: k for k, c in enumerate(RUEDA)}
ROJOS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
AVES = {7, 9, 14, 17, 21, 25, 28}
NUM = [None, None] + list(range(1, 37))          # valor numérico (0 y 00 -> None)

def color(i):
    n = NUM[i]
    return None if n is None else ("r" if n in ROJOS else "n")

def docena(i):
    n = NUM[i]
    return None if n is None else (n - 1) // 12

NOMBRES = ["H1_rueda", "H2_color", "H3_docena", "H4_consecutivo", "H5_mes", "H6_dia_semana", "H7_aves"]

def mascaras(prev, mes, dow):
    """prev: índice del ganador anterior del mismo día o None. mes 1..12, dow 0=lunes. -> dict nombre -> bool[38] o None."""
    m = {}
    if prev is None:
        for k in NOMBRES[:4] + ["H7_aves"]:
            m[k] = None
    else:
        r = POSR[prev]
        m["H1_rueda"] = np.array([min((POSR[c] - r) % 38, (r - POSR[c]) % 38) == 1 for c in range(38)])
        cp = color(prev)
        m["H2_color"] = None if cp is None else np.array([color(c) == cp for c in range(38)])
        dp = docena(prev)
        m["H3_docena"] = None if dp is None else np.array([docena(c) == dp for c in range(38)])
        np_ = NUM[prev]
        m["H4_consecutivo"] = None if np_ is None else np.array([NUM[c] is not None and abs(NUM[c] - np_) == 1 for c in range(38)])
        m["H7_aves"] = (np.array([NUM[c] in AVES for c in range(38)]) if NUM[prev] in AVES else None)
    m["H5_mes"] = np.array([NUM[c] == mes for c in range(38)])
    m["H6_dia_semana"] = np.array([NUM[c] == dow + 1 for c in range(38)])
    return m
