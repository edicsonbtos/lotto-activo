# -*- coding: utf-8 -*-
"""Genera datos_multiloteria/<slug>.csv con el esquema de la mision:
  fecha, hora, n_sorteo_dia, numero, animal, n_tablero, fuente
y documenta los tableros (datos_multiloteria/tableros.md + tableros.json).

n_tablero se deriva del RANGO OBSERVADO en >1.700 sorteos validados cruzados
por fuente independiente (ver validacion_cruzada.md). Hallazgo: los rangos
reales difieren de los "oficiales" divulgados (p.ej. Lotto Activo se anuncia
"38 figuras (0-36)" = 37 numeros; Selva Plus ya no es 38 sino ~100).
"""
import io
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

RAIZ = core.RAIZ
SALIDA = os.path.join(RAIZ, "datos_multiloteria")
PARSED = os.path.join(core.CRUDOS, "parsed")

OBJETIVO = ["lottoactivo", "lottoactivordint", "lagranjita", "selvaplus",
            "guacharoactivo"]

NOMBRES_BASE = {
    0: "Delfín", 1: "Carnero", 2: "Toro", 3: "Ciempiés", 4: "Alacrán",
    5: "León", 6: "Rana", 7: "Perico", 8: "Ratón", 9: "Águila", 10: "Tigre",
    11: "Gato", 12: "Caballo", 13: "Mono", 14: "Paloma", 15: "Zorro",
    16: "Oso", 17: "Pavo", 18: "Burro", 19: "Chivo", 20: "Cochino",
    21: "Gallo", 22: "Camello", 23: "Cebra", 24: "Iguana", 25: "Gallina",
    26: "Vaca", 27: "Perro", 28: "Zamuro", 29: "Elefante", 30: "Caimán",
    31: "Lapa", 32: "Ardilla", 33: "Pescado", 34: "Venado", 35: "Jirafa",
    36: "Culebra",
}
NOMBRE_CERO_OFICIAL = {"lagranjita": "Ballena"}


def bonito(nombre_norm, n):
    if n in NOMBRES_BASE:
        if n == 0 and nombre_norm in ("BALLENA", "DELFIN"):
            pass
        return NOMBRES_BASE[n]
    return nombre_norm.title() if nombre_norm else ""


def main():
    resumen = json.load(io.open(os.path.join(SALIDA, "resumen_validacion.json"),
                                encoding="utf-8"))
    tableros = {}
    md = ["# Tableros observados (rango de numeros por loteria)", "",
          "Derivado de 1.723-1.800 sorteos por loteria, validados cruzando",
          "fuentes independientes (ver validacion_cruzada.md).", ""]
    for slug in OBJETIVO:
        p = os.path.join(PARSED, "canonicos_%s.jsonl" % slug)
        filas = [json.loads(l) for l in io.open(p, encoding="utf-8")]
        numeros = sorted({r["numero"] for r in filas})
        n_tab = max(numeros) + 1
        # nombre canonico por numero: mayoria entre canonicos con nombre
        por_num = defaultdict(lambda: defaultdict(int))
        for r in filas:
            if r["animal"]:
                por_num[r["numero"]][r["animal"]] += 1
        num_a_animal = {}
        for n in numeros:
            if n in por_num:
                num_a_animal[n] = sorted(por_num[n].items(),
                                         key=lambda x: -x[1])[0][0]
        # nombres bonitos para la base 0-36
        bonitos = {}
        for n in numeros:
            a = num_a_animal.get(n, "")
            if n in NOMBRES_BASE:
                if n == 0:
                    bonitos[n] = NOMBRE_CERO_OFICIAL.get(slug, "Delfín")
                else:
                    bonitos[n] = NOMBRES_BASE[n]
            else:
                bonitos[n] = a.title() if a else ""
        sin_nombre = [n for n in numeros if n not in num_a_animal]

        # CSV final
        csv_p = os.path.join(SALIDA, "%s.csv" % slug)
        with io.open(csv_p, "w", encoding="utf-8") as f:
            f.write("fecha,hora,n_sorteo_dia,numero,animal,n_tablero,fuente\n")
            for r in filas:
                f.write("%s,%s,%d,%d,%s,%d,%s\n" % (
                    r["fecha"], r["hora"], r["n_sorteo_dia"], r["numero"],
                    bonitos.get(r["numero"], ""), n_tab, r["fuente"]))
        tableros[slug] = {
            "n_tablero": n_tab, "rango_observado": [numeros[0], numeros[-1]],
            "numeros_distintos_observados": len(numeros),
            "sorteos": len(filas),
            "num_a_animal": {str(k): v for k, v in sorted(bonitos.items())},
            "numeros_sin_nombre": sin_nombre,
        }
        print("%-16s csv=%4d sorteos  N=%3d  rango=[%d,%d]  sin_nombre=%s"
              % (slug, len(filas), n_tab, numeros[0], numeros[-1], sin_nombre))
        md += ["## %s" % slug,
               "- sorteos en CSV: %d" % len(filas),
               "- rango observado: %d..%d -> N = %d (%d numeros distintos)"
               % (numeros[0], numeros[-1], n_tab, len(numeros)),
               "- numeros sin nombre conocido: %s" % (sin_nombre or "ninguno"),
               "- notas: %s" % ({
                   "lottoactivo": "Se anuncia '38 figuras (delfin 0 - culebra "
                                  "36)': en la practica son 37 numeros. El 37 "
                                  "JAMAS aparece en 12.502 sorteos de "
                                  "historial.txt ni en 1.800 de esta muestra. "
                                  "El modelo del repo asumia K=38 (azar 2,63%); "
                                  "el azar real es 1/37 = 2,70%.",
                   "lagranjita": "Misma numeracion base 0-36 (37 numeros); "
                                 "el 0 es Ballena (no Delfin).",
                   "lottoactivordint": "Tablero identico al de Lotto Activo "
                                       "(0-36). Validacion cruzada TZ solo 1 "
                                       "semana (es nueva en tuazar): 100% "
                                       "acuerdo; el resto del periodo es "
                                       "LH+tablero verificado.",
                   "selvaplus": "La mision asumia 38; el tablero actual es "
                                "0-99 (100 figuras). La API oficial "
                                "(api.lotterly.co) confirma el rango completo.",
                   "guacharoactivo": "La mision asumia 77; se observa 0-75 "
                                     "(76 figuras). El 76 nunca aparecio en "
                                     "1.800 sorteos (P bajo nula 77 ~ e^-23).",
               }.get(slug, "")), ""]
    with io.open(os.path.join(SALIDA, "tableros.json"), "w", encoding="utf-8") as f:
        json.dump(tableros, f, ensure_ascii=False, indent=2)
    with io.open(os.path.join(SALIDA, "tableros.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("\ntableros.md / tableros.json / 5 CSV escritos.")


if __name__ == "__main__":
    main()
