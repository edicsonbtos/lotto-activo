# -*- coding: utf-8 -*-
"""Pruebas de la fuente oficial (lottoactivo.com) con respuestas reales.

Las muestras de scraping/muestras/ son respuestas literales del endpoint
/core/process.php, guardadas el 2026-09-20. Se prueban sin red: si manana
cambia el formato, la prueba en vivo del final es la que avisa.

Lo que se vigila (cada punto ya mordio en produccion o estuvo a punto):
  1. La respuesta trae CUATRO loterias; solo la id_game=1 es la nuestra.
     Tomar otra pondria animales ajenos en el historial.
  2. Los nombres vienen acentuados (Aguila, Raton, Leon, Alacran).
  3. Delfin es "0" y Ballena es "00": el nombre manda sobre el numero.
  4. Las horas vienen con cero delante ("08:00 AM"), HORAS no lo lleva.

Uso:  python scraping/test_fuente_oficial.py [--vivo]
"""
import json
import os
import sys

RUTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RUTA)

from scraping import fuente_oficial as fo
from scraping.auto_resultado import HORAS

MUESTRAS = os.path.join(RUTA, "scraping", "muestras")
fallos = []


def ok(cond, msg):
    print(("  OK   " if cond else "  FALLA ") + msg)
    if not cond:
        fallos.append(msg)


def muestra(fecha):
    with open(os.path.join(MUESTRAS, "oficial_%s.json" % fecha), encoding="utf-8") as f:
        return json.load(f)


print("1) se lee Lotto Activo (id_game=1) y no otra loteria")
r = fo.parse(muestra("2026-09-20"), "2026-09-20")
ok(r.get(("2026-09-20", 0)) == ("35", "Jirafa"), "8:00 AM -> 35 Jirafa (no Camello, que es la RD)")
ok(r.get(("2026-09-20", 7)) == ("13", "Mono"), "3:00 PM -> 13 Mono")
ok(len(r) == 8, "8 sorteos publicados ese dia, no 31 de las cuatro loterias (hay %d)" % len(r))
ok(all(f == "2026-09-20" for f, _ in r), "todas las claves llevan la fecha pedida")
ok(all(0 <= h < len(HORAS) for _, h in r), "las horas caen dentro de HORAS")

print("2) acentos: el nombre acentuado tiene que mapear igual")
r16 = fo.parse(muestra("2026-09-16"), "2026-09-16")
ok(r16.get(("2026-09-16", 10)) is not None and r16[("2026-09-16", 10)][0] == "9",
   "6:00 PM Aguila -> codigo 9")
ok(len(r16) == 12, "jornada completa de 12 sorteos (hay %d)" % len(r16))

print("3) Delfin y Ballena no se confunden")
ok(r16.get(("2026-09-16", 2)) is not None and r16[("2026-09-16", 2)][0] == "0",
   "10:00 AM Delfin -> codigo '0'")
r03 = fo.parse(muestra("2026-09-03"), "2026-09-03")
ballenas = [v for v in r03.values() if v[0] == "00"]
ok(len(ballenas) == 1, "Ballena -> codigo '00' (encontradas %d)" % len(ballenas))
ok(not [v for v in r03.values() if v[0] == "0"], "ese dia no hubo Delfin y no se invento ninguno")

print("4) basura y casos vacios no tumban el parseo")
ok(fo.parse({}, "2026-09-20") == {}, "respuesta vacia -> dict vacio")
ok(fo.parse({"datos": []}, "2026-09-20") == {}, "sin datos -> dict vacio")
raro = {"datos": [{"id": "1", "resultados": [
    {"time_s": "08:00 AM", "number_animal": "35", "name_animal": "Jirafa"},
    {"time_s": "08:30 AM", "number_animal": "1", "name_animal": "Carnero"},
    {"time_s": "08:00 AM", "number_animal": "99", "name_animal": "Marciano"}]}]}
r = fo.parse(raro, "2026-09-20")
ok(r == {("2026-09-20", 0): ("35", "Jirafa")},
   "se ignora la hora fuera de calendario y el animal desconocido (quedo %r)" % r)

if "--vivo" in sys.argv:
    print("5) en vivo contra lottoactivo.com")
    hoy = fo.hoy_iso()
    viv = fo.resultados(hoy)
    ok(viv is not None, "la fuente responde")
    if viv:
        ok(all(v[0] in fo.IDX for v in viv.values()), "todos los codigos son del tablero")
        print("     %d sorteos hoy: %s" % (len(viv), sorted((h, v) for (_, h), v in viv.items())))

print()
print("FALLAS: %d" % len(fallos))
sys.exit(1 if fallos else 0)
