# -*- coding: utf-8 -*-
"""Puntúa pronósticos congelados contra un resultado con dos fuentes auditables.

Esta herramienta es de investigación: solo lee pronósticos y capturas, y crea un
registro nuevo. Nunca actualiza el historial, la mesa ni los archivos sellados.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

CODIGOS = ("0", "00") + tuple(str(i) for i in range(1, 37))
K = len(CODIGOS)
PAGO = 30
FICHAS = (0, 2, 2, 2, 1, 1) + (0,) * (K - 5)


def _leer_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_probabilities(probabilities, label="pronóstico"):
    if not isinstance(probabilities, (list, tuple)) or len(probabilities) != K:
        raise ValueError(f"{label} debe tener {K} probabilidades")
    values = []
    for value in probabilities:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{label} contiene una probabilidad no numérica")
        value = float(value)
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{label} debe contener probabilidades finitas mayores que cero")
        values.append(value)
    if abs(sum(values) - 1.0) > 1e-6:
        raise ValueError(f"{label} debe sumar 1 (tolerancia 1e-6)")
    return values


def load_sealed_forecasts(prediction_path, ensemble_path, candidate_seal_path=None):
    """Carga el par sellado y valida su fecha, estructura y huellas de origen."""
    prediction_path = Path(prediction_path)
    ensemble_path = Path(ensemble_path)
    prediction = _leer_json(prediction_path)
    ensemble = _leer_json(ensemble_path)
    if not str(prediction.get("estado", "")).startswith("SELLADO"):
        raise ValueError("el pronóstico candidato no está sellado")
    if ensemble.get("winner") is not None:
        raise ValueError("el archivo del ensamble ya contiene un resultado; no es un pronóstico ciego")
    date = prediction.get("fecha_sorteo")
    if not date or ensemble.get("fecha") != date:
        raise ValueError("la fecha del pronóstico candidato y del ensamble debe coincidir")
    try:
        scheduled_hour = int(str(prediction["hora_sorteo"]).split(":", 1)[0])
        expected_slot = scheduled_hour - 8
        if not 0 <= expected_slot <= 11 or int(ensemble["hora"]) != expected_slot:
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise ValueError("la hora del pronóstico candidato y del ensamble debe coincidir")

    candidate = validate_probabilities(prediction.get("probabilidades_candidata"), "candidata")
    animals = ensemble.get("animales")
    if not isinstance(animals, list) or len(animals) != K:
        raise ValueError(f"el pronóstico del ensamble debe incluir {K} animales")
    by_index = {}
    for animal in animals:
        idx = animal.get("idx")
        if isinstance(idx, bool) or not isinstance(idx, int) or idx in by_index or not 0 <= idx < K:
            raise ValueError("el ensamble tiene índices duplicados o fuera de rango")
        by_index[idx] = animal.get("prob")
    if set(by_index) != set(range(K)):
        raise ValueError("el ensamble debe incluir todos los índices de animal 0–37")
    baseline = validate_probabilities([by_index[i] for i in range(K)], "ensamble_v2")

    seal_path = None
    if candidate_seal_path is not None:
        seal_path = Path(candidate_seal_path)
        seal = _leer_json(seal_path)
        if not str(seal.get("estado", "")).startswith("SELLADO"):
            raise ValueError("el sello de la candidata no está sellado")
        if seal.get("fecha_sorteo") != date:
            raise ValueError("la fecha del sello de candidata no coincide")
        source_hash = seal.get("sha256_origen")
        if not source_hash or _sha256(prediction_path) != source_hash:
            raise ValueError("la huella del pronóstico candidato no coincide con el sello")
        sealed_candidate = validate_probabilities(seal.get("probabilidades_ag14"), "Ag14 sellado")
        if any(abs(a - b) > 1e-12 for a, b in zip(candidate, sealed_candidate)):
            raise ValueError("las probabilidades candidatas difieren del sello Ag14")

    return {
        "fecha_sorteo": date,
        "hora_sorteo": prediction.get("hora_sorteo"),
        "candidata_nombre": prediction.get("candidata", "candidata"),
        "candidata": candidate,
        "ensamble_v2": baseline,
        "huellas": {
            "pronostico_candidata": _sha256(prediction_path),
            "pronostico_ensamble": _sha256(ensemble_path),
            **({"sello_candidata": _sha256(seal_path)} if seal_path else {}),
        },
    }


def _score_one(probabilities, winner_index):
    order = sorted(range(K), key=lambda index: (-probabilities[index], index))
    rank = order.index(winner_index) + 1
    stake = FICHAS[rank] if rank < len(FICHAS) else 0
    net_pct = 100.0 * (PAGO * stake - sum(FICHAS)) / sum(FICHAS)
    return {
        "rank": rank,
        "mbits": 1000.0 * math.log2(probabilities[winner_index] * K),
        "hit_top3": rank <= 3,
        "hit_top5": rank <= 5,
        "hit_top15": rank <= 15,
        "retorno_top5_pp_ficha": net_pct,
    }


def score_forecasts(forecasts, winner_index):
    if isinstance(winner_index, bool) or not isinstance(winner_index, int) or not 0 <= winner_index < K:
        raise ValueError("índice de ganador inválido; debe estar entre 0 y 37")
    candidate = validate_probabilities(forecasts.get("candidata"), "candidata")
    baseline = validate_probabilities(forecasts.get("ensamble_v2"), "ensamble_v2")
    candidate_score = _score_one(candidate, winner_index)
    baseline_score = _score_one(baseline, winner_index)
    return {
        "fecha_sorteo": forecasts.get("fecha_sorteo"),
        "ganador": CODIGOS[winner_index],
        "candidata_nombre": forecasts.get("candidata_nombre", "candidata"),
        "candidata": candidate_score,
        "ensamble_v2": baseline_score,
        "delta_mbits": candidate_score["mbits"] - baseline_score["mbits"],
        "delta_top5_pp_ficha": (candidate_score["retorno_top5_pp_ficha"]
                                - baseline_score["retorno_top5_pp_ficha"]),
    }


def validate_result_evidence(outcome_path, forecasts):
    """Exige fecha/hora y dos capturas independientes cuya huella se pueda verificar."""
    outcome_path = Path(outcome_path)
    outcome = _leer_json(outcome_path)
    if outcome.get("fecha_sorteo") != forecasts.get("fecha_sorteo"):
        raise ValueError("la fecha del resultado no coincide con el pronóstico sellado")
    scheduled_hour = str(forecasts.get("hora_sorteo", "")).split(":", 1)[0]
    try:
        raw_hour = outcome["hora"]
        if isinstance(raw_hour, bool) or not str(raw_hour).isdigit():
            raise ValueError
        result_hour = int(raw_hour)
        if int(scheduled_hour) != result_hour:
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise ValueError("la hora del resultado no coincide con la hora del pronóstico")

    winner = str(outcome.get("ganador", ""))
    if winner not in CODIGOS:
        raise ValueError("código ganador inválido")
    sources = outcome.get("fuentes")
    if not isinstance(sources, list) or len(sources) < 2:
        raise ValueError("se requieren al menos dos capturas de fuentes independientes")
    domains = set()
    checked = []
    confirmed_winners = set()
    scheduled_utc = datetime.fromisoformat(
        f"{forecasts['fecha_sorteo']}T{result_hour:02d}:00:00-04:00"
    ).astimezone(timezone.utc)
    for source in sources:
        url = source.get("url", "")
        parsed_url = urlsplit(url)
        domain = (parsed_url.hostname or "").lower().removeprefix("www.")
        if parsed_url.scheme not in {"http", "https"} or not domain or domain in domains:
            raise ValueError("las fuentes de resultado deben tener dominios independientes")
        domains.add(domain)
        raw_path = Path(source.get("archivo", ""))
        if not raw_path.is_absolute():
            raw_path = outcome_path.parent / raw_path
        expected_hash = source.get("sha256", "")
        if not raw_path.is_file() or not expected_hash or _sha256(raw_path) != expected_hash:
            raise ValueError("la captura de una fuente falta o su SHA-256 no coincide")
        try:
            captured = datetime.fromisoformat(str(source["capturado_utc"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            raise ValueError("cada captura debe registrar una hora de consulta UTC válida")
        if captured.tzinfo is None or captured.utcoffset().total_seconds() != 0:
            raise ValueError("la hora de consulta de cada captura debe estar en UTC")
        if captured.astimezone(timezone.utc) < scheduled_utc:
            raise ValueError("una captura del resultado no puede preceder al sorteo")
        confirmed = str(source.get("ganador_confirmado", ""))
        if confirmed not in CODIGOS:
            raise ValueError("cada fuente debe registrar el ganador que se confirmó manualmente")
        confirmed_winners.add(confirmed)
        checked.append({
            "nombre": source.get("nombre", domain), "url": url,
            "capturado_utc": source["capturado_utc"], "sha256": expected_hash,
            "ganador_confirmado": confirmed,
        })
    if len(confirmed_winners) != 1 or next(iter(confirmed_winners)) != winner:
        raise ValueError("las dos fuentes deben confirmar el mismo ganador del registro")
    return {"fecha_sorteo": outcome["fecha_sorteo"], "hora": result_hour,
            "ganador": winner, "fuentes": checked,
            "huella_resultado": _sha256(outcome_path)}


def score_evidenced_result(forecasts, outcome_path):
    evidence = validate_result_evidence(outcome_path, forecasts)
    scored = score_forecasts(forecasts, CODIGOS.index(evidence["ganador"]))
    return {"estado": "PUNTUADO_CON_EVIDENCIA_ADJUNTA", **scored,
            "hora": evidence["hora"], "fuentes": evidence["fuentes"],
            "huella_resultado": evidence["huella_resultado"],
            "huellas_pronostico": forecasts["huellas"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prediccion", required=True, type=Path)
    parser.add_argument("--ensamble", required=True, type=Path)
    parser.add_argument("--resultado", required=True, type=Path,
                        help="JSON con ganador y dos capturas (URL, hora y SHA-256)")
    parser.add_argument("--sello-candidata", type=Path,
                        help="sello Ag14 opcional para validar origen y probabilidades")
    parser.add_argument("--salida", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.salida.exists():
        parser.error(f"la salida ya existe y no se sobrescribirá: {args.salida}")
    forecasts = load_sealed_forecasts(args.prediccion, args.ensamble, args.sello_candidata)
    scored = score_evidenced_result(forecasts, args.resultado)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(scored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(scored, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
