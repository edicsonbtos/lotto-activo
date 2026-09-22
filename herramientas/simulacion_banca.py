# -*- coding: utf-8 -*-
"""¿Cuánto se puede ganar (o perder) con el Top-5 escalonado? Simulación.

Juega miles de meses imaginarios con las tasas medidas y cuenta cómo terminan.
No usa numpy (corre en cualquier PC y en Railway) ni toca ningún dato.

Jugada por sorteo (ficha = F): 2F a los puestos 1-3 y 1F a los puestos 4-5,
8F en total. Si sale uno del 1-3 se cobran 60F; si sale el 4 o 5, 30F.

Tres escenarios, porque la ventaja real no se conoce con exactitud:
  medido    : lo de la prueba ciega (Top-3 12,27 %, puestos 4-5 7,23 %)
  prudente  : el límite bajo (Top-3 11,17 %, puestos 4-5 en equilibrio 6,67 %)
  sin ventaja: el modelo no sirve y es azar (7,89 % y 5,26 %)

Uso:  python simulacion_banca.py [banca] [ficha]      (por defecto 2000 y 1)
"""
import random, sys

PAGO = 30
SORTEOS_DIA = 12
ESCENARIOS = [("medido", 0.1227, 0.0723), ("prudente", 0.1117, 0.0667),
              ("sin ventaja", 3 / 38, 2 / 38)]
PLAZOS = [(7, "1 semana"), (30, "1 mes"), (90, "3 meses")]
N_SIM = 4000


def simular(banca, ficha, pA, pB, sorteos, rng):
    b = maximo = banca
    peor_caida = 0.0
    racha = peor_racha = 0
    for _ in range(sorteos):
        if b < 8 * ficha:                       # sin plata para la jugada
            break
        u = rng.random()
        if u < pA:
            b += 60 * ficha - 8 * ficha; racha = 0
        elif u < pA + pB:
            b += 30 * ficha - 8 * ficha; racha = 0
        else:
            b -= 8 * ficha; racha += 1
            peor_racha = max(peor_racha, racha)
        maximo = max(maximo, b)
        peor_caida = max(peor_caida, maximo - b)
    return b - banca, peor_caida, peor_racha


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def main():
    banca = float(sys.argv[1]) if len(sys.argv) > 1 else 2000.0
    ficha = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    rng = random.Random(20260922)
    print(f"Banca {banca:,.0f} · ficha {ficha:g} · se apuestan {8*ficha:g} por sorteo, "
          f"{12*8*ficha:g} al día (12 sorteos)")
    print(f"{N_SIM} simulaciones por escenario y plazo.\n")
    for nombre, pA, pB in ESCENARIOS:
        ev = (pA * 60 + pB * 30 - 8) * ficha
        print("=" * 72)
        print(f"ESCENARIO {nombre.upper()}: ganancia esperada {ev:+.2f} por sorteo "
              f"({ev/(8*ficha)*100:+.1f} % de lo apostado)")
        print("=" * 72)
        print(f"{'plazo':<10}{'mitad de las veces':>20}{'1 de cada 10 mal':>18}"
              f"{'1 de cada 10 bien':>19}{'pierde':>9}")
        for dias, etiqueta in PLAZOS:
            res = [simular(banca, ficha, pA, pB, dias * SORTEOS_DIA, rng) for _ in range(N_SIM)]
            g = [r[0] for r in res]
            pierde = sum(1 for x in g if x < 0) / len(g) * 100
            print(f"{etiqueta:<10}{pct(g, .5):>+20,.0f}{pct(g, .1):>+18,.0f}{pct(g, .9):>+19,.0f}{pierde:>8.0f}%")
            if dias == 30:
                caidas = [r[1] for r in res]; rachas = [r[2] for r in res]
                nota = (f"   en 1 mes: la peor caída típica es {pct(caidas, .5):,.0f} "
                        f"(1 de cada 10 meses pasa de {pct(caidas, .9):,.0f}); la racha de fallos "
                        f"más larga típica es de {pct(rachas, .5)} sorteos seguidos")
        print(nota + "\n")
    print("Cómo leerlo: «mitad de las veces» es el resultado típico. «1 de cada 10 mal» es un")
    print("mes malo pero normal: le pasará a cualquiera que juegue varios meses. «pierde» es la")
    print("probabilidad de terminar el plazo con menos plata de la que empezó.")


if __name__ == "__main__":
    main()
