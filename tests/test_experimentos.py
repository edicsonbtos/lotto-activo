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
