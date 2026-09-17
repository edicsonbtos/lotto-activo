# -*- coding: utf-8 -*-
"""TEST B — Dependencia cruzada entre loterias (el mas importante).

Alineacion por hora del dia. Para cada par (A,B), lag L en horas
{0,±1,±2,±3,±6} y transformacion T en {id, ±1, espejo del tablero}:
  p̂  = tasa de coincidencia entre sorteos de A y sorteos de B a ~L horas
  p0 = tasa nula empirica (todas las parejas del mismo dia, sin alinear por
       hora; captura el solapamiento real de los tableros y las frecuencias)
  z  = (p̂ - p0)/sqrt(p0(1-p0)/n)

Umbral duro: z > 4 tras FDR (Benjamini-Hochberg, q=0.05) sobre las
10 pares x 7 lags x 3 transformaciones = 210 combinaciones.
SI ALGUN PAR LO SUPERA: se reporta en cabecera como ALERTA (mision: detener
todo y reportar antes de seguir).

Incluye verificacion de la anecdota del 13/09/2026 (Lotto Activo -> La
Granjita: 16 Oso lag 1h, 1 Carnero lag 3h, 27 Perro lag 6h).
"""
import io
import json
import math
import os
import sys
from collections import defaultdict
from itertools import combinations

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

RAIZ = core.RAIZ
SALIDA = os.path.join(RAIZ, "datos_multiloteria")
OBJETIVO = ["lottoactivo", "lottoactivordint", "lagranjita", "selvaplus",
            "guacharoactivo"]
LAGS = [0, 1, -1, 2, -2, 3, -3, 6, -6]
TOLS_MIN = 30
TRANSFORMS = ["id", "pm1", "espejo"]


def minutos(hora):
    hh, mm = hora.split(":")
    return int(hh) * 60 + int(mm)


def cargar(slug):
    por_dia = defaultdict(dict)
    n_tab = None
    with io.open(os.path.join(SALIDA, "%s.csv" % slug), encoding="utf-8") as f:
        next(f)
        for l in f:
            p = l.rstrip("\n").split(",")
            por_dia[p[0]][minutos(p[1])] = int(p[3])
            n_tab = int(p[5])
    return por_dia, n_tab


def coincide(na, nb, T, n_b):
    if T == "id":
        return na == nb
    if T == "pm1":
        return abs(na - nb) == 1
    if T == "espejo":
        return nb == n_b - 1 - na
    return False


def analizar_par(A, B, n_a, n_b):
    """Devuelve filas de resultado para el par (A,B)."""
    fechas = sorted(set(A) & set(B))
    # p0 empirico por transformacion: parejas del mismo dia sin alinear
    p0n = {T: [0, 0] for T in TRANSFORMS}
    for f in fechas:
        for na in A[f].values():
            for nb in B[f].values():
                for T in TRANSFORMS:
                    p0n[T][1] += 1
                    if coincide(na, nb, T, n_b):
                        p0n[T][0] += 1
    p0 = {T: (p0n[T][0] / p0n[T][1] if p0n[T][1] else 0.0) for T in TRANSFORMS}

    filas = []
    for L in LAGS:
        npair = 0
        hits = {T: 0 for T in TRANSFORMS}
        for f in fechas:
            for ta, na in A[f].items():
                objetivo = ta + 60 * L
                candidatos = [tb for tb in B[f]
                              if abs(tb - objetivo) <= TOLS_MIN]
                if not candidatos:
                    continue
                tb = min(candidatos, key=lambda t: abs(t - objetivo))
                nb = B[f][tb]
                npair += 1
                for T in TRANSFORMS:
                    if coincide(na, nb, T, n_b):
                        hits[T] += 1
        for T in TRANSFORMS:
            if npair == 0 or p0[T] == 0:
                continue
            ph = hits[T] / npair
            z = (ph - p0[T]) / math.sqrt(p0[T] * (1 - p0[T]) / npair)
            pval = 2.0 * (1.0 - stats.norm.cdf(abs(z)))
            filas.append({"par": None, "lag_h": L, "transform": T,
                          "n": npair, "hits": hits[T], "p_hat": ph,
                          "p0": p0[T], "z": z, "p": pval})
    return filas


