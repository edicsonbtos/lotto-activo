# -*- coding: utf-8 -*-
import io
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
from validar_control import cargar_historial, tablero_desde_tuazar

ini, fin = core.semana_rango(core.lunes(__import__("datetime").date(2026, 8, 10)))
lh = core.lh_historico("lottoactivo", ini, fin)
html_tz = core.tuazar_semana(ini)
tz = core.parse_tuazar_semana(html_tz, solo_slugs={"lottoactivo"})
num_a_animal, animal_a_num, _ = tablero_desde_tuazar(tz)
hist = cargar_historial()

# LH por (fecha, hora)
lh_map = {(r["fecha"], r["hora"]): r["animal"] for r in lh}
# historial por fecha
por_fecha = defaultdict(dict)
for (f, s), n in hist.items():
    por_fecha[f][s] = n

# para el lunes: animales del historial (via tablero tuazar) vs animales LH por hora
for fecha in sorted(por_fecha):
    if fecha < "2026-08-10" or fecha > "2026-08-16":
        continue
    ns = por_fecha[fecha]
    print(fecha, "sorteos en historial:", sorted(ns.keys()))
    linea_hist = " ".join("%d=%s" % (s, num_a_animal.get(ns[s], "?%d" % ns[s])) for s in sorted(ns))
    print("  HIST:", linea_hist)
    linea_lh = " ".join("%s=%s" % (h, lh_map.get((fecha, h), "-")) for h in
                        ["08:00","09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00"])
    print("  LH  :", linea_lh)
