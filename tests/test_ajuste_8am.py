"""Corrección de fecha a las 8:00 (prediccion.ajuste_8am) y sombras medidas sin ella."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import prediccion as P
import servidor as s

IDX = {c: i for i, c in enumerate(["0", "00"] + [str(i) for i in range(1, 37)])}
UNIF = np.full(38, 1 / 38)


def test_solo_a_las_8_y_desde_el_encendido():
    assert P.ajuste_8am(UNIF, "2026-10-06", 1) is None
    assert P.ajuste_8am(UNIF, "2026-10-05", 0) is None
    assert P.ajuste_8am(UNIF, P.ENCENDIDO_8AM, 0) is not None


def test_baja_la_ventana_de_fecha_y_normaliza():
    q = P.ajuste_8am(UNIF, "2026-10-06", 0)
    assert abs(q.sum() - 1) < 1e-12
    ventana = [IDX[n] for n in ("5", "6", "7")]
    resto = [i for i in range(38) if i not in ventana + [IDX[n] for n in ("8", "10")]]
    assert max(q[ventana]) < min(q[resto])
    assert q[IDX["0"]] == q[IDX["36"]]                  # fuera de la ventana y del calendario: sin cambio relativo


def test_dia_1_no_inventa_el_numero_0():
    q = P.ajuste_8am(UNIF, "2026-11-01", 0)              # ventana {0?, 1, 2}: el 0 no es día−1
    assert q[IDX["0"]] == q[IDX["36"]] and q[IDX["1"]] < q[IDX["36"]]


def test_sombra_usa_las_probabilidades_sin_la_correccion():
    base = list(UNIF)
    con = list(P.ajuste_8am(UNIF, "2026-10-06", 0))
    r = {"fecha": "2026-10-06", "hora": 0, "salio": IDX["6"], "scores": con, "scores_sin_8am": base,
         "orden_completo": sorted(range(38), key=lambda i: (-con[i], i)), "modelo": s.MODELO_MARCADOR}
    out = s.marcador_sombra({"registros": [r]})
    v8 = out["ventana_8am"]
    assert v8["n"] == 1 and v8["ventana_obs"] == 1
    esperado = sum(s._exposicion(base, "2026-10-06", 0)[IDX[n]] for n in ("5", "6", "7"))
    assert abs(v8["ventana_esp"] - esperado) < 1e-2


def test_ag12_se_calcula_sobre_las_probabilidades_sin_la_correccion():
    assert s.sc_sombra({"scores_sin_8am": [1.0] * 38}, [2.0] * 38) == [1.0] * 38
    assert s.sc_sombra({}, [2.0] * 38) == [2.0] * 38       # otras horas: las mismas que se juegan
