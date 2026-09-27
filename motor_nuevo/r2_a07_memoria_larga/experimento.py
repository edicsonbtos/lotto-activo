# -*- coding: utf-8 -*-
"""r2_a07_memoria_larga: memoria SEMANAL del operador sobre ag12 V1 (ver PREREGISTRO.md).
(a) par s1-i del mismo día de la semana (hace 7/14/21/28 días), (b) misma hora hace 7 (y 14/21/28) días,
(c) composición del día (completar un par de un día con el que hoy ya comparte pares). Placebo: desfases 6/8/13/15/...
Reajuste completo: log P_ens offset + 33 var de ag12 V1 + nuevas, λ=30, cross-fit en los mismos 5 bloques de jornada.
Métrica: Δ mbits frente a ag12 V1 (P_V1.npy). Solo filas [2000, 9357).
Uso (PowerShell, raíz del worktree):  $env:PYTHONIOENCODING='utf-8'; python motor_nuevo/r2_a07_memoria_larga/experimento.py
"""
import json, os, sys, time
from collections import defaultdict
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
K = 38
SEM = [7, 14, 21, 28]
PLA = [6, 8, 13, 15, 20, 22, 27, 29]
LMAX_SONDEO = 35
NOMBRES_NUEVOS = ["PS", "HS1", "HS2", "PP", "HP1", "HP2", "CS"]


def rasgos_nuevos(D, desde, P_ref, y):
    seq = np.asarray(D.seq); hora = np.asarray(D.hora); dia = np.asarray(D.dia)
    n = len(seq); m = n - desde
    X = np.zeros((m, K, len(NOMBRES_NUEVOS)))
    # sondeo: (tipo, L) -> [obs, esp] y por mitades
    son = defaultdict(lambda: np.zeros(6))   # obs, esp, obs_m1, esp_m1, obs_m2, esp_m2
    h_mitad = m // 2
    vec = defaultdict(lambda: defaultdict(list))   # día -> animal -> vecinos adyacentes (ambos órdenes)
    upares = defaultdict(set)                       # día -> pares adyacentes no ordenados
    dhora = defaultdict(dict)                       # día -> hora -> animal
    hoy_pares = set()
    for t in range(n):
        d = int(dia[t]); mismo = t >= 1 and dia[t - 1] == dia[t]
        if not mismo:
            hoy_pares = set()
        if t >= desde:
            j = t - desde; x = X[j]; h = int(hora[t])
            s1 = int(seq[t - 1]) if mismo else None
            if s1 is not None:
                for L in SEM:
                    for b in vec.get(d - L, {}).get(s1, ()):
                        x[b, 0] += 1
                for L in PLA:
                    for b in vec.get(d - L, {}).get(s1, ()):
                        x[b, 3] += 0.5
                for L in range(1, 29):
                    dd = d - L
                    if dd in upares and s1 in vec[dd]:
                        sh = len(hoy_pares & upares[dd])
                        if sh:
                            for b in vec[dd][s1]:
                                x[b, 6] += sh
            a7 = dhora.get(d - 7, {}).get(h)
            if a7 is not None: x[a7, 1] += 1
            for L in (14, 21, 28):
                a = dhora.get(d - L, {}).get(h)
                if a is not None: x[a, 2] += 1
            for L in (6, 8):
                a = dhora.get(d - L, {}).get(h)
                if a is not None: x[a, 4] += 0.5
            for L in (13, 15, 20, 22, 27, 29):
                a = dhora.get(d - L, {}).get(h)
                if a is not None: x[a, 5] += 0.5
            # sondeo descriptivo por desfase exacto
            p = P_ref[j]; yy = int(y[j]); mi = 0 if j < h_mitad else 1
            for L in range(1, LMAX_SONDEO + 1):
                dd = d - L
                if s1 is not None and dd in vec:
                    msk = np.zeros(K, bool); msk[list(set(vec[dd].get(s1, ())))] = True
                    if msk.any():
                        r = son[("par", L)]; o = float(msk[yy]); e = float(p[msk].sum())
                        r[0] += o; r[1] += e; r[2 + 2 * mi] += o; r[3 + 2 * mi] += e
                a = dhora.get(dd, {}).get(h)
                if a is not None:
                    r = son[("hora", L)]; o = float(a == yy); e = float(p[a])
                    r[0] += o; r[1] += e; r[2 + 2 * mi] += o; r[3 + 2 * mi] += e
        # registrar el sorteo t (queda disponible para filas posteriores)
        dhora[d][int(hora[t])] = int(seq[t])
        if mismo:
            a, b = int(seq[t - 1]), int(seq[t])
            vec[d][a].append(b); vec[d][b].append(a)
            up = (min(a, b), max(a, b)); upares[d].add(up); hoy_pares.add(up)
    X[:, :, 6] = np.log1p(X[:, :, 6])
    return X, son


