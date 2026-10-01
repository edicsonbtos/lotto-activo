# -*- coding: utf-8 -*-
"""Arma historial_la.txt (copia LOCAL de esta carpeta, no toca historial.txt):
historial.txt con la correccion de fechas 2026-09-29 aplicada (como hace servidor.py al arrancar)
y, desde 2026-09-16, los sorteos de la API oficial (oficial_multi.csv + oficial_extra.csv) hasta 2026-09-29."""
import csv, io, json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
HIST = os.path.join(RAIZ, "historial.txt")
SALIDA = os.path.join(AQUI, "historial_la.txt")
DESDE_OF = "2026-09-16"

def construir():
    cambios = {c["antes"]: c["despues"] for c in json.load(open(os.path.join(RAIZ, "herramientas", "correccion_historial_2026-09-29.json"), encoding="utf-8"))["cambios"]}
    lineas = [l.strip() for l in open(HIST, encoding="utf-8") if l.strip()]
    hits = sum(l in cambios for l in lineas)
    print("lineas", len(lineas), "a corregir encontradas", hits, "de", len(cambios))
    lineas = [cambios.get(l, l) for l in lineas]
    lineas = [l for l in lineas if l.split()[0] < DESDE_OF]
    of = []
    for ruta in (os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv"), os.path.join(AQUI, "oficial_extra.csv")):
        for r in csv.DictReader(io.open(ruta, encoding="utf-8")):
            if r["juego"] == "1" and r["fecha"] >= DESDE_OF:
                of.append(f'{r["fecha"]} {int(r["hora"][:2]) - 8} {r["codigo"]}')
    clave = lambda l: (l.split()[0], int(l.split()[1]))
    todo = sorted(set(lineas) | set(of), key=clave)
    assert len(set(map(clave, todo))) == len(todo), "duplicados"
    open(SALIDA, "w", encoding="utf-8").write("\n".join(todo) + "\n")
    print("escrito", SALIDA, len(todo), "ultimo", todo[-1])

if __name__ == "__main__":
    construir()
