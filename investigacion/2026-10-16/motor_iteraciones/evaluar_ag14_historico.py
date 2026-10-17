# -*- coding: utf-8 -*-
"""Reprecio descriptivo de Ag14 sobre matrices 2026 ya congeladas.

No recalibra modelos ni reemplaza la prueba prospectiva. El tramo "fresco" ya se
había analizado para ag12/RD y parte de sus días ya se había visto en la sombra de
exposición; por eso este informe es retrospectivo, aunque los vectores base fueran
walk-forward y se hubieran calculado antes del resultado correspondiente.
"""
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "herramientas" / "exploracion" / "ag12_2026_2026-10-07"
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT / "herramientas" / "rdint"))
sys.path.insert(0, str(ROOT))

import lotto_eval as LE  # noqa: E402
import experimentos as E  # noqa: E402
from datos import ANIMALES, sin_acentos  # noqa: E402


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _ic(pairs):
    return E.ic90_jornadas(pairs)


def _sumar(nombre, filas):
    fichas = [0, 2, 2, 2, 1, 1] + [0] * 33
    n = len(filas)
    out = {"tramo": nombre, "n": n, "jornadas": len({x["fecha"] for x in filas})}
    for key, title in (("ens", "ensamble_v2"), ("ag12rd", "ag12+RD"), ("ag14", "ag14")):
        modelo = [x[key] for x in filas]
        out[title] = {
            "mbits_medios": round(float(np.mean([x["mbits"] for x in modelo])), 2),
            "top3": sum(x["rank"] <= 3 for x in modelo),
            "top5": sum(x["rank"] <= 5 for x in modelo),
            "top15": sum(x["rank"] <= 15 for x in modelo),
            "retorno_top5_pp_ficha": round(float(np.mean([x["retorno_top5"] for x in modelo])), 2),
        }
    for candidate, base in (("ag14", "ens"), ("ag14", "ag12rd")):
        out[f"delta_mbits_{candidate}_menos_{base}"] = _ic([
            (x["fecha"], x[candidate]["mbits"] - x[base]["mbits"]) for x in filas])
    for k in (3, 5, 15):
        out[f"delta_top{k}_pp_ag14_menos_ensamble"] = _ic([
            (x["fecha"], float(x["ag14"]["rank"] <= k) - float(x["ens"]["rank"] <= k))
            for x in filas])
        v = out[f"delta_top{k}_pp_ag14_menos_ensamble"]
        if v:
            v["media"] = round(100 * v["media"], 2)
            if v["ic90"] is not None:
                v["ic90"] = [round(100 * z, 2) for z in v["ic90"]]
    out["delta_retorno_top5_pp_ficha_ag14_menos_ensamble"] = _ic([
        (x["fecha"], x["ag14"]["retorno_top5"] - x["ens"]["retorno_top5"])
        for x in filas])
    return out


def ejecutar():
    ens = np.load(DATA / "P_ens_fresco.npy").astype(float)
    ag12 = np.load(DATA / "P_ag12_V1_fresco.npy").astype(float)
    assert ens.shape == ag12.shape and ens.shape[1] == E.K

    raw_rows = []
    for line in (DATA / "hist_ext.txt").read_text(encoding="utf-8").splitlines():
        p = line.split()
        if len(p) == 3 and p[2] in LE.IDX:
            raw_rows.append((p[0], int(p[1]), LE.IDX[p[2]]))
    raw_rows.sort(key=lambda x: (x[0], x[1]))
    d = LE.cargar(str(DATA / "hist_ext.txt"))
    assert len(raw_rows) == len(d) == 12760
    assert len(ens) == len(ag12) == len(raw_rows) - 9357 == 3403

    correction_file = ROOT / "herramientas" / "correccion_historial_2026-09-29.json"
    changes = {x["antes"]: x["despues"] for x in
               json.loads(correction_file.read_text(encoding="utf-8"))["cambios"]}
    touched = ({x.split()[0] for x in changes} |
               {x.split()[0] for x in changes.values()})
    aligned = []
    for gi, (old_date, hour, winner) in enumerate(raw_rows):
        key = f"{old_date} {hour} {LE.POS[winner]}"
        date = changes.get(key, key).split()[0]
        excluded = old_date in touched or date in touched
        aligned.append((gi, old_date, date, hour, winner, excluded))

    rd = {}
    with (ROOT / "datos_multiloteria" / "rdint_hist.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            code = ANIMALES.get(sin_acentos(row["animal"]))
            if code is not None:
                rd[(row["fecha"], int(row["hora"][:2]) - 8)] = code
    with (DATA / "fresco_rd.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rd[(row["fecha"], int(row["hora"]))] = row["codigo"]

    rows = []
    fichas = [0, 2, 2, 2, 1, 1] + [0] * 33
    for j, (gi, old_date, date, hour, winner, excluded) in enumerate(aligned[9357:]):
        ens_p = ens[j].tolist()
        ag12_p = ag12[j].tolist()
        ag12rd_p, _ = E.con_rd(ag12_p, rd, date, hour)
        ag14_p = E.exposicion(ag12rd_p, date, hour)
        cod = rd.get((date, hour - 1)) if hour > 0 else None

        def score(p):
            norm = [max(float(z), 1e-9) for z in p]
            total = sum(norm)
            mbits = 1000 * np.log2(norm[winner] / total * E.K)
            order = sorted(range(E.K), key=lambda i: (-norm[i], i))
            rank = order.index(winner) + 1
            displayed = E.cambiar15(order, cod) if cod in E.IDX else order
            payout_rank = displayed.index(winner) + 1
            net = 100 * (E.PAGO * fichas[payout_rank] - sum(fichas)) / sum(fichas)
            return {"mbits": float(mbits), "rank": rank, "retorno_top5": float(net)}

        rows.append({"global_idx": gi, "fecha": date, "fecha_original": old_date,
                     "hora": hour, "excluido_correccion": excluded,
                     "ens": score(ens_p), "ag12rd": score(ag12rd_p), "ag14": score(ag14_p)})

    replica = [x for x in rows if x["global_idx"] < 12511 and not x["excluido_correccion"]
               and "2026-01-01" <= x["fecha"] <= "2026-09-16"]
    fresh = [x for x in rows if x["global_idx"] >= 12511 and not x["excluido_correccion"]]
    assert len(replica) == 2959 and len(fresh) == 249
    result = {
        "estado": "RETROSPECTIVO_DESCRIPTIVO_NO_PRUEBA_VIRGEN",
        "metodo": "Ag12 V1 congelado -> con_rd existente -> exposicion.aplicar existente",
        "nota": "El tramo fresco ya fue revisado para ag12/RD y se solapa con la sombra de exposición desde 2026-10-02. No cuenta como decisión prospectiva Ag14 ni permite reajustar parámetros.",
        "fuentes_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in (
            DATA / "P_ens_fresco.npy", DATA / "P_ag12_V1_fresco.npy", DATA / "hist_ext.txt",
            DATA / "fresco_rd.csv", ROOT / "datos_multiloteria" / "rdint_hist.csv", correction_file)},
        "replica_ya_observada": _sumar("Réplica 2026, enero–16 septiembre (ya observada)", replica),
        "fresco_ya_reportado": _sumar("Fresco, 16 septiembre–7 octubre (ya reportado)", fresh),
        "regla_prospectiva": "No se decide con estos tramos; el preregistro Ag14 exige una sola mirada con n=931 sorteos futuros válidos.",
    }
    out = Path(__file__).with_name("resultado_ag14_historico.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(ejecutar(), ensure_ascii=False, indent=2))
