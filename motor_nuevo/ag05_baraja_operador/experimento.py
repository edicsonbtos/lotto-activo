# -*- coding: utf-8 -*-
"""ag05_baraja_operador: modelos generativos "baraja/cuota" del operador, verosimilitud exacta
(producto de condicionales), cross-fitting en 5 bloques contiguos de jornadas, y apilado sobre el
ensamble_v2. Solo filas [2000, 9357). Determinista (sin azar salvo el bootstrap del arnés, con semilla).

Uso:  PYTHONIOENCODING=utf-8 python experimento.py [--sub N]   (--sub = prueba en las primeras N filas)
"""
import json, math, os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import arnes as A  # noqa: E402
import baraja as B  # noqa: E402

SUB = int(sys.argv[sys.argv.index("--sub") + 1]) if "--sub" in sys.argv else None


def main():
    t0 = time.time()
    D = A.datos().prefijo(A.CORTE)                 # nunca filas >= 9357
    P_ens, y = A.base()
    P_ens = P_ens / P_ens.sum(1, keepdims=True)
    n = len(y) if SUB is None else SUB
    P_ens, y = P_ens[:n], y[:n]
    assert np.array_equal(y, D.seq[A.W:A.W + n])
    Lens = np.log(np.clip(P_ens, 1e-12, None))
    dia = D.dia[A.W:A.W + n]
    ud = np.unique(dia)
    cortes = np.array_split(ud, 5)
    bloque = np.zeros(n, int)
    for b, ds in enumerate(cortes):
        bloque[np.isin(dia, ds)] = b

    st = B.estado(D)
    cfgs = B.configs()
    X = {B.nombre(c): B.construir(D, A.W, c, st)[:n] for c in cfgs}
    print(f"variables listas ({len(cfgs)} configuraciones) {time.time()-t0:.0f} s", flush=True)

    res = {"configs": {}, "seleccion": {"solo": [], "apilado": []}}
    LP_solo_cf = {k: np.zeros((n, 38)) for k in X}
    LP_stack_cf = {k: np.zeros((n, 38)) for k in X}
    ll_tr = {k: {"solo": [], "apilado": []} for k in X}
    thetas = {k: [] for k in X}
    for b in range(5):
        tr, te = bloque != b, bloque == b
        for k, Xk in X.items():
            th_s, ll_s = B.ajustar(Xk[tr], y[tr])
            th_a, ll_a = B.ajustar(Xk[tr], y[tr], Lens[tr])
            LP_solo_cf[k][te] = B.logp(Xk[te], th_s)
            LP_stack_cf[k][te] = B.logp(Xk[te], th_a, Lens[te])
            ll_tr[k]["solo"].append(ll_s); ll_tr[k]["apilado"].append(ll_a)
            thetas[k].append(th_a.tolist())
        print(f"bloque {b} ajustado {time.time()-t0:.0f} s", flush=True)

    # selección por BIC en entrenamiento, por bloque (nested: nunca mira el bloque retenido)
    LP_best_solo = np.zeros((n, 38)); LP_best_stack = np.zeros((n, 38))
    for b in range(5):
        te = bloque == b; ntr = int((bloque != b).sum())
        for modo, LPcf, dest in (("solo", LP_solo_cf, LP_best_solo), ("apilado", LP_stack_cf, LP_best_stack)):
            bic = {k: -2 * ll_tr[k][modo][b] + X[k].shape[2] * math.log(ntr) for k in X}
            kb = min(bic, key=bic.get)
            dest[te] = LPcf[kb][te]
            res["seleccion"][modo].append(kb)
    print("elegidos solo:", res["seleccion"]["solo"])
    print("elegidos apilado:", res["seleccion"]["apilado"])

    rows = np.arange(n)
    mb = lambda LP: float(1000 * np.mean((LP[rows, y] + math.log(38)) / math.log(2)))
    mb_ens = mb(Lens)
    print(f"\nmbits frente al uniforme (cross-fit), ensamble = {mb_ens:+.2f}")
    print(f"{'config':<12} {'solo':>8} {'apilado':>8} {'Δ apil':>8}  theta apilado (media 5 bloques)")
    for k in X:
        s, a = mb(LP_solo_cf[k]), mb(LP_stack_cf[k])
        th = np.mean(thetas[k], 0)
        res["configs"][k] = {"mbits_solo": s, "mbits_apilado": a, "delta_apilado": a - mb_ens,
                             "theta_apilado_media": th.tolist(),
                             "ll_train_solo_bloque0": ll_tr[k]["solo"][0]}
        print(f"{k:<12} {s:+8.2f} {a:+8.2f} {a-mb_ens:+8.2f}  {np.round(th, 3).tolist()}")

    # dispersión entre fases (informativa): ¿destaca alguna fase de G2/G3?
    print("\nDispersión entre fases (mbits solo, cross-fit):")
    for fam, grupos in (("G2_2", [f"G2_2_{p}" for p in range(2)]), ("G2_3", [f"G2_3_{p}" for p in range(3)]),
                        ("G2_4", [f"G2_4_{p}" for p in range(4)]), ("G3", [f"G3_{p}" for p in range(38)])):
        v = np.array([res["configs"][g]["mbits_solo"] for g in grupos])
        print(f"  {fam}: min {v.min():+.2f} max {v.max():+.2f} rango {v.max()-v.min():.2f}  (G1 = {res['configs']['G1']['mbits_solo']:+.2f})")
        res.setdefault("fases", {})[fam] = v.tolist()

    P_prim = np.exp(LP_best_stack)
    P_solo = np.exp(LP_best_solo)
    if SUB is None:
        print()
        print(A.informe(P_prim, "PRIMARIO: apilado ensamble + mejor baraja (BIC en entrenamiento)"))
        print()
        print(A.informe(P_solo, "informativo: mejor baraja SOLA"))
        res["primario"] = A.evaluar(P_prim)
        res["solo"] = A.evaluar(P_solo)
        # informativo: cada familia apilada con su mejor config fija (no candidato)
        for k in ("G1", "G2_3_0", "G4_36", "G5"):
            if k in LP_stack_cf:
                r = A.evaluar(np.exp(LP_stack_cf[k]))
                res.setdefault("apilados_fijos", {})[k] = r
                print(f"apilado fijo {k}: Δ {r['delta_mbits'][0]:+.2f} [{r['delta_mbits'][1]:+.2f}, {r['delta_mbits'][2]:+.2f}]")
        np.save(os.path.join(AQUI, "P_primario.npy"), P_prim.astype(np.float32))
        with open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
    print(f"\ntotal {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
