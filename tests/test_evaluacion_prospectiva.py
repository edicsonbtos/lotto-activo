import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "herramientas"))
import evaluacion_prospectiva as ep


def test_carga_y_puntua_pronosticos_sellados_sin_alterar_archivos(tmp_path):
    probabilities = [1 / 38] * 38
    pred = {
        "estado": "SELLADO_PENDIENTE_DE_RESULTADO",
        "fecha_sorteo": "2026-10-17",
        "hora_sorteo": "08:00 America/Caracas",
        "candidata": "ag12 + exposición",
        "probabilidades_candidata": probabilities,
    }
    ens = {
        "fecha": "2026-10-17",
        "hora": 0,
        "winner": None,
        "animales": [{"idx": i, "prob": 1 / 38} for i in range(38)],
    }
    pred_path = tmp_path / "pred.json"
    ens_path = tmp_path / "ens.json"
    pred_path.write_text(json.dumps(pred), encoding="utf-8")
    ens_path.write_text(json.dumps(ens), encoding="utf-8")
    before = hashlib.sha256(pred_path.read_bytes()).hexdigest()

    forecasts = ep.load_sealed_forecasts(pred_path, ens_path)
    score = ep.score_forecasts(forecasts, winner_index=0)

    assert score["fecha_sorteo"] == "2026-10-17"
    assert score["candidata"]["rank"] == 1
    assert score["ensamble_v2"]["rank"] == 1
    assert score["candidata"]["mbits"] == pytest.approx(0.0)
    assert score["candidata"]["hit_top15"] is True
    assert hashlib.sha256(pred_path.read_bytes()).hexdigest() == before


def test_no_puntua_si_el_pronostico_no_esta_sellado(tmp_path):
    pred_path = tmp_path / "pred.json"
    pred_path.write_text(json.dumps({"estado": "borrador"}), encoding="utf-8")
    ens_path = tmp_path / "ens.json"
    ens_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="sellado"):
        ep.load_sealed_forecasts(pred_path, ens_path)


def test_rechaza_vector_invalido_y_ganador_fuera_de_rango():
    with pytest.raises(ValueError, match="38"):
        ep.validate_probabilities([0.5, 0.5])

    with pytest.raises(ValueError, match="ganador"):
        ep.score_forecasts({"candidata": [1 / 38] * 38, "ensamble_v2": [1 / 38] * 38}, 38)


def test_exige_fecha_igual_entre_candidata_y_ensamble(tmp_path):
    pred_path = tmp_path / "pred.json"
    pred_path.write_text(json.dumps({
        "estado": "SELLADO_PENDIENTE_DE_RESULTADO", "fecha_sorteo": "2026-10-17",
        "hora_sorteo": "08:00 America/Caracas",
        "probabilidades_candidata": [1 / 38] * 38,
    }), encoding="utf-8")
    ens_path = tmp_path / "ens.json"
    ens_path.write_text(json.dumps({
        "fecha": "2026-10-16", "animales": [{"idx": i, "prob": 1 / 38} for i in range(38)],
    }), encoding="utf-8")

    with pytest.raises(ValueError, match="fecha"):
        ep.load_sealed_forecasts(pred_path, ens_path)


