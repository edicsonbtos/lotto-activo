# -*- coding: utf-8 -*-
"""¿Conviene expulsar del Top-15 al que ya salió hoy, o solo castigarlo?

La regla que mejor salió en top15_ventana48.py excluye a martillazos a todo el
que ya salió hoy, y mete en su lugar al siguiente de la lista aunque sea un
frío con menos posibilidades. Esa expulsión dura es una decisión que nadie
midió: se puso porque "tiene sentido".

Aquí se mide. La clave de orden es

    calor150[i]  -  lam * veces_que_salio_hoy[i]

con lam = 0 (no castigar nada) hasta lam = inf (expulsión dura, la regla
actual). Si el óptimo cae en un lam intermedio, la expulsión dura está
tirando aciertos a la basura.

Walk-forward sobre desarrollo [2000, 9357). Nunca toca el tramo de prueba.
Empates acreditados de forma fraccionaria (un empate que cruza el corte del 15
vale su fracción de cupos, no 1), porque con lam=0 hay empates masivos.

AVISO DE HONESTIDAD: lam se elige mirando desarrollo, así que la mejor cifra
de esta tabla está optimizada sobre los mismos datos. Para saber lo que vale
de verdad habría que mirarla una sola vez en el tramo de prueba, y eso NO se
hace aquí.

Solo stdlib. Solo lectura.
"""
import os
from collections import deque

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HIST = os.path.join(RAIZ, "historial.txt")
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}
K, TOPN, W0, CORTE = 38, 15, 2000, 9357
P_AZAR = TOPN / K
LAMS = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 1e9]


def cargar():
    filas = []
    with open(HIST, encoding="utf-8") as f:
        for ln in f:
            p = ln.split()
            if len(p) == 3 and p[2] in IDX:
                filas.append((p[0], int(p[1]), IDX[p[2]]))
    filas.sort(key=lambda r: (r[0], r[1]))
    return [r[0] for r in filas], [r[2] for r in filas]


def credito(clave, gan):
    kg = clave[gan]
    mejores = sum(1 for v in clave if v > kg)
    if mejores >= TOPN:
        return 0.0
    empat = sum(1 for v in clave if v == kg)
    cupos = TOPN - mejores
    return 1.0 if cupos >= empat else cupos / empat


def z(h, n, p):
    return (h / n - p) / (p * (1 - p) / n) ** 0.5


def ic95(h, n):
    t = h / n
    e = 1.96 * (t * (1 - t) / n) ** 0.5
    return 100 * (t - e), 100 * (t + e)


def main():
    fecha, seq = cargar()
    acc = {l: 0.0 for l in LAMS}
    n = 0
    cnt, col = [0] * K, deque()
    hoy, dia = [0] * K, None

    for t in range(len(seq)):
        if fecha[t] != dia:
            hoy, dia = [0] * K, fecha[t]
        if W0 <= t < CORTE:
            g = seq[t]
            for l in LAMS:
                acc[l] += credito([cnt[i] - l * hoy[i] for i in range(K)], g)
            n += 1
        a = seq[t]
        cnt[a] += 1
        col.append(a)
        if len(col) > 150:
            cnt[col.popleft()] -= 1
        hoy[a] += 1

    print(f"n = {n} sorteos.  azar = {100*P_AZAR:.2f} %  ·  "
          f"equilibrio 30x = 50,00 %  ·  ensamble desplegado = 53,07 %\n")
    print(f"{'castigo (lam)':<16}{'tasa':>8}{'IC95':>19}{'z vs azar':>12}{'z vs 50%':>11}")
    print("-" * 68)
    best = max(LAMS, key=lambda l: acc[l])
    for l in LAMS:
        h = acc[l]
        lo, hi = ic95(h, n)
        etiq = "0 (no castiga)" if l == 0 else ("inf (expulsa)" if l > 1e8 else f"{l:g}")
        marca = "   <-- mejor" if l == best else ""
        print(f"{etiq:<16}{100*h/n:>7.2f}%{lo:>10.2f}-{hi:<8.2f}"
              f"{z(h,n,P_AZAR):>12.2f}{z(h,n,0.5):>11.2f}{marca}")
    print("-" * 68)
    dura, mejor = acc[1e9], acc[best]
    print(f"\nExpulsión dura: {100*dura/n:.2f} %   ·   mejor castigo (lam={best:g}): "
          f"{100*mejor/n:.2f} %")
    print(f"Diferencia: {100*(mejor-dura)/n:+.2f} pp  ({mejor-dura:+.1f} aciertos en {n})")
    print("\nRecordatorio: lam se escogió mirando estos mismos datos. La cifra de")
    print("arriba es el techo optimista, no lo que rendiría a ciegas.")


if __name__ == "__main__":
    main()
