import json
import pytest
import rdint_vivo


def test_log_cargar_ausente_es_vacio(tmp_path, monkeypatch):
    monkeypatch.setattr(rdint_vivo, "RD_LOG", str(tmp_path / "no_existe.json"))
    assert rdint_vivo.log_cargar() == {"registros": []}


def test_log_cargar_corrupto_falla_en_voz_alta(tmp_path, monkeypatch):
    p = tmp_path / "rd.json"
    p.write_text("{corrupto", encoding="utf-8")
    monkeypatch.setattr(rdint_vivo, "RD_LOG", str(p))
    with pytest.raises(json.JSONDecodeError):
        rdint_vivo.log_cargar()