def test_sello_ag14_enlaza_huella_y_probabilidades(tmp_path):
    probabilities = [1 / 38] * 38
    pred_path = tmp_path / "pred.json"
    ens_path = tmp_path / "ens.json"
    seal_path = tmp_path / "ag14.json"
    pred_path.write_text(json.dumps({
        "estado": "SELLADO_PENDIENTE_DE_RESULTADO", "fecha_sorteo": "2026-10-17",
        "hora_sorteo": "08:00 America/Caracas",
        "probabilidades_candidata": probabilities,
    }), encoding="utf-8")
    ens_path.write_text(json.dumps({
        "fecha": "2026-10-17", "hora": 0, "winner": None,
        "animales": [{"idx": i, "prob": 1 / 38} for i in range(38)],
    }), encoding="utf-8")
    digest = hashlib.sha256(pred_path.read_bytes()).hexdigest()
    seal_path.write_text(json.dumps({
        "estado": "SELLADO_PENDIENTE_DE_RESULTADO", "fecha_sorteo": "2026-10-17",
        "sha256_origen": digest, "probabilidades_ag14": probabilities,
    }), encoding="utf-8")

    pair = ep.load_sealed_forecasts(pred_path, ens_path, seal_path)
    assert pair["huellas"]["pronostico_candidata"] == digest
    assert "sello_candidata" in pair["huellas"]

    seal_path.write_text(json.dumps({
        "estado": "SELLADO_PENDIENTE_DE_RESULTADO", "fecha_sorteo": "2026-10-17",
        "sha256_origen": "0" * 64, "probabilidades_ag14": probabilities,
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="huella"):
        ep.load_sealed_forecasts(pred_path, ens_path, seal_path)


def test_exige_hora_igual_entre_candidata_y_ensamble(tmp_path):
    pred_path = tmp_path / "pred.json"
    pred_path.write_text(json.dumps({
        "estado": "SELLADO_PENDIENTE_DE_RESULTADO", "fecha_sorteo": "2026-10-17",
        "hora_sorteo": "08:00 America/Caracas", "probabilidades_candidata": [1 / 38] * 38,
    }), encoding="utf-8")
    ens_path = tmp_path / "ens.json"
    ens_path.write_text(json.dumps({
        "fecha": "2026-10-17", "hora": 1,
        "animales": [{"idx": i, "prob": 1 / 38} for i in range(38)],
    }), encoding="utf-8")

    with pytest.raises(ValueError, match="hora"):
        ep.load_sealed_forecasts(pred_path, ens_path)


def test_resultado_requiere_dos_dominios_y_capturas_con_hash(tmp_path):
    forecasts = {"fecha_sorteo": "2026-10-17", "hora_sorteo": "08:00 America/Caracas"}
    first = tmp_path / "tuazar.html"
    second = tmp_path / "lotto.html"
    first.write_text("17/10 Lotto Activo 8:00 — 12", encoding="utf-8")
    second.write_text("Resultado confirmado: 12", encoding="utf-8")
    sources = [
        {"nombre": "TuAzar", "url": "https://tuazar.com.ve/loteria/animalitos/resultados/semana/",
         "archivo": first.name, "capturado_utc": "2026-10-17T12:10:00Z",
         "sha256": hashlib.sha256(first.read_bytes()).hexdigest(), "ganador_confirmado": "12"},
        {"nombre": "Lotto Activo", "url": "https://lottoactivo.com/historial/",
         "archivo": second.name, "capturado_utc": "2026-10-17T12:11:00Z",
         "sha256": hashlib.sha256(second.read_bytes()).hexdigest(), "ganador_confirmado": "12"},
    ]
    outcome_path = tmp_path / "resultado.json"
    outcome_path.write_text(json.dumps({
        "fecha_sorteo": "2026-10-17", "hora": 8, "ganador": "12", "fuentes": sources,
    }), encoding="utf-8")

    result = ep.score_evidenced_result({
        **forecasts, "candidata_nombre": "ag12+exposición", "candidata": [1 / 38] * 38,
        "ensamble_v2": [1 / 38] * 38, "huellas": {"pred": "ab"},
    }, outcome_path)
    assert result["estado"] == "PUNTUADO_CON_EVIDENCIA_ADJUNTA"
    assert result["ganador"] == "12"
    assert result["delta_mbits"] == pytest.approx(0.0)
    assert len(result["fuentes"]) == 2

    sources[1]["url"] = "https://www.tuazar.com.ve/otra-pagina"
    outcome_path.write_text(json.dumps({
        "fecha_sorteo": "2026-10-17", "hora": 8, "ganador": "12", "fuentes": sources,
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="independientes"):
        ep.validate_result_evidence(outcome_path, forecasts)

    sources[1]["url"] = "https://lottoactivo.com/historial/"
    sources[1]["ganador_confirmado"] = "13"
    outcome_path.write_text(json.dumps({
        "fecha_sorteo": "2026-10-17", "hora": 8, "ganador": "12", "fuentes": sources,
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="mismo ganador"):
        ep.validate_result_evidence(outcome_path, forecasts)
