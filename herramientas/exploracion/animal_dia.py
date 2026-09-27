# -*- coding: utf-8 -*-
"""Idea del usuario (2026-09-27): "¿el sistema puede decir qué 1, 2 o 3 animales salen HOY, sin importar la hora?"

Se eligen k animales ANTES del primer sorteo del día (solo con días anteriores) y se mira si al menos uno sale
en la jornada. Azar exacto del día d con D_d animales distintos: 1 - C(38-D_d, k) / C(38, k)
(el operador casi no repite en el día, así que no vale 1-(37/38)^12).

Dinero: 1 ficha por animal en cada sorteo HASTA que sale (luego se deja, casi nunca repite). Paga 30.
Retorno por ficha frente al equilibrio (0 %).

Candidatos (ranking del día):
  A = probabilidades del ensamble para el primer sorteo del día (fila congelada de la caché).
  B = tabla "días desde la última jornada en que salió" -> P(sale hoy), ajustada SOLO en desarrollo.

Uso:  python animal_dia.py dev          (exploración, tramo de desarrollo)
      python animal_dia.py ciega        (UNA vez, ver PREREGISTRO_animal_dia.md)
"""
import json, os, sys
from math import comb
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import lotto_eval as LE  # noqa: E402

K = 38
GMAX = 30  # días desde la última aparición, topado


def jornadas(dia, desde, hasta):
    """(ini, fin) de cada día con 10+ sorteos que cae entero dentro de [desde, hasta)."""
    cortes = np.r_[0, np.nonzero(np.diff(dia))[0] + 1, len(dia)]
    return [(a, b) for a, b in zip(cortes[:-1], cortes[1:]) if a >= desde and b <= hasta and b - a >= 10]


def huecos_dia(seq, dia, t):
    """Para el sorteo t: días (calendario) desde la última jornada con cada animal, usando seq[:t]."""
    g = np.full(K, GMAX)
    d0 = dia[t]
    visto = np.zeros(K, bool)
    for s in range(t - 1, -1, -1):
        dd = d0 - dia[s]
        if dd >= GMAX:
            break
        a = seq[s]
        if not visto[a]:
            visto[a] = True
            g[a] = dd
    return g


def azar(D, k):
    return 1 - comb(K - D, k) / comb(K, k)


def evaluar(seq, dia, hora, desde, hasta, rank_fn, ks=(1, 2, 3), excluir=None):
    out = {k: {"ac": 0, "esp": 0.0, "var": 0.0, "fichas": 0, "cobro": 0, "dias": 0} for k in ks}
    por_dia = {k: [] for k in ks}
    for a, b in jornadas(dia, desde, hasta):
        if excluir is not None and excluir(a):
            continue
        orden = rank_fn(a)
        hoy = seq[a:b]
        D = len(set(hoy.tolist()))
        for k in ks:
            elegidos = orden[:k]
            hit = int(np.isin(elegidos, hoy).any())
            p0 = azar(D, k)
            fich = cob = 0
            for e in elegidos:
                pos = np.nonzero(hoy == e)[0]
                if len(pos):
                    fich += pos[0] + 1; cob += 30
                else:
                    fich += len(hoy)
            o = out[k]
            o["ac"] += hit; o["esp"] += p0; o["var"] += p0 * (1 - p0); o["dias"] += 1
            o["fichas"] += fich; o["cobro"] += cob
            por_dia[k].append((hit - p0, cob - fich, fich))
    res = {}
    rng = np.random.default_rng(7)
    for k in ks:
        o = out[k]; arr = np.array(por_dia[k])
        B = rng.integers(0, len(arr), size=(4000, len(arr)))
        ret_b = arr[B, 1].sum(1) / arr[B, 2].sum(1)
        res[k] = {"dias": o["dias"], "acierto": o["ac"] / o["dias"], "azar": o["esp"] / o["dias"],
                  "z": (o["ac"] - o["esp"]) / o["var"] ** 0.5,
                  "retorno_ficha": (o["cobro"] - o["fichas"]) / o["fichas"],
                  "ret_ic95": [float(np.percentile(ret_b, 2.5)), float(np.percentile(ret_b, 97.5))]}
    return res


def tabla_B(seq, dia, hora, desde, hasta):
    """P(sale en la jornada | hueco en días), contada en [desde, hasta)."""
    n = np.zeros(GMAX + 1); s = np.zeros(GMAX + 1)
    for a, b in jornadas(dia, desde, hasta):
        g = huecos_dia(seq, dia, a)
        hoy = np.zeros(K, bool); hoy[np.unique(seq[a:b])] = True
        np.add.at(n, g, 1); np.add.at(s, g, hoy)
    return (s + 1) / (n + 3)


