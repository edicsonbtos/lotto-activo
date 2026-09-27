# -*- coding: utf-8 -*-
"""r2_a05_anti_patron_numerico: ¿el operador evita patrones NUMÉRICOS que ag02/ag12 no miden?

Etapa 1: barrido de 11 variables sobre ag12 V1 (score test por jornada), BH q=0,05 en mitad 1, confirmación en mitad 2.
Etapa 2: VA = corrección log P_V1 + seleccionadas (λ=30, cross-fit 5 bloques de jornada + forward); VB = las 11.
Solo desarrollo [2000, 9357). Uso (PowerShell, desde la raíz del worktree lotto-activo-motor):
  $env:PYTHONIOENCODING='utf-8'; python motor_nuevo/r2_a05_anti_patron_numerico/experimento.py
"""
import copy, json, math, os, sys, time
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); MN = os.path.dirname(AQUI)
sys.path.insert(0, MN)
import arnes as A  # noqa: E402
import importlib.util as _iu
_sp = _iu.spec_from_file_location('exp_ag02', os.path.join(MN, 'ag02_residuo_boost', 'experimento.py'))
E2 = _iu.module_from_spec(_sp); _sp.loader.exec_module(E2)

K = 38; LAM = 30.0
NOMBRES = ["prog_arit", "mono3", "mono4", "dif_hoy", "difabs_hoy", "dif_30d_z",
           "term_s1s2", "term_hoy", "paridad3", "color3", "espejo"]
F = len(NOMBRES)
NUM = np.array([False, False] + [True] * 36)
Vi = np.array([-999, -999] + list(range(1, 37)))          # -999 = sin número (0 y 00)
ROJOS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
COLOR = np.array([-1, -1] + [1 if k in ROJOS else 0 for k in range(1, 37)])
TERM = np.where(NUM, Vi % 10, -1)
PAR = np.where(NUM, Vi % 2, -1)
FRAC = np.array([(36 - abs(d)) / (36 * 35) if 0 < abs(d) < 36 else 0.0 for d in range(-35, 36)])
IDX = np.arange(K)


def construir(datos, desde):
    """X (n-desde, 38, 11). Fila j = sorteo t = desde+j; usa solo seq[:t] (y el calendario de t)."""
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); n = len(seq)
    X = np.zeros((n - desde, K, F), np.float32)
    dif_dia = {}                      # día -> conteo (71) de saltos con signo de los pares consecutivos numéricos del día
    ini_dia = 0
    for t in range(n):
        if t > 0 and dia[t] != dia[t - 1]:
            ini_dia = t
        k = t - ini_dia                                   # sorteos previos de hoy
        if t >= desde and k > 0:
            x = X[t - desde]
            s1 = seq[t - 1]
            antes = seq[ini_dia:t - 2] if k >= 3 else ()
            for a in antes:                               # terminaciones de hoy sin s1 ni s2
                if NUM[a]:
                    x[:, 7] += (TERM == TERM[a]) & NUM
            if NUM[s1]:
                di = np.where(NUM, Vi - Vi[s1], 0)
                ok = NUM & (IDX != s1)
                dh = [Vi[seq[j]] - Vi[seq[j - 1]] for j in range(ini_dia + 1, t) if NUM[seq[j]] and NUM[seq[j - 1]]]
                if dh:
                    dh = np.array(dh)
                    x[:, 3] = ok * (di[:, None] == dh[None, :]).sum(1)
                    x[:, 4] = ok * (np.abs(di)[:, None] == np.abs(dh)[None, :]).sum(1)
                c30 = np.zeros(71)                        # jornadas 1-30 anteriores (días ya cerrados)
                for dd in range(dia[t] - 30, dia[t]):
                    a = dif_dia.get(dd)
                    if a is not None:
                        c30 += a
                N = c30.sum()
                if N > 0:
                    e = N * FRAC[di + 35]
                    with np.errstate(divide="ignore", invalid="ignore"):
                        x[:, 5] = np.where(ok & (e > 0), (c30[di + 35] - e) / np.sqrt(np.maximum(e, 1e-12)), 0.0)
                x[:, 10] = ok & (Vi + Vi[s1] == 37)
                if k >= 2 and NUM[seq[t - 2]]:
                    s2 = seq[t - 2]
                    st = Vi[s1] - Vi[s2]
                    x[:, 0] = ok & (di == st) & (st != 0)
                    x[:, 1] = ok & (((Vi[s2] < Vi[s1]) & (Vi[s1] < Vi)) | ((Vi[s2] > Vi[s1]) & (Vi[s1] > Vi)))
                    x[:, 6] = ok & (TERM == TERM[s1]) & (TERM[s1] == TERM[s2])
                    x[:, 8] = ok & (PAR == PAR[s1]) & (PAR[s1] == PAR[s2])
                    x[:, 9] = ok & (COLOR == COLOR[s1]) & (COLOR[s1] == COLOR[s2])
                    if k >= 3 and NUM[seq[t - 3]]:
                        s3 = seq[t - 3]
                        up = (Vi[s3] < Vi[s2]) & (Vi[s2] < Vi[s1]) & (Vi[s1] < Vi)
                        dn = (Vi[s3] > Vi[s2]) & (Vi[s2] > Vi[s1]) & (Vi[s1] > Vi)
                        x[:, 2] = ok & (up | dn)
        # registrar el sorteo t (ya predicho)
        if k > 0 and NUM[seq[t]] and NUM[seq[t - 1]]:
            dif_dia.setdefault(dia[t], np.zeros(71))[Vi[seq[t]] - Vi[seq[t - 1]] + 35] += 1
    for f in (3, 4, 7):
        X[:, :, f] = np.log1p(X[:, :, f])
    return X


