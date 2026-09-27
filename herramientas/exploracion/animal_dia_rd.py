# -*- coding: utf-8 -*-
""""Animal del día" en RD Internacional (2026-09-27). Mismo método que animal_dia.py (Lotto Activo):
Top-k del modelo de RD (B1, el de producción) en el PRIMER sorteo del día (8:30, ya con LA 8:00) → ¿sale alguno hoy?
Datos: herramientas/rdint/cache_todo.npz (walk-forward). Ver PREREGISTRO_animal_dia_rd.md.

  python animal_dia_rd.py dev | ciega
"""
import json, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI); sys.path.insert(0, os.path.dirname(AQUI))
from animal_dia import azar  # noqa: E402

REG = os.path.join(AQUI, "registro_animal_dia_rd.jsonl")
UMBRAL_Z = 2.39


def evaluar(P, y, h, dia, sel):
    res = {k: {"ac": 0, "esp": 0.0, "var": 0.0, "fichas": 0, "cobro": 0, "dias": 0, "pd": []} for k in (1, 2, 3)}
    cortes = np.r_[0, np.nonzero(np.diff(dia))[0] + 1, len(dia)]
    for a, b in zip(cortes[:-1], cortes[1:]):
        if not sel[a] or not sel[b - 1] or b - a < 10 or h[a] != 0:
            continue
        hoy = y[a:b]; D = len(set(hoy.tolist())); o = np.argsort(-P[a], kind="stable")
        for k, r in res.items():
            hit = int(np.isin(o[:k], hoy).any()); p0 = azar(D, k); f = c = 0
            for x in o[:k]:
                pos = np.nonzero(hoy == x)[0]
                if len(pos): f += pos[0] + 1; c += 30
                else: f += len(hoy)
            r["ac"] += hit; r["esp"] += p0; r["var"] += p0 * (1 - p0); r["dias"] += 1
            r["fichas"] += f; r["cobro"] += c; r["pd"].append((c - f, f))
    out = {}
    rng = np.random.default_rng(7)
    for k, r in res.items():
        arr = np.array(r["pd"], float); I = rng.integers(0, len(arr), (4000, len(arr)))
        rb = arr[I, 0].sum(1) / arr[I, 1].sum(1)
        out[k] = {"dias": r["dias"], "acierto": r["ac"] / r["dias"], "azar": r["esp"] / r["dias"],
                  "z": (r["ac"] - r["esp"]) / r["var"] ** 0.5, "retorno_ficha": (r["cobro"] - r["fichas"]) / r["fichas"],
                  "ret_ic95": [float(np.percentile(rb, 2.5)), float(np.percentile(rb, 97.5))]}
        print(f"  k={k}: {out[k]['acierto']*100:5.1f} % vs azar {out[k]['azar']*100:5.1f} % (z {out[k]['z']:+.2f}, "
              f"{r['dias']} días) · retorno/ficha {out[k]['retorno_ficha']*100:+5.1f} % "
              f"[{out[k]['ret_ic95'][0]*100:+.1f}; {out[k]['ret_ic95'][1]*100:+.1f}]")
    return out


def cargar():
    z = np.load(os.path.join(os.path.dirname(AQUI), "rdint", "cache_todo.npz"))
    P = z["P1"].astype(float); P /= P.sum(1, keepdims=True)
    return P, z["y"], z["hora"], z["dia"], z["tramo"]


def dev():
    P, y, h, dia, tr = cargar()
    sel = tr == "dev"; idx = np.nonzero(sel)[0]; m = idx[len(idx) // 2]; i = np.arange(len(y))
    print("dev 1.ª mitad"); evaluar(P, y, h, dia, sel & (i < m))
    print("dev 2.ª mitad"); evaluar(P, y, h, dia, sel & (i >= m))


def ciega():
    import hashlib
    if os.path.exists(REG):
        sys.exit("Ya se corrió (registro_animal_dia_rd.jsonl). No se repite.")
    P, y, h, dia, tr = cargar()
    print("CIEGA: test + desc (2025-07-01 .. 2026-09-13)")
    res = evaluar(P, y, h, dia, np.isin(tr, ["test", "desc"]))
    for r in res.values():
        r["pasa"] = bool(r["z"] >= UMBRAL_Z)
    print("PASA:", {k: r["pasa"] for k, r in res.items()})
    out = {"prerregistro_sha256": hashlib.sha256(open(os.path.join(AQUI, "PREREGISTRO_animal_dia_rd.md"), "rb")
                                                  .read()).hexdigest(), "resultado": res}
    open(REG, "a", encoding="utf-8").write(json.dumps(out, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    {"dev": dev, "ciega": ciega}[sys.argv[1]]()
