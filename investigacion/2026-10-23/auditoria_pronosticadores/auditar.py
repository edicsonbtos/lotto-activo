# -*- coding: utf-8 -*-
"""Auditoría del archivo de pronosticadores (pendiente 7a de investigacion/2026-10-15/RETOMAR.md).

Para cada día guardado por Railway entre 6:00 y 7:55 (antes del primer sorteo), compara los animales de la página
de esa mañana (/datos_publicados/<fecha>/<fuente>.html) con:
  (1) el archivo por fecha que se baja HOY (POST fecha=...), y
  (2) la copia del archivo que se bajó el 2026-10-15 (datos/publicados.jsonl), si cubre ese día.
Si el archivo se rehace después de los sorteos, aparecerán diferencias, sobre todo animales que se quitan y que luego
salieron. Uso: python auditar.py  →  salida.txt, resultado.json
"""
import json, os, subprocess, sys, time, urllib.request
from collections import Counter
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
P15 = os.path.join(RAIZ, "investigacion/2026-10-15/pronosticadores")
sys.path.insert(0, P15)
import descargar as D   # p_lotoven, p_ldh, bajar (mismo parser que el estudio del 15-oct)
WEB = "https://lotto-activo-production.up.railway.app"
FUENTES = {"lotoven": ("lotoven_datos", D.p_lotoven, D.URL["lotoven"]),
           "loteriadehoy": ("loteriadehoy_datos", D.p_ldh, D.URL["loteriadehoy"])}
CRUDO = os.path.join(AQUI, "crudo"); os.makedirs(CRUDO, exist_ok=True)


def get(url):
    with urllib.request.urlopen(url, timeout=90) as r:
        return r.read().decode("utf-8", "replace")


def archivo_15oct():
    out = {}
    for ln in open(os.path.join(P15, "datos", "publicados.jsonl"), encoding="utf-8"):
        r = json.loads(ln); out[(r["fuente"], r["fecha"])] = r["datos"]
    return out


def ganadores():
    import csv
    g = {}
    for r in csv.DictReader(open(os.path.join(RAIZ, "datos_multiloteria/oficial_multi.csv"), encoding="utf-8")):
        juego = {"1": "Lotto Activo", "2": "Lotto Activo RD Int"}.get(r["juego"])
        if juego:
            g.setdefault((juego, r["fecha"]), set()).add(r["codigo"])
    return g


def main():
    dias = sorted(json.loads(get(WEB + "/api/datos_publicados"))["ultimos"])
    viejo, gan = archivo_15oct(), ganadores()
    filas, resumen = [], Counter()
    for f in dias:
        for fuente, (nombre, parse, url) in FUENTES.items():
            try:
                h_m = get(f"{WEB}/datos_publicados/{f}/{nombre}.html")
            except Exception as ex:  # noqa: BLE001
                filas.append({"fecha": f, "fuente": fuente, "error": f"mañana: {ex!r}"[:120]}); continue
            open(os.path.join(CRUDO, f"{f}_{fuente}_manana.html"), "w", encoding="utf-8").write(h_m)
            h_a = D.bajar(url, f); time.sleep(0.7)
            open(os.path.join(CRUDO, f"{f}_{fuente}_archivo_hoy.html"), "w", encoding="utf-8").write(h_a)
            m, a = parse(h_m, f), parse(h_a, f)
            v = viejo.get((fuente, f))
            for juego in ("Lotto Activo", "Lotto Activo RD Int"):
                pm = m.get(juego, {}); pa = a.get(juego, {})
                nm, na = pm.get("nums"), pa.get("nums")
                nv = (v or {}).get(juego, {}).get("nums") if v and "error" not in v else None
                g = gan.get((juego, f), set())
                fila = {"fecha": f, "fuente": fuente, "juego": juego, "fecha_pag_manana": pm.get("fecha_pagina"),
                        "manana": nm, "archivo_hoy": na, "archivo_15oct": nv,
                        "igual_hoy": None if nm is None or na is None else sorted(nm) == sorted(na),
                        "igual_15oct": None if nm is None or nv is None else sorted(nm) == sorted(nv),
                        "quitados_que_salieron": sorted((set(nm or []) - set(na or [])) & g),
                        "agregados_que_salieron": sorted((set(na or []) - set(nm or [])) & g)}
                filas.append(fila)
                k = (fuente, juego)
                if fila["igual_hoy"] is True: resumen[k + ("igual",)] += 1
                elif fila["igual_hoy"] is False: resumen[k + ("distinto",)] += 1
                else: resumen[k + ("sin_dato",)] += 1
                if fila["fecha_pag_manana"] and fila["fecha_pag_manana"] != f: resumen[k + ("pagina_de_otro_dia",)] += 1
        print(f, flush=True)
    json.dump({"filas": filas, "resumen": {"|".join(k): v for k, v in resumen.items()}},
              open(os.path.join(AQUI, "resultado.json"), "w"), ensure_ascii=False, indent=1)
    with open(os.path.join(AQUI, "salida.txt"), "w", encoding="utf-8") as o:
        for k, v in sorted(resumen.items()):
            o.write(f"{' | '.join(k)}: {v}\n")
        o.write("\nDiferencias:\n")
        for r in filas:
            if r.get("error") or r.get("igual_hoy") is False or r.get("igual_15oct") is False:
                o.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(open(os.path.join(AQUI, "salida.txt"), encoding="utf-8").read())


if __name__ == "__main__":
    main()
