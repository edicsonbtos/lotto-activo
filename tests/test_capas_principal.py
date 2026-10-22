"""Capas del motor principal (2026-10-22): exposición por fecha/hora y vecinos de rueda del anterior del mismo día."""
import os, sys
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
import experimentos as x
from comun import IDX, POS

UNI = [1.0 / 38] * 38


def _reg(hora=3, fecha="2026-10-23", **extra):
    r = {"fecha": fecha, "hora": hora, "salio": None, "scores": list(UNI), "sombra": {"ag12": list(UNI)}}
    r.update(extra)
    return r


def test_vecinos_rueda_americana():
    assert sorted(x.vecinos_rueda("0")) == sorted([IDX["2"], IDX["28"]])
    assert sorted(x.vecinos_rueda("00")) == sorted([IDX["1"], IDX["27"]])


def test_congelar_capas_fija_el_anterior_del_mismo_dia_antes_del_sorteo():
    r = _reg(hora=3)                                   # 11:00; el anterior es el de las 10:00
    filas = [("2026-10-23", 1, IDX["5"]), ("2026-10-23", 2, IDX["9"])]
    assert x.congelar_capas(r, filas, datetime(2026, 10, 23, 10, 20)) is True
    assert r["sombra"]["capas"] == {"v": x.CAPAS_VERSION, "prev": "9"}
    assert x.congelar_capas(r, filas + [("2026-10-23", 3, IDX["1"])], datetime(2026, 10, 23, 10, 30)) is False
    assert r["sombra"]["capas"]["prev"] == "9"         # una sola vez: no se reescribe


def test_congelar_capas_no_actua_pasada_la_hora_ni_resuelto_ni_sin_ag12():
    filas = [("2026-10-23", 2, IDX["9"])]
    r = _reg(hora=3)
    assert x.congelar_capas(r, filas, datetime(2026, 10, 23, 11, 0)) is False and "capas" not in r["sombra"]
    r = _reg(hora=3, salio=4)
    assert x.congelar_capas(r, filas, datetime(2026, 10, 23, 10, 0)) is False
    r = _reg(hora=3); r["sombra"] = {}
    assert x.congelar_capas(r, filas, datetime(2026, 10, 23, 10, 0)) is False


def test_a_las_8_no_hay_anterior_del_dia():
    r = _reg(hora=0)
    assert x.congelar_capas(r, [("2026-10-22", 11, IDX["9"])], datetime(2026, 10, 23, 7, 0)) is True
    assert r["sombra"]["capas"]["prev"] is None


def test_sin_capas_principal_es_ag12_con_rd():
    r = _reg()
    q, _ = x.principal(r, {})
    assert q == x.con_rd(r["sombra"]["ag12"], {}, r["fecha"], r["hora"])[0]


def test_capas_aplican_fecha_y_rueda():
    r = _reg(hora=3, fecha="2026-10-23")
    r["sombra"]["capas"] = {"v": x.CAPAS_VERSION, "prev": "9"}
    q, _ = x.principal(r, {})
    assert abs(sum(q) - 1) < 1e-9
    base = q[IDX["30"]]                                # ni fecha (22-25, 11, 10) ni vecino de 9 (28, 26)
    for c in ("28", "26"):
        assert abs(q[IDX[c]] / base - x.RUEDA_MULT) < 1e-9
    assert abs(q[IDX["23"]] / base - 0.816) < 1e-9     # número del día


def test_marcador_principal_solo_cuenta_registros_con_capas():
    sin = _reg(hora=3, salio=IDX["28"])
    con = _reg(hora=4, salio=IDX["28"]); con["sombra"]["capas"] = {"v": x.CAPAS_VERSION, "prev": "9"}
    m = x.marcador_sombra([sin], [0] + [1] * 38)["marcador"]
    assert "principal" not in m
    m = x.marcador_sombra([sin, con], [0] + [1] * 38)["marcador"]
    assert m["principal"]["n"] == 1 and m["ag12_rd"]["n"] == 2
