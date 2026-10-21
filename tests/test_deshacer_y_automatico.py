"""Deshacer + anotado automático: lo que se anota a mano no puede caer en la hora equivocada."""
import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import servidor as s
from test_registro_marcador import datos  # noqa: F401  (fixture)


@pytest.fixture(autouse=True)
def auto_limpio(monkeypatch):
    monkeypatch.setitem(s.AUTO, "activo", True)
    monkeypatch.setitem(s.AUTO, "pausa_hasta", None)


def _form(num, e):
    return f"num={num}&pf={e['pf']}&ph={e['ph']}"


def test_deshacer_pausa_el_automatico_y_anotar_a_mano_lo_reanuda(datos):
    s.registrar("1")
    s._accion_deshacer("")
    assert s.auto_pausado()
    assert "pausa" in s.auto_estado()["txt"]
    e = s.estado(s.cargar())
    s._accion_registrar(_form("2", e))
    assert not s.auto_pausado()


def test_la_pausa_caduca(datos):
    s._accion_deshacer("")
    assert not s.auto_pausado(datetime.now() + timedelta(seconds=s.AUTO_PAUSA_DESHACER + 1))


def test_buscar_ahora_levanta_la_pausa(datos, monkeypatch):
    monkeypatch.setattr(s, "auto_pasada", lambda: 0)
    s._accion_deshacer("")
    s._accion_auto("")
    assert not s.auto_pausado()


def test_anotar_un_sorteo_que_ya_anoto_el_automatico_no_corre_el_historial(datos):
    hist, _, lineas = datos
    e = s.estado(s.cargar())              # la página se abrió esperando este sorteo
    s.registrar("5")                      # entretanto el automático lo anota
    antes = hist.read_text(encoding="utf-8")
    s._accion_registrar(_form("7", e))    # el usuario envía el formulario viejo
    assert hist.read_text(encoding="utf-8") == antes
    assert s.AVISO["clase"] == "bad" and "NO se guardó" in s.AVISO["texto"]


def test_anotar_con_el_sorteo_correcto_si_guarda(datos):
    hist, _, lineas = datos
    e = s.estado(s.cargar())
    s._accion_registrar(_form("7", e))
    assert hist.read_text(encoding="utf-8").splitlines()[-1] == f"{e['pf']} {e['ph']} 7"


def test_formulario_lleva_el_sorteo_esperado(datos):
    e = s.estado(s.cargar())
    html = s.html_registro(e)
    assert f'name="pf" value="{e["pf"]}"' in html and f'name="ph" value="{e["ph"]}"' in html
