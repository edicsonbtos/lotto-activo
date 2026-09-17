# -*- coding: utf-8 -*-
"""TEST A — Firma de politica por loteria (individual).

a) Evitacion intradia: para cada sorteo del dia tras el primero, X=1 si el
   numero ya salio ese dia. Bajo iid uniforme con tablero N, en la posicion
   k (0-based) p_k = 1-(1-1/N)^k. z = (S_X - S_p)/sqrt(S_p(1-p)).
b) Bump 13-27 condicionado a no-salio-hoy: sobre sorteos cuyo numero no
   salio antes ese dia, Y=1 si numero en [13,27]. Bajo uniforme p = 15/N.
c) Uniformidad chi^2 del primer sorteo del dia (n_sorteo_dia = 0).

Control: lottoactivo. Referencia fuerte: historial.txt completo (12.502
sorteos, 3 anos, SOLO LECTURA). FDR de Benjamini-Hochberg q=0.05 entre
loterias x subtests. Umbral de senal: |z| > 3 y significativo con FDR.

Clasificacion: MISMA FIRMA / DISTINTA / SIN SESGO / INCONCLUSO.
"""
import io
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

RAIZ = core.RAIZ
SALIDA = os.path.join(RAIZ, "datos_multiloteria")
OBJETIVO = ["lottoactivo", "lottoactivordint", "lagranjita", "selvaplus",
            "guacharoactivo"]


def cargar_csv(slug):
    filas = []
    with io.open(os.path.join(SALIDA, "%s.csv" % slug), encoding="utf-8") as f:
        next(f)
        for l in f:
            p = l.rstrip("\n").split(",")
            filas.append({"fecha": p[0], "hora": p[1],
                          "n_sorteo_dia": int(p[2]), "numero": int(p[3]),
                          "n_tablero": int(p[5])})
    return filas


def cargar_historial():
    por_dia = defaultdict(list)
    with io.open(os.path.join(RAIZ, "historial.txt"), encoding="utf-8") as f:
        for linea in f:
            p = linea.split()
            if len(p) >= 3:
                por_dia[p[0]].append((int(p[1]), int(p[2])))
    return por_dia


def test_intradia(por_dia, n_tab, desde=None, hasta=None):
    sx = sp = 0.0
    for fecha, rs in por_dia.items():
        if desde and not (desde <= fecha <= hasta):
            continue
        vistos = set()
        for _, n in sorted(rs):
            if vistos:
                k = len(vistos)
                p = 1.0 - (1.0 - 1.0 / n_tab) ** k
                sp += p
                sx += 1.0 if n in vistos else 0.0
            vistos.add(n)
    if sp == 0:
        return None
    z = (sx - sp) / math.sqrt(sp * (1.0 - 1.0 / n_tab))
    pval = 2.0 * (1.0 - stats.norm.cdf(abs(z)))
    return {"n_esperado": sp, "n_observado": sx, "z": z, "p": pval}


def test_bump(por_dia, n_tab, desde=None, hasta=None):
    sy = sn = 0.0
    p0 = 15.0 / n_tab
    for fecha, rs in por_dia.items():
        if desde and not (desde <= fecha <= hasta):
            continue
        vistos = set()
        for _, n in sorted(rs):
            if vistos and n not in vistos:
                sn += 1
                sy += 1.0 if 13 <= n <= 27 else 0.0
            vistos.add(n)
    if sn == 0:
        return None
    z = (sy - sn * p0) / math.sqrt(sn * p0 * (1 - p0))
    pval = 2.0 * (1.0 - stats.norm.cdf(abs(z)))
    return {"n_cond": sn, "obs": sy, "esp": sn * p0, "z": z, "p": pval}


def test_chi2_primero(por_dia, n_tab, desde=None, hasta=None):
    cont = np.zeros(n_tab, dtype=np.int64)
    for fecha, rs in por_dia.items():
        if desde and not (desde <= fecha <= hasta):
            continue
        prim = min(rs)
        cont[prim[1]] += 1
    tot = cont.sum()
    if tot == 0:
        return None
    esp = tot / n_tab
    chi2 = float(((cont - esp) ** 2 / esp).sum())
    pval = float(stats.chi2.sf(chi2, n_tab - 1))
    top = int(cont.argmax())
    return {"chi2": chi2, "p": pval, "n": int(tot), "top_numero": top,
            "top_cuenta": int(cont[top])}


def bh_fdr(resultados):
    """resultados: lista de dicts con 'p'; anade 'p_fdr' y 'sig'."""
    orden = sorted((i for i in range(len(resultados)) if resultados[i]),
                   key=lambda i: resultados[i]["p"])
    m = len(orden)
    prev = 1.0
    for rango, i in reversed(list(enumerate(orden, start=1))):
        q = min(prev, float(resultados[i]["p"]) * m / rango)
        resultados[i]["p_fdr"] = float(q)
        resultados[i]["sig"] = bool(q < 0.05)
        prev = q


