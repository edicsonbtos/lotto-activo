# -*- coding: utf-8 -*-
"""r2_a01_forma_transicion: forma continua del mecanismo de pares (edad en sorteos, decaimiento exponencial,
repeticiones, hora). Reajuste completo (log P_ens offset + 33 var de ag12 V1 + nuevas), cross-fit 5 bloques de
jornada (los mismos de ag02/ag12), vida media elegida dentro de cada pliegue de entrenamiento.
Métrica: Δmbits frente a ag12 V1 (P_V1.npy).
Uso (PowerShell):  $env:PYTHONIOENCODING='utf-8'; python motor_nuevo/r2_a01_forma_transicion/experimento.py
"""
import json, os, sys, time
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI)
sys.path.insert(0, MN); sys.path.insert(0, os.path.join(MN, "ag02_residuo_boost"))
sys.path.insert(0, os.path.join(MN, "ag12_transiciones"))
import arnes as A  # noqa
import importlib.util as _iu
_sp = _iu.spec_from_file_location('exp_ag02', os.path.join(MN, 'ag02_residuo_boost', 'experimento.py'))
E2 = _iu.module_from_spec(_sp); _sp.loader.exec_module(E2)
import rasgos12 as R12  # noqa

LAM = 30.0
GRID = np.array([6, 12, 24, 48, 96, 192], float)   # vidas medias en sorteos
G = len(GRID)
K = 38


def rasgos_nuevos(D, desde):
    """EF[j,i,g], ER[j,i,g], HM[j,i,g] (sumas decaídas, sin log), N2[j,i] (conteo en 30 jornadas)."""
    seq = np.asarray(D.seq); hora = np.asarray(D.hora)
    _, dn = np.unique(np.asarray(D.dia), return_inverse=True)
    n = len(seq); m = n - desde
    EF = np.zeros((m, K, G)); ER = np.zeros((m, K, G)); HM = np.zeros((m, K, G)); N2 = np.zeros((m, K))
    fwd = {a: [] for a in range(K)}   # a -> [(t_ocurr, b, jornada, hora_b)]
    bwd = {b: [] for b in range(K)}   # b -> [(t_ocurr, a)]
    for t in range(n):
        if t >= desde and t >= 1 and dn[t - 1] == dn[t]:
            s1 = int(seq[t - 1]); j = t - desde
            L = fwd[s1]
            if L:
                arr = np.array(L, float)
                age = t - arr[:, 0]; b = arr[:, 1].astype(int)
                w = 2.0 ** (-age[:, None] / GRID[None, :])            # (occ, G)
                np.add.at(EF[j], b, w)
                same = arr[:, 3] == hora[t]
                if same.any():
                    np.add.at(HM[j], b[same], w[same])
                rec = (dn[t] - arr[:, 2]) <= 30
                if rec.any():
                    np.add.at(N2[j], b[rec], 1.0)
            L = bwd[s1]
            if L:
                arr = np.array(L, float)
                age = t - arr[:, 0]; a = arr[:, 1].astype(int)
                w = 2.0 ** (-age[:, None] / GRID[None, :])
                np.add.at(ER[j], a, w)
        if t >= 1 and dn[t - 1] == dn[t]:
            a, b = int(seq[t - 1]), int(seq[t])
            fwd[a].append((t, b, dn[t], hora[t]))
            bwd[b].append((t, a))
    return EF, ER, HM, N2


def matriz(Xbase, EF, ER, extra_fn, idx, gf, gr):
    return np.concatenate([Xbase[idx], np.log1p(EF[idx][:, :, gf:gf + 1]), np.log1p(ER[idx][:, :, gr:gr + 1])]
                          + extra_fn(idx, gf), axis=2)


def ajustar_con_h(Xbase, EF, ER, extra_fn, LPE, y, tr):
    """Elige (h_f, h_r) por verosimilitud penalizada de ENTRENAMIENTO; devuelve (w, gf, gr, perdida)."""
    mejor = None
    for gf in range(G):
        for gr in range(G):
            Xc = matriz(Xbase, EF, ER, extra_fn, tr, gf, gr)
            w = E2.ajustar_lineal(Xc, LPE[tr], y[tr], LAM)
            loss = E2._perdida(w, Xc, LPE[tr], y[tr], LAM)[0]
            if mejor is None or loss < mejor[3]:
                mejor = (w, gf, gr, loss)
    return mejor


def correr(Xbase, EF, ER, extra_fn, LPE, y, blo, modo="cf"):
    P = np.full((len(y), K), np.nan); info = []
    ks = range(blo.max() + 1) if modo == "cf" else range(1, blo.max() + 1)
    for k in ks:
        tr = (blo != k) if modo == "cf" else (blo < k); te = blo == k
        w, gf, gr, loss = ajustar_con_h(Xbase, EF, ER, extra_fn, LPE, y, tr)
        P[te] = E2.predecir_lineal(w, matriz(Xbase, EF, ER, extra_fn, te, gf, gr), LPE[te])
        nb = Xbase.shape[2]
        info.append({"bloque": int(k), "h_f": float(GRID[gf]), "h_r": float(GRID[gr]),
                     "pesos_nuevos": [round(float(v), 4) for v in w[nb:]],
                     "pesos_ventanas_T1T2T3R1R2R3": [round(float(v), 4) for v in w[27:33]] if nb == 33 else None})
        print(f"   bloque {k}: h_f={GRID[gf]:g} h_r={GRID[gr]:g} pesos nuevos {np.round(w[nb:], 3)}"
              + (f" ventanas {np.round(w[27:33], 3)}" if nb == 33 else ""), flush=True)
    return P, info


