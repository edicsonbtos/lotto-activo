# -*- coding: utf-8 -*-
"""Descarga los juegos de animalitos que Tuazar no muestra, desde loteriadehoy.com.

Usa core.lh_historico (parser probado). Solo da el ANIMAL (sin numero).
Cache de HTML en scraping/crudos/loteriadehoy/.
Salida: scraping/resultados/<slug>_2026-04-11_2026-10-07.csv
Columnas: fecha,hora,slot,animal_numero,animal_nombre,operador,timestamp_publicacion
(animal_numero queda vacío: esta fuente no lo publica).
"""
import csv
import os
import sys
from collections import defaultdict
from datetime import date, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import core  # noqa: E402

core.CRUDOS = os.path.join(RAIZ, "crudos")

from core import lh_historico, semanas_entre  # noqa: E402

INI = date(2026, 4, 11)
FIN = date(2026, 10, 7)
RES = os.path.join(RAIZ, "resultados")
LOGS = os.path.join(RAIZ, "logs")
CAMPOS = ["fecha", "hora", "slot", "animal_numero", "animal_nombre", "operador", "timestamp_publicacion"]

# juegos que Tuazar no muestra y LH sí tiene con resultados en la semana del 2026-09-28
SLUGS = ["la-ricachona", "cazaloton", "centenaplus", "centenaanimalitos",
         "ruletaactiva", "lottoactivordominicana",
         # Tuazar solo los tiene desde 2026-09-07: LH cubre el periodo completo
         "lottoactivordint", "lottoactivo2(monjemillonario)"]


def main():
    resumen = []
    for slug in SLUGS:
        filas = {}
        for lunes in semanas_entre(INI, FIN):
            try:
                rows = lh_historico(slug, lunes, lunes + timedelta(days=6))
            except Exception as e:  # noqa: BLE001
                print("  fallo", slug, lunes, repr(e)[:120])
                continue
            for f in rows:
                d = date.fromisoformat(f["fecha"])
                if INI <= d <= FIN:
                    filas[(f["fecha"], f["hora"])] = f["animal"]
        por_dia = defaultdict(list)
        for (fecha, hora), animal in filas.items():
            por_dia[fecha].append((hora, animal))
        salida = []
        for fecha in sorted(por_dia):
            for i, (hora, animal) in enumerate(sorted(por_dia[fecha]), 1):
                salida.append({"fecha": fecha, "hora": hora + ":00", "slot": i,
                               "animal_numero": "", "animal_nombre": animal,
                               "operador": slug, "timestamp_publicacion": ""})
        ruta = os.path.join(RES, "%s_%s_%s.csv" % (slug, INI.isoformat(), FIN.isoformat()))
        with open(ruta, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(salida)
        resumen.append("%-22s sorteos=%6d dias=%4d desde=%s hasta=%s" % (
            slug, len(salida), len(por_dia),
            min(por_dia) if por_dia else "-", max(por_dia) if por_dia else "-"))
        print(resumen[-1])
    with open(os.path.join(LOGS, "loteriadehoy_resumen.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(resumen) + "\n")


if __name__ == "__main__":
    main()
