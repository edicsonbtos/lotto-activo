# -*- coding: utf-8 -*-
"""ag10_comodin: composición del día / anti-déjà-vu sobre el ensamble_v2 (ver PREREGISTRO.md).

Uso: PYTHONIOENCODING=utf-8 python motor_nuevo/ag10_comodin/experimento.py [--sin-ag02]
Imprime arnes.informe(...) y guarda resultados.json (arnes.evaluar). Solo filas < 9357.
Determinista (sin azar salvo el desempate de rankings del arnés, con semilla fija).
"""
import importlib.util, json, os, sys, time
import numpy as np
from scipy.optimize import minimize

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa: E402
import rasgos as R  # noqa: E402

NBLOQ = 5
LAMBDA = 30.0


def _perdida(w, X, LPE, y, lam):
    z = LPE + X @ w
    z = z - z.max(1, keepdims=True)
    ez = np.exp(z); s = ez.sum(1)
    n = len(y)
    ll = z[np.arange(n), y] - np.log(s)
    Pm = ez / s[:, None]
    Pm[np.arange(n), y] -= 1.0
    g = np.einsum("ti,tif->f", Pm, X)
    return -ll.sum() + lam / 2 * w @ w, g + lam * w


def estandarizar(Xtr):
    F = Xtr.reshape(-1, Xtr.shape[2])
    mu, sd = F.mean(0), F.std(0)
    sd[sd < 1e-12] = 1.0
    return mu, sd


def ajustar(X, LPE, y, lam=LAMBDA):
    """Devuelve (w en escala estandarizada, mu, sd)."""
    mu, sd = estandarizar(X)
    Z = (X - mu) / sd
    r = minimize(_perdida, np.zeros(X.shape[2]), args=(Z, LPE, y, lam), jac=True,
                 method="L-BFGS-B", options={"maxiter": 500})
    return r.x, mu, sd


def predecir(par, X, LPE):
    w, mu, sd = par
    z = LPE + ((X - mu) / sd) @ w
    z = z - z.max(1, keepdims=True)
    P = np.exp(z)
    return P / P.sum(1, keepdims=True)


def bloques_jornada(dia, nb=NBLOQ):
    u = np.unique(dia)
    b = np.zeros(len(dia), int)
    for k, c in enumerate(np.array_split(u, nb)):
        b[np.isin(dia, c)] = k
    return b


def cross_fit(X, LPE, y, blo):
    P = np.empty(LPE.shape); pesos = []
    for k in range(NBLOQ):
        tr, te = blo != k, blo == k
        par = ajustar(X[tr], LPE[tr], y[tr])
        pesos.append(par[0] / par[2])                # w por unidad cruda
        P[te] = predecir(par, X[te], LPE[te])
    return P, np.array(pesos)


def forward(X, LPE, y, blo):
    P = np.exp(LPE); P = P / P.sum(1, keepdims=True)
    for k in range(1, NBLOQ):
        tr, te = blo < k, blo == k
        P[te] = predecir(ajustar(X[tr], LPE[tr], y[tr]), X[te], LPE[te])
    return P


def _ag02_rasgos():
    ruta = os.path.join(os.path.dirname(AQUI), "ag02_residuo_boost", "rasgos.py")
    spec = importlib.util.spec_from_file_location("ag02_rasgos", ruta)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def main():
    t0 = time.time()
    D = A.datos().prefijo(A.CORTE)                    # nada >= 9357
    P_ens, y = A.base()
    LPE = np.log(np.clip(P_ens, 1e-12, None)); LPE -= np.log(np.exp(LPE).sum(1, keepdims=True))
    X = R.construir(D, A.W)
    assert X.shape[:2] == P_ens.shape and np.array_equal(np.asarray(D.seq)[A.W:A.CORTE], y)
    dia = np.asarray(D.dia[A.W:A.CORTE]); blo = bloques_jornada(dia)
    print(f"variables listas en {time.time()-t0:.0f}s; medias:",
          {nm: round(float(X[:, :, i].mean()), 3) for i, nm in enumerate(R.NOMBRES)})
    res = {}

    P1, W = cross_fit(X, LPE, y, blo)
    print(A.informe(P1, "V1 composición del día, cross-fit 5 bloques, λ=30 (PRIMARIA)"))
    res["V1_primaria"] = A.evaluar(P1)
    res["V1_pesos_por_bloque_crudos"] = {nm: [round(float(v), 4) for v in W[:, i]] for i, nm in enumerate(R.NOMBRES)}
    print("pesos por bloque (unidad cruda):")
    for nm, v in res["V1_pesos_por_bloque_crudos"].items():
        print(f"  {nm:10s} {v}")
    np.save(os.path.join(AQUI, "P_V1.npy"), P1.astype(np.float32))

    Pf = forward(X, LPE, y, blo)
    print(A.informe(Pf, "V1 forward-chaining (informativo; bloque 0 = ensamble)"))
    res["V1_forward_informativo"] = A.evaluar(Pf)

    if "--sin-ag02" not in sys.argv:
        R2 = _ag02_rasgos()
        X2, _ = R2.construir(D, A.W)
        X2 = X2.astype(float)
        Pa, _ = cross_fit(X2, LPE, y, blo)
        Pb, _ = cross_fit(np.concatenate([X2, X], axis=2), LPE, y, blo)
        print(A.informe(Pa, "informativo: ag02 (27 var) re-ajustado aquí"))
        print(A.informe(Pb, "informativo: ag02 + ag10 (36 var)"))
        r_inc = A.evaluar(Pb, P_ref=Pa, y=y)
        f = lambda t: f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}]"
        print(f"INCREMENTO ag10 sobre ag02: Delta mbits {f(r_inc['delta_mbits'])} · mitad1 "
              f"{f(r_inc['delta_mitad1'])} · mitad2 {f(r_inc['delta_mitad2'])} · delta ret T5 {f(r_inc['delta_ret_t5'])}")
        res["ag02_solo_informativo"] = A.evaluar(Pa)
        res["ag02_mas_ag10_informativo"] = A.evaluar(Pb)
        res["incremento_ag10_sobre_ag02"] = r_inc
    json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1)
    print(f"listo en {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
