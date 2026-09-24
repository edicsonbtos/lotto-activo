# -*- coding: utf-8 -*-
"""Hilo 8, señal (PREREGISTRO_lard_cruzado.md): ¿un juego evita el animal del sorteo anterior de otro?
Python puro. Por defecto SOLO desarrollo; la prueba ciega exige --ciega (una sola vez, tras cerrar dev).

Uso: python herramientas/lard/senal.py [--ciega]
"""
import csv, io, os, sys
from collections import defaultdict
from math import exp, factorial

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATOS = os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv")
DEV = ("2025-07-01", "2026-02-01")
CIEGA = ("2026-02-01", "2026-09-23")
NOMBRE = {"1": "LA", "2": "RD", "3": "LARD"}


def minutos(h):
    a, b = h.split(":"); return int(a) * 60 + int(b)


# (juego objetivo, juego previo, minutos antes). Sólo mismo día.
PARES = [("P1: LA h:00 <- LARD (h-1):00", "1", "3", 60),
         ("P2: RD h:30 <- LARD h:00", "2", "3", 30),
         ("P3: LARD h:00 <- RD (h-1):30", "3", "2", 30),
         ("P4: LARD h:00 <- LA (h-1):00", "3", "1", 60),
         ("desc: LA h:00 = LARD h:00 (simultaneos)", "1", "3", 0),
         ("control hilo 7: RD h:30 <- LA h:00", "2", "1", 30),
         ("control hilo 7: LA h:00 <- RD (h-1):30", "1", "2", 30)]


def p_menos(k, mu):
    return sum(exp(-mu) * mu ** i / factorial(i) for i in range(k + 1))


def main():
    a, b = CIEGA if "--ciega" in sys.argv else DEV
    res = defaultdict(dict)   # (fecha, juego) -> {minuto: codigo}
    with io.open(DATOS, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if a <= r["fecha"] < b:
                res[(r["fecha"], r["juego"])][minutos(r["hora"])] = r["codigo"]
    fechas = sorted({f for f, _ in res})
    print("Ventana %s..%s: %d días  (%s)" % (a, b, len(fechas), "PRUEBA CIEGA" if "--ciega" in sys.argv else "desarrollo"))
    print("| par | n | repite | esperado n/38 | ratio | p (menos) | pasa dev (p<0,0025) |")
    print("|---|---|---|---|---|---|---|")
    for nom, obj, prev, antes in PARES:
        n = rep = 0
        for f in fechas:
            O = res.get((f, obj), {}); P = res.get((f, prev), {})
            for m, c in O.items():
                q = P.get(m - antes)
                if q is None:
                    continue
                n += 1; rep += c == q
        mu = n / 38
        p = p_menos(rep, mu) if n else 1
        print("| %s | %d | %d | %.1f | %.2f | %.2g | %s |" % (nom, n, rep, mu, rep / mu if mu else 0, p,
              "SÍ" if p < 0.01 / 4 and not nom.startswith(("desc", "control")) else ""))


if __name__ == "__main__":
    main()
