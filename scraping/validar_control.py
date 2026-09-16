# -*- coding: utf-8 -*-
"""Validacion del scraper (control Lotto Activo contra historial.txt, solo lectura).

1. Parsea una semana LH cacheada y una semana tuazar cacheada.
2. Construye el tablero animal->numero desde tuazar (co-ocurrencia numero+animal).
3. Compara LH (animal->numero via tablero) y tuazar contra historial.txt
   (fecha, n_sorteo_dia, numero). Exige >=99% de coincidencia.
"""
import io
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

RAIZ = core.RAIZ


def cargar_historial():
    """historial.txt -> {(fecha, n_sorteo): numero}  (SOLO LECTURA)."""
    hist = {}
    with io.open(os.path.join(RAIZ, "historial.txt"), encoding="utf-8") as f:
        for linea in f:
            p = linea.split()
            if len(p) >= 3:
                hist[(p[0], int(p[1]))] = int(p[2])
    return hist


def tablero_desde_tuazar(filas_tz, slug=None):
    """Quorum: numero->animal y animal->numero por mayoria de co-ocurrencias.

    override_loteria: ajustes documentados por loteria. Para lottoactivo, el 0
    es DELFIN segun reglamento oficial (PDF) y tablero LH; tuazar etiqueta el
    alt de la imagen 0 como BALLENA la mayoria de las veces (error conocido de
    tuazar, heredado de La Granjita)."""
    por_num = defaultdict(Counter)
    for r in filas_tz:
        por_num[r["numero"]][core.norm_animal(r["animal"])] += 1
    num_a_animal = {}
    conflicto = []
    for n, c in por_num.items():
        top, veces = c.most_common(1)[0]
        total = sum(c.values())
        if veces < total:  # hubo discordancia
            conflicto.append((n, dict(c)))
        num_a_animal[n] = top
    if slug == "lottoactivo":
        num_a_animal[0] = "DELFIN"  # arbitro: reglamento oficial + LH (tuazar erra)
    animal_a_num = {}
    for n, a in num_a_animal.items():
        animal_a_num.setdefault(a, n)
    if slug == "lottoactivo":
        # LH (y a veces tuazar) etiquetan el 0 como BALLENA en sus propias
        # filas; el numero es siempre 0. Alias documentado para el lookup.
        animal_a_num["BALLENA"] = 0
    return num_a_animal, animal_a_num, conflicto


def hora_a_sorteo(hora):
    """Lotto Activo: sorteo 0 = 08:00 ... sorteo 11 = 19:00 (convencion historial.txt)."""
    hh, mm = hora.split(":")
    return int(hh) - 8


def main():
    # --- datos de prueba: semana 2026-08-10..16 (ambas fuentes cacheadas)
    ini, fin = core.semana_rango(core.lunes(__import__("datetime").date(2026, 8, 10)))
    lh = core.lh_historico("lottoactivo", ini, fin)
    html_tz = core.tuazar_semana(ini)
    tz = core.parse_tuazar_semana(html_tz, solo_slugs={"lottoactivo"})
    print("LH filas:", len(lh), " tuazar filas:", len(tz))

    num_a_animal, animal_a_num, conflicto = tablero_desde_tuazar(tz, slug="lottoactivo")
    print("tablero (num->animal):", len(num_a_animal), "numeros; conflictos:", conflicto)
    print(json.dumps({k: num_a_animal[k] for k in sorted(num_a_animal)}, ensure_ascii=False))

    hist = cargar_historial()

    def evaluar(filas, nombre, usar_tablero):
        total = aciertos = sin_ref = 0
        errores = []
        for r in filas:
            k = (r["fecha"], r.get("n_sorteo_dia") or hora_a_sorteo(r["hora"]))
            if k not in hist:
                sin_ref += 1
                continue
            total += 1
            if usar_tablero:
                num = animal_a_num.get(core.norm_animal(r["animal"]))
            else:
                num = r.get("numero")
            if num == hist[k]:
                aciertos += 1
            else:
                errores.append((k, num, hist[k], r["animal"]))
        return total, aciertos, sin_ref, errores

    for filas, nombre, modo in ((lh, "loteriadehoy", "tablero"),
                                (tz, "tuazar", "directo")):
        total, aciertos, sin_ref, errores = evaluar(filas, nombre, modo == "tablero")
        pct = 100.0 * aciertos / total if total else 0.0
        print("\n[%s] total=%d aciertos=%d (%.2f%%) sin_referencia=%d"
              % (nombre, total, aciertos, pct, sin_ref))
        for e in errores[:10]:
            print("   DISCREPANCIA", e)
        if pct < 99.0:
            print("   *** VALIDACION FALLIDA para", nombre)
            sys.exit(2)
    print("\nVALIDACION OK: ambas fuentes >=99% contra historial.txt")


if __name__ == "__main__":
    main()

