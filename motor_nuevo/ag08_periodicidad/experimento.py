# -*- coding: utf-8 -*-
"""Experimento principal ag08_periodicidad (determinista, sin azar salvo el de arnes).
Primario (prerregistrado, reserva porque el barrido no confirmó nada): 8 indicadoras
F1 L∈{12,24,36,38,76,84} + F1b k∈{1,7} sobre el ensamble, θ por cross-fitting en 5 bloques
contiguos de jornadas. Variante 2 (exploratoria, ver README): familia F4 entera (236 variables)."""
import json, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa: E402
import rasgos as R  # noqa: E402

PRIMARIO = [("lag", L) for L in (12, 24, 36, 38, 76, 84)] + [("dia", 1), ("dia", 7)]
F4 = ([("gh", b, h) for b in range(8) for h in range(12)] + [("gd", b, d) for b in range(8) for d in range(7)]
      + [("gdh", d, h) for d in range(7) for h in range(12)])


def bloques_jornada(dia, nb=5):
    u, inv = np.unique(dia, return_inverse=True)
    cortes = np.array_split(np.arange(len(u)), nb)
    b = np.empty(len(u), int)
    for i, c in enumerate(cortes):
        b[c] = i
    return b[inv]


def crossfit(P, X, y, blq, lam):
    out = np.empty_like(P); thetas = []
    for b in np.unique(blq):
        tr = blq != b
        th = R.ajustar(P[tr], X[tr], y[tr], lam)
        thetas.append(th.tolist())
        out[~tr] = R.aplicar(P[~tr], X[~tr], th)
    return out, thetas


def main():
    D = A.datos(); P, y = A.base(); P = P / P.sum(1, keepdims=True)
    Dd = D.prefijo(A.CORTE)
    blq = bloques_jornada(Dd.dia[A.W:A.CORTE])
    res = {}
    X = R.construir(Dd, A.W, PRIMARIO)
    Pc, th = crossfit(P, X, y, blq, 1.0)
    print(A.informe(Pc, "ag08 primario: desfases 12/24/36/38/76/84 + misma hora 1 y 7 días"))
    print("theta por bloque:", np.round(np.array(th), 3).tolist())
    res["primario"] = {"specs": PRIMARIO, "theta_bloques": th, "evaluar": A.evaluar(Pc)}
    np.save(os.path.join(AQUI, "P_primario.npy"), Pc.astype(np.float32))
    del X
    X = R.construir(Dd, A.W, F4)
    Pc2, th2 = crossfit(P, X, y, blq, 30.0)
    print(A.informe(Pc2, "ag08 variante 2 (exploratoria): familia F4 calendario x hueco, 236 variables, ridge 30"))
    res["variante2_F4"] = {"lam": 30.0, "evaluar": A.evaluar(Pc2)}
    json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=lambda o: list(o) if isinstance(o, tuple) else float(o))


if __name__ == "__main__":
    main()