def prueba_fuga(datos, desde, t_corte, semilla=0):
    """Barajar seq[t_corte:] no debe cambiar las filas < t_corte."""
    X1 = construir(datos, desde)
    d2 = copy.copy(datos); s = np.array(datos.seq).copy()
    rng = np.random.default_rng(semilla); s[t_corte:] = rng.permutation(s[t_corte:]); d2.seq = s
    X2 = construir(d2, desde)
    j = t_corte - desde
    return float(np.abs(X1[:j] - X2[:j]).max()), float(np.abs(X1[j + 1:] - X2[j + 1:]).max())


def score(X, P, y, dia, filas):
    Xs, Ps, ys, ds = X[filas], P[filas], y[filas], dia[filas]
    obs = Xs[np.arange(len(ys)), ys]
    esp = np.einsum("ti,tif->tf", Ps, Xs)
    u = obs - esp
    _, inv = np.unique(ds, return_inverse=True)
    sb = np.zeros((inv.max() + 1, X.shape[2])); np.add.at(sb, inv, u)
    z = u.sum(0) / np.sqrt((sb ** 2).sum(0))
    p = np.array([math.erfc(abs(v) / math.sqrt(2)) for v in z])
    return z, p, obs.sum(0), esp.sum(0)


def bh(p, q=0.05):
    m = len(p); o = np.argsort(p); ok = np.zeros(m, bool)
    below = np.where(p[o] <= q * np.arange(1, m + 1) / m)[0]
    if len(below):
        ok[o[:below.max() + 1]] = True
    return ok


