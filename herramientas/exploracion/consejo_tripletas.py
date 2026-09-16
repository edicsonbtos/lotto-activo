# -*- coding: utf-8 -*-
"""Progreso de las tripletas pendientes contra el historial actual."""
import json, os
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POS = ["0", "00"] + [str(i) for i in range(1, 37)]

filas = []
for ln in open(os.path.join(RAIZ, "historial.txt"), encoding="utf-8"):
    p = ln.split()
    if len(p) == 3:
        filas.append((p[0], int(p[1]), p[2]))
indice = {(f, h): a for f, h, a in filas}
orden = sorted((f, h) for f, h, _ in filas)

d = json.load(open(os.path.join(RAIZ, "predicciones.json"), encoding="utf-8"))
for t in d.get("tripletas", []):
    if t.get("anulado") or t.get("estado") != "pendiente":
        continue
    ini = (t["inicio_fecha"], t["inicio_hora"])
    if ini not in orden:
        print(f"\nTripleta desde {ini[0]} h{ini[1]}: aun no empieza su ventana")
        for j, jug in enumerate(t["jugadas"], 1):
            print(f"  jugada {j}: {[POS[i] for i in jug]}")
        continue
    i0 = orden.index(ini)
    ventana = orden[i0:i0 + 12]
    salidos = [indice[k] for k in ventana]
    print(f"\nTripleta desde {ini[0]} h{ini[1]} ({len(ventana)}/12 sorteos jugados)")
    for j, jug in enumerate(t["jugadas"], 1):
        animales = [POS[i] for i in jug]
        hits = [a for a in animales if a in salidos]
        print(f"  jugada {j}: {animales}  -> salieron {hits} ({len(hits)}/3)")
    print(f"  ventana hasta ahora: {salidos}")
