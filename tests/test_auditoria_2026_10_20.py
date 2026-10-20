"""Regresiones de la auditoría por ciclos del 2026-10-20 (investigacion/2026-10-20/auditoria_ciclos).

P1 sellos tardíos -> test_evaluacion_prospectiva.py; P1 RD posterior en Ag14 -> test_ag14.py.
Aquí: pendiente contable creado tras el sorteo, redondeo de pp y cliente lento. Solo localhost y datos temporales.
"""
import http.client
import os
import socket
import sys
import threading

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import experimentos as E
import servidor as S


# ------------------------------------------------------------- P1: pendiente creado pasada la hora
@pytest.fixture
def motor(tmp_path, monkeypatch):
    hist, log = tmp_path / "historial.txt", tmp_path / "predicciones.json"
    with open(S.HIST, encoding="utf-8") as f:
        hist.write_text("".join(f.readlines()[-400:]), encoding="utf-8")
    monkeypatch.setattr(S, "HIST", str(hist))
    monkeypatch.setattr(S, "LOG", str(log))

    class Predictor:
        error = None

        def obtener(self, *args):
            return [1 / 38] * 38, {"frontera_pesos": 1, "pesos_vigentes": True}

    monkeypatch.setattr(S, "PRED", Predictor())
    monkeypatch.setattr(S, "sombra_de", lambda *a: {"ag12": [1 / 38] * 38})
    monkeypatch.setattr(E, "_rd_por_slot", lambda: {})
    monkeypatch.setattr(E, "completar_pron", lambda *a: False)
    e = S.estado(S.cargar())
    return E.hora_sorteo(e["pf"], e["ph"])


def _reloj(monkeypatch, cuando):
    monkeypatch.setattr(S, "_ahora_dt", lambda: cuando)
    monkeypatch.setattr(S, "ahora", lambda: cuando.isoformat(timespec="seconds"))


@pytest.mark.parametrize("minutos", [0, 1, 90])
def test_no_se_crea_pronostico_contable_a_la_hora_del_sorteo_o_despues(motor, monkeypatch, minutos):
    _reloj(monkeypatch, motor + S.timedelta(minutes=minutos))
    assert S.preparar()["pend"] is None
    assert S.log_cargar()["registros"] == []


def test_antes_del_sorteo_si_se_congela(motor, monkeypatch):
    _reloj(monkeypatch, motor - S.timedelta(minutes=1))
    pend = S.preparar()["pend"]
    assert pend is not None and pend["creado"] < motor.isoformat()


def test_resueltas_excluye_creado_tarde_solo_desde_que_la_hora_es_fiable():
    base = {"salio": 3, "modelo": S.MODELO_MARCADOR}
    regs = [dict(base, fecha="2026-10-18", hora=2, creado="2026-10-18T09:59:59"),   # 10:00: a tiempo
            dict(base, fecha="2026-10-18", hora=3, creado="2026-10-18T11:00:00"),   # 11:00: tarde
            dict(base, fecha="2026-09-15", hora=0, creado="2026-09-15T12:36:38")]   # TZ no fiable: se conserva
    assert [(r["fecha"], r["hora"]) for r in S.resueltas({"registros": regs})] == [
        ("2026-10-18", 2), ("2026-09-15", 0)]


# ------------------------------------------------------------- P2: redondeo antes de pasar a pp
def test_diferencia_de_un_acierto_en_221_sorteos_no_se_redondea_a_cero():
    pares = [("2026-10-%02d" % (1 + i % 5), 0.0) for i in range(220)] + [("2026-10-01", -1.0)]
    r = E.ic90_jornadas(pares, escala=100)
    assert r["media"] == pytest.approx(-100 / 221, abs=0.005)        # −0,45 pp, no −0,00
    assert r["ic90"][0] < r["media"] < r["ic90"][1]


# ------------------------------------------------------------- P1: cliente lento no bloquea el servicio
@pytest.fixture
def servidor_local():
    srv = S.Servidor(("127.0.0.1", 0), S.H)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    yield srv
    srv.shutdown()
    srv.server_close()
    hilo.join(timeout=2)


def test_cliente_lento_no_bloquea_otra_peticion(servidor_local):
    lento = socket.create_connection(servidor_local.server_address, timeout=1)
    lento.sendall(b"POST /audit-inexistente HTTP/1.0\r\nContent-Length: 4\r\n\r\na")
    rapido = http.client.HTTPConnection(*servidor_local.server_address, timeout=.4)
    try:
        rapido.request("GET", "/audit-inexistente")
        assert rapido.getresponse().status == 404
    finally:
        lento.close()
        rapido.close()


def test_cuerpo_lento_no_retiene_el_cerrojo(servidor_local):
    lento = socket.create_connection(servidor_local.server_address, timeout=1)
    lento.sendall(b"POST /registrar HTTP/1.0\r\nContent-Length: 4\r\n\r\na")
    try:
        assert S.CERROJO.acquire(timeout=.4)
        S.CERROJO.release()
    finally:
        lento.close()


def test_vivo_responde_sin_tocar_los_datos(servidor_local):
    c = http.client.HTTPConnection(*servidor_local.server_address, timeout=2)
    try:
        c.request("GET", "/vivo")
        r = c.getresponse()
        assert (r.status, r.read()) == (200, b"ok")
    finally:
        c.close()


def test_el_handler_tiene_timeout():
    assert 0 < S.H.timeout <= 30
