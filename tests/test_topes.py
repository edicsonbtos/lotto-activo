"""Topes de la taquilla: validación, guardado y O/E (solo cuentan los anotados antes del sorteo)."""
import os, sys
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
import topes


def test_leer_animales():
    assert topes.leer_animales("5, 12 00 05 ,0") == (["5", "12", "00", "0"], [])
    assert topes.leer_animales("37 x 3") == (["3"], ["37", "x"])


def test_anotar_valida_y_guarda(tmp_path):
    ruta = str(tmp_path / "topes.json")
    assert topes.anotar(ruta, "2026-10-23", "la", 3, "99")[1] == "bad"
    assert topes.anotar(ruta, "2026-13-01", "la", 3, "5")[1] == "bad"
    assert topes.anotar(ruta, "2026-10-23", "xx", 3, "5")[1] == "bad"
    assert topes.anotar(ruta, "2026-10-23", "la", 12, "5")[1] == "bad"
    assert topes.anotar(ruta, "2026-10-23", "la", 3, "")[1] == "bad"
    assert topes.cargar(ruta) == []
    texto, clase = topes.anotar(ruta, "2026-10-23", "rd", 3, "5 00", "Agencia X",
                                ahora=datetime(2026, 10, 23, 10, 0))
    assert clase == "ok"
    (e,) = topes.cargar(ruta)
    assert e == {"creado": "2026-10-23T10:00:00", "fecha": "2026-10-23", "juego": "rd", "hora": 3,
                 "animales": ["5", "00"], "agencia": "Agencia X"}


def test_resumen_cuenta_solo_lo_anotado_antes():
    ent = [
        {"creado": "2026-10-23T08:30:00", "fecha": "2026-10-23", "juego": "la", "hora": 2, "animales": ["5", "7"]},
        {"creado": "2026-10-23T08:30:00", "fecha": "2026-10-23", "juego": "la", "hora": 3, "animales": ["9"]},
        {"creado": "2026-10-23T12:00:00", "fecha": "2026-10-23", "juego": "la", "hora": 2, "animales": ["5"]},  # tarde
        {"creado": "2026-10-23T08:30:00", "fecha": "2026-10-23", "juego": "la", "hora": 9, "animales": ["1"]},  # pendiente
    ]
    gano = {("la", "2026-10-23", 2): "5", ("la", "2026-10-23", 3): "1"}
    hora = lambda j, f, h: datetime(2026, 10, 23, 8 + h)
    r = topes.resumen(ent, lambda j, f, h: gano.get((j, f, h)), None, hora)
    assert (r["resueltas"], r["salieron"], r["anotadas_tarde"], r["pendientes"]) == (2, 1, 1, 1)
    assert r["animal_sorteos"] == 3
    assert abs(r["esperado"] - 3 / 38) < 0.01
    # con probabilidades del modelo: masa del tope normalizada
    p = [1.0] * 38; p[topes.IDX["5"]] = 20.0
    r2 = topes.resumen(ent[:1], lambda j, f, h: gano.get((j, f, h)), lambda j, f, h: p, hora)
    assert abs(r2["filas"][0]["prob_tope"] - 21 / 57) < 1e-3
