# -*- coding: utf-8 -*-
"""Descarga todos los juegos de animalitos desde tuazar.com (una pagina por semana).

Usa el parser ya probado de scraping/core.py. Los HTML crudos se guardan en
scraping/crudos/ (no en datos_multiloteria/, que está protegido).

Salida:
  scraping/resultados/<juego>_<ini>_<fin>.csv   (un CSV por juego)
  scraping/resultados/consolidado_todos.csv
  scraping/logs/resumen_descarga.txt

Formato de columnas (el del plan): fecha,hora,slot,animal_numero,animal_nombre,operador,timestamp_publicacion
timestamp_publicacion queda vacío: tuazar no muestra la hora de publicación.

Uso (desde scraping/):  ..\\.venv_scrape\\Scripts\\python.exe scripts\\descargar_animalitos.py
"""
import csv
import os
import re
import sys
from collections import defaultdict
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import core  # noqa: E402  (scraping/core.py: parser y fetch de tuazar)

core.CRUDOS = os.path.join(RAIZ, "crudos")  # cache de HTML fuera de datos_multiloteria/

from core import Selector, norm, parse_tuazar_semana, semanas_entre, tuazar_semana  # noqa: E402

INI = date(2026, 4, 11)
FIN = date(2026, 10, 7)

RES = os.path.join(RAIZ, "resultados")
LOGS = os.path.join(RAIZ, "logs")
os.makedirs(RES, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)

CAMPOS = ["fecha", "hora", "slot", "animal_numero", "animal_nombre", "operador", "timestamp_publicacion"]


def juegos_no_mapeados(html, mapeados):
    """Nombres de juego que tuazar muestra y que core.py no conoce."""
    sel = Selector(html)
    raros = set()
    for tabla in sel.css("table"):
        for tr in tabla.css("tbody tr"):
            celdas = tr.css("th, td")
            if len(celdas) < 3:
                continue
            nombre = re.sub(r"<[^>]+>", "", celdas[1].get() or "").strip()
            if nombre and norm(nombre) not in mapeados:
                raros.add(nombre)
    return raros


def main():
    from core import TZ_A_SLUG  # noqa: E402

    # juegos que tuazar muestra y core.py no conocía (se agregan aquí, sin tocar core.py)
    TZ_A_SLUG[norm("Granja Millonaria - Animalitos")] = "granjamillionaria"
    TZ_A_SLUG[norm("Granja Millonaria - Granjazo")] = "granjazo"

    mapeados = set(TZ_A_SLUG.keys())
    filas = []
    no_mapeados = set()
    semanas = semanas_entre(INI, FIN)
    print("semanas a descargar:", len(semanas))
    for lunes in semanas:
        html = tuazar_semana(lunes)
        no_mapeados |= juegos_no_mapeados(html, mapeados)
        for f in parse_tuazar_semana(html):
            d = date.fromisoformat(f["fecha"])
            if INI <= d <= FIN:
                filas.append(f)
        print("  semana", lunes.isoformat(), "acumulado", len(filas))

    # deduplicar por (juego, fecha, hora)
    vistos = {}
    for f in filas:
        vistos[(f["loteria"], f["fecha"], f["hora"])] = f
    unicas = list(vistos.values())

    # slot = orden de la hora dentro del dia, por juego
    por_dia = defaultdict(list)
    for f in unicas:
        por_dia[(f["loteria"], f["fecha"])].append(f)
    for (_, _), lst in por_dia.items():
        lst.sort(key=lambda x: x["hora"])
        for i, f in enumerate(lst, 1):
            f["slot"] = i

    por_juego = defaultdict(list)
    for f in unicas:
        por_juego[f["loteria"]].append(f)

    consolidado = []
    resumen = []
    for juego in sorted(por_juego):
        lst = sorted(por_juego[juego], key=lambda x: (x["fecha"], x["hora"]))
        filas_csv = [{
            "fecha": f["fecha"], "hora": f["hora"] + ":00", "slot": f["slot"],
            "animal_numero": f["numero"], "animal_nombre": f["animal"],
            "operador": juego, "timestamp_publicacion": "",
        } for f in lst]
        nombre = "%s_%s_%s.csv" % (juego, INI.isoformat(), FIN.isoformat())
        with open(os.path.join(RES, nombre), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(filas_csv)
        consolidado += filas_csv

        dias = defaultdict(int)
        for f in lst:
            dias[f["fecha"]] += 1
        completos = sum(1 for n in dias.values() if n == max(dias.values()))
        ultimo = max(dias)
        resumen.append((juego, len(lst), len(dias), max(dias.values()),
                        completos, min(dias), ultimo))

    with open(os.path.join(RES, "consolidado_todos.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(sorted(consolidado, key=lambda r: (r["fecha"], r["hora"], r["operador"])))

    lineas = []
    lineas.append("Descarga %s a %s (tuazar, %d semanas)" % (INI, FIN, len(semanas)))
    lineas.append("%-22s %8s %6s %8s %8s %12s %12s %s" % (
        "juego", "sorteos", "dias", "max/dia", "dias_ok", "desde", "hasta", "vigente"))
    for juego, n, dias_n, mx, ok, desde, hasta in resumen:
        vig = "SI" if hasta >= FIN.isoformat() or (date.fromisoformat(hasta) - FIN).days >= -3 else "NO"
        lineas.append("%-22s %8d %6d %8d %8d %12s %12s %s" % (juego, n, dias_n, mx, ok, desde, hasta, vig))
    if no_mapeados:
        lineas.append("")
        lineas.append("Juegos que tuazar muestra y no están mapeados (no descargados):")
        for x in sorted(no_mapeados):
            lineas.append("  - " + x)
    texto = "\n".join(lineas)
    print(texto)
    with open(os.path.join(LOGS, "resumen_descarga.txt"), "w", encoding="utf-8") as fh:
        fh.write(texto + "\n")


if __name__ == "__main__":
    main()
