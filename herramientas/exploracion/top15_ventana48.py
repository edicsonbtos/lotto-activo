# -*- coding: utf-8 -*-
"""Top-15 a partir de ventanas recientes: foto de las ultimas 48 + prueba con poder.

Parte 1: describe las ultimas 48 (frecuencias, ausencias, repeticiones) y pone
al lado el SUELO DE RUIDO por Monte Carlo uniforme. Sirve para ver con los datos
propios que 48 sorteos no distinguen nada.

Parte 2: la prueba que si tiene poder. Cada "patron de ventana reciente" se
convierte en una regla de ranking Top-15 y se evalua WALK-FORWARD sobre TODO el
desarrollo [2000, 9357). Nunca toca el tramo de prueba (>=9357).

Empates: si el ganador cae en un grupo empatado que cruza el corte del 15, se
acredita la FRACCION de cupos disponibles, no 1. Asi los empates masivos de las
ventanas cortas (en 48 sorteos casi todos los animales empatan en 1) no inflan
la tasa. La regla 'control_azar' verifica que ese manejo no sesga: debe dar
~39,5 % con z~0.

Solo stdlib: no usa numpy. Es de solo lectura: no escribe nada ni toca el
modelo, los pesos ni el historial.
"""
import os, random
from collections import deque, Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HIST = os.path.join(RAIZ, "historial.txt")
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}
K, TOPN, W0, CORTE = 38, 15, 2000, 9357
P_AZAR = TOPN / K


# --------------------------------------------------------------------------- #
def cargar():
    filas = []
    with open(HIST, encoding="utf-8") as f:
        for ln in f:
            p = ln.split()
            if len(p) == 3 and p[2] in IDX:
                filas.append((p[0], int(p[1]), IDX[p[2]]))
    filas.sort(key=lambda r: (r[0], r[1]))
    return [r[0] for r in filas], [r[1] for r in filas], [r[2] for r in filas]


def credito(clave, gan):
    """Fraccion de acierto Top-15 del ganador bajo desempate aleatorio justo."""
    kg = clave[gan]
    mejores = sum(1 for v in clave if v > kg)
    if mejores >= TOPN:
        return 0.0
    empat = sum(1 for v in clave if v == kg)
    cupos = TOPN - mejores
    return 1.0 if cupos >= empat else cupos / empat


def z_binom(h, n, p):
    return (h / n - p) / (p * (1 - p) / n) ** 0.5


def ic95(h, n):
    t = h / n
    e = 1.96 * (t * (1 - t) / n) ** 0.5
    return t - e, t + e


# --------------------------------------------------------------------------- #
def parte1(seq):
    ult = seq[-48:]
    print("=" * 76)
    print("PARTE 1 - FOTO DE LOS ULTIMOS 48 SORTEOS (con su suelo de ruido)")
    print("=" * 76)
    c = Counter(ult)
    print(f"\n48 sorteos entre {K} animales -> cada uno se espera {48 / K:.2f} veces.")
    print("Los mas repetidos:")
    for a, n in c.most_common(8):
        print(f"   {POS[a]:>3}   {n} veces")
    maxobs = c.most_common(1)[0][1]
    ausentes = K - len(c)
    reps = sum(1 for i in range(1, 48) if ult[i] == ult[i - 1])

    R, rng = 20000, random.Random(20260922)
    gmax = gaus = grep = 0
    for _ in range(R):
        s = [rng.randrange(K) for _ in range(48)]
        cc = Counter(s)
        if cc.most_common(1)[0][1] >= maxobs:
            gmax += 1
        if K - len(cc) >= ausentes:
            gaus += 1
        if sum(1 for i in range(1, 48) if s[i] == s[i - 1]) >= reps:
            grep += 1

    print(f"\n{'medida':<36}{'observado':>10}{'p (azar puro)':>18}")
    print("-" * 76)
    print(f"{'veces del animal mas repetido':<36}{maxobs:>10}{gmax / R:>18.3f}")
    print(f"{'animales que no salieron ninguna vez':<36}{ausentes:>10}{gaus / R:>18.3f}")
    print(f"{'repeticiones en sorteos seguidos':<36}{reps:>10}{grep / R:>18.3f}")
    print("-" * 76)
    print("p alto = lo observado es lo normal en 48 tiradas de una moneda justa.")
    print(f"Con n=48 el error estandar de una tasa Top-15 es +-"
          f"{100 * (P_AZAR * (1 - P_AZAR) / 48) ** .5:.1f} pp:")
    print("ni la ventaja real del modelo (+13,6 pp) se ve fiablemente aqui.")


