# -*- coding: utf-8 -*-
"""Sondeo: ¿los animales que salen del Top-15 entre un pronóstico y el siguiente aciertan más de lo que dice su probabilidad?"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import arnes as A
P, y = A.base(); P = P / P.sum(1, keepdims=True)
D = A.datos(); dia = D.dia[A.W:A.CORTE]
n = len(y)
rank = np.argsort(np.argsort(-P, 1), 1) + 1  # 1 = primero
hit = np.zeros_like(P, bool); hit[np.arange(n), y] = True
# pares consecutivos del mismo día
m = np.r_[False, dia[1:] == dia[:-1]]
prev_in = np.zeros_like(P, bool); prev_in[1:] = rank[:-1] <= 15
now_in = rank <= 15
# excluye el animal que acaba de salir en t-1 (sale del top por la regla de no repetir)
just = np.zeros_like(P, bool); just[np.arange(1, n), y[:-1]] = True
for nombre, M in [("sacados (estaban en Top-15, ya no)", prev_in & ~now_in & ~just & m[:, None]),
                  ("sacados, cualquier día", prev_in & ~now_in & ~just),
                  ("entrados (no estaban, ahora sí)", ~prev_in & now_in & m[:, None]),
                  ("fuera del Top-15 y no sacados", ~now_in & ~prev_in & m[:, None])]:
    k = M.sum(); obs = hit[M].sum(); esp = P[M].sum()
    print(f"{nombre:40s} casos {k:6d}  salieron {obs:5d}  esperado por el modelo {esp:7.1f}  O/E {obs/esp:5.3f}  z {(obs-esp)/np.sqrt(esp):+.2f}")
# puesto 16-20 sacados vs no sacados
for lo, hi in [(16, 18), (16, 20), (21, 25)]:
    band = (rank >= lo) & (rank <= hi) & m[:, None] & ~just
    for tag, M in [("sacados", band & prev_in), ("no sacados", band & ~prev_in)]:
        k = M.sum(); obs = hit[M].sum(); esp = P[M].sum()
        print(f"puestos {lo}-{hi} {tag:11s} casos {k:6d} tasa {obs/k*100:5.2f}%  modelo {esp/k*100:5.2f}%  O/E {obs/esp:5.3f}")
print("Top-15 ensamble en desarrollo:", f"{(rank[np.arange(n), y] <= 15).mean()*100:.2f}%")
