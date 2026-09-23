# -*- coding: utf-8 -*-
"""Hilo 7: PRUEBA CIEGA, una sola corrida (PREREGISTRO_rdint_cruzado.md, enmienda 2026-09-23).

E1 (RD Int): B0 = secuencia_v3 y B1 = modelo.cruzado, walk-forward con los datos truncados
    al primer sorteo 'desc'. Métricas SOLO sobre las filas 'test' (2025-07-01 .. 2026-04-12).
H4 (Lotto Activo): logit congelado de ensamble_v2 (calor_cache.npz) + RD de antes de h:00,
    coeficientes walk-forward. Métricas sobre las filas LA con fecha en [2025-07-01, 2025-12-17).

Uso: python herramientas/rdint/prueba_ciega.py   (anota el resultado en registro_final.jsonl)
"""
import json, os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.dirname(AQUI)
sys.path.insert(0, HERR); sys.path.insert(0, AQUI)
import lotto_eval as LE
import datos as DT
import modelo as MB
import correr_modelo as CM
import sonda_inversa as SI

SALIDA_MD = os.path.join(HERR, "resultados", "hilo7_prueba_ciega.md")
INI_TEST, FIN_LA = "2025-07-01", "2025-12-17"
rng = np.random.default_rng(20260923)
L = []


def di(s=""):
    print(s, flush=True); L.append(s)


def ic(v, dia):
    m, lo, hi = CM.boot_media(v, dia, rng)
    return "%+.2f [%+.2f, %+.2f]" % (m, lo, hi), lo


def e1():
    rd, la_h, la_h1, la_hoy, tramo = DT.cargar()
    n_fin = int(np.flatnonzero(tramo == "desc")[0])
    assert set(np.unique(tramo[:n_fin])) <= {"cal", "dev", "test"}
    rd = rd.prefijo(n_fin)
    P0, P1, hist = MB.predecir(CM.modelo_b0("secuencia_v3"), rd, la_h[:n_fin], la_h1[:n_fin],
                               la_hoy[:n_fin], CM.DESDE)
    y = rd.seq[CM.DESDE:]; te = tramo[CM.DESDE:n_fin] == "test"
    P0, P1, y, dia = P0[te], P1[te], y[te], rd.dia[CM.DESDE:][te]
    d = CM.mbits(P1, y) - CM.mbits(P0, y)
    top3, r3, r5 = CM.apuestas(P1, y)
    _, r3b0, _ = CM.apuestas(P0, y)
    jug = P1 * LE.PAGO >= 1.10                         # E2 literal: 1 ficha plana
    fichas = jug.sum(1); gana = jug[np.arange(len(y)), y]
    di("## E1 — RD Int (tramo test %s .. %s, %d sorteos, %d días)"
       % (INI_TEST, rd.fecha[-1], len(y), len(np.unique(dia))))
    txt, lo = ic(d, dia)
    di("- Δ mbits B1−B0: %s" % txt)
    di("- mbits B0 frente al uniforme: %+.1f · B1: %+.1f"
       % (CM.mbits(P0, y).mean(), CM.mbits(P1, y).mean()))
    t3 = top3.mean()
    di("- Top-3 B1: %.2f %% (%d/%d) · Top-3 B0: %.2f %%"
       % (100 * t3, top3.sum(), len(y), 100 * np.mean(CM.apuestas(P0, y)[0])))
    di("- Retorno por ficha Top-3 plano B1: %s %% · B0: %s %%"
       % (ic(100 * r3, dia)[0], ic(100 * r3b0, dia)[0]))
    di("- Retorno por ficha Top-5 escalonado B1: %s %%" % ic(100 * r5, dia)[0])
    ret_e2 = (LE.PAGO * gana.sum() - fichas.sum()) / max(fichas.sum(), 1)
    di("- E2 literal (1 ficha si p·30 ≥ 1,10): %+.1f %% sobre %d fichas; sin jugar %.1f %% de sorteos"
       % (100 * ret_e2, fichas.sum(), 100 * np.mean(fichas == 0)))
    di("- Coeficientes B1 al final: %s" % np.round(hist[-1][1], 3).tolist())
    ok = t3 > 0.10 and lo > 0
    di("- **VEREDICTO E1: %s** (Top-3 > 10 %% y Δ mbits con IC95 > 0)" % ("PASA" if ok else "FALLA"))
    return ok, {"n": int(len(y)), "top3": float(t3), "dmbits": float(d.mean()), "dmbits_lo": float(lo),
                "ret_top3": float(r3.mean()), "ret_top5": float(r5.mean()), "ret_e2": float(ret_e2)}


def h4():
    la = LE.cargar()
    z = np.load(SI.CACHE_LA)
    fin = LE.CORTE_FIJO
    assert np.array_equal(z["y"], la.seq[SI.DESDE_LA:fin])
    P = LE.normalizar(z["P"]); y = z["y"]
    fechas = list(la.fecha[SI.DESDE_LA:fin]); hora = la.hora[SI.DESDE_LA:fin]; dia = la.dia[SI.DESDE_LA:fin]
    rd, _, _, _, tramo = DT.cargar()
    n_fin = int(np.flatnonzero(tramo == "desc")[0])
    rdd = {}
    for f, h, s in zip(rd.fecha[:n_fin], rd.hora[:n_fin], rd.seq[:n_fin]):
        rdd.setdefault(f, {})[int(h)] = int(s)
    X, _ = SI.features(fechas, hora, rdd)
    P1, hist = MB.cruzado(P, X, y)
    sel = np.array([INI_TEST <= f < FIN_LA for f in fechas])
    d = CM.mbits(P1[sel], y[sel]) - CM.mbits(P[sel], y[sel])
    di("\n## H4 — Lotto Activo con RD de antes de h:00 (%s .. %s, %d sorteos)"
       % (INI_TEST, max(np.array(fechas)[sel]), sel.sum()))
    txt, lo = ic(d, dia[sel])
    di("- Δ mbits: %s" % txt)
    t0 = CM.apuestas(P[sel], y[sel]); t1 = CM.apuestas(P1[sel], y[sel])
    di("- Top-3 ensamble: %.2f %% · con RD: %.2f %%" % (100 * t0[0].mean(), 100 * t1[0].mean()))
    di("- Retorno Top-5 escalonado ensamble: %+.1f %% · con RD: %+.1f %%"
       % (100 * t0[2].mean(), 100 * t1[2].mean()))
    di("- Coeficientes al final: %s" % np.round(hist[-1][1], 3).tolist())
    ok = lo > 0
    di("- **VEREDICTO H4: %s** (Δ mbits con IC95 > 0)" % ("PASA" if ok else "FALLA"))
    return ok, {"n": int(sel.sum()), "dmbits": float(d.mean()), "dmbits_lo": float(lo),
                "top3_base": float(t0[0].mean()), "top3_rd": float(t1[0].mean())}


def main():
    di("# Hilo 7 — prueba ciega (una sola corrida, %s)\n" % time.strftime("%Y-%m-%d %H:%M"))
    ok1, r1 = e1()
    ok4, r4 = h4()
    with open(SALIDA_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with open(LE.REGISTRO_FINAL, "a", encoding="utf-8") as f:
        f.write(json.dumps({"cuando": time.strftime("%Y-%m-%d %H:%M:%S"), "modelo": "hilo7 rdint_cruzado",
                            "e1": dict(r1, pasa=ok1), "h4": dict(r4, pasa=ok4)}) + "\n")


if __name__ == "__main__":
    main()
