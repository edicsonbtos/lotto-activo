"""Contrato HTTP del handler de servidor.py: estado, tipo de contenido y forma de cada ruta.

Solo toca rutas que no escriben datos (nada de /deshacer, /auto ni registros válidos).
"""
import http.client, json, os, sys, threading
from http.server import HTTPServer

import pytest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
import servidor

HAY_DATOS = os.path.exists(servidor.HIST)
JSON_UTF8 = "application/json; charset=utf-8"


@pytest.fixture(scope="module")
def web():
    srv = HTTPServer(("127.0.0.1", 0), servidor.H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv.server_address[1]
    srv.shutdown(); srv.server_close()


def pedir(puerto, metodo, ruta, cuerpo=None, cabeceras=None):
    c = http.client.HTTPConnection("127.0.0.1", puerto, timeout=60)
    c.request(metodo, ruta, body=cuerpo, headers=cabeceras or {})
    r = c.getresponse()
    out = (r.status, r.getheader("Content-Type"), r.getheader("Location"), r.read().decode("utf-8", "replace"))
    c.close()
    return out


def test_ruta_desconocida_da_404_en_texto(web):
    st, tipo, _, cuerpo = pedir(web, "GET", "/no-existe")
    assert (st, tipo, cuerpo) == (404, "text/plain; charset=utf-8", "No encontrado")


def test_post_desconocido_da_404(web):
    st, tipo, _, _ = pedir(web, "POST", "/no-existe", "x=1", {"Content-Type": "application/x-www-form-urlencoded"})
    assert (st, tipo) == (404, "text/plain; charset=utf-8")


def test_post_con_content_length_basura_o_enorme_da_400(web):
    for largo in ("abc", "-5", str(servidor.MAX_POST + 1)):
        c = http.client.HTTPConnection("127.0.0.1", web, timeout=30)
        c.putrequest("POST", "/registrar"); c.putheader("Content-Length", largo); c.endheaders()
        assert c.getresponse().status == 400, largo
        c.close()


def test_registrar_numero_invalido_redirige_y_avisa(web):
    st, _, loc, _ = pedir(web, "POST", "/registrar", "num=99", {"Content-Type": "application/x-www-form-urlencoded"})
    assert (st, loc) == (303, "/")
    assert servidor.AVISO["clase"] == "bad" and "no es válido" in servidor.AVISO["texto"]
    servidor.AVISO.update(texto="", clase="")


def test_tablas_de_rutas():
    assert set(servidor.RUTAS_JSON) == {"/tareas.json", "/listo.json", "/api/mesa", "/api/mesa_stats",
                                        "/api/rdint", "/api/cambio_rd", "/api/cambio_rd15", "/api/sombra_decision", "/api/sombra", "/api/salud",
                                        "/api/datos_publicados"}
    assert set(servidor.ACCIONES_POST) == {"/auto", "/deshacer", "/registrar", "/", "/tripleta/registrar"}
    for fn, tipo in servidor.RUTAS_JSON.values():
        assert callable(fn) and tipo.startswith("application/json")


def test_accion_registrar_invalida_avisa_y_vuelve_arriba():
    ancla = servidor.ACCIONES_POST["/registrar"]("num=%3Cb%3E")
    assert ancla == ""
    assert servidor.AVISO["clase"] == "bad" and "&lt;b&gt;" in servidor.AVISO["texto"]   # escapado
    servidor.AVISO.update(texto="", clase="")


@pytest.mark.skipif(not HAY_DATOS, reason="falta historial.txt")
@pytest.mark.parametrize("ruta,tipo", [
    ("/tareas.json", JSON_UTF8),
    ("/listo.json", "application/json"),
    ("/api/mesa", JSON_UTF8),
    ("/api/mesa?offset=2", JSON_UTF8),
    ("/api/mesa_stats", JSON_UTF8),
    ("/api/cambio_rd", JSON_UTF8),
    ("/api/cambio_rd15", JSON_UTF8),
    ("/api/sombra_decision", JSON_UTF8),
    ("/api/sombra", JSON_UTF8),
    ("/api/salud", JSON_UTF8),
    ("/api/rdint", JSON_UTF8),
    ("/api/datos_publicados", JSON_UTF8),
])
def test_rutas_json(web, ruta, tipo):
    st, ct, _, cuerpo = pedir(web, "GET", ruta)
    assert (st, ct) == (200, tipo)
    json.loads(cuerpo)


@pytest.mark.skipif(not HAY_DATOS, reason="falta historial.txt")
def test_pagina_principal_y_pestanas(web):
    for ruta in ("/", "/index.html", "/?tab=rd", "/?tab=la&atras=3", "/?banca=300", "/?atras=abc&banca=x"):
        st, ct, _, cuerpo = pedir(web, "GET", ruta)
        assert (st, ct) == (200, "text/html; charset=utf-8"), ruta
        assert "<html" in cuerpo


@pytest.mark.skipif(not HAY_DATOS, reason="falta historial.txt")
def test_respaldo_cerrado_sin_clave_y_zip_con_clave(web, monkeypatch):
    import io, zipfile
    monkeypatch.delenv("RESPALDO_CLAVE", raising=False)
    assert pedir(web, "GET", "/respaldo.zip?clave=x")[0] == 404
    monkeypatch.setenv("RESPALDO_CLAVE", "secreta")
    assert pedir(web, "GET", "/respaldo.zip")[0] == 404
    assert pedir(web, "GET", "/respaldo.zip?clave=mala")[0] == 404
