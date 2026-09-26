# -*- coding: utf-8 -*-
"""Baja el tramo SELLADO: Lotto Activo en loteriadehoy ANTES del 2023-09-04.
NO CORRER hasta congelar los candidatos (commit en la rama motor-nuevo).

Uso (desde el worktree): ..\\lotto-activo\\.venv_scrape\\Scripts\\python.exe motor_nuevo\\sellado\\descargar.py
Salida: motor_nuevo/sellado/sellado_la.txt, una línea por sorteo: "fecha hora_idx codigo"
(hora_idx = hora del reloj - 8: 8AM=0 ... 7PM=11, el mismo formato que usa lotto_eval.cargar).
"""
import io, os, sys, datetime as dt, collections
AQUI = os.path.dirname(os.path.abspath(__file__))
WT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(WT, "scraping")); sys.path.insert(0, os.path.join(WT, "herramientas"))
import core  # noqa: E402
from rdint.datos import ANIMALES, sin_acentos  # noqa: E402

INICIO = dt.date(2019, 1, 7)
FIN = dt.date(2023, 9, 3)          # último día sellado (inclusive)
SALIDA = os.path.join(AQUI, "sellado_la.txt")


def main():
    filas, raros = [], collections.Counter()
    for ini in core.semanas_entre(INICIO, FIN):
        try:
            f = core.lh_historico("lottoactivo", ini, ini + dt.timedelta(days=6))
        except RuntimeError as e:
            print("FALLO", ini, e, flush=True); continue
        for r in f:
            if r["fecha"] > FIN.isoformat():
                continue
            cod = ANIMALES.get(sin_acentos(r["animal"]))
            h = int(r["hora"][:2]) - 8
            if cod is None or not r["hora"].endswith(":00") or not 0 <= h <= 11:
                raros[(r["animal"], r["hora"])] += 1; continue
            filas.append((r["fecha"], h, cod))
        print(ini, len(f), flush=True)
    filas = sorted(set(filas))
    with io.open(SALIDA, "w", encoding="utf-8") as out:
        for fe, h, c in filas:
            out.write(f"{fe} {h} {c}\n")
    por_dia = collections.Counter(fe for fe, _, _ in filas)
    print("total", len(filas), "sorteos,", len(por_dia), "días; sorteos/día:",
          collections.Counter(por_dia.values()).most_common(5))
    print("descartados:", raros.most_common(10))


if __name__ == "__main__":
    main()
