#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRIPLETA por ventana: 3 animales que salgan en los PRÓXIMOS 12 SORTEOS
contados desde el sorteo siguiente (p.ej. 2 PM de hoy hasta 1 PM de mañana).
Paga 45x. Se puede comprar antes de cualquier sorteo, así que hay una ventana
posible por cada sorteo de inicio t.

Modelo: regresión logística por (inicio t, animal) con pesos compartidos:
P(animal i sale en seq[t:t+12] | seq[:t], calendario de t).
Reajuste cada REAJ inicios con los inicios s cuya ventana ya terminó
(s + 12 <= T), ponderados exponencialmente en el tiempo.

Evaluación (solo desarrollo salvo --final):
  * Tasa base real por ventana: C(D_w,3)/C(38,3), D_w = distintos en la ventana.
  * Las ventanas se solapan: IC y z con bootstrap por bloques de días.
"""
import argparse, json, math, os, sys, time
from math import comb
import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lotto_eval as LE

K = 38
VENTANA = 12
PAGO_TRIPLETA = 45
GBINS = [1, 2, 3, 5, 7, 10, 13, 19, 26, 37, 61, 10**7]   # tramos de retraso en sorteos
DIAS_VENT = [(1, 3), (4, 7), (8, 14), (15, 30), (31, 60)]
BANDAS = [(38, 200), (200, 700)]
REGISTRO = os.path.join(LE.AQUI, "registro_final.jsonl")


def construir(datos):
    """X: (n, 38, d) para cada inicio t en [0, n) usando solo seq[:t] y calendario de t.
    Y: (n, 38) con 1 si el animal sale en seq[t:t+12] (NaN si la ventana no terminó)."""
    seq = np.asarray(datos.seq); dia = np.asarray(datos.dia); n = len(seq)
    nuevo = np.r_[True, dia[1:] != dia[:-1]]
    didx = np.cumsum(nuevo) - 1
    nd = int(didx[-1]) + 1
    Cday = np.zeros((nd, K))
    np.add.at(Cday, (didx, seq), 1)
    Cdcum = np.vstack([np.zeros((1, K)), np.cumsum(Cday > 0, 0)])     # días con aparición en [0, j)
    oh = np.zeros((n, K)); oh[np.arange(n), seq] = 1
    Cs = np.vstack([np.zeros((1, K)), np.cumsum(oh, 0)])               # conteo en seq[:t]

    last = np.full(K, -10**7); hoy = np.zeros(K); k = 0
    G = np.empty((n, K)); HOY = np.empty((n, K)); KK = np.empty(n, int)
    for t in range(n):
        if nuevo[t]:
            hoy[:] = 0; k = 0
        G[t] = t - last; HOY[t] = hoy; KK[t] = k
        last[seq[t]] = t; hoy[seq[t]] += 1; k += 1

    feats, nombres = [], []
    hoy1 = HOY >= 1
    feats.append((HOY >= 2).astype(float)); nombres.append("hoy2+")
    for kk in range(1, 12):                                            # salió hoy × sorteos ya jugados hoy
        feats.append((hoy1 & (KK[:, None] == kk)).astype(float)); nombres.append(f"hoy_k{kk}")
    b = np.searchsorted(GBINS, G, side="right") - 1
    ref = np.searchsorted(GBINS, 13, side="right") - 1
    for i in range(len(GBINS) - 1):
        if i != ref:
            feats.append(((b == i) & ~hoy1).astype(float)); nombres.append(f"g{GBINS[i]}-{GBINS[i+1]-1}")
    # apariciones ayer (día natural anterior al de t)
    ayer = np.where(didx[:, None] >= 1, Cday[np.maximum(didx - 1, 0)], 0)
    feats.append(((ayer >= 1) & ~hoy1).astype(float)); nombres.append("ayer1+")
    feats.append((ayer >= 2).astype(float)); nombres.append("ayer2+")
    for a, bb in DIAS_VENT:                                            # días con aparición, excluye hoy
        lo = np.maximum(didx - bb, 0); hi = np.maximum(didx - a + 1, 0)
        c = Cdcum[hi] - Cdcum[lo]; m = ((hi - lo) * 0.3)[:, None]
        feats.append((c - m) / np.sqrt(m + 1.0)); nombres.append(f"dias{a}-{bb}")
    ar = np.arange(n)
    for a, bb in BANDAS:
        lo = np.maximum(ar - bb, 0); hi = np.maximum(ar - a, 0)
        c = Cs[hi] - Cs[lo]; m = ((hi - lo) / K)[:, None]
        feats.append((c - m) / np.sqrt(m + 1.0)); nombres.append(f"banda{a}-{bb}")
    X = np.stack(feats, axis=2).astype(np.float32)

    Y = np.full((n, K), np.nan)
    Cw = Cs[np.minimum(ar + VENTANA, n)] - Cs[ar]
    ok = ar + VENTANA <= n
    Y[ok] = (Cw[ok] > 0).astype(float)
    return X, Y, nombres


def ajustar(X, Y, w, lam, th0):
    N, _, d = X.shape
    Xf = X.reshape(-1, d).astype(np.float64); yf = Y.reshape(-1); wf = np.repeat(w, K)

    def f(th):
        z = Xf @ th[1:] + th[0]
        p = 1 / (1 + np.exp(-z))
        r = wf * (yf - p)
        val = -(wf * (yf * z - np.logaddexp(0, z))).sum() + 0.5 * lam * th[1:] @ th[1:]
        return val, -np.r_[r.sum(), Xf.T @ r] + lam * np.r_[0, th[1:]]

    return minimize(f, th0, jac=True, method="L-BFGS-B", options={"maxiter": 200}).x


class Modelo:
    def __init__(self, reaj=250, tau=3000.0, ventana=6000, lam=1.0, inicio=800):
        self.reaj, self.tau, self.ventana, self.lam, self.inicio = reaj, tau, ventana, lam, inicio

    def pesos(self, X, Y, T, th0=None):
        """Ajuste con inicios s en [max(inicio, T-ventana), T-12]: sus ventanas terminaron antes de T."""
        hi = T - VENTANA + 1
        lo = max(self.inicio, hi - self.ventana)
        s = np.arange(lo, hi)
        w = np.exp(-(T - s) / self.tau)
        return ajustar(X[lo:hi], Y[lo:hi], w, self.lam, np.zeros(X.shape[2] + 1) if th0 is None else th0)

    def predecir(self, X, Y, desde, hasta=None):
        n = X.shape[0] if hasta is None else hasta
        out = np.empty((n - desde, K)); th = None
        for T in range(desde, n, self.reaj):
            th = self.pesos(X, Y, T, th)
            b = min(T + self.reaj, n)
            z = X[T:b].astype(np.float64) @ th[1:] + th[0]
            out[T - desde:b - desde] = 1 / (1 + np.exp(-z))
        self.th = th
        return out


def frontera(n, reaj=250):
    return LE.W + ((n - LE.W) // reaj) * reaj


ESTRATEGIAS = {
    "A_123_456": lambda o: [list(o[:3]), list(o[3:6])],
    "B_123_124": lambda o: [list(o[:3]), [o[0], o[1], o[3]]],
}


def evaluar(P, Y, D, dias, estrategia, semilla=0):
    orden = np.argsort(-P, axis=1, kind="stable")
    base = np.array([comb(int(x), 3) / comb(K, 3) for x in D])
    tri = [ESTRATEGIAS[estrategia](o) for o in orden]
    hit = np.array([sum(float(np.all(Y[t, tr] > 0)) for tr in tri[t]) for t in range(len(P))])
    m = len(tri[0])
    n = len(P) * m
    exceso = hit - m * base
    # bootstrap por bloques de días (las ventanas se solapan)
    ud, inv = np.unique(dias, return_inverse=True)
    sh = np.bincount(inv, hit); se = np.bincount(inv, exceso); cnt = np.bincount(inv)
    rng = np.random.default_rng(semilla)
    B = []
    for _ in range(3000):
        i = rng.integers(0, len(ud), len(ud))
        B.append((sh[i].sum() / (cnt[i].sum() * m), se[i].sum() / (cnt[i].sum() * m)))
    B = np.array(B)
    tasa = hit.sum() / n
    se_exc = B[:, 1].std()
    z = (exceso.sum() / n) / se_exc
    lo, hi = np.percentile(B[:, 0], [2.5, 97.5])
    return {"ventanas": len(P), "tripletas": n, "aciertos": int(hit.sum()), "tasa": tasa,
            "tasa_azar": float(base.mean()), "umbral": 1 / PAGO_TRIPLETA, "z_bloques": float(z),
            "ev_45x": tasa * PAGO_TRIPLETA - 1, "ic95_tasa": [float(lo), float(hi)],
            "ic95_ev": [float(lo) * PAGO_TRIPLETA - 1, float(hi) * PAGO_TRIPLETA - 1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true", help="evalúa el tramo de prueba (NO es ciego: ver docstring)")
    a = ap.parse_args()
    datos = LE.cargar(); n = len(datos)
    t0 = time.time()
    X, Y, nombres = construir(datos)
    W, corte = LE.particion(n)
    m = Modelo()
    fin = n - VENTANA + 1
    P = m.predecir(X, Y, W, fin)
    print(f"inicios {W}-{fin} | desarrollo <{corte} | {time.time()-t0:.1f}s")
    print("coeficientes:", {k: round(float(c), 2) for k, c in zip(["const"] + nombres, m.th)})
    seq = np.asarray(datos.seq)
    D = np.array([len(set(seq[t:t + VENTANA])) for t in range(W, fin)])
    dias = np.asarray(datos.dia)[W:fin]
    Yv = Y[W:fin]
    tramos = [("desarrollo", slice(0, corte - W))]
    if a.final:
        tramos.append(("prueba (no ciega)", slice(corte - W, None)))
    res = {}
    for nombre, sl in tramos:
        orden = np.argsort(-P[sl], axis=1)
        prs = [round(float(np.nanmean(np.take_along_axis(Yv[sl], orden[:, r:r + 1], 1))), 3) for r in range(6)]
        print(f"\n== {nombre}: P(sale en 12) por rango 1..6 {prs}  (base {np.nanmean(Yv[sl]):.3f})")
        res[nombre] = {}
        for e in ESTRATEGIAS:
            r = evaluar(P[sl], Yv[sl], D[sl], dias[sl], e)
            res[nombre][e] = r
            print(f"  {e:<10} {r['tripletas']:>6} tripletas  aciertos {r['aciertos']:>4} = {r['tasa']*100:5.2f}% "
                  f"[{r['ic95_tasa'][0]*100:.2f}-{r['ic95_tasa'][1]*100:.2f}]  azar {r['tasa_azar']*100:.2f}%  "
                  f"umbral 2.22%  z(bloques)={r['z_bloques']:+.2f}  EV 45x {r['ev_45x']*100:+.1f}% "
                  f"[{r['ic95_ev'][0]*100:+.0f}, {r['ic95_ev'][1]*100:+.0f}]")
    if a.final:
        with open(REGISTRO, "a", encoding="utf-8") as f:
            f.write(json.dumps({"cuando": time.strftime("%Y-%m-%d %H:%M:%S"), "modelo": "tripleta_ventana",
                                "nota": "segunda mirada al tramo de prueba para tripletas (no ciega)",
                                "prueba": res["prueba (no ciega)"]}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