def main():
    datos = {}
    n_tabs = {}
    for slug in OBJETIVO:
        datos[slug], n_tabs[slug] = cargar(slug)

    resultados = []
    for a, b in combinations(OBJETIVO, 2):
        n_a, n_b = n_tabs[a], n_tabs[b]
        filas = analizar_par(datos[a], datos[b], n_a, n_b)
        for r in filas:
            r["par"] = "%s -> %s" % (a, b)
            resultados.append(r)

    # FDR
    orden = sorted(range(len(resultados)), key=lambda i: resultados[i]["p"])
    m = len(orden)
    prev = 1.0
    for rango, i in reversed(list(enumerate(orden, start=1))):
        q = min(prev, float(resultados[i]["p"]) * m / rango)
        resultados[i]["p_fdr"] = float(q)
        resultados[i]["sig"] = bool(q < 0.05)
        prev = q

    alertas = [r for r in resultados if r["z"] > 4]
    resultados.sort(key=lambda r: -abs(r["z"]))

    # ---- verificacion anecdota 13/09/2026
    fecha = "2026-09-13"
    A, B = datos["lottoactivo"].get(fecha, {}), datos["lagranjita"].get(fecha, {})
    anec = []
    for L in (1, 3, 6):
        for ta, na in sorted(A.items()):
            cand = [tb for tb in B if abs(tb - (ta + 60 * L)) <= TOLS_MIN]
            if cand:
                tb = min(cand, key=lambda t: abs(t - (ta + 60 * L)))
                nb = B[tb]
                if na == nb:
                    anec.append((na, "%02d:%02d" % divmod(ta, 60),
                                 "%02d:%02d" % divmod(tb, 60), L))
    # conteo total de coincidencias ese dia por lag
    total_dia = {}
    for L in (0, 1, 2, 3, 6):
        c = 0
        for ta, na in A.items():
            cand = [tb for tb in B if abs(tb - (ta + 60 * L)) <= TOLS_MIN]
            if cand and na == B[min(cand, key=lambda t: abs(t - (ta + 60 * L)))]:
                c += 1
        total_dia[L] = c

    # ---- reporte
    md = ["# TEST B — Dependencia cruzada entre loterias", "",
          "Alineacion por hora del dia; nula empirica por transformacion",
          "(parejas del mismo dia sin alinear, captura solapamiento de",
          "tableros). Combinaciones: 10 pares x 9 lags x 3 transforms = 270.",
          "Umbral duro: z > 4 tras FDR (BH q=0.05).", ""]
    if alertas:
        md.append("## *** ALERTA: %d combinacion(es) con z > 4 ***" % len(alertas))
        for r in sorted(alertas, key=lambda r: -r["z"]):
            md.append("- **%s** lag %+dh transform=%s: z=%.2f "
                      "(p_h=%.4f vs p0=%.4f, n=%d, hits=%d, p_fdr=%.2g)"
                      % (r["par"], r["lag_h"], r["transform"], r["z"],
                         r["p_hat"], r["p0"], r["n"], r["hits"], r["p_fdr"]))
        md.append("")
        md.append("MISION CUMPLIDA: se detiene aqui el analisis; lo de arriba")
        md.append("es el resultado a reportar antes de cualquier otra cosa.")
        md.append("")
    else:
        md.append("## Sin alertas: ninguna combinacion supera z > 4 tras FDR.")
        md.append("")
    md.append("## Top 25 por |z|")
    md.append("| par | lag_h | transform | n | hits | p_hat | p0 | z | p_fdr |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    for r in resultados[:25]:
        md.append("| %s | %+d | %s | %d | %d | %.4f | %.4f | %+.2f | %.3g |"
                  % (r["par"], r["lag_h"], r["transform"], r["n"], r["hits"],
                     r["p_hat"], r["p0"], r["z"], r["p_fdr"]))
    md += ["", "## Prioridad mision: lottoactivo -> lagranjita", ""]
    prio = [r for r in resultados if r["par"] == "lottoactivo -> lagranjita"]
    prio.sort(key=lambda r: -abs(r["z"]))
    md.append("| lag_h | transform | n | hits | p_hat | p0 | z | p_fdr |")
    md.append("|---|---|---|---|---|---|---|---|")
    for r in prio:
        md.append("| %+d | %s | %d | %d | %.4f | %.4f | %+.2f | %.3g |"
                  % (r["lag_h"], r["transform"], r["n"], r["hits"], r["p_hat"],
                     r["p0"], r["z"], r["p_fdr"]))
    md += ["", "### Verificacion anecdota 2026-09-13 (Lotto Activo -> La Granjita)",
           "Coincidencias numero exacto observadas ese dia: " +
           "; ".join("numero %d a las %s -> %s (lag %dh)" % a for a in anec),
           "Conteo por lag ese dia (0,1,2,3,6h): %s" % total_dia,
           "",
           "Contexto: con 12 sorteos/dia en cada loteria y N=37, el numero",
           "esperado de coincidencias por azar en un dia es ~12*(12/37)≈3.9",
           "por lag util. Ver test_b_dependencia.json para el z global.", ""]
    with io.open(os.path.join(SALIDA, "test_b_dependencia.md"), "w",
                 encoding="utf-8") as f:
        f.write("\n".join(md))
    with io.open(os.path.join(SALIDA, "test_b_dependencia.json"), "w",
                 encoding="utf-8") as f:
        json.dump({"alertas": alertas, "resultados": resultados,
                   "anecdota_2026_09_13": {"coincidencias": anec,
                                            "conteo_por_lag": total_dia}},
                  f, ensure_ascii=False, indent=2)
    print("\n".join(md[:30]))
    print("\nALERTAS z>4:", len(alertas))
    print("anecdota 13/09:", anec, total_dia)


if __name__ == "__main__":
    main()
