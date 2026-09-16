# -*- coding: utf-8 -*-
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core

PARSED = os.path.join(core.CRUDOS, "parsed")
SALIDA = os.path.join(core.RAIZ, "datos_multiloteria")

for slug in ("selva-plus", "guacharo-activo"):
    datos = json.load(io.open(os.path.join(SALIDA, "crudos", "arbitro_%s.json" % slug), encoding="utf-8"))
    fechas = sorted({d["date"] for d in datos})
    vals = Counter(d["result"] for d in datos)
    no_num = {v: c for v, c in vals.items() if not v.isdigit()}
    print("==", slug, "items", len(datos), "rango fechas", fechas[0], "..", fechas[-1])
    print("   valores no numericos:", dict(sorted(no_num.items(), key=lambda x: -x[1])[:12]))
    print("   n numeros distintos:", len([v for v in vals if v.isdigit()]))
    # cruce vs LH
    lh_slug = "selvaplus" if slug == "selva-plus" else "guacharoactivo"
    lh = [json.loads(l) for l in io.open(os.path.join(PARSED, "lh_%s.jsonl" % lh_slug), encoding="utf-8")]
    # tablero animal->num desde pareo con TZ ya conocido: reusar cruzar? simplificar:
    # pareo LH->num usando arbitro mismo en la ventana de solapamiento
    arb = {(d["date"], d["time"][:5]): int(d["result"]) for d in datos if d["result"].isdigit()}
    par = defaultdict(Counter)
    for r in lh:
        n = arb.get((r["fecha"], r["hora"]))
        if n is not None:
            par[core.norm(r["animal"])][n] += 1
    print("   animales LH distintos en solapamiento:", len(par))
    splits = {a: dict(c) for a, c in par.items() if len(c) > 1}
    print("   nombres LH ambiguos:", len(splits))
    for a, c in list(splits.items())[:10]:
        print("     ", a, c)
    # cobertura: cuantas claves LH tienen arbitro
    claves_lh = {(r["fecha"], r["hora"]) for r in lh}
    cub = sum(1 for k in claves_lh if k in arb)
    print("   cobertura arbitro sobre LH: %d/%d" % (cub, len(claves_lh)))
