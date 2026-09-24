# -*- coding: utf-8 -*-
"""Hilo 9, anexo M (PREREGISTRO_hilo9_subir.md): prueba de techo en LA, sólo desarrollo.

M-A: elección condicional (softmax sobre los 38) con ~91 variables en tramos, SIN el ensamble.
M-B: lo mismo + log P del ensamble como variable (apilado): ¿queda estructura sin capturar?
Walk-forward: reajuste cada 500 filas con sólo filas pasadas; las primeras 1500 filas sólo entrenan.
L2 fijo λ = 1 (elegido antes de correr). Python + numpy + scipy; ~200 MB de RAM.

Uso: python herramientas/hilo9/techo.py  -> herramientas/resultados/hilo9_techo.md
"""
import os, sys, bisect
from collections import defaultdict
import numpy as np
from scipy.optimize import minimize

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import residuos as RS
LE, DT, HERR, RAIZ = RS.LE, RS.DT, RS.HERR, RS.RAIZ
K = 38
SALIDA = os.path.join(HERR, "resultados", "hilo9_techo.md")
LAMBDA, BLOQUE, INICIO = float(os.environ.get("HILO9_LAMBDA", 1.0)), 500, 1500
if os.environ.get("HILO9_LAMBDA"):   # robustez: no pisa el resultado pre-registrado (λ = 1)
    SALIDA = SALIDA.replace(".md", "_lambda%g.md" % LAMBDA)

GAP_B = [1, 2, 3, 4, 5, 8, 12, 18, 24, 36, 60, 110]          # 12 tramos + "nunca" = 13
GAP2_B = [13, 25, 49, 97]                                      # 5 tramos + "nunca" = 6
DIAS_B = [1, 2, 3, 4, 7]                                       # 0,1,2,3,4-6,7+ = 6


def franja(h):
    return 0 if h == 0 else 1 if h <= 3 else 2 if h <= 7 else 3


def tramo(v, bordes):
    return bisect.bisect_right(bordes, v) - 1 if v >= bordes[0] else 0


def construir():
    la = LE.cargar(RS.ruta(RAIZ, "historial.txt"))
    seq = np.asarray(la.seq); hora = np.asarray(la.hora); dia = np.asarray(la.dia); fecha = list(la.fecha)
    rd, *_ = DT.cargar()
    rd_d = defaultdict(dict)
    for f, h, s in zip(rd.fecha, rd.hora, rd.seq):
        rd_d[f][int(h)] = int(s)
    C = np.load(RS.ruta(HERR, "exploracion", "calor_cache.npz")); PL = C["P"]; yl = C["y"]
    filas = np.arange(LE.W, LE.W + len(yl))
    m = np.array([fecha[t] < RS.LA_FIN and fecha[t] in rd_d for t in filas])
    objetivo = set(filas[m].tolist())
    pos = [[] for _ in range(K)]; hoy = defaultdict(int); dia_act = None
    last_dia = np.full(K, -10 ** 6)
    G, FL, Y, PE, D = [], [], [], [], []
    for t in range(len(seq)):
        if dia[t] != dia_act:
            dia_act = dia[t]; hoy = defaultdict(int)
        if t in objetivo:
            h = int(hora[t]); fr = franja(h); f = fecha[t]; dd = rd_d.get(f, {})
            ayer = set(rd_d.get(RS.dia_menos(f, 1), {}).values())
            idx = np.zeros((K, 6), np.int16); fl = np.zeros((K, 4), np.float32)
            for i in range(K):
                p = pos[i]
                g1 = 12 if not p else tramo(t - p[-1], GAP_B)
                g2 = 5 if len(p) < 2 else tramo(t - p[-2], [1] + GAP2_B)
                c36 = min(4, len(p) - bisect.bisect_left(p, t - 36))
                c120 = len(p) - bisect.bisect_left(p, t - 120); c120 = max(0, min(5, c120 - 1))
                ch = min(2, hoy[i])
                ds = dia[t] - last_dia[i]; gd = 5 if ds >= 7 else (4 if ds >= 4 else int(max(ds, 0)))
                idx[i] = [g1 * 4 + fr, 52 + g2, 58 + c36, 63 + c120, 69 + ch * 4 + fr, 81 + gd]
                fl[i] = [dd.get(h - 1) == i if h >= 1 else 0, dd.get(h - 2) == i if h >= 2 else 0,
                         any(a == i for hh, a in dd.items() if hh < h - 2), i in ayer]
            j = t - LE.W
            G.append(idx); FL.append(fl); Y.append(int(seq[t])); PE.append(PL[j] / PL[j].sum()); D.append(int(dia[t]))
        s = int(seq[t]); pos[s].append(t); hoy[s] += 1; last_dia[s] = dia[t]
    return np.array(G), np.array(FL), np.array(Y), np.array(PE), np.array(D)


NW = 87 + 4   # 87 one-hot (52+6+5+6+12+6) + 4 banderas


def logits(w, G, FL, LPE, beta_on):
    # Grupo a grupo en vez de w[G].sum(2): la PC del usuario tiene ~150 MB libres.
    z = w[G[:, :, 0]]
    for k in range(1, G.shape[2]):
        z += w[G[:, :, k]]
    z += np.einsum("tif,f->ti", FL, w[87:91])
    if beta_on:
        z += w[91] * LPE
    return z


