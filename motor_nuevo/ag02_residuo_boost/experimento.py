# -*- coding: utf-8 -*-
"""ag02_residuo_boost: corrección residual log P_ens + g(x) con cross-fitting por bloques de jornada.

Uso: PYTHONIOENCODING=utf-8 python motor_nuevo/ag02_residuo_boost/experimento.py [--sin-lgb]
Imprime arnes.informe(...) de cada variante y guarda resultados.json (arnes.evaluar).
Solo usa filas < 9357 (datos.prefijo(CORTE)).
"""
import json, os, sys, time
import numpy as np
from scipy.optimize import minimize

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa: E402
import rasgos as R  # noqa: E402

NBLOQ = 5
LAMBDA_PRIM = 30.0
SEMILLA = 20260925


# ----------------------------- g lineal ------------------------------------ #
def _perdida(w, X, LPE, y, lam):
    z = LPE + X @ w
    z = z - z.max(1, keepdims=True)
    ez = np.exp(z); s = ez.sum(1)
    n = len(y)
    ll = z[np.arange(n), y] - np.log(s)
    Pm = ez / s[:, None]
    Pm[np.arange(n), y] -= 1.0                       # p - 1[y]
    g = np.einsum("ti,tif->f", Pm, X)
    return -ll.sum() + lam / 2 * w @ w, g + lam * w


def ajustar_lineal(X, LPE, y, lam):
    w0 = np.zeros(X.shape[2])
    r = minimize(_perdida, w0, args=(X, LPE, y, lam), jac=True, method="L-BFGS-B",
                 options={"maxiter": 500})
    return r.x


def predecir_lineal(w, X, LPE):
    z = LPE + X @ w
    z = z - z.max(1, keepdims=True)
    P = np.exp(z)
    return P / P.sum(1, keepdims=True)


# ----------------------------- g boosting ---------------------------------- #
PARAM_LGB = dict(learning_rate=0.03, num_leaves=4, min_data_in_leaf=3000, lambda_l2=50.0,
                 feature_fraction=1.0, bagging_fraction=1.0, max_bin=15, verbose=-1,
                 num_threads=1, seed=SEMILLA, deterministic=True, force_row_wise=True)
RONDAS = 150


def _plano(X, extra):
    n = X.shape[0]
    ex = np.repeat(extra[:, None, :], R.K, axis=1)
    return np.concatenate([X, ex], axis=2).reshape(n * R.K, -1)


def ajustar_lgb(X, extra, LPE, y):
    import lightgbm as lgb
    n = X.shape[0]
    Y = np.zeros((n, R.K)); Y[np.arange(n), y] = 1
    Yf = Y.ravel()

    def obj(preds, ds):
        z = preds.reshape(n, R.K)          # incluye init_score
        z = z - z.max(1, keepdims=True)
        p = np.exp(z); p /= p.sum(1, keepdims=True)
        p = p.ravel()
        return p - Yf, np.maximum(p * (1 - p), 1e-6)

    ds = lgb.Dataset(_plano(X, extra), label=Yf, init_score=LPE.ravel(), free_raw_data=True)
    prm = dict(PARAM_LGB); prm["objective"] = obj
    return lgb.train(prm, ds, num_boost_round=RONDAS)


def predecir_lgb(b, X, extra, LPE):
    f = b.predict(_plano(X, extra), raw_score=True).reshape(X.shape[0], R.K)
    z = LPE + f
    z = z - z.max(1, keepdims=True)
    P = np.exp(z)
    return P / P.sum(1, keepdims=True)


# ----------------------------- cross-fitting -------------------------------- #
def bloques_jornada(dia, nb=NBLOQ):
    u = np.unique(dia)
    cortes = np.array_split(u, nb)
    b = np.zeros(len(dia), int)
    for k, c in enumerate(cortes):
        b[np.isin(dia, c)] = k
    return b


def cross_fit(fit, pred, blo):
    P = np.zeros((len(blo), R.K))
    pars = []
    for k in range(blo.max() + 1):
        tr, te = blo != k, blo == k
        m = fit(tr)
        P[te] = pred(m, te)
        pars.append(m)
    return P, pars


def forward(fit, pred, blo):
    """Forward-chaining: el bloque k se predice con los bloques < k; el bloque 0 queda = ensamble."""
    P = np.full((len(blo), R.K), np.nan)
    for k in range(1, blo.max() + 1):
        m = fit(blo < k)
        P[blo == k] = pred(m, blo == k)
    return P


def main():
    t0 = time.time()
    D = A.datos().prefijo(A.CORTE)                   # nada >= 9357 entra en memoria
    Pens, y = A.base()
    Pens = Pens / Pens.sum(1, keepdims=True)
    LPE = np.log(np.clip(Pens, 1e-12, None))
    X, extra = R.construir(D, A.W)
    X = X.astype(np.float64)
    dia = np.asarray(D.dia[A.W:A.CORTE])
    blo = bloques_jornada(dia)
    assert len(y) == len(X) == len(dia)
    res = {}
    salida = []

    def reporta(nombre, P):
        txt = A.informe(P, nombre); print(txt, flush=True); salida.append(txt)
        res[nombre] = A.evaluar(P)

    # V1 primario
    for lam in (LAMBDA_PRIM, 10.0, 100.0):
        nombre = f"V1_lineal_lambda{lam:g}" + ("" if lam == LAMBDA_PRIM else "_sensibilidad")
        P, pars = cross_fit(lambda tr: ajustar_lineal(X[tr], LPE[tr], y[tr], lam),
                            lambda w, te: predecir_lineal(w, X[te], LPE[te]), blo)
        reporta(nombre, P)
        if lam == LAMBDA_PRIM:
            W = np.array(pars)
            res["pesos_V1_por_bloque"] = {n: [round(float(v), 4) for v in W[:, i]] for i, n in enumerate(R.NOMBRES)}
            print("pesos V1 por bloque (media, min, max):")
            for i, n in enumerate(R.NOMBRES):
                print(f"  {n:22s} {W[:, i].mean():+.3f} [{W[:, i].min():+.3f}, {W[:, i].max():+.3f}]")
            # forward-chaining (informativo): bloque 0 = ensamble
            Pf = forward(lambda tr: ajustar_lineal(X[tr], LPE[tr], y[tr], lam),
                         lambda w, te: predecir_lineal(w, X[te], LPE[te]), blo)
            Pf[blo == 0] = Pens[blo == 0]
            reporta("V1_forward_chaining_informativo", Pf)
        print(f"  [{time.time() - t0:.0f} s]", flush=True)

    if "--sin-lgb" not in sys.argv:
        P, _ = cross_fit(lambda tr: ajustar_lgb(X[tr], extra[tr], LPE[tr], y[tr]),
                         lambda b, te: predecir_lgb(b, X[te], extra[te], LPE[te]), blo)
        reporta("V2_lgb_residual", P)
        print(f"  [{time.time() - t0:.0f} s]", flush=True)

    with open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(os.path.join(AQUI, "salida_experimento.txt"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(salida) + "\n")


if __name__ == "__main__":
    main()
