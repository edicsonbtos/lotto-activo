# -*- coding: utf-8 -*-
"""Validacion cruzada v2 — registro a registro entre fuentes INDEPENDIENTES.

Fuentes por loteria:
  lottoactivo      : LH + tuazar (22 sem). Arbitro de discrepancias: historial.txt
  lagranjita       : LH + tuazar (22 sem). Sin arbitro oficial disponible.
  lottoactivordint : LH (22 sem) + tuazar (1 sem; es nueva en tuazar).
  selvaplus        : LH + ARBITRO OFICIAL api.lotterly.co (22 sem) + tuazar (1 sem).
  guacharoactivo   : LH + ARBITRO OFICIAL api.lotterly.co (22 sem) + tuazar (1 sem).

Independencia: lotoven.com NO cuenta (misma BD que LH, verificado). tuazar es
independiente de LH. api.lotterly.co es el backend oficial de selvaplus.com y
guacharoactivo.com.ve (independiente de LH y tuazar).

Traduccion animal(LH)->numero: pareo empirico por mayoria contra la fuente
numerada de la loteria (arbitro o tuazar). Resuelve variantes como
CHIGUIRE(LH)/CHUGUIRE(TZ), OSO HORMIGUERO/HORMIGUERO, ZEBRA/CEBRA y el caso
documentado 0=Delfin/Ballena (etiqueta inconsistente en ambas fuentes; el
NUMERO siempre es consistente).

Salidas: datos_multiloteria/validacion_cruzada.md, discrepancias.csv,
resumen_validacion.json, y crudos/parsed/canonicos_<slug>.jsonl
"""
import io
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

RAIZ = core.RAIZ
SALIDA = os.path.join(RAIZ, "datos_multiloteria")
PARSED = os.path.join(core.CRUDOS, "parsed")

OBJETIVO = ["lottoactivo", "lottoactivordint", "lagranjita", "selvaplus",
            "guacharoactivo"]

# nombre canonico del numero 0 segun arbitros documentados
NOMBRE_CERO = {"lottoactivo": "DELFIN", "lagranjita": "BALLENA",
               "lottoactivordint": "DELFIN"}


def cargar_jsonl(nombre):
    p = os.path.join(PARSED, nombre)
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in io.open(p, encoding="utf-8")]


def cargar_historial():
    hist = {}
    with io.open(os.path.join(RAIZ, "historial.txt"), encoding="utf-8") as f:
        for linea in f:
            p = linea.split()
            if len(p) >= 3:
                hist[(p[0], int(p[1]))] = int(p[2])
    return hist


def cargar_arbitro(slug):
    """Arbitro oficial lotterly -> {(fecha,hora): numero}."""
    p = os.path.join(SALIDA, "crudos", "arbitro_%s.json" % slug)
    if not os.path.exists(p):
        return {}
    datos = json.load(io.open(p, encoding="utf-8"))
    out = {}
    for d in datos:
        if str(d.get("result", "")).isdigit():
            out[(d["date"], d["time"][:5])] = int(d["result"])
    return out


def pareo_lh_a_num(lh, num_por_clave):
    """animal(LH) -> numero por mayoria sobre claves comunes."""
    par = defaultdict(Counter)
    for r in lh:
        n = num_por_clave.get((r["fecha"], r["hora"]))
        if n is not None:
            par[core.norm_animal(r["animal"])][n] += 1
    return {a: c.most_common(1)[0][0] for a, c in par.items()}, par


