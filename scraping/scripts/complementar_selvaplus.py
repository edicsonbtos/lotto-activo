# -*- coding: utf-8 -*-
"""Completa Selva Plus con la API de lotterly.co para los dias que tuazar no tiene.

- Descarga dia a dia api.lotterly.co/v1/results/selva-plus/?exact_date=YYYY-MM-DD
  (pausa 2,4 s entre requests). Cache en scraping/crudos/lotterly/.
- Como lotterly solo trae el NUMERO, el nombre del animal sale de tuazar: se
  arma el mapa numero -> animal con los dias que ambas fuentes tienen y se
  verifica que sea unico (si un numero tiene dos nombres, se avisa y no se usa).
- Escribe scraping/resultados/selvaplus_2026-04-11_2026-10-07.csv (sustituye el
  que solo tenia tuazar) y deja el log en scraping/logs/selvaplus_lotterly.txt.
"""
import csv
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import date, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(RAIZ, "resultados")
CACHE = os.path.join(RAIZ, "crudos", "lotterly")
LOGS = os.path.join(RAIZ, "logs")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(LOGS, exist_ok=True)

INI = date(2026, 4, 11)
FIN = date(2026, 10, 7)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
CAMPOS = ["fecha", "hora", "slot", "animal_numero", "animal_nombre", "operador", "timestamp_publicacion"]
PAUSA = 2.4


def bajar(dia):
    ruta = os.path.join(CACHE, "selva-plus_%s.json" % dia.isoformat())
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as fh:
            return json.load(fh)
    url = "https://api.lotterly.co/v1/results/selva-plus/?exact_date=%s&extended=true" % dia.isoformat()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        datos = json.loads(r.read().decode("utf-8"))
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False)
    time.sleep(PAUSA)
    return datos


def leer_tuazar():
    ruta = os.path.join(RES, "selvaplus_2026-04-11_2026-10-07.csv")
    filas = []
    with open(ruta, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            filas.append(r)
    return filas


def main():
    tz = leer_tuazar()
    tz_fechas = {r["fecha"] for r in tz}
    tz_claves = {(r["fecha"], r["hora"][:5]) for r in tz}

    # mapa numero -> animal, solo con numeros que tuazar da de forma unica
    nombres = defaultdict(set)
    for r in tz:
        nombres[int(r["animal_numero"])].add(r["animal_nombre"])
    mapa = {n: list(v)[0] for n, v in nombres.items() if len(v) == 1}
    conflictos = {n: sorted(v) for n, v in nombres.items() if len(v) > 1}

    # lotterly: solo los dias que tuazar no cubre
    faltan = []
    d = INI
    while d <= FIN:
        if d.isoformat() not in tz_fechas:
            faltan.append(d)
        d += timedelta(days=1)
    print("dias sin tuazar:", len(faltan))

    nuevas = []
    sin_mapa = set()
    fallos = []
    for dia in faltan:
        try:
            datos = bajar(dia)
        except Exception as e:  # noqa: BLE001
            fallos.append((dia.isoformat(), repr(e)))
            continue
        for sorteo in datos:
            hora = sorteo["time"][:5]
            res = sorteo.get("results") or []
            if not res:
                continue
            num = int(res[0]["result"])
            animal = mapa.get(num)
            if animal is None:
                sin_mapa.add(num)
            nuevas.append({"fecha": sorteo["date"], "hora": hora, "numero": num, "animal": animal or ""})
        print("  %s: %d sorteos" % (dia.isoformat(), len(datos)))

    # unir: tuazar + lotterly, sin duplicar
    todas = {}
    for r in tz:
        todas[(r["fecha"], r["hora"][:5])] = {
            "fecha": r["fecha"], "hora": r["hora"][:5],
            "numero": int(r["animal_numero"]), "animal": r["animal_nombre"], "fuente": "tuazar"}
    for r in nuevas:
        k = (r["fecha"], r["hora"])
        if k not in todas:
            todas[k] = {**r, "fuente": "lotterly"}

    lista = sorted(todas.values(), key=lambda x: (x["fecha"], x["hora"]))
    por_dia = defaultdict(list)
    for x in lista:
        por_dia[x["fecha"]].append(x)
    salida = []
    for dia in sorted(por_dia):
        for i, x in enumerate(por_dia[dia], 1):
            salida.append({
                "fecha": x["fecha"], "hora": x["hora"] + ":00", "slot": i,
                "animal_numero": x["numero"], "animal_nombre": x["animal"],
                "operador": "selvaplus", "timestamp_publicacion": ""})

    with open(os.path.join(RES, "selvaplus_2026-04-11_2026-10-07.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(salida)

    lineas = [
        "Selva Plus: tuazar + lotterly",
        "dias sin tuazar: %d (descargados o en cache: %d, fallos: %d)" % (len(faltan), len(faltan) - len(fallos), len(fallos)),
        "sorteos finales: %d en %d dias" % (len(salida), len(por_dia)),
        "numeros con nombre unico en tuazar: %d; sin nombre (no mapeados): %s" % (len(mapa), sorted(sin_mapa) or "ninguno"),
        "numeros con nombres en conflicto en tuazar (no usados): %s" % (conflictos or "ninguno"),
    ]
    for f_, e in fallos[:10]:
        lineas.append("fallo %s: %s" % (f_, e))
    texto = "\n".join(lineas)
    print(texto)
    with open(os.path.join(LOGS, "selvaplus_lotterly.txt"), "w", encoding="utf-8") as fh:
        fh.write(texto + "\n")


if __name__ == "__main__":
    main()
