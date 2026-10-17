# -*- coding: utf-8 -*-
"""Auditoría independiente del archivo de pronosticadores con copias del Wayback Machine.
Para cada copia de lotoven/loteriadehoy tomada el día D (hora Venezuela, UTC-4) se extraen los números de LA y RD Int
y se comparan con lo que el archivo devuelve hoy para D (publicados.jsonl del estudio 2026-10-15 o capturas/).
Si el archivo hubiera sido rehecho quitando ganadores, la copia vieja tendría animales que el archivo ya no tiene.
Cortés con archive.org: 1 consulta cada 6 s y reintentos con espera larga ante 429."""
import json, os, subprocess, sys, time
from datetime import datetime, timedelta
AQUI = os.path.dirname(os.path.abspath(__file__))
EST = os.path.join(AQUI, "..", "..", "2026-10-15", "pronosticadores")
sys.path.insert(0, EST)
import descargar as d

SITIOS = {"lotoven": ("lotoven.com/datos/", d.p_lotoven), "loteriadehoy": ("loteriadehoy.com/datos/animalitos/", d.p_ldh)}
COP = os.path.join(AQUI, "wayback"); os.makedirs(COP, exist_ok=True)

def get(url, intentos=6):
    for i in range(intentos):
        r = subprocess.run(["curl", "-s", "-L", "-m", "90", "-w", "\n%{http_code}", url], capture_output=True)
        txt = r.stdout.decode("utf-8", "replace"); cuerpo, _, cod = txt.rpartition("\n")
        if cod == "200":
            time.sleep(6); return cuerpo
        print("  HTTP", cod, "esperando", 120 * (i + 1), "s", flush=True); time.sleep(120 * (i + 1))
    return None

viejo = {}
for ln in open(os.path.join(EST, "datos", "publicados.jsonl"), encoding="utf-8"):
    r = json.loads(ln); viejo[(r["fuente"], r["fecha"])] = r["datos"]

filas = []
for fuente, (url, parse) in SITIOS.items():
    cdx = get(f"https://web.archive.org/cdx/search/cdx?url={url}&from=2024&filter=statuscode:200&fl=timestamp&collapse=timestamp:10")
    if cdx is None:
        print("CDX no disponible para", fuente); continue
    ts = [t for t in cdx.split() if t.isdigit()]
    print(fuente, len(ts), "copias", flush=True)
    for t in ts:
        utc = datetime.strptime(t, "%Y%m%d%H%M%S"); vet = utc - timedelta(hours=4); D = vet.date().isoformat()
        if (fuente, D) not in viejo:
            filas.append({"fuente": fuente, "ts": t, "fecha": D, "estado": "fecha fuera del archivo bajado"}); continue
        ruta = os.path.join(COP, f"{fuente}_{t}.html")
        if not os.path.exists(ruta):
            h = get(f"https://web.archive.org/web/{t}id_/https://{url}")
            if h is None:
                continue
            open(ruta, "w", encoding="utf-8").write(h)
        h = open(ruta, encoding="utf-8").read()
        cop = parse(h, D)
        for j in ("Lotto Activo", "Lotto Activo RD Int"):
            c = cop.get(j, {}); a = viejo[(fuente, D)].get(j, {})
            if c.get("fecha_pagina") != D:
                est = f"la copia muestra otra fecha ({c.get('fecha_pagina')})"
            elif c.get("nums") == a.get("nums"):
                est = "IGUAL"
            else:
                est = "DISTINTO"
            filas.append({"fuente": fuente, "ts": t, "hora_vet": vet.strftime("%H:%M"), "fecha": D, "juego": j,
                          "copia": c.get("nums"), "archivo": a.get("nums"), "estado": est})
        print(fuente, t, D, [f["estado"] for f in filas[-2:]], flush=True)

json.dump(filas, open(os.path.join(AQUI, "wayback_resultado.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print(Counter((f["fuente"], f["estado"]) for f in filas))
