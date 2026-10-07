# -*- coding: utf-8 -*-
"""Complemento de analizar.py: conteos de la regla RD en Top-15 y p por volteo de signo por jornada (mas fiable que el bootstrap con 22 jornadas)."""
import io, os, runpy, contextlib, json
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.path.join(AQUI, "analizar.py"))
SER, S, flip, rd1, y, R_e = g["SER"], g["S"], g["flip"], g["rd1"], g["y"], g["R_e"]
out = {}
for nm in ("REPLICA_2026 (ene-16sep)", "FRESCO (16sep-7oct)", "2026_TODO (replica+fresco)"):
    sel = S[nm]
    rp = np.where(rd1 >= 0, R_e[np.arange(len(y)), np.where(rd1 >= 0, rd1, 0)], 99)
    cambia = sel & (rp <= 15); gano_rd = cambia & (y == rd1)
    # el que entra es el 16.o del ensamble: lo contamos via posicion del ganador
    pos = SER["ens"]["_pos"]; gano16 = cambia & (pos == 16)
    d_ens = SER["ens"]["p15r"] - SER["ens"]["p15"]; d_ag = SER["ag12V1"]["p15r"] - SER["ag12V1"]["p15"]
    out[nm] = dict(n=int(sel.sum()), con_rd=int((sel & (rd1 >= 0)).sum()), cambios=int(cambia.sum()), gano_el_de_rd=int(gano_rd.sum()), gano_el_16=int(gano16.sum()),
                   flip_regla_ens=flip(d_ens, sel), flip_regla_ag12=flip(d_ag, sel),
                   flip_t5r_ag12_vs_ens=flip(SER["ag12V1"]["t5r"] - SER["ens"]["t5r"], sel),
                   flip_mbits_ag12_rd_vs_ens_rd=flip(SER["ag12V1_rd"]["mbits"] - SER["ens_rd"]["mbits"], sel))
    print(nm, json.dumps(out[nm]))
json.dump(out, open(os.path.join(AQUI, "extra_regla.json"), "w"), indent=1)
