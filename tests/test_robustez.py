"""Regresión: POST con Content-Length basura/enorme y guardado atómico de estado_banca.json."""
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import gestion_banca
import servidor


class _FalsoH:
    """Lo mínimo de H que usa _post antes de leer el cuerpo."""
    def __init__(self, content_length, cuerpo=b""):
        self.headers = {"Content-Length": content_length}
        self.rfile = io.BytesIO(cuerpo)
        self.path = "/registrar"
        self.enviado = None

    def _send(self, cuerpo, tipo="text/plain", codigo=200):
        self.enviado = codigo


def test_post_content_length_no_numerico_da_400():
    h = _FalsoH("abc")
    servidor.H._post(h)
    assert h.enviado == 400


def test_post_content_length_negativo_da_400():
    h = _FalsoH("-5")
    servidor.H._post(h)
    assert h.enviado == 400


def test_post_demasiado_grande_da_400_sin_leer():
    h = _FalsoH(str(servidor.MAX_POST + 1), b"x" * 10)
    servidor.H._post(h)
    assert h.enviado == 400
    assert h.rfile.tell() == 0


def test_guardar_estado_atomico(tmp_path, monkeypatch):
    ruta = str(tmp_path / "estado_banca.json")
    monkeypatch.setattr(gestion_banca, "ESTADO", ruta)
    gestion_banca.guardar_estado({"dia": "2026-10-03", "maximo": 5})
    assert gestion_banca.cargar_estado()["maximo"] == 5
    assert not os.path.exists(ruta + ".tmp")

    # Un fallo al serializar no debe tocar el archivo bueno.
    try:
        gestion_banca.guardar_estado({"x": object()})
    except TypeError:
        pass
    with open(ruta, encoding="utf-8") as f:
        assert json.load(f)["maximo"] == 5
