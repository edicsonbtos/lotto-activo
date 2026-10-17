# -*- coding: utf-8 -*-
"""1) Reconstruye resultados/consolidado_todos.csv desde los CSV por juego.
2) Prueba exploratoria de copia: ¿el animal de cada juego coincide con el de Lotto Activo?

Para cada juego X y cada sorteo de X (fecha d, hora h):
  - lag0: animal de LA en (d, h)
  - lag1: animal de LA en (d, h-1)
  - control: animal de LA en (d+37 dias, h)  (misma hora, otro dia: linea base)
Tasa de coincidencia y su IC95 (Wilson). Exploratorio: NO es prueba ciega.
"""
import csv
import glob
import math
import os
import unicodedata
from collections import defaultdict
from datetime import date, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(RAIZ, "resultados")
LOGS = os.path.join(RAIZ, "logs")
CAMPOS = ["fecha", "hora", "slot", "animal_numero", "animal_nombre", "operador", "timestamp_publicacion"]


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return s.strip().upper()


def cargar_juegos():
    juegos = {}
    for ruta in sorted(glob.glob(os.path.join(RES, "*_2026-04-11_2026-10-07.csv"))):
        nombre = os.path.basename(ruta).split("_2026-04-11")[0]
        if nombre == "consolidado":
            continue
        with open(ruta, encoding="utf-8") as fh:
            juegos[nombre] = list(csv.DictReader(fh))
    return juegos


def consolidar(juegos):
    filas = []
    for nombre, lst in juegos.items():
        filas += lst
    filas.sort(key=lambda r: (r["fecha"], r["hora"], r["operador"]))
    with open(os.path.join(RES, "consolidado_todos.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)
    return len(filas)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def main():
    juegos = cargar_juegos()
    total = consolidar(juegos)
    print("consolidado filas:", total)

    # mapa LA: (fecha, hora entera) -> animal
    la = {}
    for r in juegos["lottoactivo"]:
        la[(r["fecha"], int(r["hora"][:2]))] = norm(r["animal_nombre"])

    lineas = ["Copia exploratoria vs Lotto Activo (animal igual). Base: LA mismo dia y hora (lag0),",
              "LA hora anterior (lag1), y control: LA misma hora 37 dias despues.", ""]
    lineas.append("%-26s %6s %8s %8s %8s %8s  %s" % ("juego", "n", "lag0", "lag1", "control", "O/E0", "IC95 lag0"))
    for nombre in sorted(juegos):
        if nombre == "lottoactivo":
            continue
        n = k0 = k1 = kc = nc = 0
        for r in juegos[nombre]:
            d = date.fromisoformat(r["fecha"])
            h = int(r["hora"][:2])
            x = norm(r["animal_nombre"])
            a0 = la.get((r["fecha"], h))
            a1 = la.get((r["fecha"], h - 1))
            dc = (d + timedelta(days=37)).isoformat()
            ac = la.get((dc, h))
            if a0 is not None:
                n += 1
                k0 += (x == a0)
            if a1 is not None:
                k1 += (x == a1)
            if ac is not None:
                nc += 1
                kc += (x == ac)
        if n == 0:
            continue
        p0 = k0 / n
        pc = kc / nc if nc else 0
        oe = p0 / pc if pc else float("nan")
        lo, hi = wilson(k0, n)
        lineas.append("%-26s %6d %7.2f%% %7.2f%% %7.2f%% %8.2f  [%.2f; %.2f]%%" % (
            nombre, n, 100 * p0, 100 * (k1 / n), 100 * pc, oe, 100 * lo, 100 * hi))
    texto = "\n".join(lineas)
    print(texto)
    with open(os.path.join(LOGS, "copia_exploratoria.txt"), "w", encoding="utf-8") as fh:
        fh.write(texto + "\n")


if __name__ == "__main__":
    main()
