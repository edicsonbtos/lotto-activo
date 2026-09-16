# -*- coding: utf-8 -*-
"""ETL completo: descarga LH + tuazar para las loterias objetivo y guarda
JSONL parseados en datos_multiloteria/crudos/parsed/.

Uso: python etl.py [semanas]
Por defecto 22 semanas terminando en la ultima semana completa disponible en
tuazar (max = 2026-09-13 segun su propio datepicker; se auto-descubre).
"""
import io
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

OBJETIVO = ["lottoactivo", "lottoactivordint", "lagranjita", "selvaplus",
            "guacharoactivo"]

PARSED = os.path.join(core.CRUDOS, "parsed")
os.makedirs(PARSED, exist_ok=True)


def asignar_sorteo_dia(filas):
    """n_sorteo_dia = indice 0-based por hora dentro de (loteria, fecha)."""
    por_dia = {}
    for r in filas:
        por_dia.setdefault((r["loteria"], r["fecha"]), []).append(r)
    for k, rs in por_dia.items():
        rs.sort(key=lambda r: r["hora"])
        for i, r in enumerate(rs):
            r["n_sorteo_dia"] = i
    return filas


def guardar_jsonl(nombre, filas):
    p = os.path.join(PARSED, nombre)
    with io.open(p, "w", encoding="utf-8") as f:
        for r in filas:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return p


def main():
    semanas = int(sys.argv[1]) if len(sys.argv) > 1 else 22
    hoy = date.today()
    # ultima semana completa: la semana cuyo domingo ya paso
    domingo_pasado = hoy - timedelta(days=hoy.weekday() + 1)
    fin_lunes = core.lunes(domingo_pasado)
    inicio = fin_lunes - timedelta(days=7 * (semanas - 1))
    semanas_lista = core.semanas_entre(inicio, fin_lunes)
    print("ETL: %d semanas, %s .. %s" % (len(semanas_lista), inicio, fin_lunes))

    # ---- tuazar: 1 request por semana cubre TODAS las loterias
    filas_tz = []
    for m in semanas_lista:
        try:
            html = core.tuazar_semana(m)
            f = core.parse_tuazar_semana(html)
            filas_tz.extend(f)
            print("tuazar %s: %d filas (acum %d)" % (m, len(f), len(filas_tz)))
        except Exception as e:  # noqa: BLE001
            print("tuazar %s: ERROR %r" % (m, e))
    guardar_jsonl("tuazar_todas.jsonl", filas_tz)

    # ---- LH: 1 request por (loteria, semana)
    for slug in OBJETIVO:
        filas = []
        for m in semanas_lista:
            ini, fin = core.semana_rango(m)
            try:
                f = core.lh_historico(slug, ini, fin)
                filas.extend(f)
            except Exception as e:  # noqa: BLE001
                print("LH %s %s: ERROR %r" % (slug, m, e))
        print("LH %s: %d filas" % (slug, len(filas)))
        guardar_jsonl("lh_%s.jsonl" % slug, filas)

    # n_sorteo_dia
    for nombre in os.listdir(PARSED):
        if not nombre.endswith(".jsonl"):
            continue
        p = os.path.join(PARSED, nombre)
        filas = [json.loads(l) for l in io.open(p, encoding="utf-8")]
        asignar_sorteo_dia(filas)
        guardar_jsonl(nombre, filas)
        print("sorteo_dia asignado:", nombre, len(filas))


if __name__ == "__main__":
    main()