def tablero_canonico(slug, filas_tz, arb_map, lh, base_animal_a_num=None):
    """Devuelve (num->animal canonico, animal->num, conflictos, fuente)."""
    por_num = defaultdict(Counter)
    fuente_nombres = "tuazar"
    if arb_map:
        # nombres desde pareo LH<->arbitro (cubre todo el rango observado)
        par, _ = pareo_lh_a_num(lh, arb_map)
        for a, n in par.items():
            por_num[n][a] += 1
        fuente_nombres = "pareo(LH,arbitro)+tuazar"
    # tuazar aporta co-ocurrencias numero+nombre (acotado a su cobertura)
    for r in filas_tz:
        por_num[r["numero"]][core.norm_animal(r["animal"])] += 1
    num_a_animal = {}
    conflictos = []
    for n, c in por_num.items():
        top, veces = c.most_common(1)[0]
        if veces < sum(c.values()):
            conflictos.append((n, dict(c)))
        num_a_animal[n] = top
    if slug in NOMBRE_CERO and 0 in num_a_animal:
        num_a_animal[0] = NOMBRE_CERO[slug]
    animal_a_num = {}
    for n in sorted(num_a_animal):
        animal_a_num.setdefault(num_a_animal[n], n)
    # fallback al tablero base (lottoactivo, verificado contra historial.txt):
    # todas las loterias comparten la numeracion base; se anade solo si no
    # hay conflicto con el pareo propio de la loteria.
    if base_animal_a_num:
        for a, n in base_animal_a_num.items():
            if a in animal_a_num and animal_a_num[a] != n:
                conflictos.append(("BASE_CONFLICTO", {a: (n, animal_a_num[a])}))
                continue
            animal_a_num.setdefault(a, n)
    if slug in NOMBRE_CERO:
        animal_a_num.setdefault("BALLENA", 0)
        animal_a_num.setdefault("DELFIN", 0)
    return num_a_animal, animal_a_num, conflictos, fuente_nombres


