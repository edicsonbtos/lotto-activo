import sys, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2/M3")
import arnes as A, m3
def fn(seq, hora, dow, fecha, i):
    X, _, nb, dia, _ = m3.construir(seq, hora, fecha)   # se construye con la secuencia ENTERA (incluido el futuro alterado)
    P, _, _ = m3.walk_forward(X, np.asarray(seq), dia, nb, 120.0, 30.0, fila_ini=i - 30, hasta=i + 1)
    return P[-1]
A.chequear_fuga(fn)