def main():
    # referencia: historial.txt completo (control, 3 anos)
    hist = cargar_historial()
    ref = {
        "intradia": test_intradia(hist, 37),
        "bump": test_bump(hist, 37),
        "chi2": test_chi2_primero(hist, 37),
    }
    ventana = {}
    resultados = {}
    for slug in OBJETIVO:
        filas = cargar_csv(slug)
        n_tab = filas[0]["n_tablero"]
        por_dia = defaultdict(list)
        for r in filas:
            por_dia[r["fecha"]].append((r["n_sorteo_dia"], r["numero"]))
        ventana[slug] = (min(por_dia), max(por_dia))
        resultados[slug] = [
            dict(subtest="a_evitacion_intradia",
                 **test_intradia(por_dia, n_tab)),
            dict(subtest="b_bump_13_27", **test_bump(por_dia, n_tab)),
            dict(subtest="c_chi2_primero", **test_chi2_primero(por_dia, n_tab)),
        ]
    # FDR global entre loterias x subtests
    planos = [r for slug in OBJETIVO for r in resultados[slug]]
    bh_fdr(planos)

    # ---- reporte
    md = ["# TEST A — Firma de politica por loteria", "",
          "Ventana: 2026-04-13 .. 2026-09-13 (5 meses). N = tablero observado",
          "(ver tableros.md). FDR: Benjamini-Hochberg q=0.05 entre las 15",
          "celdas (5 loterias x 3 subtests). Umbral: |z| > 3 y p_fdr < 0.05.",
          "",
          "## Referencia control — Lotto Activo en historial.txt (12.502 sorteos, 3 anos, solo lectura)",
          "- a) evitacion intradia: z = %+.2f (p=%.2g)  esperado %.1f vs observado %.0f"
          % (ref["intradia"]["z"], ref["intradia"]["p"],
             ref["intradia"]["n_esperado"], ref["intradia"]["n_observado"]),
          "- b) bump 13-27: z = %+.2f (p=%.2g)  observado %.0f vs esperado %.1f"
          % (ref["bump"]["z"], ref["bump"]["p"], ref["bump"]["obs"],
             ref["bump"]["esp"]),
          "- c) chi2 primero: %.1f (p=%.2g), n=%d, top=%d (%d veces)"
          % (ref["chi2"]["chi2"], ref["chi2"]["p"], ref["chi2"]["n"],
             ref["chi2"]["top_numero"], ref["chi2"]["top_cuenta"]),
          ""]
    tabla = ["| loteria | N | subtest | estadistico | p | p_fdr | senal |",
             "|---|---|---|---|---|---|---|"]
    clasif = {}
    for slug in OBJETIVO:
        n_tab = cargar_csv(slug)[0]["n_tablero"]
        senales = []
        for r in resultados[slug]:
            if r["subtest"].startswith("c"):
                est = "chi2=%.1f" % r["chi2"]
                fuerte = abs(r["z"]) > 3 if "z" in r else False
                marca = "SIG" if (r["sig"] and r["p"] < 0.001) else \
                        ("marginal" if r["sig"] else "no")
                z_txt = ""
            else:
                est = "z=%+.2f" % r["z"]
                marca = "SIG" if (r["sig"] and abs(r["z"]) > 3) else \
                        ("marginal" if r["sig"] else "no")
                z_txt = r["z"]
            if marca == "SIG":
                senales.append((r["subtest"], z_txt if z_txt != "" else None))
            tabla.append("| %s | %d | %s | %s | %.3g | %.3g | %s |"
                         % (slug, n_tab, r["subtest"], est, r["p"],
                            r["p_fdr"], marca))
        # clasificacion
        n = resultados[slug][0]["n_observado"] if "n_observado" in resultados[slug][0] else 0
        total = len(cargar_csv(slug))
        ref_sig = [s for s, z in (("a", ref["intradia"]["z"]),
                                  ("b", ref["bump"]["z"]))]
        if total < 600:
            c = "INCONCLUSO (muy pocos datos)"
        elif not senales:
            c = "SIN SESGO detectable"
        else:
            coinciden = all(s[0] in ("a_evitacion_intradia", "b_bump_13_27") for s in senales)
            dirs = all(((s[1] or 0) < 0) == (ref["intradia"]["z"] < 0)
                       for s in senales if s[0] == "a_evitacion_intradia")
            c = "MISMA FIRMA que el control" if (coinciden and dirs) else \
                "DISTINTA (senal con signo/patron diferente)"
        clasif[slug] = c
        md.append("## %s — **%s**" % (slug, c))
        for s in senales:
            md.append("- senal: %s (z=%s)" % (s[0], ("%+.2f" % s[1]) if s[1] is not None else "chi2"))
        md.append("")
    md += tabla
    md.append("")
    md.append("## Clasificacion final")
    for slug in OBJETIVO:
        md.append("- **%s**: %s" % (slug, clasif[slug]))
    with io.open(os.path.join(SALIDA, "test_a_firma.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    with io.open(os.path.join(SALIDA, "test_a_firma.json"), "w", encoding="utf-8") as f:
        json.dump({"referencia_historial": ref, "resultados": resultados,
                   "clasificacion": clasif}, f, ensure_ascii=False, indent=2)
    print("\n".join(md[:40]))
    print("...\nclasificacion:", json.dumps(clasif, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