def perdida(w, G, FL, Y, LPE, beta_on):
    z = logits(w, G, FL, LPE, beta_on); z -= z.max(1, keepdims=True)
    n = len(Y); ll = z[np.arange(n), Y].copy()
    np.exp(z, out=z); s = z.sum(1); ll -= np.log(s)
    z /= -s[:, None]; R = z; R[np.arange(n), Y] += 1   # d ll / d z = 1[y] − p (en el mismo buffer)
    g = np.zeros_like(w)
    for k in range(G.shape[2]):
        g += np.bincount(G[:, :, k].ravel(), weights=R.ravel(), minlength=len(w))
    g[87:91] = np.einsum("ti,tif->f", R, FL)
    if beta_on:
        g[91] = (R * LPE).sum()
    reg = w.copy()
    if beta_on:
        reg[91] = 0                                 # el ensamble sin penalizar
    return -(ll.sum()) + LAMBDA / 2 * (reg ** 2).sum(), -(g) + LAMBDA * reg


def walk_forward(G, FL, Y, LPE, beta_on):
    w = np.zeros(NW + (1 if beta_on else 0))
    if beta_on:
        w[91] = 1.0
    out = np.full(len(Y), np.nan); P = np.zeros((len(Y), K))
    for k0 in range(INICIO, len(Y), BLOQUE):
        tr = slice(0, k0)
        r = minimize(perdida, w, args=(G[tr], FL[tr], Y[tr], LPE[tr], beta_on), jac=True, method="L-BFGS-B",
                     options={"maxiter": 300})
        w = r.x
        te = slice(k0, min(k0 + BLOQUE, len(Y)))
        z = logits(w, G[te], FL[te], LPE[te], beta_on); z = z - z.max(1, keepdims=True)
        lp = z - np.log(np.exp(z).sum(1, keepdims=True))
        out[te] = lp[np.arange(len(lp)), Y[te]]; P[te] = np.exp(lp)
        print("  bloque %d: ll/n=%.4f" % (k0, r.fun / k0), flush=True)
    return out, P, w


def tasas(P, y):
    rk = (P > P[np.arange(len(y)), y][:, None]).sum(1) + 1
    return tuple(100 * (rk <= k).mean() for k in (3, 5, 15))


def main():
    G, FL, Y, PE, D = construir()
    LPE = np.log(np.clip(PE, 1e-12, 1))
    print("filas:", len(Y), flush=True)
    base = LPE[np.arange(len(Y)), Y]
    ev = np.arange(INICIO, len(Y))
    u, g = np.unique(D[ev], return_inverse=True); mitad = len(u) // 2
    rng = np.random.default_rng(20260925)
    L = ["# Hilo 9 — anexo M: prueba de techo en LA (sólo desarrollo, walk-forward)\n",
         "Filas evaluadas: %d (las %d primeras sólo entrenan). λ=%.1f, reajuste cada %d filas.\n" % (len(ev), INICIO, LAMBDA, BLOQUE),
         "| modelo | Δ mbits vs ensamble | IC95 | 1ª mitad | 2ª mitad | Top-3 | Top-5 | Top-15 | pasa |",
         "|---|---|---|---|---|---|---|---|---|"]
    t0 = tasas(PE[ev], Y[ev])
    L.append("| ensamble_v2 (en uso) | 0 | — | — | — | %.2f %% | %.2f %% | %.2f %% | — |" % t0)
    for nom, beta_on in (("M-A flexible, sin ensamble", False), ("M-B flexible + ensamble (apilado)", True)):
        print(nom, flush=True)
        lp, P, w = walk_forward(G, FL, Y, LPE, beta_on)
        d = (lp[ev] - base[ev]) / np.log(2) * 1000

        def ic(sel):
            du = np.unique(g[sel]); S = np.bincount(g[sel], d[sel], len(u)); N = np.bincount(g[sel], None, len(u))
            bs = [S[k].sum() / N[k].sum() for k in (rng.choice(du, len(du)) for _ in range(2000))]
            return d[sel].mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
        a = ic(np.ones(len(d), bool)); m1 = ic(g < mitad); m2 = ic(g >= mitad)
        ok = m1[0] >= 5 and m1[1] > 0 and m2[0] >= 5 and m2[1] > 0
        t = tasas(P[ev], Y[ev])
        L.append("| %s | %+.2f | [%+.2f, %+.2f] | %+.2f [%+.2f, %+.2f] | %+.2f [%+.2f, %+.2f] | %.2f %% | %.2f %% | %.2f %% | %s |"
                 % (nom, a[0], a[1], a[2], *m1, *m2, *t, "**SÍ**" if ok else "no"))
        if beta_on:
            L.append("\nPeso final del ensamble en M-B: %.3f. Banderas RD [(h−1), (h−2), hoy, ayer]: %s"
                     % (w[91], np.round(w[87:91], 3).tolist()))
    txt = "\n".join(L)
    print(txt, flush=True)
    with open(SALIDA, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    main()
