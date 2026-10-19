"""Revisión 2026-10-19: clave para escribir, RD congelado en ag12+RD y ag12 que faltaba en algunos sorteos."""
import http.client, os, sys, threading
from datetime import datetime
from http.server import HTTPServer

import pytest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
import experimentos
import servidor as s

RAIZ = os.path.join(AQUI, "..")
HIST_REAL = next(p for p in (os.path.join(RAIZ, "historial.txt"),
                             os.path.join(RAIZ, "verificacion", "hilo9", "datos", "historial.txt"))
                 if os.path.exists(p))
FORM = {"Content-Type": "application/x-www-form-urlencoded"}
AG12 = [1.0 / 38] * 38
AG12[5] = AG12[6] = 0.05          # índices 5 y 6 arriba: la regla de RD los baja si salieron en RD
C5, C6 = s.POS[5], s.POS[6]       # sus códigos ("4" y "5")


@pytest.fixture
def datos(tmp_path, monkeypatch):
    with open(HIST_REAL, encoding="utf-8") as f:
        lineas = [l for l in f if l.strip()][-400:]
    hist, log = tmp_path / "historial.txt", tmp_path / "predicciones.json"
    hist.write_text("".join(lineas), encoding="utf-8")
    monkeypatch.setattr(s, "HIST", str(hist))
    monkeypatch.setattr(s, "LOG", str(log))
    monkeypatch.setattr(s, "PRED", None)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    s.AVISO.update(texto="", clase="")
    return hist, log, lineas


