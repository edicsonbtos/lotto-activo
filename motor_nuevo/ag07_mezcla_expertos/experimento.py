# -*- coding: utf-8 -*-
"""ag07: mezcla de expertos con compuerta por contexto. Cross-fitting en 5 bloques contiguos de jornadas.
Uso: python experimento.py      (necesita cache_sub_*.npy, copiadas de ag04 o generadas con ../ag04_no_estacionario/cache_sub.py)"""
import os, sys, json
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa
import nucleo as N  # noqa

A0 = 1000                     # las cachés empiezan en la fila 1000
REPO = ["intradia_v2", "secuencia_v3", "haz_v1"]
NB = 5


def main():
    D = A.datos().prefijo(A.CORTE)          # nunca filas >= 9357
    seq, dia = D.seq, D.dia
    Lrepo = np.stack([N.lognorm(np.load(os.path.join(AQUI, f"cache_sub_{m}.npy"))) for m in REPO], 1)  # (8357,3,38)
    Lrec = N.lognorm(N.recencia(seq)[A0:])[:, None, :]
    L4 = np.concatenate([Lrepo, Lrec], 1)
    X = N.contexto(seq, dia, np.concatenate([np.zeros((A0, 3, 38)), Lrepo], 0))[A0:]
    y = seq[A0:]
    P_ens, y_dev = A.base()
    assert np.array_equal(y[A.W - A0:], y_dev)

    # bloques contiguos de jornadas en [W, CORTE)
    d_dev = dia[A.W:A.CORTE]
    dias = np.unique(d_dev)
    cortes = np.array_split(dias, NB)
    bloque = np.full(len(y), -1)            # -1 = filas [1000,2000): siempre entrenamiento
    for b, ds in enumerate(cortes):
        bloque[A.W - A0 + np.flatnonzero(np.isin(d_dev, ds))] = b

    dev = slice(A.W - A0, None)
    res = {}
    coefs = {}
    variantes = {
        "V1_loglineal_contexto": (L4, "ll"),
        "V2_moe_lineal": (L4, "moe"),
        "V3_loglineal_sin_recencia": (Lrepo, "ll"),
    }
    for nombre, (L, tipo) in variantes.items():
        P = np.empty((len(y), 38))
        coefs[nombre] = []
        for b in range(NB):
            tr = bloque != b
            te = bloque == b
            if tipo == "ll":
                Wm = N.ajustar_loglineal(L[tr], X[tr], y[tr])
                P[te] = N.predecir_loglineal(L[te], X[te], Wm)
            else:
                Wm = N.ajustar_moe(L[tr], X[tr], y[tr])
                P[te] = N.predecir_moe(L[te], X[te], Wm)
            coefs[nombre].append(np.round(Wm, 3).tolist())
        Pd = P[dev]
        np.save(os.path.join(AQUI, f"P_{nombre}.npy"), Pd.astype(np.float32))
        print(A.informe(Pd, nombre), flush=True)
        print("  coeficientes bloque 0 (filas=expertos, cols=[1,k,k2,rep,disp]):", coefs[nombre][0], flush=True)
        r = A.evaluar(Pd)
        res[nombre] = r
    res["_coeficientes_por_bloque"] = coefs
    with open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