# --------------------------------------------------------------------------- #
def parte2(fecha, hora, seq):
    print("\n" + "=" * 76)
    print(f"PARTE 2 - LAS MISMAS IDEAS, WALK-FORWARD SOBRE [{W0}, {CORTE})")
    print("=" * 76)
    VENT = (24, 48, 96, 150)
    reglas = ([f"calientes_{w}" for w in VENT] + [f"frios_{w}" for w in VENT] +
              ["atrasados", "recientes", "calientes_hoy", "frios_hoy",
               "no_salio_hoy_y_cal150", "misma_hora_150", "control_azar"])
    acc = {r: 0.0 for r in reglas}
    n = 0
    ctl = random.Random(4815162342)

    cnt = {w: [0] * K for w in VENT}
    col = {w: deque() for w in VENT}
    ultvez = [-1] * K
    hcnt = [[0] * K for _ in range(13)]
    hcol = [deque() for _ in range(13)]
    hoy = [0] * K
    dia_ant = None

    for t in range(len(seq)):
        if fecha[t] != dia_ant:          # jornada nueva: 'salio hoy' vuelve a cero
            hoy = [0] * K
            dia_ant = fecha[t]

        if W0 <= t < CORTE:              # predecir sorteo t con datos < t
            clave = {}
            for w in VENT:
                clave[f"calientes_{w}"] = cnt[w][:]
                clave[f"frios_{w}"] = [-v for v in cnt[w]]
            clave["atrasados"] = [t - u for u in ultvez]
            clave["recientes"] = [u for u in ultvez]
            clave["calientes_hoy"] = hoy[:]
            clave["frios_hoy"] = [-v for v in hoy]
            # desempata los muchos "no salio hoy" (0) por calor a 150 sorteos
            clave["no_salio_hoy_y_cal150"] = [-1000 * v + cnt[150][i]
                                              for i, v in enumerate(hoy)]
            clave["misma_hora_150"] = hcnt[hora[t]][:]
            clave["control_azar"] = [ctl.random() for _ in range(K)]
            g = seq[t]
            for r in reglas:
                acc[r] += credito(clave[r], g)
            n += 1

        a, h = seq[t], hora[t]           # ahora si se observa el sorteo t
        for w in VENT:
            cnt[w][a] += 1
            col[w].append(a)
            if len(col[w]) > w:
                cnt[w][col[w].popleft()] -= 1
        hcnt[h][a] += 1
        hcol[h].append(a)
        if len(hcol[h]) > 150:
            hcnt[h][hcol[h].popleft()] -= 1
        hoy[a] += 1
        ultvez[a] = t

    print(f"\nn = {n} sorteos puntuados.   azar = {100 * P_AZAR:.2f} %   "
          f"equilibrio 30x = 50,00 %   modelo actual = 53,07 %\n")
    print(f"{'regla':<18}{'tasa':>8}{'IC95':>19}{'z vs azar':>12}{'z vs 50%':>11}")
    print("-" * 76)
    for r in reglas:
        h = acc[r]
        lo, hi = ic95(h, n)
        print(f"{r:<18}{100 * h / n:>7.2f}%{100 * lo:>10.2f}-{100 * hi:<8.2f}"
              f"{z_binom(h, n, P_AZAR):>12.2f}{z_binom(h, n, 0.5):>11.2f}")
    print("-" * 76)
    print(f"Umbral Bonferroni ({len(reglas)} reglas, una cola, 5 %): z > 2.87")
    print("Para valer la pena de verdad hace falta z vs 50% > 0 con IC95 sobre 50.")


if __name__ == "__main__":
    fecha, hora, seq = cargar()
    print(f"historial: {len(seq)} sorteos ({fecha[0]} a {fecha[-1]})")
    parte1(seq)
    parte2(fecha, hora, seq)
