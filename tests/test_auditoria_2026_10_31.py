"""Auditoría 8:00 del 2026-10-31 (investigacion/2026-10-31/auditoria_8am, hallazgo P2): las vistas no pueden presentar
como previo un pronóstico creado a la hora del sorteo o después, que el marcador (`resueltas`) ya rechaza."""
import os, sys

import pytest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
import servidor as s


def _reg(creado):
    # Sorteo 23-oct 08:00, ganador en el puesto 1 (Delfín = índice 0).
    return {"fecha": "2026-10-23", "hora": 0, "creado": creado, "modelo": s.MODELO_MARCADOR, "salio": 0,
            "scores": [1 / 38] * 38, "orden_completo": list(range(38)), "top3": [0, 1, 2],
            "sombra": {"ag12": [1 / 38] * 38}}


TARDE = "2026-10-23T08:10:00"
PREVIO = "2026-10-23T07:50:00"


@pytest.fixture
def sin_rd(monkeypatch):
    monkeypatch.setattr(s.experimentos, "_rd_por_slot", lambda: {})


def test_marcador_ya_excluye_el_tardio():
    assert s.resueltas({"registros": [_reg(TARDE)]}) == []


def test_resumen_no_cuenta_el_tardio():
    assert s.resumen_resultados({"registros": [_reg(TARDE)]}) == "aún no hay resultados con pronóstico"


def test_historico_no_muestra_el_tardio():
    assert "Todavía no hay resultados" in s.html_resultados({"registros": [_reg(TARDE)]})


def test_tarjeta_del_dia_no_usa_el_tardio():
    r = _reg(TARDE)
    assert s.html_animales_hoy({"registros": [r]}, [], {"pf": r["fecha"]}) == ""


def test_sombra_conserva_creado_y_sus_vistas_excluyen_el_tardio(sin_rd):
    d = {"registros": [_reg(TARDE)]}
    regs = s.sombra_registros(d)
    assert len(regs) == 1 and regs[0]["creado"] == TARDE
    assert s.resumen_resultados(d, regs=regs) == "aún no hay resultados con pronóstico"
    assert "Todavía no hay resultados" in s.html_resultados(d, regs=regs)


def test_mesa_stats_no_cuenta_el_tardio(monkeypatch):
    monkeypatch.setattr(s, "cargar", lambda: [])
    monkeypatch.setattr(s, "log_cargar", lambda: {"registros": [_reg(TARDE)]})
    assert s.mesa_stats("la")["resueltos"] == 0


def test_el_pronostico_previo_sigue_contando(sin_rd, monkeypatch):
    r = _reg(PREVIO); d = {"registros": [r]}
    assert len(s.resueltas(d)) == 1
    assert "Top-15 en 1" in s.resumen_resultados(d)
    assert "Delfín" in s.html_resultados(d)
    assert "Elegidos antes del primer sorteo" in s.html_animales_hoy(d, [], {"pf": r["fecha"]})
    assert "Top-15 en 1" in s.resumen_resultados(d, regs=s.sombra_registros(d))
    monkeypatch.setattr(s, "cargar", lambda: [])
    monkeypatch.setattr(s, "log_cargar", lambda: d)
    assert s.mesa_stats("la")["resueltos"] == 1


# Revisión revisor-sesgo: la navegación «atrás» de la pestaña principal y de ag12 tenía el mismo fallo.
NOTA_PREVIO = "Es el Top congelado antes del sorteo"


def test_navegacion_atras_no_lista_el_tardio():
    assert s.la_pasados({"registros": [_reg(TARDE)]}) == []
    assert len(s.la_pasados({"registros": [_reg(PREVIO)]})) == 1


@pytest.mark.parametrize("creado, se_ve", [(TARDE, False), (PREVIO, True)])
def test_navegacion_atras_de_ag12(sin_rd, creado, se_ve):
    d = {"registros": [_reg(creado)]}
    html = s.html_sombra({"pf": "2026-10-23", "ph": 1}, d, None, [], atras=1)
    assert (NOTA_PREVIO in html) is se_ve


# Pendientes menores de la misma revisión.
import json
import historial_txt as ht


def test_creado_con_zona_horaria_se_convierte_a_caracas():
    # 11:30 UTC = 07:30 en Caracas (UTC−4): fue antes del sorteo de las 8:00.
    assert not s.creado_tarde(_reg("2026-10-23T11:30:00+00:00"))
    assert s.creado_tarde(_reg("2026-10-23T12:10:00+00:00"))
    assert not s.creado_tarde(_reg(PREVIO)) and s.creado_tarde(_reg(TARDE))


def test_mesa_marca_el_tardio(monkeypatch):
    d = {"registros": [_reg(TARDE), dict(_reg(PREVIO), hora=1, creado="2026-10-23T08:50:00")]}
    monkeypatch.setattr(s, "cargar", lambda: [])
    monkeypatch.setattr(s, "log_cargar", lambda: d)
    monkeypatch.setattr(s, "estado", lambda filas: {"pf": "2026-10-23", "ph": 5, "sc": [1 / 38] * 38})
    monkeypatch.setattr(s, "mesa_huecos", lambda filas, f, h: [None] * 38)
    assert s.mesa_datos(1, "la")["tardio"] is False     # 09:00, guardado 08:50
    assert s.mesa_datos(2, "la")["tardio"] is True      # 08:00, guardado 08:10


def test_historial_txt_marca_el_tardio():
    log = json.dumps({"registros": [_reg(TARDE), dict(_reg(PREVIO), hora=1, creado="2026-10-23T08:50:00")]})
    texto = ht.armar(None, log, None, None, tardio=s.creado_tarde)
    seccion = texto.split("===== predicciones.jsonl =====\n")[1].split("\n\n")[0]
    regs = [json.loads(x) for x in seccion.splitlines()]
    assert [r.get("tardio", False) for r in regs] == [True, False]
    assert '"tardio":true' in texto.split("=====")[0]
