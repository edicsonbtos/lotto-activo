"""Experimentos en vivo (regla de cambio por RD y pronósticos en sombra) fuera de servidor.py.

oro_experimentos.json es lo que daba servidor.py ANTES de moverlos, sobre datos sintéticos
(tests/datos_experimentos.py): el movimiento no puede cambiar ni un número del marcador.
"""
import json, os, sys

import pytest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
sys.path.insert(0, AQUI)
import experimentos
import rdint_vivo
import servidor
from datos_experimentos import log_sintetico, rd_como_lista

with open(os.path.join(AQUI, "oro_experimentos.json"), encoding="utf-8") as f:
    ORO = json.load(f)


@pytest.fixture
def datos(monkeypatch):
    d, rd = log_sintetico()
    monkeypatch.setattr(rdint_vivo, "cargar_rd", lambda: rd_como_lista(rd))
    return d, rd


def test_cambiar_reproduce_lo_de_antes():
    orden = list(range(38))
    for cod, esperado in ORO["cambiar"].items():
        nuevo = experimentos.cambiar(orden, cod)
        assert (None if nuevo is orden else nuevo) == esperado


def test_cambio_rd_reproduce_lo_de_antes(datos):
    d, _ = datos
    for h in (0, 1, 3):
        o = [r for r in d["registros"] if r["hora"] == h][0]["orden_completo"]
        n, info = experimentos.cambio_rd(o, "2026-09-29", h)
        esperado = ORO["cambio_rd"]["h%d" % h]
        assert (n, info, n is o) == (esperado["orden"], esperado["info"], esperado["mismo"])
    assert experimentos.cambio_rd(list(range(38)), "2031-01-01", 2)[1] == ORO["cambio_rd"]["sin_rd"]


def test_marcadores_reproducen_lo_de_antes(datos):
    d, _ = datos
    res, fichas = servidor.resueltas(d), servidor.fichas_por_puesto()
    assert experimentos.marcador_cambio_rd(res, fichas) == ORO["marcador_cambio_rd"]
    assert experimentos.marcador_sombra(res, fichas) == ORO["marcador_sombra"]


def test_el_oro_cubre_exposicion_y_cambios():
    """Si el oro no ejercita estas ramas, el test de arriba no protege nada."""
    assert ORO["marcador_sombra"]["exposicion"]["marcador"]["ensamble"]["n"] > 0
    assert ORO["marcador_sombra"]["exposicion"]["fallos"] == 0
    assert ORO["marcador_cambio_rd"]["cambios"] > 0
    assert ORO["marcador_sombra"]["ventana_8am"]["n"] > 0


def test_con_rd_y_ic90_reproducen_lo_de_antes(datos):
    _, rd = datos
    q, usado = experimentos.con_rd([0.1] * 38, rd, "2026-09-29", 3)
    assert [usado, q[:8]] == ORO["con_rd"]
    assert [experimentos.ic90_jornadas([]), experimentos.ic90_jornadas([("a", 1.0)]),
            experimentos.ic90_jornadas([("a", 1.0), ("a", 3.0), ("b", -1.0), ("c", 2.0)])] == ORO["ic90"]


def test_servidor_conserva_sus_nombres_y_da_lo_mismo(datos):
    d, _ = datos
    assert servidor.marcador_cambio_rd(d) == ORO["marcador_cambio_rd"]
    assert servidor.marcador_sombra(d) == ORO["marcador_sombra"]
    assert servidor.cambio_rd(list(range(38)), "2031-01-01", 2)[1] == ORO["cambio_rd"]["sin_rd"]


def test_sombra_de_nunca_tumba_el_pronostico():
    assert experimentos.sombra_de(None, "2026-10-04", 3, None) is None


def test_cambiar15_top5_identico_a_cambiar_y_mueve_6_a_15():
    orden = list(range(38))
    for cod in ("0", "00", "1", "2", "3"):                  # índices 0..4 = puestos 1..5
        assert experimentos.cambiar15(orden, cod)[:5] == experimentos.cambiar(orden, cod)[:5]
    n = experimentos.cambiar15(orden, experimentos.POS[9])  # índice 9 = puesto 10
    assert n[:9] == orden[:9] and n[9:14] == orden[10:15] and n[14] == 15 and n[15] == 9 and n[16:] == orden[16:]
    assert experimentos.cambiar15(orden, experimentos.POS[20]) is orden   # fuera del Top-15: sin cambio


def test_cambio_rd15_marca_el_tope(datos):
    d, rd = datos
    o = [r for r in d["registros"] if r["hora"] == 3][0]["orden_completo"]
    n, info = experimentos.cambio_rd15(o, "2026-09-29", 3)
    cod = info["rd"]
    assert sorted(n) == sorted(o) and n[:15] == experimentos.cambiar15(o, cod)[:15]
    if "sale" in info:
        assert info["tope"] == (5 if o.index(experimentos.IDX[cod]) < 5 else 15)


def test_marcador_cambio_rd15_cuenta(datos):
    d, _ = datos
    res = servidor.resueltas(d)
    m = experimentos.marcador_cambio_rd15(res, servidor.fichas_por_puesto(servidor.PONDERADO))
    assert m["n"] > 0 and m["dif"] == m["con"] - m["sin"] and m["cambios"] <= m["n"]


def test_decision_sombra_cuenta_y_trae_ics(datos):
    d, _ = datos
    m = experimentos.decision_sombra(servidor.resueltas(d), servidor.fichas_por_puesto())
    assert m["n"] > 0 and m["decide_con"] == 931
    for k in ("mbits_ag12_menos_ensamble", "top5_pp_ficha_sin_regla", "top5_pp_ficha_con_regla_rd"):
        assert m[k]["n"] == m["n"] and m[k]["ic90"][0] <= m[k]["media"] <= m[k]["ic90"][1]
