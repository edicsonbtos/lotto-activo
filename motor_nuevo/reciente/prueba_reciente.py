# -*- coding: utf-8 -*-
"""Segunda prueba ciega de ag12 en la época reciente: filas [9357, 12511) del historial (ver PREREGISTRO_RECIENTE.md).
Una sola corrida: queda en registro_reciente.jsonl. Bonferroni k=4."""
import json, os, subprocess, sys, hashlib
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
MN = os.path.dirname(AQUI); WT = os.path.dirname(MN)
sys.path.insert(0, os.path.join(WT, "herramientas")); sys.path.insert(0, MN)
import lotto_eval as LE  # noqa: E402
import arnes as A  # noqa: E402

DESDE, HASTA, KBONF = 9357, 12511, 4
EXCLUIR = {"2025-12-15", "2025-12-16", "2025-12-17", "2025-12-18", "2025-12-19", "2025-12-25", "2025-12-26",
           "2025-12-27", "2026-01-01", "2026-01-02", "2026-01-03"}
CAND = {"ag12_V1": {"variante": "V1"}, "ag12_V0": {"variante": "V0"}}
REG = os.path.join(AQUI, "registro_reciente.jsonl")

HIJO = r'''
import sys, os, importlib.util, numpy as np
sys.path.insert(0, {wt!r}); sys.path.insert(0, os.path.join({wt!r}, "herramientas"))
import lotto_eval as LE
carpeta = os.path.join({mn!r}, "ag12_transiciones"); sys.path.insert(0, carpeta)
spec = importlib.util.spec_from_file_location("modelo_cand", os.path.join(carpeta, "modelo.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
D = LE.cargar().prefijo({hasta})
m = mod.Modelo(**{kw!r}); m.P_ens = np.load({pens!r})
np.save({salida!r}, LE.normalizar(m.predecir(D, {desde})))
'''


def main():
    D = LE.cargar().prefijo(HASTA)
    assert len(D) == HASTA, len(D)
    y = np.asarray(D.seq[DESDE:]); dia = np.asarray(D.dia[DESDE:])
    ok = np.array([f not in EXCLUIR for f in D.fecha[DESDE:]])
    print(f"filas {DESDE}..{HASTA}: {len(y)}; puntuadas {ok.sum()} ({D.fecha[DESDE]}..{D.fecha[-1]})", flush=True)
    rp = os.path.join(AQUI, "P_ens_reciente.npy")
    m = LE.cargar_modelo(os.path.join(WT, "herramientas", "modelos", "ensamble_v2.py"))
    Pens = LE.normalizar(m.predecir(D, DESDE)); np.save(rp, Pens)
    y, dia, Pe = y[ok], dia[ok], Pens[ok]
    mb_e = A.mbits_fila(Pe, y); pos_e = A.puestos(Pe, y)
    out = {"n": int(len(y)), "k_bonferroni": KBONF, "commit_modelos": "c4a2b17",
           "ensamble": {"mbits": float(mb_e.mean()), "top3": float((pos_e <= 3).mean()), "top5": float((pos_e <= 5).mean()),
                        "top15": float((pos_e <= 15).mean()), "ret_t5": float(A.retorno_t5(pos_e).mean())},
           "resultados": {}}
    print("ensamble:", out["ensamble"], flush=True)
    alfa = 0.05 / KBONF
    for nombre, kw in CAND.items():
        sal = os.path.join(AQUI, f"P_{nombre}.npy")
        subprocess.run([sys.executable, "-c", HIJO.format(wt=WT, mn=MN, hasta=HASTA, kw=kw, pens=rp,
                                                          salida=sal, desde=DESDE)], check=True)
        P = np.load(sal)[ok]
        d = A.mbits_fila(P, y) - mb_e
        _, inv = np.unique(dia, return_inverse=True)
        sums = np.bincount(inv, weights=d); cnt = np.bincount(inv)
        rng = np.random.default_rng(7); B = rng.integers(0, len(sums), size=(4000, len(sums)))
        mm = sums[B].sum(1) / cnt[B].sum(1)
        lo, hi = np.percentile(mm, [100 * alfa / 2, 100 * (1 - alfa / 2)])
        pos = A.puestos(P, y)
        r = {"delta_mbits": float(d.mean()), "ic_bonferroni": [float(lo), float(hi)], "pasa": bool(lo > 0),
             "ic95_sin_corregir": list(A.ic_bloques(d, dia))[1:],
             "top3": float((pos <= 3).mean()), "top5": float((pos <= 5).mean()), "top15": float((pos <= 15).mean()),
             "delta_ret_t5": A.ic_bloques(A.retorno_t5(pos) - A.retorno_t5(pos_e), dia)}
        out["resultados"][nombre] = r
        print(nombre, json.dumps(r, ensure_ascii=False), flush=True)
    with open(REG, "a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
    json.dump(out, open(os.path.join(AQUI, "resultado_reciente.json"), "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    if os.path.exists(REG):
        sys.exit("Esta prueba ya se corrió (registro_reciente.jsonl existe). No se repite.")
    main()
