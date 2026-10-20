import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "herramientas", "modelos"))

import ag14
import experimentos as E


FICHAS = [0, 2, 2, 2, 1, 1] + [0] * 33


def test_ag14_aplica_exposicion_y_conserva_probabilidades():
    p = [1 / 38] * 38
    q = ag14.cadena(p, "2026-10-17", 3)
    assert len(q) == 38
    assert abs(sum(q) - 1) < 1e-12
    assert q[ag14.IDX["17"]] < q[ag14.IDX["1"]]
    assert q[ag14.IDX["1"]] > 0


def test_marcador_ag14_no_requiere_pron_y_usa_fecha_preregistrada():
    base = [1 / 38] * 38
    records = [
        {"fecha": "2026-10-16", "hora": 3, "salio": ag14.IDX["17"], "scores": base,
         "sombra": {"ag12": base}},
        {"fecha": "2026-10-17", "hora": 3, "salio": ag14.IDX["17"], "scores": base,
         "sombra": {"ag12": base, "rd": {"1": None, "2": None}}},
    ]
    m = E.marcador_ag14(records, FICHAS, {})
    assert m["n"] == 1
    assert m["sin_ag12"] == 0
    assert m["rd_no_congelado"] == 0
    assert m["desde"] == E.AG14_DESDE
    assert m["estado"].startswith("acumulando")
    assert "delta_mbits" in m


def test_marcador_ag14_vacio():
    m = E.marcador_ag14([], FICHAS, {})
    assert m["n"] == 0
    assert m["estado"] == "esperando sorteos prospectivos"


def test_ag14_solo_usa_el_rd_congelado_antes_del_sorteo(monkeypatch):
    p = [1.0] * 38
    recibidos = []
    monkeypatch.setattr(ag14, "cadena", lambda q, fecha, hora: recibidos.append(list(q)) or [1 / 38] * 38)
    r = [{"fecha": "2026-10-17", "hora": 3, "salio": ag14.IDX["1"], "scores": p,
          "sombra": {"ag12": p, "rd": {"1": "17", "2": "30"}}}]
    # El historial RD de hoy dice otra cosa (anotado o corregido después): no debe pesar.
    rd = {("2026-10-17", 2): "5", ("2026-10-17", 1): "6",
          ("2026-10-17", 3): "7", ("2026-10-17", 4): "8"}
    out = E.marcador_ag14(r, FICHAS, rd)
    assert out["n"] == 1
    assert recibidos[0][ag14.IDX["17"]] == 0.5
    assert recibidos[0][ag14.IDX["30"]] == 0.75
    for cod in ("5", "6", "7", "8"):
        assert recibidos[0][ag14.IDX[cod]] == 1.0


def test_ag14_intradia_sin_rd_congelado_no_decide_ni_depende_del_rd_posterior():
    base = [1 / 38] * 38
    regs = [{"fecha": "2026-10-17", "hora": 0, "salio": 0, "scores": base, "sombra": {"ag12": base}},
            {"fecha": "2026-10-17", "hora": 3, "salio": 1, "scores": base, "sombra": {"ag12": base}}]
    con = E.marcador_ag14(regs, FICHAS, {("2026-10-17", 2): "17"})
    assert con == E.marcador_ag14(regs, FICHAS, {})
    assert con["n"] == 1 and con["rd_no_congelado"] == 1          # solo el de las 8:00 entra a la cohorte
    assert con["historico_sin_rd_posterior"]["n"] == 2