@pytest.fixture
def web():
    srv = HTTPServer(("127.0.0.1", 0), s.H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv.server_address[1]
    srv.shutdown(); srv.server_close()


def pedir(puerto, ruta, cuerpo="", cabeceras=None):
    c = http.client.HTTPConnection("127.0.0.1", puerto, timeout=60)
    c.request("POST", ruta, body=cuerpo, headers=dict(FORM, **(cabeceras or {})))
    r = c.getresponse(); r.read()
    out = (r.status, r.getheader("Set-Cookie"))
    c.close()
    return out


# ------------------------------------------------------------------ 1. clave para escribir
def test_con_clave_configurada_deshacer_sin_clave_no_toca_el_historial(datos, web, monkeypatch):
    hist, _, lineas = datos
    monkeypatch.setattr(s, "CLAVE_ESCRITURA", "110593")
    st, cookie = pedir(web, "/deshacer")
    assert st == 303 and cookie is None
    assert hist.read_text(encoding="utf-8") == "".join(lineas)
    assert s.AVISO["clase"] == "bad" and "clave" in s.AVISO["texto"].lower()


def test_clave_incorrecta_no_escribe(datos, web, monkeypatch):
    hist, _, lineas = datos
    monkeypatch.setattr(s, "CLAVE_ESCRITURA", "110593")
    st, cookie = pedir(web, "/deshacer", "clave=000000")
    assert cookie is None and hist.read_text(encoding="utf-8") == "".join(lineas)


def test_clave_correcta_escribe_y_deja_cookie_que_sirve_despues(datos, web, monkeypatch):
    hist, _, lineas = datos
    monkeypatch.setattr(s, "CLAVE_ESCRITURA", "110593")
    st, cookie = pedir(web, "/entrar", "clave=110593")
    assert st == 303 and cookie and "HttpOnly" in cookie and "SameSite=Strict" in cookie
    assert "110593" not in cookie                      # la cookie lleva una firma, no la clave
    valor = cookie.split(";")[0]
    pedir(web, "/deshacer", "", {"Cookie": valor})
    assert hist.read_text(encoding="utf-8") == "".join(lineas[:-1])


def test_clave_en_el_mismo_formulario_tambien_vale(datos, web, monkeypatch):
    hist, _, lineas = datos
    monkeypatch.setattr(s, "CLAVE_ESCRITURA", "110593")
    st, cookie = pedir(web, "/deshacer", "clave=110593")
    assert cookie and hist.read_text(encoding="utf-8") == "".join(lineas[:-1])


def test_herramientas_tambien_piden_clave(datos, web, monkeypatch):
    monkeypatch.setattr(s, "CLAVE_ESCRITURA", "110593")
    llamadas = []
    monkeypatch.setattr(s, "iniciar_tarea", lambda clave: llamadas.append(clave))
    pedir(web, "/herramienta/tripleta")
    assert llamadas == []


def test_en_railway_sin_clave_configurada_no_se_puede_escribir(datos, web, monkeypatch):
    hist, _, lineas = datos
    monkeypatch.setattr(s, "CLAVE_ESCRITURA", "")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    pedir(web, "/deshacer")
    assert hist.read_text(encoding="utf-8") == "".join(lineas)


def test_en_local_sin_clave_se_puede_escribir(datos, web, monkeypatch):
    hist, _, lineas = datos
    monkeypatch.setattr(s, "CLAVE_ESCRITURA", "")
    pedir(web, "/deshacer")
    assert hist.read_text(encoding="utf-8") == "".join(lineas[:-1])


def test_la_pagina_pide_la_clave_si_no_hay_cookie(monkeypatch):
    monkeypatch.setattr(s, "CLAVE_ESCRITURA", "110593")
    assert 'name="clave"' in s.html_registro(None, autorizado=False)
    assert 'name="clave"' not in s.html_registro(None, autorizado=True)


# ------------------------------------------------------------------ 2. RD congelado antes del sorteo
def _reg_sombra(**extra):
    r = {"fecha": "2026-10-19", "hora": 3, "salio": None, "modelo": s.MODELO_MARCADOR,
         "scores": [1.0 / 38] * 38, "orden_completo": list(range(38)), "top3": [0, 1, 2],
         "sombra": {"ag12": list(AG12)}}
    r.update(extra)
    return r


def test_congelar_rd_guarda_lo_conocido_antes_del_sorteo():
    r = _reg_sombra()
    rd = {("2026-10-19", 2): C5}                      # 10:30 ya salió; 9:30 no está anotado
    assert experimentos.congelar_rd(r, rd, datetime(2026, 10, 19, 10, 45)) is True
    assert r["sombra"]["rd"] == {"1": C5, "2": None}
    assert experimentos.congelar_rd(r, rd, datetime(2026, 10, 19, 10, 50)) is False   # sin cambios


def test_congelar_rd_no_toca_nada_despues_de_la_hora_del_sorteo():
    r = _reg_sombra()
    rd = {("2026-10-19", 2): C5}
    assert experimentos.congelar_rd(r, rd, datetime(2026, 10, 19, 11, 0)) is False
    assert "rd" not in r["sombra"]


def test_rd_que_llega_tarde_no_cambia_el_historial_de_ag12_rd(monkeypatch):
    r = _reg_sombra(salio=6, sombra={"ag12": list(AG12), "rd": {"1": None, "2": None}})
    monkeypatch.setattr(experimentos, "_rd_por_slot", lambda: {("2026-10-19", 2): C5})   # anotado DESPUÉS
    reg = s.sombra_registros({"registros": [r], "tripletas": []})[0]
    assert reg["orden_completo"][:2] == [5, 6]          # el índice 5 no se castiga: no se conocía a las 11:00


def test_rd_congelado_se_usa_aunque_el_rd_de_hoy_sea_otro(monkeypatch):
    r = _reg_sombra(salio=6, sombra={"ag12": list(AG12), "rd": {"1": C5, "2": None}})
    monkeypatch.setattr(experimentos, "_rd_por_slot", lambda: {("2026-10-19", 2): C6})
    reg = s.sombra_registros({"registros": [r], "tripletas": []})[0]
    assert reg["orden_completo"][0] == 6                # se castigó al índice 5 (lo congelado), no al 6


def test_marcador_sombra_usa_el_rd_congelado(monkeypatch):
    r = _reg_sombra(salio=5, sombra={"ag12": list(AG12), "rd": {"1": None, "2": None}})
    monkeypatch.setattr(experimentos, "_rd_por_slot", lambda: {("2026-10-19", 2): C5})
    m = experimentos.marcador_sombra([r], s.fichas_por_puesto())
    assert m["sorteos_con_rd"] == 0 and m["marcador"]["ag12_rd"]["top3"] == 1


def test_registro_viejo_sin_rd_congelado_sigue_con_el_rd_anotado(monkeypatch):
    r = _reg_sombra(salio=6)
    monkeypatch.setattr(experimentos, "_rd_por_slot", lambda: {("2026-10-19", 2): C5})
    reg = s.sombra_registros({"registros": [r], "tripletas": []})[0]
    assert reg["orden_completo"][0] == 6


# ------------------------------------------------------------------ 3. ag12 que faltaba
class PredFalso:
    error = None

    def obtener(self, hist, f, h):
        return [1.0 / 38] * 38, {"frontera_pesos": 1, "pesos_vigentes": True}


@pytest.fixture
def motor(datos, monkeypatch):
    monkeypatch.setattr(s, "PRED", PredFalso())
    monkeypatch.setattr(s, "modelo_de", lambda info: s.MODELO_MARCADOR)
    monkeypatch.setattr(experimentos, "completar_pron", lambda *a, **k: False)
    monkeypatch.setattr(experimentos, "_rd_por_slot", lambda: {})
    return datos


def _antes_del_sorteo(monkeypatch, minutos=-5):
    e = s.estado(s.cargar())
    monkeypatch.setattr(s, "_ahora_dt", lambda: experimentos.hora_sorteo(e["pf"], e["ph"]) + s.timedelta(minutes=minutos))


def test_preparar_reintenta_ag12_si_fallo_al_congelar(motor, monkeypatch):
    _antes_del_sorteo(monkeypatch)
    monkeypatch.setattr(s, "sombra_de", lambda *a: None)
    s.preparar()
    pend = [r for r in s.log_cargar()["registros"] if r.get("salio") is None][0]
    assert "sombra" not in pend
    monkeypatch.setattr(s, "sombra_de", lambda *a: {"ag12": list(AG12)})
    s.preparar()
    pend = [r for r in s.log_cargar()["registros"] if r.get("salio") is None][0]
    assert pend["sombra"]["ag12"] == AG12


def test_preparar_congela_el_rd_del_pendiente_antes_del_sorteo(motor, monkeypatch):
    monkeypatch.setattr(s, "sombra_de", lambda *a: {"ag12": list(AG12)})
    e = s.estado(s.cargar())
    hora_sorteo = datetime.fromisoformat(e["pf"]).replace(hour=8 + e["ph"])
    monkeypatch.setattr(s, "_ahora_dt", lambda: hora_sorteo.replace(minute=0) - s.timedelta(minutes=5))
    monkeypatch.setattr(experimentos, "_rd_por_slot", lambda: {(e["pf"], e["ph"] - 1): C5})
    s.preparar()
    pend = [r for r in s.log_cargar()["registros"] if r.get("salio") is None][0]
    assert pend["sombra"]["rd"]["1"] == (C5 if e["ph"] >= 1 else None)


def test_registrar_desde_cache_tambien_guarda_ag12(motor, monkeypatch):
    monkeypatch.setattr(s, "sombra_de", lambda *a: {"ag12": list(AG12)})
    s.registrar("5")
    r = [x for x in s.log_cargar()["registros"] if x.get("salio") is not None][-1]
    assert r["sombra"]["ag12"] == AG12


def _pendiente_sin_ag12(monkeypatch, **extra):
    monkeypatch.setattr(s, "sombra_de", lambda *a: None)
    s.preparar()
    d = s.log_cargar()
    pend = [r for r in d["registros"] if r.get("salio") is None][0]
    pend.update(extra); s.log_guardar(d)
    monkeypatch.setattr(s, "sombra_de", lambda *a: {"ag12": list(AG12)})
    s.preparar()
    return [r for r in s.log_cargar()["registros"] if r.get("salio") is None][0]


def test_no_reintenta_ag12_en_un_sorteo_reabierto_con_deshacer(motor, monkeypatch):
    _antes_del_sorteo(monkeypatch)
    pend = _pendiente_sin_ag12(monkeypatch, correcciones=[{"salio_anterior": 3}])
    assert "sombra" not in pend       # ya se conocía el resultado: meterlo sería elegir qué entra al marcador


def test_no_reintenta_ag12_despues_de_la_hora_del_sorteo(motor, monkeypatch):
    _antes_del_sorteo(monkeypatch, minutos=+1)
    assert "sombra" not in _pendiente_sin_ag12(monkeypatch)
