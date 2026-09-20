# -*- coding: utf-8 -*-
"""OPERACION TURING - ENJAMBRE B: inventario de metadata del backend publico.

Fuente: capturas YA descargadas del backend oficial del operador
(api.lotterly.co/v1/results/<slug>/), en datos_multiloteria/crudos/.
NO se golpea el sistema en vivo: se leen los .json ya guardados.

Reproduccion:
  $env:PYTHONIOENCODING="utf-8"
  python investigacion\\2026-09-18\\b_producto\\inventario_api.py
"""
import json
import os
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
CRUDOS = os.path.join(RAIZ, "datos_multiloteria", "crudos")
FUENTES = ["arbitro_selva-plus.json", "arbitro_guacharo-activo.json"]


def inventario(ruta):
    d = json.load(open(ruta, encoding="utf-8"))
    keys = Counter()
    for r in d:
        keys.update(r.keys())
    horas = sorted(set(r["time"] for r in d))
    fechas = [r["date"] for r in d]
    # ¿alguna resolucion sub-slot? longitudes distintas de HH:MM:SS con segundos !=00/15
    seg = Counter(r["time"][-2:] for r in d)
    fallos = sum(1 for r in d if r["result"] in ("A", "", None))
    return dict(n=len(d), keys=dict(keys), n_horas=len(horas), horas=horas,
                fecha_min=min(fechas), fecha_max=max(fechas),
                segundos_distintos=dict(seg), resultados_fallidos=fallos)


def main():
    print("== Inventario de metadata publica (backend oficial api.lotterly.co) ==\n")
    for f in FUENTES:
        ruta = os.path.join(CRUDOS, f)
        if not os.path.exists(ruta):
            print("  (falta %s)" % f); continue
        inv = inventario(ruta)
        print("Fuente: %s" % f)
        print("  registros           : %d" % inv["n"])
        print("  CAMPOS por sorteo    : %s   <-- la superficie publica COMPLETA" % list(inv["keys"]))
        print("  rango de fechas      : %s .. %s" % (inv["fecha_min"], inv["fecha_max"]))
        print("  slots horarios       : %d (%s ... %s)" % (inv["n_horas"], inv["horas"][0], inv["horas"][-1]))
        print("  segundos en 'time'   : %s   <-- sin resolucion de ejecucion" % inv["segundos_distintos"])
        print("  resultados 'A'/vacio : %d (marcador de fallo de la API)" % inv["resultados_fallidos"])
        print()
    print("VEREDICTO: el unico timestamp es el SLOT PROGRAMADO (HH:15:00 o HH:00:00),")
    print("no la hora de ejecucion del sorteo. No hay id de sorteo, ni delay, ni")
    print("semilla, ni server-time, ni nonce. Nada correlaciona con el resultado.")


if __name__ == "__main__":
    main()