def main():
    t0 = time.time()
    D = A.datos().prefijo(A.CORTE)
    Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True)
    LPE = np.log(np.clip(Pens, 1e-12, None))
    P_ref = np.load(os.path.join(MN, "ag12_transiciones", "P_V1.npy"))
    X33, _ = R12.construir(D, A.W); X33 = X33.astype(np.float64)
    XN, son = rasgos_nuevos(D, A.W, P_ref, y)
    dia = np.asarray(D.dia[A.W:A.CORTE]); blo = E2.bloques_jornada(dia)
    assert len(y) == len(X33) == len(XN) == len(P_ref)
    print(f"rasgos listos [{time.time()-t0:.0f} s]", flush=True)
    res, out = {"nuevos": NOMBRES_NUEVOS}, []
    res["frecuencia_no_cero_por_sorteo"] = {nm: float((XN[:, :, c] > 0).sum(1).mean()) for c, nm in enumerate(NOMBRES_NUEVOS)}
    print("candidatos marcados por sorteo:", res["frecuencia_no_cero_por_sorteo"], flush=True)
    fmt = lambda t: f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}]"

    # ---- sondeo descriptivo ----
    lin = ["SONDEO O/E frente a ag12 V1 por desfase exacto L (días naturales)",
           "tipo  L   obs    esp     O/E    z     | m1 O/E  m2 O/E"]
    son_out = {}
    for tipo in ("par", "hora"):
        for L in range(1, LMAX_SONDEO + 1):
            r = son.get((tipo, L))
            if r is None or r[1] == 0: continue
            z = (r[0] - r[1]) / np.sqrt(r[1])
            son_out[f"{tipo}_{L}"] = [float(v) for v in r] + [float(z)]
            mark = " <- semana" if L % 7 == 0 else ""
            lin.append(f"{tipo:5s} {L:2d} {r[0]:6.0f} {r[1]:7.1f}  {r[0]/r[1]:5.3f} {z:+6.2f}  | "
                       f"{r[2]/max(r[3],1e-9):5.3f}  {r[4]/max(r[5],1e-9):5.3f}{mark}")
        for nombre, Ls in (("SEMANA 7/14/21/28", SEM), ("PLACEBO 6/8/13/15/20/22/27/29", PLA)):
            o = sum(son[(tipo, L)][0] for L in Ls); e = sum(son[(tipo, L)][1] for L in Ls)
            z = (o - e) / np.sqrt(e)
            son_out[f"{tipo}_{nombre}"] = [float(o), float(e), float(o / e), float(z)]
            lin.append(f"  {tipo} agregado {nombre}: obs {o:.0f} esp {e:.1f} O/E {o/e:.3f} z {z:+.2f}")
    res["sondeo"] = son_out
    print("\n".join(lin), flush=True); out.append("\n".join(lin))

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

    def fit(Xc, tr): return E2.ajustar_lineal(Xc[tr], LPE[tr], y[tr], LAM)
    def pred(Xc, w, te): return E2.predecir_lineal(w, Xc[te], LPE[te])

    def cf(Xc, etiqueta):
        P, pars = E2.cross_fit(lambda tr: fit(Xc, tr), lambda w, te: pred(Xc, w, te), blo)
        W = np.array(pars)[:, 33:]
        res[f"pesos_{etiqueta}"] = W.round(4).tolist()
        print(f"   pesos nuevos por bloque ({etiqueta}):\n{np.round(W, 3)}", flush=True)
        return P

    # control: reproducir V1
    Pv1 = E2.cross_fit(lambda tr: fit(X33, tr), lambda w, te: pred(X33, w, te), blo)[0]
    res["control_max_abs_Pv1"] = float(np.abs(Pv1 - P_ref).max())
    print("control V1 reproducido, max |P - P_V1| =", res["control_max_abs_Pv1"], flush=True)

    X1 = np.concatenate([X33, XN[:, :, 0:3]], axis=2)
    X2 = np.concatenate([X33, XN[:, :, 3:6]], axis=2)
    X3 = np.concatenate([X33, XN[:, :, 6:7]], axis=2)
    P1 = cf(X1, "V1_PS_HS1_HS2"); r1 = rep("V1_primaria_semana", P1)
    P2 = cf(X2, "V2_PP_HP1_HP2"); r2 = rep("V2_placebo_desfases_no_naturales", P2)
    P3 = cf(X3, "V3_CS"); r3 = rep("V3_composicion_dia", P3)
    np.save(os.path.join(AQUI, "P_V1sem.npy"), P1)
    dd = A.mbits_fila(P1, y) - A.mbits_fila(P2, y)
    res["V1_menos_placebo"] = A.ic_bloques(dd, dia)
    s = f"Δ(V1) − Δ(V2 placebo) = {fmt(res['V1_menos_placebo'])}"; print(s); out.append(s)

    # forward informativo (V1 frente al forward de ag12 V1, mismo procedimiento)
    fw = lambda Xc: E2.forward(lambda tr: fit(Xc, tr), lambda w, te: pred(Xc, w, te), blo)
    P1f = fw(X1); P33f = fw(X33)
    P1f[blo == 0] = P_ref[blo == 0]; P33f[blo == 0] = P_ref[blo == 0]
    rep("V1_forward_vs_ag12_forward", P1f, ref=P33f, etiqueta="ag12 V1 forward")
    m = blo >= 1
    res["V1_forward_bloques1a4"] = A.ic_bloques(A.mbits_fila(P1f[m], y[m]) - A.mbits_fila(P33f[m], y[m]), dia[m])
    s = f"V1 forward (solo bloques 1-4, n={m.sum()}): {fmt(res['V1_forward_bloques1a4'])}"; print(s); out.append(s)
    P3f = fw(X3); P3f[blo == 0] = P_ref[blo == 0]
    res["V3_forward_bloques1a4"] = A.ic_bloques(A.mbits_fila(P3f[m], y[m]) - A.mbits_fila(P33f[m], y[m]), dia[m])
    s = f"V3 forward (solo bloques 1-4): {fmt(res['V3_forward_bloques1a4'])}"; print(s); out.append(s)
    print(f"[{time.time()-t0:.0f} s]", flush=True)

    json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    open(os.path.join(AQUI, "salida_experimento.txt"), "w", encoding="utf-8").write("\n\n".join(out) + "\n")


if __name__ == "__main__":
    main()
