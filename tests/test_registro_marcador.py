"""Registro, deshacer (escritura atómica) y marcador de servidor.py, sobre archivos temporales."""
import json
import math
import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import servidor as s

RAIZ = os.path.join(os.path.dirname(__file__), "..")
# historial.txt no va al repo (.gitignore); en un clon limpio se usa la copia versionada.
HIST_REAL = next(p for p in (os.path.join(RAIZ, "historial.txt"),
                             os.path.join(RAIZ, "verificacion", "hilo9", "datos", "historial.txt"))
                 if os.path.exists(p))


@pytest.fixture
def datos(tmp_path, monkeypatch):
    """Historial real (últimas 400 líneas, solo lectura) copiado a una carpeta temporal."""
    with open(HIST_REAL, encoding="utf-8") as f:
        lineas = [l for l in f if l.strip()][-400:]
    hist, log = tmp_path / "historial.txt", tmp_path / "predicciones.json"
    hist.write_text("".join(lineas), encoding="utf-8")
    monkeypatch.setattr(s, "HIST", str(hist))
    monkeypatch.setattr(s, "LOG", str(log))
    monkeypatch.setattr(s, "PRED", None)      # sin motor: no se crea pronóstico nuevo
    return hist, log, lineas


def _reg(salio, orden, modelo=None):
    return {"fecha": "2026-01-01", "hora": 0, "top3": orden[:3], "orden_completo": orden,
            "salio": salio, "modelo": modelo or s.MODELO_MARCADOR}


ORDEN = list(range(38))


def test_deshacer_quita_solo_la_ultima_linea_y_no_deja_tmp(datos):
    hist, _, lineas = datos
    msg, ok = s.deshacer()
    assert ok, msg
    assert hist.read_text(encoding="utf-8") == "".join(lineas[:-1])
    assert not os.path.exists(str(hist) + ".tmp")


def test_deshacer_es_atomico_si_falla_la_escritura(datos, monkeypatch):
    """Si os.replace falla, el historial original queda intacto (antes se vaciaba)."""
    hist, _, lineas = datos
    def roto(*a, **k): raise OSError("corte")
    monkeypatch.setattr(s.os, "replace", roto)
    with pytest.raises(OSError):
        s.deshacer()
    assert hist.read_text(encoding="utf-8") == "".join(lineas)


def test_deshacer_con_ultima_linea_invalida_no_toca_nada(datos):
    hist, _, lineas = datos
    hist.write_text("".join(lineas) + "basura\n", encoding="utf-8")
    antes = hist.read_text(encoding="utf-8")
    msg, ok = s.deshacer()
    assert not ok and hist.read_text(encoding="utf-8") == antes


def test_deshacer_sin_historial(datos):
    hist, _, _ = datos
    hist.write_text("", encoding="utf-8")
    assert s.deshacer()[1] is False


def test_registrar_agrega_la_linea_del_siguiente_sorteo(datos):
    hist, _, lineas = datos
    e = s.estado(s.cargar())
    texto, clase = s.registrar("1")
    assert clase in ("ok", "no")
    nuevo = hist.read_text(encoding="utf-8").splitlines()[-1]
    assert nuevo == "%s %d 1" % (e["pf"], e["ph"])


def test_registrar_y_deshacer_dejan_el_historial_igual(datos):
    hist, _, lineas = datos
    s.registrar("1")
    s.deshacer()
    assert hist.read_text(encoding="utf-8") == "".join(lineas)


def test_deshacer_reabre_el_pronostico_en_vez_de_anularlo(datos):
    """No se puede borrar un fallo con deshacer + anotar de nuevo."""
    hist, log, _ = datos
    e = s.estado(s.cargar())
    log.write_text(json.dumps({"registros": [{
        "fecha": e["pf"], "hora": e["ph"], "top3": [0, 1, 2], "orden_completo": ORDEN,
        "salio": None, "modelo": s.MODELO_MARCADOR}]}), encoding="utf-8")
    s.registrar("3")                      # anota un número
    s.deshacer()
    r = json.loads(log.read_text(encoding="utf-8"))["registros"][0]
    assert r["salio"] is None and not r.get("anulado")
    assert r["correcciones"][0]["salio_anterior"] is not None


def test_registrar_error_de_escritura_no_anota(datos, monkeypatch):
    hist, _, lineas = datos
    real = open
    def open_roto(f, mode="r", *a, **k):
        if str(f) == s.HIST and "a" in mode: raise OSError("sin escritura")
        return real(f, mode, *a, **k)
    monkeypatch.setattr("builtins.open", open_roto)
    texto, clase = s.registrar("1")
    assert clase == "bad" and "NO se registró" in texto
    monkeypatch.undo()
    assert hist.read_text(encoding="utf-8") == "".join(lineas)


# ----------------------------------------------------------------- marcador
def test_marcador_vacio():
    assert s.marcador({"registros": []}) == dict(n=0, n15=0)


def test_marcador_cuenta_top1_top3_top5_top15():
    d = {"registros": [_reg(0, ORDEN),     # puesto 1
                       _reg(2, ORDEN),     # puesto 3
                       _reg(4, ORDEN),     # puesto 5
                       _reg(14, ORDEN),    # puesto 15
                       _reg(30, ORDEN)]}   # fuera del Top-15
    m = s.marcador(d)
    assert (m["n"], m["t1"], m["t3"], m["t5"], m["t15"]) == (5, 1, 2, 3, 4)
    assert m["puesto_medio"] == pytest.approx((1 + 3 + 5 + 15 + 31) / 5)
    assert m["tasa3"] == pytest.approx(40.0)


def test_marcador_ignora_anulados_pendientes_y_otro_modelo():
    d = {"registros": [_reg(0, ORDEN),
                       dict(_reg(0, ORDEN), anulado=True),
                       _reg(None, ORDEN),
                       _reg(0, ORDEN, modelo="hazard-viejo")]}
    assert s.marcador(d)["n"] == 1


def test_registro_sin_orden_completo_no_cuenta_para_top15_ni_inventa_fallo():
    r = _reg(0, ORDEN); r.pop("orden_completo")
    m = s.marcador({"registros": [r]})
    assert m["n"] == 1 and m["n15"] == 0
    assert s.puesto_ganador(r) is None


def test_puesto_ganador_es_base_1():
    assert s.puesto_ganador(_reg(0, ORDEN)) == 1
    assert s.puesto_ganador(_reg(37, ORDEN)) == 38


def test_cola_binomial():
    assert s.cola_binomial(0, 10, 0.5) == 1.0
    assert s.cola_binomial(1, 0, 0.5) == 1.0
    assert s.cola_binomial(10, 10, 0.5) == pytest.approx(0.5 ** 10)
    assert s.cola_binomial(1, 3, 0.5) == pytest.approx(1 - 0.5 ** 3)


def test_factor_de_bayes_sube_con_aciertos_y_baja_con_fallos():
    acierto = s.marcador({"registros": [_reg(0, ORDEN)]})["factor"]
    fallo = s.marcador({"registros": [_reg(30, ORDEN)]})["factor"]
    assert acierto > 1 > fallo
    assert acierto == pytest.approx(s.P_MOD_T3 / s.P_AZAR_T3)
    assert fallo == pytest.approx((1 - s.P_MOD_T3) / (1 - s.P_AZAR_T3))
