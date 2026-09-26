# -*- coding: utf-8 -*-
"""ag01_gbm_ranker: LightGBM con softmax condicional por sorteo, solo (A) y apilado sobre el ensamble (B).

Cross-fitting en 5 bloques contiguos de jornadas del tramo de desarrollo [2000, 9357), con 2 días de
embargo a cada lado del bloque predicho. Nada de filas >= 9357.

Uso:  PYTHONIOENCODING=utf-8 python motor_nuevo/ag01_gbm_ranker/experimento.py [--rapido]
Salida: resultados.json, P_A.npy/P_B.npy (predicciones cross-fit), modelo_B.txt (congelado).
"""
import json, os, sys, time
import numpy as np
import lightgbm as lgb

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A          # noqa: E402
import variables as V      # noqa: E402

K = 38
SEMILLA = 20260925
NBLOQ, EMBARGO = 5, 2
RAPIDO = "--rapido" in sys.argv
PARAMS = dict(num_leaves=15, learning_rate=0.03, min_data_in_leaf=400, feature_fraction=0.8,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, max_bin=63, seed=SEMILLA,
              num_threads=1, verbose=-1, deterministic=True, force_row_wise=True)
MAX_ARB, PACIENCIA = (60, 10) if RAPIDO else (1000, 50)


def softmax_obj(preds, ds):
    z = preds.reshape(-1, K)
    z = z - z.max(1, keepdims=True); p = np.exp(z); p /= p.sum(1, keepdims=True)
    y = ds.get_label().reshape(-1, K)
    return (p - y).ravel(), np.maximum(p * (1 - p), 1e-6).ravel()


def softmax_nll(preds, ds):
    z = preds.reshape(-1, K); y = ds.get_label().reshape(-1, K)
    z = z - z.max(1, keepdims=True)
    ll = (z * y).sum(1) - np.log(np.exp(z).sum(1))
    return "nll", float(-ll.mean()), False


def dataset(X, Y1, init, filas, ref=None):
    d = lgb.Dataset(X[filas].reshape(-1, X.shape[2]), label=Y1[filas].ravel(),
                    init_score=None if init is None else init[filas].ravel(), free_raw_data=True,
                    reference=ref, params={"max_bin": 63})
    return d


def entrenar(X, Y1, init, tr, va=None, n_arb=None):
    dtr = dataset(X, Y1, init, tr)
    if va is not None:
        dva = dataset(X, Y1, init, va, ref=dtr)
        b = lgb.train(dict(PARAMS, objective=softmax_obj), dtr, num_boost_round=MAX_ARB, valid_sets=[dva],
                      feval=softmax_nll, callbacks=[lgb.early_stopping(PACIENCIA, verbose=False)])
        return b, max(1, b.best_iteration)
    b = lgb.train(dict(PARAMS, objective=softmax_obj), dtr, num_boost_round=n_arb)
    return b, n_arb


def predecir(b, X, init, filas):
    s = b.predict(X[filas].reshape(-1, X.shape[2]), raw_score=True).reshape(-1, K)
    if init is not None:
        s = s + init[filas]
    s -= s.max(1, keepdims=True); p = np.exp(s)
    return p / p.sum(1, keepdims=True)


def cross_fit(X, Y1, init, dia, nombre):
    n = len(Y1)
    dias = np.unique(dia)
    trozos = np.array_split(dias, NBLOQ)
    bloque = np.empty(n, int)
    for b, tz in enumerate(trozos):
        bloque[np.isin(dia, tz)] = b
    P = np.zeros((n, K)); arboles = []
    for b in range(NBLOQ):
        lo, hi = trozos[b][0] - EMBARGO, trozos[b][-1] + EMBARGO
        entreno = (bloque != b) & ~((dia >= lo) & (dia <= hi))
        vb = NBLOQ - 1 if b != NBLOQ - 1 else NBLOQ - 2          # último bloque de entrenamiento en el tiempo
        tr_in = np.where(entreno & (bloque != vb))[0]; va_in = np.where(entreno & (bloque == vb))[0]
        t0 = time.time()
        _, nb = entrenar(X, Y1, init, tr_in, va_in)
        bst, _ = entrenar(X, Y1, init, np.where(entreno)[0], n_arb=nb)
        te = np.where(bloque == b)[0]
        P[te] = predecir(bst, X, init, te)
        arboles.append(int(nb))
        print(f"  [{nombre}] bloque {b}: {len(te)} filas, entreno {entreno.sum()}, árboles {nb}, {time.time()-t0:.0f}s",
              flush=True)
    return P, arboles


