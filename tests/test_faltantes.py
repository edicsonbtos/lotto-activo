"""agregar_faltantes(): inserta una vez el sorteo perdido y corre las tripletas posteriores."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import servidor as s


def _hist():
    out = []
    for f in ("2026-06-23", "2026-06-24", "2026-06-25"):
        for h in range(12):
            if (f, h) != ("2026-06-24", 11):
                out.append(f"{f} {h} {(h * 7 + int(f[-2:])) % 36 + 1}")
    return out


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    hist, log, falt = tmp_path / "historial.txt", tmp_path / "predicciones.json", tmp_path / "falt.json"
    lineas = _hist()
    hist.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    i = lineas.index("2026-06-25 0 " + lineas[23].split()[2])        # primer sorteo del 06-25
    log.write_text(json.dumps({"registros": [], "sorteos_conocidos": [], "tripletas": [
        {"inicio_fecha": "2026-06-23", "inicio_hora": 2, "n_inicio": 2, "jugadas": [[0, 1, 2]], "estado": "pendiente"},
        {"inicio_fecha": "2026-06-25", "inicio_hora": 0, "n_inicio": i, "jugadas": [[0, 1, 2]], "estado": "pendiente"}]}),
        encoding="utf-8")
    falt.write_text(json.dumps({"agregar": ["2026-06-24 11 22"]}), encoding="utf-8")
    for k, v in (("HIST", hist), ("LOG", log), ("DATOS", tmp_path), ("FALTANTES_HIST", falt)):
        monkeypatch.setattr(s, k, str(v))
    return hist, log, i


def test_inserta_y_corre_tripletas(entorno):
    hist, log, i = entorno
    s.agregar_faltantes()
    lineas = [l for l in hist.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lineas) == 36 and lineas[23] == "2026-06-24 11 22"
    t = json.loads(log.read_text(encoding="utf-8"))["tripletas"]
    assert t[0]["n_inicio"] == 2 and t[1]["n_inicio"] == i + 1
    d = s.log_cargar(); s.resolver_tripletas(d, s.cargar())
    assert all("anulado" not in x for x in d["tripletas"])
    assert (os.path.exists(os.path.join(s.DATOS, "respaldo", "historial_antes_faltantes_2026-10-03.txt")))


def test_una_sola_vez(entorno):
    hist, log, i = entorno
    s.agregar_faltantes(); antes = hist.read_bytes()
    s.agregar_faltantes()
    assert hist.read_bytes() == antes
    assert json.loads(log.read_text(encoding="utf-8"))["tripletas"][1]["n_inicio"] == i + 1


def test_no_toca_si_ya_esta(entorno, monkeypatch, tmp_path):
    hist, log, _ = entorno
    otro = tmp_path / "otro.json"
    otro.write_text(json.dumps({"agregar": ["2026-06-24 10 5"]}), encoding="utf-8")
    monkeypatch.setattr(s, "FALTANTES_HIST", str(otro))
    antes = hist.read_bytes()
    s.agregar_faltantes()
    assert hist.read_bytes() == antes
    assert not os.path.exists(os.path.join(s.DATOS, "faltantes_historial_2026-10-03.hecho.json"))
