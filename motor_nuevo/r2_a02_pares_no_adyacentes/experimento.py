# -*- coding: utf-8 -*-
"""r2_a02_pares_no_adyacentes: ¿evita el operador pares NO adyacentes / misma posición relativa recientes?
Barrido 24 pruebas frente a P_V1 (ag12 V1) con BH en mitad 1 + confirmación en mitad 2; luego modelo.
Uso: PYTHONIOENCODING=utf-8 python motor_nuevo/r2_a02_pares_no_adyacentes/experimento.py
Solo filas < 9357 (datos().prefijo(CORTE)). Ver PREREGISTRO.md.
"""
import json, math, os, sys, time
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI)
sys.path.insert(0, MN); sys.path.insert(0, os.path.join(MN, "ag12_transiciones"))
import arnes as A  # noqa
import importlib.util as _iu
_sp = _iu.spec_from_file_location('exp_ag02', os.path.join(MN, 'ag02_residuo_boost', 'experimento.py'))
E2 = _iu.module_from_spec(_sp); _sp.loader.exec_module(E2)
import rasgos12 as R12  # noqa

K = 38; LAM = 30.0
FAM = ["A_s2i_desf2", "B_is2_desf2", "C_s1i_desf3+", "D_is1_desf3+", "E_s1i_mismas_horas", "F_s1i_otras_horas"]
VENT = [(1, 1), (2, 7), (8, 30), (31, 90)]
NOMBRES = [f"{f}@{lo}-{hi}" for f in FAM for (lo, hi) in VENT]
MAXAGE = 90


def rasgos(D, desde):
    """(n-desde, 38, 24) conteos. Fila t usa solo seq[:t] y hora/día de t."""
    seq = np.asarray(D.seq).astype(int); hora = np.asarray(D.hora).astype(int)
    _, dn = np.unique(np.asarray(D.dia), return_inverse=True)
    n = len(seq)
    X = np.zeros((n - desde, K, len(FAM) * len(VENT)), np.float32)
    f1 = [[] for _ in range(K)]    # a -> (jornada, b, hora_a, hora_b) consecutivos
    f2 = [[] for _ in range(K)]    # a -> (jornada, b) desfase 2 (a antes)
    b2 = [[] for _ in range(K)]    # b -> (jornada, a) desfase 2
    f3 = [[] for _ in range(K)]    # a -> (jornada, b) desfase >= 3 mismo día
    b3 = [[] for _ in range(K)]    # b -> (jornada, a)
    hoy = []                       # [(hora, animal)] del día actual (ya salidos)

    def win(age):
        for v, (lo, hi) in enumerate(VENT):
            if lo <= age <= hi:
                return v
        return -1

    def poda(L, d):
        i = 0
        while i < len(L) and d - L[i][0] > MAXAGE:
            i += 1
        if i:
            del L[:i]

    for t in range(n):
        d = dn[t]
        if t >= 1 and dn[t - 1] != d:
            hoy = []
        k = len(hoy)
        if t >= desde:
            x = X[t - desde]
            if k >= 1:
                s1 = seq[t - 1]
                for (jd, b, ha, hb) in f1[s1]:
                    v = win(d - jd)
                    if v < 0:
                        continue
                    fam = 4 if (ha == hora[t - 1] and hb == hora[t]) else 5
                    x[b, fam * 4 + v] += 1
                for (jd, b) in f3[s1]:
                    v = win(d - jd)
                    if v >= 0:
                        x[b, 2 * 4 + v] += 1
                for (jd, a) in b3[s1]:
                    v = win(d - jd)
                    if v >= 0:
                        x[a, 3 * 4 + v] += 1
            if k >= 2:
                s2 = seq[t - 2]
                for (jd, b) in f2[s2]:
                    v = win(d - jd)
                    if v >= 0:
                        x[b, 0 * 4 + v] += 1
                for (jd, a) in b2[s2]:
                    v = win(d - jd)
                    if v >= 0:
                        x[a, 1 * 4 + v] += 1
        # registrar el sorteo t (ya predicho)
        s = int(seq[t])
        for j, (hh, a) in enumerate(hoy):
            lag = k - j
            if lag == 1:
                f1[a].append((d, s, hh, int(hora[t])))
            elif lag == 2:
                f2[a].append((d, s)); b2[s].append((d, a))
            else:
                f3[a].append((d, s)); b3[s].append((d, a))
        hoy.append((int(hora[t]), s))
        if t % 200 == 0:
            for L in (f1, f2, b2, f3, b3):
                for l in L:
                    poda(l, d)
    return X


