# -*- coding: utf-8 -*-
"""Dato DESCRIPTIVO: la retro-computacion del tramo fresco (analizar.py) partida en antes/despues del inicio de la sombra en vivo (2026-09-26)
y comparada con /api/sombra (sombra_en_vivo.json). Importa los objetos de analizar.py (no relanza placebos: usa resultados ya guardados)."""
import json, os, sys, io, runpy, contextlib
AQUI = os.path.dirname(os.path.abspath(__file__))
# reusa las funciones sin repetir los placebos: se ejecuta analizar.py silenciando su salida y se leen sus variables
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    g = runpy.run_path(os.path.join(AQUI, "analizar.py"))
import numpy as np
fe, SER, ic, S = g["fe"], g["SER"], g["ic"], g["S"]
fres = S["FRESCO (16sep-7oct)"]
vivo = json.load(open(os.path.join(AQUI, "sombra_en_vivo.json"), encoding="utf-8"))["marcador"]
out = {}
for nm, sel in (("fresco 09-16..09-25 (antes de la sombra)", fres & (fe < "2026-09-26")), ("fresco 09-26..10-07 (mismas fechas que la sombra)", fres & (fe >= "2026-09-26"))):
    d = ic(SER["ag12V1"]["mbits"] - SER["ens"]["mbits"], sel)
    t = ic(SER["ag12V1"]["t5"] - SER["ens"]["t5"], sel)
    out[nm] = dict(n=d["n"], dMbits=d["media"], ic95=d["ic95"], dT5_pp_ficha=t["media"],
                   ens_mbits=float(SER["ens"]["mbits"][sel].mean()), ag12_mbits=float(SER["ag12V1"]["mbits"][sel].mean()),
                   top15=[float(SER["ens"]["top15"][sel].mean()), float(SER["ag12V1"]["top15"][sel].mean())])
out["sombra_en_vivo"] = vivo
print(json.dumps(out, indent=1, ensure_ascii=False))
json.dump(out, open(os.path.join(AQUI, "cruce_sombra.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
