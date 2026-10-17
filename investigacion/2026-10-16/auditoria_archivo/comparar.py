# -*- coding: utf-8 -*-
"""Compara las capturas de hoy (capturas/) contra el archivo que bajó el estudio del 2026-10-15 (publicados.jsonl)."""
import json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
EST = os.path.join(AQUI, "..", "..", "2026-10-15", "pronosticadores")
sys.path.insert(0, EST)
import descargar as d

viejo = {}
for ln in open(os.path.join(EST, "datos", "publicados.jsonl"), encoding="utf-8"):
    r = json.loads(ln); viejo[(r["fuente"], r["fecha"])] = r["datos"]
for f in ["2026-10-14", "2026-10-15", "2026-10-16", "2026-10-17"]:
    for fuente, parse in (("lotoven", d.p_lotoven), ("loteriadehoy", d.p_ldh)):
        h = open(os.path.join(AQUI, "capturas", f"{fuente}_{f}.html"), encoding="utf-8", errors="replace").read()
        nuevo = parse(h, f)
        antes = viejo.get((fuente, f))
        for j in ("Lotto Activo", "Lotto Activo RD Int"):
            a = (antes or {}).get(j, {}); n = nuevo.get(j, {})
            igual = "IGUAL" if antes is not None and a.get("nums") == n.get("nums") else ("sin dato previo" if antes is None else "DISTINTO")
            print(f, fuente, j, "| hoy:", n.get("fecha_pagina"), n.get("nums"), "| antes:", a.get("nums"), "|", igual)