def main():
    t0 = time.time(); out = []

    def pr(s=""):
        print(s, flush=True); out.append(str(s))
    D = A.datos().prefijo(A.CORTE)                  # nada >= 9357
    P_ref = np.load(os.path.join(MN, "ag12_transiciones", "P_V1.npy")); P_ref = P_ref / P_ref.sum(1, keepdims=True)
    y = A.base()[1]
    LPR = np.log(np.clip(P_ref, 1e-12, None))
    dia = np.asarray(D.dia[A.W:A.CORTE]); blo = E2.bloques_jornada(dia)
    fuga = prueba_fuga(D, A.W, 6000)
    pr(f"prueba de fuga: barajar seq[6000:] -> máx dif filas < 6000 = {fuga[0]} (control: filas > 6000 cambian {fuga[1]:.3f})")
    X = construir(D, A.W).astype(np.float64)
    pr(f"X {X.shape}, {time.time()-t0:.0f} s. Candidatos con x != 0 por sorteo (media, de 38):")
    for f, nm in enumerate(NOMBRES):
        pr(f"  {nm:11s} {(X[:, :, f] != 0).sum(1).mean():.2f}")
    n = len(y); h = n // 2
    z1, p1, o1, e1 = score(X, P_ref, y, dia, np.arange(h))
    z2, p2, o2, e2 = score(X, P_ref, y, dia, np.arange(h, n))
    zt, pt, ot, et = score(X, P_ref, y, dia, np.arange(n))
    sel1 = bh(p1, 0.05)
    p2u = np.array([0.5 * math.erfc(abs(v) / math.sqrt(2)) for v in z2])
    conf = sel1 & (np.sign(z2) == np.sign(z1)) & (p2u < 0.05)
    pr("\n== Etapa 1: barrido sobre ag12 V1 (O/E = observado / esperado por ag12 V1; z robusto por jornada) ==")
    pr("(para variables continuas O/E es la razón de sumas; el z es lo que cuenta)")
    pr(f"{'variable':11s} | mitad1 O/E    z      p     BH | mitad2 O/E    z   | total O/E    z   | confirma")
    barr = {}
    for f, nm in enumerate(NOMBRES):
        r1 = o1[f] / e1[f] if e1[f] else float('nan'); r2 = o2[f] / e2[f] if e2[f] else float('nan')
        rt = ot[f] / et[f] if et[f] else float('nan')
        pr(f"{nm:11s} | {r1:7.3f} {z1[f]:+6.2f} {p1[f]:.4f} {'SI' if sel1[f] else 'no':>3s} | {r2:7.3f} {z2[f]:+6.2f} |"
           f" {rt:7.3f} {zt[f]:+6.2f} | {'SI' if conf[f] else 'no'}")
        barr[nm] = dict(m1_OE=float(r1), m1_z=float(z1[f]), m1_p=float(p1[f]), bh_m1=bool(sel1[f]), m2_OE=float(r2),
                        m2_z=float(z2[f]), m2_p_unilateral=float(p2u[f]), tot_OE=float(rt), tot_z=float(zt[f]),
                        confirma_m2=bool(conf[f]), obs_tot=float(ot[f]), esp_tot=float(et[f]))
    res = {"prueba_fuga_maxdif": fuga, "barrido": barr}
    fm = lambda t: f"{t[0]:+.2f} [{t[1]:+.2f}, {t[2]:+.2f}]"

    def ajusta(cols, nombre):
        Xc = X[:, :, cols]
        fit = lambda tr: E2.ajustar_lineal(Xc[tr], LPR[tr], y[tr], LAM)
        prd = lambda w, te: E2.predecir_lineal(w, Xc[te], LPR[te])
        P, pars = E2.cross_fit(fit, prd, blo)
        Pf = E2.forward(fit, prd, blo); Pf[blo == 0] = P_ref[blo == 0]
        r = {}
        for tag, PP in (("crossfit", P), ("forward", Pf)):
            ev = A.evaluar(PP, P_ref=P_ref, y=y)
            pr(f"\n== {nombre} {tag} (frente a ag12 V1) ==")
            pr(f"Delta mbits {fm(ev['delta_mbits'])} · mitad1 {fm(ev['delta_mitad1'])} · mitad2 {fm(ev['delta_mitad2'])}")
            pr(f"Top-3 {ev['top3_cand']*100:.2f}% vs {ev['top3_ens']*100:.2f}% · Top-5 {ev['top5_cand']*100:.2f}% vs "
               f"{ev['top5_ens']*100:.2f}% · Top-15 {ev['top15_cand']*100:.2f}% vs {ev['top15_ens']*100:.2f}%")
            pr(f"Top-5 escalonado/ficha {ev['ret_t5_cand']*100:+.2f}% vs {ev['ret_t5_ens']*100:+.2f}% · delta {fm(ev['delta_ret_t5'])}")
            pr(f"pasa_barra_dev (arnes, sin forward): {ev['pasa_barra_dev']}")
            r[tag] = ev
        m = blo > 0
        dd = A.mbits_fila(Pf, y)[m] - A.mbits_fila(P_ref, y)[m]
        r["forward_bloques1a4"] = A.ic_bloques(dd, dia[m])
        pr(f"forward, solo bloques 1-4 (los predichos): {fm(r['forward_bloques1a4'])}")
        W_ = np.array(pars)
        r["pesos"] = {NOMBRES[c]: [float(W_[:, i].mean()), float(W_[:, i].min()), float(W_[:, i].max())]
                      for i, c in enumerate(cols)}
        for nm, (mu, lo, hi) in r["pesos"].items():
            pr(f"  peso {nm:11s} {mu:+.3f} [{lo:+.3f}, {hi:+.3f}]")
        r["pasa_barra_completa"] = bool(r["crossfit"]["pasa_barra_dev"] and r["forward_bloques1a4"][0] > 0)
        pr(f"PASA BARRA COMPLETA (arnes + forward > 0): {r['pasa_barra_completa']}")
        return r, P
    cols = [f for f in range(F) if conf[f]]
    pr(f"\nSeleccionadas para VA (BH mitad 1 + confirmación mitad 2): {[NOMBRES[c] for c in cols]}")
    if cols:
        res["VA"], PA = ajusta(cols, "VA_seleccion"); res["VA"]["cols"] = [NOMBRES[c] for c in cols]
        np.save(os.path.join(AQUI, "P_VA.npy"), PA)
    else:
        pr("VA = P_V1 (ninguna sobrevive): Δ = 0, no pasa.")
        res["VA"] = {"cols": [], "delta_mbits": [0.0, 0.0, 0.0], "pasa_barra_completa": False}
    res["VB"], _ = ajusta(list(range(F)), "VB_11var")
    json.dump(res, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    pr(f"[{time.time()-t0:.0f} s]")
    open(os.path.join(AQUI, "consola.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
