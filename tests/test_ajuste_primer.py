"""Ajuste del primer sorteo del día (prediccion.ajuste_primer_sorteo): solo usa el pasado."""
import os
import sys
from datetime import date, timedelta

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "herramientas"))
import lotto_eval as LE
import prediccion as P


def _datos(dias, desde="2026-09-01"):
    """dias: lista de listas de (hora, idx); un día por elemento, consecutivos."""
    d0 = date.fromisoformat(desde); seq, hora, fecha = [], [], []
    for k, sorteos in enumerate(dias):
        for h, v in sorteos:
            seq.append(v); hora.append(h); fecha.append((d0 + timedelta(days=k)).isoformat())
    dia = np.array([(date.fromisoformat(f) - d0).days for f in fecha])
    dow = np.array([date.fromisoformat(f).weekday() for f in fecha])
    return LE.Datos(np.array(seq), np.array(hora), dow, dia, fecha)


def test_primer_sorteo_castiga_ayer_y_premia_hace_3_dias():
    d = _datos([[(0, 5), (1, 6)], [(0, 7)], [(0, 8)], [(0, 9), (11, 10)]])
    m, det = P.ajuste_primer_sorteo(d, "2026-09-05", 0)
    assert det == {"1": 9, "3": 7}
    assert m[9] == P.AJUSTE_PRIMER[1] and m[7] == P.AJUSTE_PRIMER[3]
    assert np.count_nonzero(m != 1) == 2


def test_no_aplica_si_no_es_el_primer_sorteo_del_dia():
    d = _datos([[(0, 5)], [(0, 7), (1, 8)]])
    assert P.ajuste_primer_sorteo(d, "2026-09-02", 2) == (None, None)


def test_dia_cerrado_ayer_no_inventa_animal():
    d = _datos([[(0, 5)], []])                # 09-01 con sorteo, 09-02 cerrado
    assert P.ajuste_primer_sorteo(d, "2026-09-03", 0) == (None, None)
    d = _datos([[(0, 5)], [], [(0, 7)]])      # 09-01, (09-02 cerrado), 09-03
    m, det = P.ajuste_primer_sorteo(d, "2026-09-04", 0)
    assert det == {"1": 7, "3": 5}


def test_hora_distinta_no_cuenta():
    d = _datos([[(1, 5)], [(1, 6)]])          # era en que el primero era a las 9:00
    assert P.ajuste_primer_sorteo(d, "2026-09-03", 0) == (None, None)
