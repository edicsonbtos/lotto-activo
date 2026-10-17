# -*- coding: utf-8 -*-
"""Ag14: capa de exposición aplicada al ag12 ya corregido por RD.

No aprende del resultado ni de pronosticadores externos. Las probabilidades ag12
y los multiplicadores RD/exposición se consumen congelados; la composición y la
ventana prospectiva están descritas en PREREGISTRO_ag14.md.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.append(AQUI)
import exposicion  # noqa: E402

IDX = exposicion.IDX
K = len(exposicion.POS)
VERSION = "ag12_v1_rd_exposicion_2026-10-17"


def cadena(p_ag12_rd, fecha, hora):
    """Devuelve el vector ag14 normalizado desde ag12 después de con_rd."""
    if len(p_ag12_rd) != K:
        raise ValueError("ag14 requiere un vector de 38 probabilidades")
    return exposicion.aplicar(p_ag12_rd, fecha, int(hora))
