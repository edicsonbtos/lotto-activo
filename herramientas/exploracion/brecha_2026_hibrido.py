# -*- coding: utf-8 -*-
"""Reproduce las cifras del híbrido (Top-15 49,26 -> 51,43 %) pasando 2026 por el MISMO código de la sombra
(servidor.marcador_brecha26). Uso: python herramientas/exploracion/brecha_2026_hibrido.py"""
import os, sys, json
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path[:0] = [AQUI, os.path.join(RAIZ, "herramientas"), RAIZ]
import lotto_eval as LE, hora_8am_ciega as H8, brecha_2026 as B  # noqa: E402
B.log = H8.log = lambda *a: None
H8.armar_historial(); D, Pall = H8.walk_forward(); RD, _ = B.cargar_rd_lard()
import servidor as SV  # noqa: E402
n0 = LE.W; F = D.fecha[n0:]; P = Pall / Pall.sum(1, keepdims=True)
rdmap = {k: LE.POS[v] for k, v in RD.items()}
for nom, a, b in (("2025", "2025-01-01", "2025-12-19"), ("2026-A", "2025-12-19", "2026-06-01"),
                  ("2026-B", "2026-06-01", "2026-09-30"), ("2026", "2025-12-19", "2026-09-30")):
    regs = []
    for i in range(len(F)):
        if a <= F[i] < b:
            sc = [float(x) for x in P[i]]
            regs.append(dict(fecha=F[i], hora=int(D.hora[n0 + i]), salio=int(D.seq[n0 + i]), modelo=SV.MODELO_MARCADOR,
                             orden_completo=sorted(range(38), key=lambda k: (-sc[k], k)), scores=sc))
    SV.SOMBRA_B26_DESDE = a; SV.SOMBRA_B26_N_FINAL = 10 ** 9
    o = SV.marcador_brecha26({"registros": regs}, rdmap)
    m = o["marcador"]
    print(f"{nom:7} n={o['n']} Top-15 {m['produccion']['top15_pct']} -> {m['brecha26']['top15_pct']} "
          f"dif {o['dif_top15_pp']['media']} pp IC90 {o['dif_top15_pp']['ic90']}; solo RD fuera del Top-15 "
          f"{o['secundaria_solo_rd_fuera_top15_pp']['media']} pp; ponderado {o['dif_ponderado_pp_ficha']['media']}")