def main():
    t0 = time.time()
    D = A.datos().prefijo(A.CORTE)
    Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True)
    LPE = np.log(np.clip(Pens, 1e-12, None))
    P_ref = np.load(os.path.join(MN, "ag12_transiciones", "P_V1.npy"))
    X33, _ = R12.construir(D, A.W); X33 = X33.astype(np.float64)
    EF, ER, HM, N2 = rasgos_nuevos(D, A.W)
    dia = np.asarray(D.dia[A.W:A.CORTE]); blo = E2.bloques_jornada(dia)
    assert len(y) == len(X33) == len(EF) == len(P_ref)
    print(f"rasgos listos [{time.time()-t0:.0f} s]", flush=True)
    res, out = {"grid_vida_media_sorteos": GRID.tolist()}, []
    fmt = lambda t: f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}]"

    def rep(nombre, Pc, ref=P_ref, etiqueta="ag12 V1"):
        r = A.evaluar(Pc, P_ref=ref, y=y)
        s = (f"== {nombre} (Δ frente a {etiqueta}) ==\n"
             f"mbits cand {r['mbits_cand']:+.2f} · ref {r['mbits_ens']:+.2f}\n"
             f"Delta {fmt(r['delta_mbits'])} · mitad1 {fmt(r['delta_mitad1'])} · mitad2 {fmt(r['delta_mitad2'])}\n"
             f"Top-3 {r['top3_cand']*100:.2f}% vs {r['top3_ens']*100:.2f}% · Top-5 {r['top5_cand']*100:.2f}% vs {r['top5_ens']*100:.2f}% · "
             f"Top-15 {r['top15_cand']*100:.2f}% vs {r['top15_ens']*100:.2f}%\n"
             f"Top-5 escalonado/ficha {r['ret_t5_cand']*100:+.2f}% vs {r['ret_t5_ens']*100:+.2f}% · delta {fmt(r['delta_ret_t5'])}\n"
             f"PASA BARRA DEV: {r['pasa_barra_dev']}")
        print(s, flush=True); out.append(s); res[nombre] = r
        return r

    sin = lambda idx, gf: []
    conBH = lambda idx, gf: [np.log1p(np.maximum(N2[idx] - 1, 0))[:, :, None], np.log1p(HM[idx][:, :, gf:gf + 1])]

    # Control: reproducir V1 con el mismo código (debe coincidir con P_V1)
    Pv1, _ = E2.cross_fit(lambda tr: E2.ajustar_lineal(X33[tr], LPE[tr], y[tr], LAM),
                          lambda w, te: E2.predecir_lineal(w, X33[te], LPE[te]), blo)
    res["control_max_abs_Pv1"] = float(np.abs(Pv1 - P_ref).max())
    print("control V1 reproducido, max |P - P_V1| =", res["control_max_abs_Pv1"], flush=True)

    print("A (primaria)", flush=True)
    PA, infoA = correr(X33, EF, ER, sin, LPE, y, blo); res["info_A"] = infoA
    np.save(os.path.join(AQUI, "P_A.npy"), PA)
    rep("A_primaria_33V1_mas_EF_ER_sorteos", PA)
    print(f"[{time.time()-t0:.0f} s]", flush=True)

    print("A forward (informativo)", flush=True)
    PAf, infoAf = correr(X33, EF, ER, sin, LPE, y, blo, modo="fw"); res["info_A_forward"] = infoAf
    PAf[blo == 0] = P_ref[blo == 0]
    rep("A_forward_vs_P_V1", PAf)
    Pv1f = E2.forward(lambda tr: E2.ajustar_lineal(X33[tr], LPE[tr], y[tr], LAM),
                      lambda w, te: E2.predecir_lineal(w, X33[te], LPE[te]), blo)
    Pv1f[blo == 0] = P_ref[blo == 0]
    rep("A_forward_vs_V1_forward", PAf, ref=Pv1f, etiqueta="ag12 V1 forward")
    print(f"[{time.time()-t0:.0f} s]", flush=True)

    print("B (repeticiones + hora)", flush=True)
    PB, infoB = correr(X33, EF, ER, conBH, LPE, y, blo); res["info_B"] = infoB
    rep("B_A_mas_N2_HM", PB)

    print("C (reemplazo de ventanas)", flush=True)
    PC, infoC = correr(X33[:, :, :27], EF, ER, sin, LPE, y, blo); res["info_C"] = infoC
    rep("C_27ag02_mas_EF_ER", PC)
    print(f"[{time.time()-t0:.0f} s]", flush=True)

    json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    open(os.path.join(AQUI, "salida_experimento.txt"), "w", encoding="utf-8").write("\n\n".join(out) + "\n")


if __name__ == "__main__":
    main()
