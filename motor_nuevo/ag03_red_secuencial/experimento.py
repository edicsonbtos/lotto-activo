# -*- coding: utf-8 -*-
"""ag03_red_secuencial: MLP equivariante sobre los últimos 72 ganadores. Sola y apilada con el ensamble.
Cross-fitting en 5 bloques contiguos de jornadas de [2000, 9357). Semilla fija.
Uso: PYTHONIOENCODING=utf-8 python experimento.py"""
import json, os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI); sys.path.insert(0, os.path.dirname(AQUI))
import arnes as A  # noqa: E402
import rasgos as R  # noqa: E402
import red  # noqa: E402

NB = 5


def bloques(dia):
    u = np.unique(dia)
    corte = np.array_split(u, NB)
    b = np.zeros(len(dia), int)
    for i, c in enumerate(corte):
        b[np.isin(dia, c)] = i
    return b


def cross_fit(X, y, off, blq, forward=False, P_ens=None):
    P = np.empty((len(y), A.K)); eps = []
    for b in range(NB):
        te = np.where(blq == b)[0]
        tr = np.where(blq < b)[0] if forward else np.where(blq != b)[0]
        if len(tr) == 0:
            P[te] = P_ens[te]; continue
        n_val = int(0.15 * len(tr))
        idx_tr, idx_val = tr[:-n_val], tr[-n_val:]          # validación interna: lo último en el tiempo
        t0 = time.time()
        p, e = red.entrenar(X, y, off, idx_val=idx_val, idx_tr=idx_tr, semilla=0)
        eps.append(e)
        P[te] = red.probs(p, X[te], None if off is None else off[te])
        print(f"  bloque {b}: {len(tr)} filas de entrenamiento, épocas {e}, {time.time()-t0:.0f}s", flush=True)
    return P, eps


def main():
    D = A.datos()
    P_ens, y = A.base()
    X = R.construir(D, A.W, A.CORTE)
    assert np.array_equal(y, D.seq[A.W:A.CORTE])
    blq = bloques(D.dia[A.W:A.CORTE])
    off = np.log(np.clip(P_ens, 1e-12, None)).astype(np.float32)
    res = {}
    salida = []
    for nombre, o, fw in [("V_apilado (primaria)", off, False), ("V_solo", None, False),
                          ("V_apilado forward-chaining (informativa)", off, True)]:
        print(nombre, flush=True)
        P, eps = cross_fit(X, y, o, blq, forward=fw, P_ens=P_ens)
        r = A.evaluar(P)
        r["epocas"] = eps
        res[nombre] = r
        txt = A.informe(P, "ag03 " + nombre)
        print(txt, flush=True); salida.append(txt)
        if nombre.startswith("V_apilado (primaria)"):
            np.save(os.path.join(AQUI, "P_apilado.npy"), P.astype(np.float32))
    json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    open(os.path.join(AQUI, "salida_experimento.txt"), "w", encoding="utf-8").write("\n\n".join(salida) + "\n")


if __name__ == "__main__":
    main()