def _ncdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def prueba(mask, P, y):
    o = int(mask[np.arange(len(y)), y].sum())
    pm = (P * mask).sum(1)
    e = float(pm.sum()); v = float((pm * (1 - pm)).sum())
    z = (o - e) / math.sqrt(v) if v > 0 else 0.0
    return dict(obs=o, esp=round(e, 1), OE=round(o / e, 3) if e > 0 else None, z=round(z, 2),
                p_bil=2 * (1 - _ncdf(abs(z))), p_uni_neg=_ncdf(z), p_uni_pos=1 - _ncdf(z))


def bh(p, q=0.05):
    p = np.asarray(p); m = len(p); o = np.argsort(p)
    ok = p[o] <= q * (np.arange(1, m + 1) / m)
    kmax = int(np.max(np.where(ok)[0]) + 1) if ok.any() else 0
    r = np.zeros(m, bool); r[o[:kmax]] = True
    return r


def main():
    t0 = time.time()
    D = A.datos().prefijo(A.CORTE)
    Pens, y = A.base(); Pens = Pens / Pens.sum(1, keepdims=True)
    LPE = np.log(np.clip(Pens, 1e-12, None))
    P_ref = np.load(os.path.join(MN, "ag12_transiciones", "P_V1.npy"))
    P_ref = P_ref / P_ref.sum(1, keepdims=True); LPR = np.log(np.clip(P_ref, 1e-12, None))
    dia = np.asarray(D.dia[A.W:A.CORTE]); blo = E2.bloques_jornada(dia)
    n = len(y); h = n // 2
    Xn = rasgos(D, A.W)
    print(f"rasgos {Xn.shape} [{time.time()-t0:.0f} s]", flush=True)
    res = {"barrido": {}}
    # ---------------- barrido ----------------
    p1 = []
    for f, nm in enumerate(NOMBRES):
        M = Xn[:, :, f] >= 1
        r1 = prueba(M[:h], P_ref[:h], y[:h]); r2 = prueba(M[h:], P_ref[h:], y[h:]); rt = prueba(M, P_ref, y)
        res["barrido"][nm] = {"mitad1": r1, "mitad2": r2, "total": rt}
        p1.append(r1["p_bil"])
    sig1 = bh(p1)
    surv = []
    print(f"\n{'prueba':30s} | mitad1 obs/esp O/E z | mitad2 obs/esp O/E z | total O/E z | BH1 conf2")
    for f, nm in enumerate(NOMBRES):
        b = res["barrido"][nm]; r1, r2, rt = b["mitad1"], b["mitad2"], b["total"]
        conf = False
        if sig1[f]:
            conf = (r2["p_uni_neg"] < 0.05) if r1["z"] < 0 else (r2["p_uni_pos"] < 0.05)
        b["BH_mitad1"] = bool(sig1[f]); b["confirma_mitad2"] = bool(conf)
        if sig1[f] and conf:
            surv.append(f)
        print(f"{nm:30s} | {r1['obs']:4d}/{r1['esp']:7.1f} {r1['OE']} {r1['z']:+.2f} | "
              f"{r2['obs']:4d}/{r2['esp']:7.1f} {r2['OE']} {r2['z']:+.2f} | {rt['OE']} {rt['z']:+.2f} | {int(sig1[f])} {int(conf)}")
    res["sobrevivientes"] = [NOMBRES[f] for f in surv]
    print("\nSOBREVIVIENTES:", res["sobrevivientes"], flush=True)
    Xl = np.log1p(Xn).astype(np.float64)

    def rep(nombre, Pc, Pr=P_ref):
        r = A.evaluar(Pc, P_ref=Pr, y=y); res[nombre] = r
        f_ = lambda t: f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}]"
        s = (f"== {nombre} ==\nDelta mbits vs ref {f_(r['delta_mbits'])} · m1 {f_(r['delta_mitad1'])} · "
             f"m2 {f_(r['delta_mitad2'])}\nTop-5 {r['top5_cand']*100:.2f}% vs {r['top5_ens']*100:.2f}% · "
             f"Top-15 {r['top15_cand']*100:.2f}% vs {r['top15_ens']*100:.2f}% · ret T5 {r['ret_t5_cand']*100:+.2f}% vs "
             f"{r['ret_t5_ens']*100:+.2f}% · PASA {r['pasa_barra_dev']}")
        print(s, flush=True); return r

    def corr_cf(cols):
        Xc = Xl[:, :, cols]
        P, pars = E2.cross_fit(lambda tr: E2.ajustar_lineal(Xc[tr], LPR[tr], y[tr], LAM),
                               lambda w, te: E2.predecir_lineal(w, Xc[te], LPR[te]), blo)
        return P, np.array(pars)

    def corr_fw(cols):
        Xc = Xl[:, :, cols]
        P = E2.forward(lambda tr: E2.ajustar_lineal(Xc[tr], LPR[tr], y[tr], LAM),
                       lambda w, te: E2.predecir_lineal(w, Xc[te], LPR[te]), blo)
        P[blo == 0] = P_ref[blo == 0]
        return P

    def fw_ic(Pa, Pb):
        dd = A.mbits_fila(Pa, y) - A.mbits_fila(Pb, y); m = blo > 0
        return A.ic_bloques(dd[m], dia[m])

    # ---------------- V1 / V2 ----------------
    if surv:
        P1, W1 = corr_cf(surv); rep("V1_correccion_sobre_ag12", P1)
        for i, f in enumerate(surv):
            print(f"  w {NOMBRES[f]:28s} {W1[:, i].mean():+.3f} [{W1[:, i].min():+.3f}, {W1[:, i].max():+.3f}]")
        res["V1_forward_bloques1a4"] = fw_ic(corr_fw(surv), P_ref)
        print("V1 forward (b1-4):", res["V1_forward_bloques1a4"])
        X12, _ = R12.construir(D, A.W); X12 = X12.astype(np.float64)
        XJ = np.concatenate([X12, Xl[:, :, surv]], axis=2)
        fitJ = lambda Xa: (lambda tr: E2.ajustar_lineal(Xa[tr], LPE[tr], y[tr], LAM))
        predJ = lambda Xa: (lambda w, te: E2.predecir_lineal(w, Xa[te], LPE[te]))
        P2, _ = E2.cross_fit(fitJ(XJ), predJ(XJ), blo); rep("V2_ag12_mas_sobrev_conjunto", P2)
        Ff = E2.forward(fitJ(XJ), predJ(XJ), blo); Ff[blo == 0] = Pens[blo == 0]
        Fa = E2.forward(fitJ(X12), predJ(X12), blo); Fa[blo == 0] = Pens[blo == 0]
        res["V2_forward_vs_ag12_forward_b1a4"] = fw_ic(Ff, Fa)
        print("V2 forward vs ag12 forward (b1-4):", res["V2_forward_vs_ag12_forward_b1a4"])
    else:
        print("Sin sobrevivientes: V1 = V2 = ag12 V1 (Delta 0 por definición).")
    # ---------------- V3 exploratoria ----------------
    todas = list(range(len(NOMBRES)))
    P3, W3 = corr_cf(todas); rep("V3_exploratoria_24var", P3)
    res["V3_pesos_media"] = {NOMBRES[i]: float(W3[:, i].mean()) for i in todas}
    for i in todas:
        print(f"  w {NOMBRES[i]:28s} {W3[:, i].mean():+.3f} [{W3[:, i].min():+.3f}, {W3[:, i].max():+.3f}]")
    res["V3_forward_bloques1a4"] = fw_ic(corr_fw(todas), P_ref)
    print("V3 forward (b1-4):", res["V3_forward_bloques1a4"])
    json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1)
    print(f"[{time.time()-t0:.0f} s]")


if __name__ == "__main__":
    main()
