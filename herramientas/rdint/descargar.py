# -*- coding: utf-8 -*-
"""Hilo 7: baja el historico completo de Lotto Activo RD Internacional (loteriadehoy).

Uso: .venv_scrape\Scripts\python.exe herramientas\rdint\descargar.py
Salida: datos_multiloteria/rdint_hist.csv  (fecha,hora,animal) — nombres crudos de LH.
Usa la cache de scraping/core.py (no vuelve a bajar semanas ya guardadas).
"""
import io, os, sys, datetime as dt
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scraping"))
import core

INICIO = dt.date(2023, 9, 4)
FIN = dt.date.today() - dt.timedelta(days=1)
SALIDA = os.path.join(RAIZ, "datos_multiloteria", "rdint_hist.csv")


def main():
    filas = []
    for ini in core.semanas_entre(INICIO, FIN):
        fin = ini + dt.timedelta(days=6)
        try:
            f = core.lh_historico("lottoactivordint", ini, fin)
        except RuntimeError as e:
            print("FALLO", ini, e, flush=True)
            continue
        filas += [r for r in f if r["fecha"] <= FIN.isoformat()]
        print(ini, len(f), flush=True)
    filas.sort(key=lambda r: (r["fecha"], r["hora"]))
    with io.open(SALIDA, "w", encoding="utf-8") as out:
        out.write("fecha,hora,animal\n")
        for r in filas:
            out.write("%s,%s,%s\n" % (r["fecha"], r["hora"], r["animal"]))
    print("total", len(filas), "->", SALIDA)


if __name__ == "__main__":
    main()