def forward_chain(X, Y1, init, dia, P_ens, nombre):
    """Diagnóstico: bloque b (b>=1) predicho con modelos entrenados SÓLO con bloques < b (menos embargo)."""
    n = len(Y1); dias = np.unique(dia); trozos = np.array_split(dias, NBLOQ)
    P = P_ens / P_ens.sum(1, keepdims=True); P = P.copy()
    for b in range(1, NBLOQ):
        lim = trozos[b][0] - EMBARGO
        entreno = dia < lim
        if b == 1:   # validación interna: último 20 % de días del pasado
            corte_va = np.unique(dia[entreno])[int(0.8 * len(np.unique(dia[entreno])))]
        else:
            corte_va = trozos[b - 1][0]
        tr_in = np.where(entreno & (dia < corte_va))[0]; va_in = np.where(entreno & (dia >= corte_va))[0]
        _, nb = entrenar(X, Y1, init, tr_in, va_in)
        bst, _ = entrenar(X, Y1, init, np.where(entreno)[0], n_arb=nb)
        te = np.where(np.isin(dia, trozos[b]))[0]
        P[te] = predecir(bst, X, init, te)
        print(f"  [{nombre}] bloque {b}: árboles {nb}", flush=True)
    return P


def main():
    D = A.datos()
    W, CORTE = A.W, A.CORTE
    seq = np.asarray(D.seq)[:CORTE]; hora = np.asarray(D.hora)[:CORTE]; dia_all = np.asarray(D.dia)[:CORTE]
    P_ens, y = A.base()
    assert np.array_equal(y, seq[W:CORTE])
    t0 = time.time()
    X = V.construir(seq, hora, dia_all, W, CORTE)
    print(f"variables: {X.shape} en {time.time()-t0:.0f}s", flush=True)
    Y1 = np.zeros((len(y), K), np.float32); Y1[np.arange(len(y)), y] = 1
    dia = dia_all[W:CORTE]
    XB, lp = V.con_ensamble(X, P_ens)
    res = {"params": {k: v for k, v in PARAMS.items()}, "rapido": RAPIDO}
    salida = []
    for nombre, XX, init in (("A_solo", X, None), ("B_apilado", XB, lp.astype(np.float64))):
        P, arb = cross_fit(XX, Y1, init, dia, nombre)
        salida.append(A.informe(P, "ag01 " + nombre))
        print(salida[-1], flush=True)
        r = A.evaluar(P); r["arboles_por_bloque"] = arb
        res[nombre] = r
        if not RAPIDO:
            np.save(os.path.join(AQUI, f"P_{nombre}.npy"), P.astype(np.float32))
    # Diagnósticos (deviación 2 del prerregistro)
    lpd = lp.astype(np.float64)
    Pf = forward_chain(XB, Y1, lpd, dia, P_ens, "B_forward")
    salida.append(A.informe(Pf, "ag01 diag B forward-chaining (bloque 0 = ensamble)"))
    print(salida[-1], flush=True); res["diag_B_forward"] = A.evaluar(Pf)
    XC = XB[:, :, -2:].copy()
    Pc, arb = cross_fit(XC, Y1, lpd, dia, "C_recal")
    salida.append(A.informe(Pc, "ag01 diag recalibración (sólo log P_ens y rango)"))
    print(salida[-1], flush=True); res["diag_recal"] = A.evaluar(Pc); res["diag_recal"]["arboles_por_bloque"] = arb
    if not RAPIDO:
        # Congelado: variante B con todo el desarrollo y la mediana de árboles del cross-fitting
        n_arb = int(np.median(res["B_apilado"]["arboles_por_bloque"]))
        bst, _ = entrenar(XB, Y1, lp.astype(np.float64), np.arange(len(y)), n_arb=n_arb)
        bst.save_model(os.path.join(AQUI, "modelo_B.txt"))
        res["congelado"] = {"variante": "B_apilado", "arboles": n_arb, "filas_entreno": [W, CORTE]}
        with open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1, ensure_ascii=False)
    print("\n\n".join(salida))
    print(f"total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
