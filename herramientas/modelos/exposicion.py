# -*- coding: utf-8 -*-
"""Corrección por EXPOSICIÓN (2026-10-01, herramientas/exploracion/top15_70/): el operador esquiva el
número de la fecha (día−1, día, día+1, día+2), el de la hora en reloj de 12 h y el del mes.

Multiplicadores CONGELADOS, ajustados SOLO en dev-A (filas 2000..5687) sobre P6 (ronda 3, λ = 30).
Solo dependen del calendario, así que se aplican al PUNTUAR sobre lo ya congelado (no hay fuga):
la sombra los mide en vivo desde 2026-10-02 (PREREGISTRO_sombra_exposicion.md).

aplicar(p, fecha, hora) -> 38 probabilidades normalizadas.  fecha 'AAAA-MM-DD', hora 0..11 (0 = 8:00).
"""
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {c: i for i, c in enumerate(POS)}
MULT = {"dia-1": 0.881, "dia": 0.816, "dia+1": 0.750, "dia+2": 0.984, "hora12": 0.955, "mes": 0.903}


def numeros(fecha, hora):
    """[(número, clave)] que la gente asocia a ese sorteo."""
    d = int(fecha[8:10]); m = int(fecha[5:7]); h12 = (hora + 8 - 1) % 12 + 1
    return [(d - 1, "dia-1"), (d, "dia"), (d + 1, "dia+1"), (d + 2, "dia+2"), (h12, "hora12"), (m, "mes")]


def aplicar(p, fecha, hora):
    q = [float(x) for x in p]
    for n, clave in numeros(fecha, int(hora)):
        if 1 <= n <= 36:
            q[IDX[str(n)]] *= MULT[clave]
    s = sum(q)
    return [x / s for x in q]
