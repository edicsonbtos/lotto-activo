# -*- coding: utf-8 -*-
"""ag09_multi_escala: experimento principal (determinista; L-BFGS sin azar, bootstrap con semilla del arnés).

V1  (primaria): log P_ens + f(multi-escala), cross-fit 5 bloques contiguos de jornadas, λ por CV interna.
V1f (robustez): lo mismo con forward-chaining en 10 bloques (bloque 0 = ensamble).
V2  (informativa): f sola, sin ensamble (offset uniforme), cross-fit.
Congela w (todo el desarrollo, filas < 9357) en parametros.json.
"""
import json, os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa: E402
import nucleo as N  # noqa: E402


def crossfit(X, off, y, dia, k=5):
    lab = N.bloques_dia(dia, k)
    Q = np.zeros_like(off); lams = []
    for b in range(k):
        tr, te = np.where(lab != b)[0], np.where(lab == b)[0]
        Xtr = N.filas_X(X, tr)
        lam, punt = N.elegir_lam(Xtr, off[tr], y[tr], dia[tr])
        w = N.ajustar(Xtr, off[tr], y[tr], lam)
        Q[te] = N.predecir_log(N.filas_X(X, te), off[te], w)
        lams.append(lam)
        print(f"  bloque {b}: λ={lam} (CV {np.round(punt, 1).tolist()})", flush=True)
    return Q, lams


def forward(X, off, y, dia, k=10):
    lab = N.bloques_dia(dia, k)
    Q = np.exp(off - off.max(1, keepdims=True)); Q /= Q.sum(1, keepdims=True)
    lams = []
    for b in range(1, k):
        tr, te = np.where(lab < b)[0], np.where(lab == b)[0]
        Xtr = N.filas_X(X, tr)
        lam, _ = N.elegir_lam(Xtr, off[tr], y[tr], dia[tr])
        w = N.ajustar(Xtr, off[tr], y[tr], lam)
        Q[te] = N.predecir_log(N.filas_X(X, te), off[te], w)
        lams.append(lam)
    return Q, lams


def main():
    t0 = time.time()
    D = A.datos().prefijo(A.CORTE)            # nunca se leen filas >= 9357
    dia = np.asarray(D.dia[A.W:A.CORTE])
    P, y = A.base()
    off = np.log(np.clip(P / P.sum(1, keepdims=True), 1e-12, None))
    X = N.construir(D, A.W)
    res = {}
    print("V1 cross-fit", flush=True)
    Q1, l1 = crossfit(X, off, y, dia)
    np.save(os.path.join(AQUI, "P_V1.npy"), Q1.astype(np.float32))
    print(A.informe(Q1, "V1 multi-escala sobre ensamble (cross-fit 5 bloques)"), flush=True)
    res["V1"] = A.evaluar(Q1); res["V1"]["lams"] = l1
    print("V1f forward-chaining", flush=True)
    Q1f, l1f = forward(X, off, y, dia)
    print(A.informe(Q1f, "V1f multi-escala sobre ensamble (forward-chaining 10 bloques)"), flush=True)
    res["V1f"] = A.evaluar(Q1f); res["V1f"]["lams"] = l1f
    print("V2 sin ensamble", flush=True)
    off0 = np.zeros_like(off)
    Q2, l2 = crossfit(X, off0, y, dia)
    print(A.informe(Q2, "V2 multi-escala SOLA (sin ensamble, cross-fit)"), flush=True)
    res["V2"] = A.evaluar(Q2); res["V2"]["lams"] = l2
    # congelar con todo el desarrollo
    lam, punt = N.elegir_lam(X, off, y, dia, k=5)
    w = N.ajustar(X, off, y, lam)
    json.dump({"lam": lam, "cv": punt, "P": N.P, "grupos": N.GRUPOS, "w": w.tolist(),
               "filas_ajuste": [A.W, A.CORTE]}, open(os.path.join(AQUI, "parametros.json"), "w"), indent=1)
    for g, (a, b) in N.GRUPOS.items():
        print(f"  w[{g}]: rango [{w[a:b].min():+.3f}, {w[a:b].max():+.3f}]")
    print(f"congelado λ={lam}")
    json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w"), indent=1)
    print(f"tiempo {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
