# -*- coding: utf-8 -*-
"""ag03 — definiciones comunes: agrupaciones de los 38 códigos y utilidades."""
import os, numpy as np
from scipy import stats

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
NUM = np.array([0, -1] + list(range(1, 37)))      # 00 -> -1
d = np.load(os.path.join(BASE, "base8.npz"), allow_pickle=True)
seq, hora, dia, fecha, dow = d["seq"], d["hora"], d["dia"], d["fecha"], d["dow"]
P, Paj, prim, tramo = d["P"], d["P_aj"], d["es_primero"], d["tramo"]
n = len(seq)

ROJOS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
# cilindro americano (sentido horario desde el 0)
RUEDA = ["0", "28", "9", "26", "30", "11", "7", "20", "32", "17", "5", "22", "34", "15", "3", "24", "36", "13", "1",
         "00", "27", "10", "25", "29", "12", "8", "19", "31", "18", "6", "21", "33", "16", "4", "23", "35", "14", "2"]
POSRUEDA = np.array([RUEDA.index(p) for p in POS])


def grupos():
    """Particiones de los 38 índices. Cada una: nombre -> array de etiquetas (int por índice); -1 = fuera."""
    G = {}
    lab = lambda f: np.array([f(i) for i in range(38)])
    G["verde_0_00"] = lab(lambda i: 1 if i < 2 else 0)                       # 0/00 vs resto
    G["par_impar"] = lab(lambda i: -1 if i < 2 else NUM[i] % 2)             # 0=par 1=impar
    G["bajo_alto"] = lab(lambda i: -1 if i < 2 else int(NUM[i] > 18))
    G["docenas"] = lab(lambda i: -1 if i < 2 else (NUM[i] - 1) // 12)
    G["columnas"] = lab(lambda i: -1 if i < 2 else (NUM[i] - 1) % 3)
    G["rojo_negro"] = lab(lambda i: -1 if i < 2 else int(NUM[i] in ROJOS))
    G["sector_rueda4"] = (POSRUEDA * 4) // 38                                # 4 sectores contiguos del cilindro
    G["sector_rueda2"] = (POSRUEDA * 2) // 38                                # 2 mitades (0 lado / 00 lado)
    G["cumple_1_31"] = lab(lambda i: -1 if i < 2 else int(NUM[i] <= 31))     # 1=1..31, 0=32..36
    return G


def poisson_ic(o, a=0.05):
    lo = 0.0 if o == 0 else stats.chi2.ppf(a / 2, 2 * o) / 2
    hi = stats.chi2.ppf(1 - a / 2, 2 * o + 2) / 2
    return lo, hi


def oe_grupo(rows, miembro):
    """O/E contra el motor: rows = índices de fila; miembro = bool(38)."""
    O = int(miembro[seq[rows]].sum())
    E = float(Paj[rows][:, miembro].sum())
    return O, E


def p_dos_colas_poisson(O, E):
    lo = stats.poisson.cdf(O, E); hi = stats.poisson.sf(O - 1, E)
    return min(1.0, 2 * min(lo, hi))


def mbits(q, rows):
    y = seq[rows]
    return 1000 * np.mean(np.log2(q[np.arange(len(rows)), y] / Paj[rows, y]))


def mbits_boot(q, rows, B=2000, rng=None):
    rng = rng or np.random.default_rng(0)
    y = seq[rows]
    g = np.log2(q[np.arange(len(rows)), y] / Paj[rows, y]) * 1000   # una fila por día => bootstrap de filas = de días
    m = g.mean()
    bs = np.array([g[rng.integers(0, len(g), len(g))].mean() for _ in range(B)])
    return m, np.percentile(bs, 2.5), np.percentile(bs, 97.5)