def main():
    tz_all = cargar_jsonl("tuazar_todas.jsonl")
    hist = cargar_historial()
    ARB_SLUG = {"selvaplus": "selva-plus", "guacharoactivo": "guacharo-activo"}

    reporte_md = ["# Validacion cruzada de fuentes (v2)", "",
                  "Fuentes INDEPENDIENTES: loteriadehoy.com (LH), tuazar.com (TZ)",
                  "y api.lotterly.co (ARBITRO oficial, backend de selvaplus.com y",
                  "guacharoactivo.com.ve). lotoven.com queda DESCARTADO como fuente:",
                  "comparte base de datos con LH (mismos animales y rutas de imagen",
                  "/dist/animals_img/ verificados en la misma semana).", ""]
    discrep_csv = ["loteria,fecha,hora,votos,resolucion"]
    resumen = {}

    # tablero base = lottoactivo (control verificado contra historial.txt)
    lh_ctrl = cargar_jsonl("lh_lottoactivo.jsonl")
    tz_ctrl = [r for r in cargar_jsonl("tuazar_todas.jsonl")
               if r["loteria"] == "lottoactivo"]
    tz_ctrl_map = {(r["fecha"], r["hora"]): r["numero"] for r in tz_ctrl}
    base_a_n, _ = pareo_lh_a_num(lh_ctrl, tz_ctrl_map)
    base_a_n.setdefault("BALLENA", 0)

    for slug in OBJETIVO:
        lh = cargar_jsonl("lh_%s.jsonl" % slug)
        filas_tz = [r for r in tz_all if r["loteria"] == slug]
        arb_map = cargar_arbitro(ARB_SLUG[slug]) if slug in ARB_SLUG else {}

        num_a_animal, animal_a_num, conflictos, fuente_nombres = \
            tablero_canonico(slug, filas_tz, arb_map, lh, base_a_n)

        # ventana de estudio = rango de fechas cubierto por LH para esta loteria
        fechas_lh = sorted({r["fecha"] for r in lh})
        if fechas_lh:
            ini_w, fin_w = fechas_lh[0], fechas_lh[-1]
            filas_tz = [r for r in filas_tz if ini_w <= r["fecha"] <= fin_w]
            arb_map = {k: v for k, v in arb_map.items()
                       if ini_w <= k[0] <= fin_w}

        # votos por clave: {clave: {fuente: numero}}
        votos = defaultdict(dict)
        for r in lh:
            n = animal_a_num.get(core.norm_animal(r["animal"]))
            votos[(r["fecha"], r["hora"])]["LH"] = n
        for r in filas_tz:
            votos[(r["fecha"], r["hora"])]["TZ"] = r["numero"]
        for k, n in arb_map.items():
            votos[k]["ARB"] = n

        canonicos, stats = [], Counter()
        detalle_disc = []
        for k in sorted(votos):
            v = votos[k]
            nums = {f: n for f, n in v.items() if n is not None}
            if len(nums) >= 2:
                c = Counter(nums.values())
                top, veces = c.most_common(1)[0]
                if veces >= 2:  # quorum 2 de 3 (o 2 de 2)
                    fuentes = sorted(f for f, n in nums.items() if n == top)
                    canonicos.append({"fecha": k[0], "hora": k[1], "numero": top,
                                      "animal": num_a_animal.get(top, ""),
                                      "fuente": "+".join(fuentes)})
                    stats["acuerdo_%d_fuentes" % len(nums)] += 1
                else:
                    # discordancia real 1-1 (o 1-1-1)
                    stats["discrepancia"] += 1
                    resol = "SIN_RESOLVER"
                    if slug == "lottoactivo":
                        s = int(k[1][:2]) - 8
                        h = hist.get((k[0], s))
                        if h is not None:
                            votos_arb = "historial[%d]" % h
                            if h in nums.values():
                                gan = [f for f, n in nums.items() if n == h]
                                canonicos.append({
                                    "fecha": k[0], "hora": k[1], "numero": h,
                                    "animal": num_a_animal.get(h, ""),
                                    "fuente": "+".join(sorted(gan + ["historial"]))})
                                resol = "historial coincide con %s" % gan
                                stats["resuelta_historial"] += 1
                            else:
                                resol = "historial dice %d (distinto!)" % h
                    detalle_disc.append((k, dict(nums), resol))
                    discrep_csv.append("%s,%s,%s,%s,%s"
                                       % (slug, k[0], k[1],
                                          json.dumps(nums, ensure_ascii=False),
                                          resol))
            elif len(nums) == 1:
                f, n = next(iter(nums.items()))
                canonicos.append({"fecha": k[0], "hora": k[1], "numero": n,
                                  "animal": num_a_animal.get(n, ""),
                                  "fuente": f + "(solo)"})
                stats["solo_%s" % f] += 1

        # n_sorteo_dia por orden horario dentro del dia
        por_dia = defaultdict(list)
        for r in canonicos:
            por_dia[r["fecha"]].append(r)
        for fecha, rs in por_dia.items():
            rs.sort(key=lambda r: r["hora"])
            for i, r in enumerate(rs):
                r["n_sorteo_dia"] = i
        canonicos.sort(key=lambda r: (r["fecha"], r["n_sorteo_dia"]))
        with io.open(os.path.join(PARSED, "canonicos_%s.jsonl" % slug), "w",
                     encoding="utf-8") as f:
            for r in canonicos:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        n_tab = (max(num_a_animal) + 1) if num_a_animal else 0
        n_fechas = len(por_dia)
        resumen[slug] = {
            "canonicos": len(canonicos), "dias": n_fechas,
            "stats": dict(stats), "n_tablero_obs": n_tab,
            "rango_obs": [min(num_a_animal), max(num_a_animal)] if num_a_animal else None,
            "conflictos_nombre": conflictos,
            "fuente_nombres": fuente_nombres,
            "discrepancias": detalle_disc,
        }
        print("%-16s canonicos=%4d dias=%3d N=%3d rango=%s | %s"
              % (slug, len(canonicos), n_fechas, n_tab,
                 resumen[slug]["rango_obs"], dict(stats)))

        reporte_md += ["## %s" % slug,
                       "- fuentes votantes: %s" % (
                           ", ".join(["LH", "TZ"] + (["ARBITRO oficial"] if arb_map else []))),
                       "- registros canonicos: %d (%d dias)" % (len(canonicos), n_fechas),
                       "- acuerdos: %s" % {k: v for k, v in stats.items()
                                            if k.startswith("acuerdo")},
                       "- unicos: %s" % {k: v for k, v in stats.items()
                                          if k.startswith("solo")},
                       "- discrepancias reales: %d (%s)" % (
                           len(detalle_disc), "; ".join(
                               "%s %s -> %s [%s]" % (k[0], k[1], d, r)
                               for k, d, r in detalle_disc[:12]) or "ninguna"),
                       "- n_tablero observado: %s -> N=%d (nombres desde %s)"
                       % (resumen[slug]["rango_obs"], n_tab, fuente_nombres),
                       "- conflictos de nombre en tablero: %s"
                       % (conflictos or "ninguno"), ""]

    with io.open(os.path.join(SALIDA, "validacion_cruzada.md"), "w",
                 encoding="utf-8") as f:
        f.write("\n".join(reporte_md))
    with io.open(os.path.join(SALIDA, "discrepancias.csv"), "w",
                 encoding="utf-8") as f:
        f.write("\n".join(discrep_csv))
    with io.open(os.path.join(SALIDA, "resumen_validacion.json"), "w",
                 encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2, default=str)
    print("\nreportes escritos.")


if __name__ == "__main__":
    main()
