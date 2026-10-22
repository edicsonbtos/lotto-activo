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
    assert pedir(web, "/historial.zip")[0] == 404
    assert pedir(web, "/historial.zip", cookie=f"{s.COOKIE_CLAVE}=falsa")[0] == 404


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


def test_el_boton_sale_solo_con_permiso():
    assert 'action="/historial.zip"' in s.html_registro(None, autorizado=True)
    assert 'action="/historial.zip"' not in s.html_registro(None, autorizado=False)
