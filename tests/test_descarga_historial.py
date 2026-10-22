"""Botón «Descargar historial»: /historial.zip con la cookie de la clave (o ?clave=RESPALDO_CLAVE) y nada sin ella."""
import io, json, os, sys, threading, zipfile
from http.server import HTTPServer
import http.client

import pytest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
import servidor as s
import rdint_vivo


@pytest.fixture
def datos(tmp_path, monkeypatch):
    (tmp_path / "historial.txt").write_text("2026-10-20 8:00 12\n2026-10-20 9:00 0\n\n", encoding="utf-8")
    (tmp_path / "predicciones.json").write_text(json.dumps({"registros": [{"fecha": "2026-10-20"}]}), encoding="utf-8")
    (tmp_path / "rdint_historial.txt").write_text("2026-10-20 8:30 5\n", encoding="utf-8")
    pub = tmp_path / "datos_publicados" / "2026-10-20"
    pub.mkdir(parents=True)
    (pub / "meta.json").write_text("{}", encoding="utf-8")
    (pub / "pagina.html").write_text("<html>", encoding="utf-8")
    monkeypatch.setattr(s, "DATOS", str(tmp_path))
    monkeypatch.setattr(s, "HIST", str(tmp_path / "historial.txt"))
    monkeypatch.setattr(s, "LOG", str(tmp_path / "predicciones.json"))
    monkeypatch.setattr(rdint_vivo, "RD_HIST", str(tmp_path / "rdint_historial.txt"))
    monkeypatch.setattr(rdint_vivo, "RD_LOG", str(tmp_path / "rdint_predicciones.json"))
    monkeypatch.setattr(s, "CLAVE_ESCRITURA", "110593")
    monkeypatch.delenv("RESPALDO_CLAVE", raising=False)
    return tmp_path


@pytest.fixture
def web():
    srv = HTTPServer(("127.0.0.1", 0), s.H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv.server_address[1]
    srv.shutdown(); srv.server_close()


def pedir(puerto, ruta, cookie=None):
    c = http.client.HTTPConnection("127.0.0.1", puerto, timeout=30)
    c.request("GET", ruta, headers={"Cookie": cookie} if cookie else {})
    r = c.getresponse()
    out = (r.status, r.getheader("Content-Type"), r.getheader("Content-Disposition"), r.read())
    c.close()
    return out


def _cookie():
    return f"{s.COOKIE_CLAVE}={s._firma_clave()}"


def test_sin_cookie_ni_clave_no_hay_descarga(datos, web):
    for cookie in (None, f"{s.COOKIE_CLAVE}=falsa"):
        st, tipo, _, cuerpo = pedir(web, "/historial.zip", cookie=cookie)
        assert st == 303 and tipo != "application/zip"                       # vuelve a la página y pide la clave
    assert "clave" in s.AVISO["texto"]
    s.AVISO["texto"] = ""
    assert pedir(web, "/respaldo.zip")[0] == 404                               # la ruta sin botón sigue muda


def test_con_cookie_baja_el_zip_con_todo_y_leeme(datos, web):
    st, tipo, disp, cuerpo = pedir(web, "/historial.zip?", cookie=_cookie())   # el form GET agrega «?»
    assert (st, tipo) == (200, "application/zip")
    assert disp.startswith("attachment;")
    z = zipfile.ZipFile(io.BytesIO(cuerpo))
    nombres = set(z.namelist())
    assert {"historial.txt", "predicciones.json", "rdint_historial.txt", "LEEME.txt",
            "datos_publicados/2026-10-20/meta.json"} <= nombres
    assert "datos_publicados/2026-10-20/pagina.html" not in nombres          # el HTML crudo pesa y no hace falta
    leeme = z.read("LEEME.txt").decode("utf-8")
    assert "historial.txt: 2 sorteos" in leeme
    assert "predicciones.json: 1 pronósticos congelados" in leeme
    assert "rdint_predicciones.json: no existe" in leeme
    assert z.read("historial.txt") == (datos / "historial.txt").read_bytes()


def test_respaldo_por_clave_sigue_funcionando(datos, web, monkeypatch):
    monkeypatch.setenv("RESPALDO_CLAVE", "secreta")
    assert pedir(web, "/respaldo.zip?clave=mala")[0] == 404
    assert pedir(web, "/respaldo.zip?clave=secreta")[0] == 200
    assert pedir(web, "/historial.zip?clave=secreta")[0] == 200


def test_boton_arriba_baja_un_txt_sin_clave(datos, web):
    reg = {"fecha": "2026-10-20", "hora": 0, "salio": 12, "orden_completo": [12, 0], "scores": [0.1] * 38}
    (datos / "predicciones.json").write_text(json.dumps({"registros": [reg]}), encoding="utf-8")
    st, tipo, disp, cuerpo = pedir(web, "/historial.txt?")                    # sin cookie ni clave
    assert (st, tipo) == (200, "text/plain; charset=utf-8")
    assert disp.startswith("attachment;") and ".txt" in disp
    texto = cuerpo.decode("utf-8")
    assert "historial.txt (Lotto Activo, sorteos h:00): 2 sorteos" in texto
    assert "===== historial.txt =====\n2026-10-20 8:00 12\n2026-10-20 9:00 0" in texto
    assert "===== rdint_historial.txt =====\n2026-10-20 8:30 5" in texto
    linea = texto.split("===== predicciones.jsonl =====\n")[1].split("\n")[0]
    assert json.loads(linea) == {k: v for k, v in reg.items() if k != "scores"}   # sin los 38 puntajes
    assert "rdint_predicciones (RD Internacional): no existe" in texto


@pytest.mark.skipif(not os.path.exists(s.HIST), reason="falta historial.txt")
def test_el_boton_esta_al_inicio_de_la_pagina():
    html = s.render()
    i = html.index('<main class="w">')
    assert html.index('action="/historial.txt"') - i < 120                  # lo primero dentro de la página
    assert ">Descargar historial</button>" in html
    assert 'action="/historial.zip"' not in html                             # un solo botón, el simple
