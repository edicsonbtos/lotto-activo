# -*- coding: utf-8 -*-
"""Arnés común de la búsqueda de un motor nuevo (rama motor-nuevo).

Todo candidato se mide IGUAL, contra el ensamble_v2 congelado, en el tramo de
desarrollo [2000, 9357) de historial.txt. El tramo >= 9357 NO se usa.

Uso desde un script de agente:

    import sys, os; sys.path.insert(0, os.path.join(<raiz worktree>, "motor_nuevo"))
    import arnes as A
    D = A.datos()                 # lotto_eval.Datos completo (no leas filas >= A.CORTE)
    P_ens, y = A.base()           # (7357, 38) ensamble_v2 walk-forward, y = ganador
    ...construye P_cand (7357, 38): fila j = sorteo t = A.W + j, usando SOLO seq[:t]
    print(A.informe(P_cand, "mi_candidato"))

Si el candidato tiene parámetros ajustados, deben salir de datos anteriores a t
(forward-chaining) o de validación cruzada por BLOQUES DE JORNADA (cross-fitting:
la fila t se predice con parámetros ajustados sin su bloque). Nunca con la fila t.
"""
import math, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE  # noqa: E402

W, CORTE, K, PAGO = LE.W, LE.CORTE_FIJO, 38, 30
CACHE = os.path.join(RAIZ, "herramientas", "exploracion", "calor_cache.npz")
# Top-5 escalonado 2-2-2-1-1 (jugada oficial) y Top-3 plano
FICHAS_T5 = np.array([2, 2, 2, 1, 1])


def datos():
    return LE.cargar()


def base():
    z = np.load(CACHE)
    return z["P"].astype(float), z["y"].astype(int)


def _norm(P):
    P = np.clip(np.asarray(P, float), 1e-9, None)
    return P / P.sum(1, keepdims=True)


def mbits_fila(P, y):
    P = _norm(P)
    return 1000 * np.log2(P[np.arange(len(y)), y] * K)


def puestos(P, y, semilla=12345):
    orden = LE.rankings(_norm(P), semilla)
    return np.argmax(orden == y[:, None], axis=1) + 1   # 1 = primero


def retorno_t5(pos):
    """Neto por ficha del Top-5 escalonado, por sorteo (array)."""
    f = np.zeros(39); f[1:6] = FICHAS_T5
    return (PAGO * f[pos] - FICHAS_T5.sum()) / FICHAS_T5.sum()


def ic_bloques(x, dia, reps=2000, semilla=7):
    """Media e IC95 por bootstrap de bloques de jornada (día)."""
    x = np.asarray(x, float)
    _, inv = np.unique(dia, return_inverse=True)
    sums = np.bincount(inv, weights=x); cnt = np.bincount(inv)
    rng = np.random.default_rng(semilla)
    B = rng.integers(0, len(sums), size=(reps, len(sums)))
    m = sums[B].sum(1) / cnt[B].sum(1)
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def evaluar(P_cand, P_ref=None, y=None):
    """Delta frente al ensamble: mbits (métrica primaria) y dinero Top-5/Top-3."""
    if P_ref is None or y is None:
        P_ref, y = base()
    P_cand = np.asarray(P_cand, float)
    assert P_cand.shape == P_ref.shape, f"forma {P_cand.shape}, esperaba {P_ref.shape}"
    assert np.all(np.isfinite(P_cand)), "NaN/inf"
    dia = datos().dia[W:CORTE]
    d = mbits_fila(P_cand, y) - mbits_fila(P_ref, y)
    n = len(d); h = n // 2
    pc, pr = puestos(P_cand, y), puestos(P_ref, y)
    out = {
        "n": n,
        "mbits_cand": float(mbits_fila(P_cand, y).mean()),
        "mbits_ens": float(mbits_fila(P_ref, y).mean()),
        "delta_mbits": ic_bloques(d, dia),
        "delta_mitad1": ic_bloques(d[:h], dia[:h]),
        "delta_mitad2": ic_bloques(d[h:], dia[h:]),
        "top3_cand": float((pc <= 3).mean()), "top3_ens": float((pr <= 3).mean()),
        "top5_cand": float((pc <= 5).mean()), "top5_ens": float((pr <= 5).mean()),
        "top15_cand": float((pc <= 15).mean()), "top15_ens": float((pr <= 15).mean()),
        "ret_t5_cand": float(retorno_t5(pc).mean()), "ret_t5_ens": float(retorno_t5(pr).mean()),
        "delta_ret_t5": ic_bloques(retorno_t5(pc) - retorno_t5(pr), dia),
    }
    lo1, lo2 = out["delta_mitad1"][1], out["delta_mitad2"][1]
    out["pasa_barra_dev"] = bool(out["delta_mbits"][0] >= 3.0 and out["delta_mbits"][1] > 0
                                 and out["delta_mitad1"][0] > 0 and out["delta_mitad2"][0] > 0)
    return out


def informe(P_cand, nombre="candidato"):
    r = evaluar(P_cand)
    f = lambda t: f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}]"
    return "\n".join([
        f"== {nombre} (desarrollo n={r['n']}) ==",
        f"mbits: cand {r['mbits_cand']:+.1f} · ensamble {r['mbits_ens']:+.1f}",
        f"Delta mbits {f(r['delta_mbits'])} · mitad1 {f(r['delta_mitad1'])} · mitad2 {f(r['delta_mitad2'])}",
        f"Top-3 {r['top3_cand']*100:.2f}% vs {r['top3_ens']*100:.2f}% · Top-5 {r['top5_cand']*100:.2f}% vs "
        f"{r['top5_ens']*100:.2f}% · Top-15 {r['top15_cand']*100:.2f}% vs {r['top15_ens']*100:.2f}%",
        f"Top-5 escalonado por ficha: {r['ret_t5_cand']*100:+.2f}% vs {r['ret_t5_ens']*100:+.2f}% · delta {f(r['delta_ret_t5'])}",
        f"PASA BARRA DEV: {r['pasa_barra_dev']}",
    ])


if __name__ == "__main__":
    P, y = base()
    print(informe(P, "ensamble_v2 contra sí mismo (control: delta 0)"))
    U = np.full_like(P, 1 / K)
    print(informe(U, "uniforme (control: delta muy negativo)"))