def imprimir(nombre, res):
    for k, r in res.items():
        print(f"  {nombre} k={k}: {r['acierto']*100:5.1f} % vs azar {r['azar']*100:5.1f} % "
              f"(z {r['z']:+.2f}, {r['dias']} días) · retorno/ficha {r['retorno_ficha']*100:+5.1f} % "
              f"[{r['ret_ic95'][0]*100:+.1f}; {r['ret_ic95'][1]*100:+.1f}]")


def dev():
    D = LE.cargar()
    seq, dia, hora = np.asarray(D.seq), np.asarray(D.dia), np.asarray(D.hora)
    c = np.load(os.path.join(AQUI, "calor_cache.npz")); P = c["P"]
    assert (c["y"] == seq[LE.W:LE.W + len(P)]).all()
    ini, fin = LE.W, LE.W + len(P)
    rankA = lambda t: np.argsort(-P[t - ini], kind="stable")
    mitad = (ini + fin) // 2
    # B: tabla ajustada en la 1.ª mitad de desarrollo, medida en la 2.ª (y al revés) para no medir en muestra.
    tB1 = tabla_B(seq, dia, hora, ini, mitad); tB2 = tabla_B(seq, dia, hora, mitad, fin)
    print("tabla B (1.ª mitad), hueco 1..10:", np.round(tB1[1:11], 3), " 30+:", round(tB1[GMAX], 3))
    for nom, a, b, tb in (("1.ª mitad", ini, mitad, tB2), ("2.ª mitad", mitad, fin, tB1)):
        print(f"--- desarrollo {nom} [{a},{b}) ---")
        imprimir("A ensamble", evaluar(seq, dia, hora, a, b, rankA))
        rankB = lambda t, tb=tb: np.argsort(-tb[huecos_dia(seq, dia, t)], kind="stable")
        imprimir("B huecos  ", evaluar(seq, dia, hora, a, b, rankB))


MN = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(AQUI))), "lotto-activo-motor", "motor_nuevo")
REG = os.path.join(AQUI, "registro_animal_dia.jsonl")
EXCLUIR = {"2025-12-15", "2025-12-16", "2025-12-17", "2025-12-18", "2025-12-19", "2025-12-25", "2025-12-26",
           "2025-12-27", "2026-01-01", "2026-01-02", "2026-01-03"}
UMBRAL_Z = 2.39


def ciega():
    import hashlib
    if os.path.exists(REG):
        sys.exit("Esta prueba ya se corrió (registro_animal_dia.jsonl existe). No se repite.")
    prereg = os.path.join(AQUI, "PREREGISTRO_animal_dia.md")
    out = {"prerregistro_sha256": hashlib.sha256(open(prereg, "rb").read()).hexdigest(), "tramos": {}}
    # 1) época reciente
    D = LE.cargar().prefijo(12511)
    seq, dia, hora = np.asarray(D.seq), np.asarray(D.dia), np.asarray(D.hora)
    P = np.load(os.path.join(MN, "reciente", "P_ens_reciente.npy")); ini = 9357
    assert len(P) == 12511 - ini
    rank = lambda t: np.argsort(-P[t - ini], kind="stable")
    exc = lambda a: D.fecha[a] in EXCLUIR
    out["tramos"]["reciente"] = evaluar(seq, dia, hora, ini, 12511, rank, excluir=exc)
    # 2) sellado 2019-2023
    D = LE.cargar(os.path.join(MN, "sellado", "sellado_la.txt"))
    seq, dia, hora = np.asarray(D.seq), np.asarray(D.dia), np.asarray(D.hora)
    P = np.load(os.path.join(MN, "sellado", "P_ens_sellado.npy")); ini = 2000
    assert len(P) == len(seq) - ini
    rank = lambda t: np.argsort(-P[t - ini], kind="stable")
    out["tramos"]["sellado"] = evaluar(seq, dia, hora, ini, len(seq), rank)
    for nom, res in out["tramos"].items():
        print(f"--- {nom} ---")
        imprimir("A ensamble", res)
        for k, r in res.items():
            r["pasa"] = bool(r["z"] >= UMBRAL_Z)
        print("  PASA:", {k: r["pasa"] for k, r in res.items()})
    with open(REG, "a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    if sys.argv[1:] == ["dev"]:
        dev()
    elif sys.argv[1:] == ["ciega"]:
        ciega()
    else:
        sys.exit("uso: animal_dia.py dev | ciega")
