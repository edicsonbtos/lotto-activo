#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modelo y banco de pruebas para la TRIPLETA (3 animales que salgan en la jornada, paga 45x).

Supuesto: la tripleta se compra ANTES del primer sorteo del día, así que la
predicción de la jornada d solo usa jornadas anteriores.

Modelo: regresión logística por (jornada, animal) con pesos compartidos,
P(animal i sale en la jornada d | historia < d), ajustada por máxima
verosimilitud con L2 y ponderación exponencial en el tiempo; reajuste cada
REAJ jornadas usando solo jornadas pasadas.

Evaluación:
  * Tasa base REAL de una tripleta al azar en la jornada d: C(D_d,3)/C(38,3),
    con D_d = animales distintos que salieron ese día (el azar no es 1/45 ni
    el cálculo con reemplazo: el operador casi no repite en el día).
  * Aciertos esperados bajo azar = suma de tasas base; z y p-valor con la
    varianza de Poisson-binomial. EV con pago 45x e IC 95 % por bootstrap de días.
  * Partición igual que lotto_eval: desarrollo = jornadas que empiezan antes del
    sorteo 9357; prueba = desde ahí. --final registra la mirada.
"""
import argparse, json, math, os, sys, time
from math import comb
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lotto_eval as LE

K = 38
PAGO_TRIPLETA = 45
REGISTRO = os.path.join(LE.AQUI, "registro_final.jsonl")
VENT_DIAS = [(1, 1), (2, 3), (4, 7), (8, 14), (15, 30), (31, 60)]
BANDAS = [(38, 200), (200, 700)]


def jornadas(datos):
    """Lista de (ini, fin) de índices de sorteo por día natural."""
    dia = np.asarray(datos.dia)
    cortes = np.r_[0, np.nonzero(np.diff(dia))[0] + 1, len(dia)]
    return [(int(cortes[i]), int(cortes[i + 1])) for i in range(len(cortes) - 1)]


def construir(datos):
    """X: (J, 38, d) con información anterior a cada jornada; Y: (J, 38) 0/1; D: distintos por día."""
    seq = np.asarray(datos.seq)
    J = jornadas(datos)
    nJ = len(J)
    Y = np.zeros((nJ, K))
    for j, (a, b) in enumerate(J):
        Y[j, np.unique(seq[a:b])] = 1
    Cd = np.vstack([np.zeros((1, K)), np.cumsum(Y, 0)])            # días con aparición en jornadas [0, j)
    oh = np.zeros((len(seq), K)); oh[np.arange(len(seq)), seq] = 1
    Cs = np.vstack([np.zeros((1, K)), np.cumsum(oh, 0)])            # conteo en sorteos [0, t)
    feats, nombres = [], []
    # días desde la última jornada con aparición (1..10, 11-20, 21+)
    ult = np.full(K, -10**6); dd = np.zeros((nJ, K))
    for j in range(nJ):
        dd[j] = j - ult
        ult[Y[j] > 0] = j
    for lo, hi in [(1, 1), (2, 2), (3, 3), (4, 4), (5, 6), (7, 10), (11, 20)]:
        feats.append(((dd >= lo) & (dd <= hi)).astype(float)); nombres.append(f"dd{lo}-{hi}")
    # veces que salió ayer (2+)
    ayer = np.zeros((nJ, K))
    for j in range(1, nJ):
        a, b = J[j - 1]; ayer[j] = np.bincount(seq[a:b], minlength=K)
    feats.append((ayer >= 2).astype(float)); nombres.append("ayer2+")
    # frecuencia en ventanas de días, estandarizada respecto a lo esperado
    idx = np.arange(nJ)
    for a, b in VENT_DIAS[1:]:
        lo = np.maximum(idx - b, 0); hi = np.maximum(idx - a + 1, 0)
        c = Cd[hi] - Cd[lo]; w = (hi - lo)[:, None]
        m = w * 0.297
        feats.append((c - m) / np.sqrt(m + 1.0)); nombres.append(f"dias{a}-{b}")
    # bandas de conteo en sorteos antes del inicio de la jornada
    ini = np.array([a for a, _ in J])
    for a, b in BANDAS:
        lo = np.maximum(ini - b, 0); hi = np.maximum(ini - a, 0)
        c = Cs[hi] - Cs[lo]; m = ((hi - lo) / K)[:, None]
        feats.append((c - m) / np.sqrt(m + 1.0)); nombres.append(f"banda{a}-{b}")
    X = np.stack(feats, axis=2)
    D = Y.sum(1)
    return J, X, Y, D, nombres


def ajustar(X, Y, w, lam, b0):
    N, _, d = X.shape
    Xf = X.reshape(-1, d); yf = Y.reshape(-1); wf = np.repeat(w, K)

    def f(th):
        z = Xf @ th[1:] + th[0]
        ll = wf * (yf * z - np.logaddexp(0, z))
        p = 1 / (1 + np.exp(-z))
        r = wf * (yf - p)
        g = -np.r_[r.sum(), Xf.T @ r] + lam * np.r_[0, th[1:]]
        return -ll.sum() + 0.5 * lam * th[1:] @ th[1:], g

    return minimize(f, b0, jac=True, method="L-BFGS-B", options={"maxiter": 300}).x


class ModeloTripleta:
    def __init__(self, reaj=30, tau=400.0, lam=1.0, inicio=30):
        self.reaj, self.tau, self.lam, self.inicio = reaj, tau, lam, inicio

    def predecir(self, X, Y, desde):
        """P (J-desde, 38): jornada j usando solo Y[:j] (X ya es causal)."""
        nJ, _, d = X.shape
        out = np.empty((nJ - desde, K)); th = np.zeros(d + 1)
        for T in range(desde, nJ, self.reaj):
            a = self.inicio
            w = np.exp(-(T - 1 - np.arange(a, T)) / self.tau)
            th = ajustar(X[a:T], Y[a:T], w, self.lam, th)
            b = min(T + self.reaj, nJ)
            z = X[T:b] @ th[1:] + th[0]
            out[T - desde:b - desde] = 1 / (1 + np.exp(-z))
        self.th = th
        return out


ESTRATEGIAS = {
    "A_123_456": lambda o: [o[:3], o[3:6]],
    "B_123_124": lambda o: [o[:3], [o[0], o[1], o[3]]],
    "C_solo_123": lambda o: [o[:3]],
}


def evaluar_tramo(P, Y, D, estrategia, semilla=0):
    base = np.array([comb(int(x), 3) / comb(K, 3) for x in D])
    orden = np.argsort(-P, axis=1, kind="stable")
    gan = []       # (acierto, tasa_base) por tripleta jugada
    for j in range(len(P)):
        for tri in ESTRATEGIAS[estrategia](orden[j]):
            gan.append((float(np.all(Y[j, tri] > 0)), base[j]))
    g = np.array(gan)
    n = len(g); hits = g[:, 0].sum(); esp = g[:, 1].sum(); var = (g[:, 1] * (1 - g[:, 1])).sum()
    z = (hits - esp) / math.sqrt(var)
    rng = np.random.default_rng(semilla)
    por_dia = len(ESTRATEGIAS[estrategia](np.arange(K)))
    G = g[:, 0].reshape(-1, por_dia).sum(1)
    boots = [G[rng.integers(0, len(G), len(G))].sum() / n for _ in range(4000)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"jornadas": len(P), "tripletas": n, "aciertos": int(hits), "tasa": hits / n,
            "tasa_azar": esp / n, "umbral_45x": 1 / PAGO_TRIPLETA, "z_vs_azar": z,
            "p_valor": float(norm.sf(z)), "ev_45x": hits / n * PAGO_TRIPLETA - 1,
            "ic95_tasa": [float(lo), float(hi)], "ic95_ev": [float(lo) * PAGO_TRIPLETA - 1, float(hi) * PAGO_TRIPLETA - 1]}


def calibracion(P, Y):
    p0 = Y.mean()
    ll = np.mean(Y * np.log(P) + (1 - Y) * np.log(1 - P))
    ll0 = np.mean(Y * np.log(p0) + (1 - Y) * np.log(1 - p0))
    orden = np.argsort(-P, axis=1)
    top = [float(np.mean(np.take_along_axis(Y, orden[:, k:k + 1], 1))) for k in range(6)]
    return {"mbits_por_animal_dia": (ll - ll0) / math.log(2) * 1000, "tasa_base_animal": float(p0),
            "P_sale_por_rango_1a6": top}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--reaj", type=int, default=30)
    ap.add_argument("--tau", type=float, default=400.0)
    ap.add_argument("--lam", type=float, default=1.0)
    a = ap.parse_args()
    datos = LE.cargar()
    J, X, Y, D, nombres = construir(datos)
    W, corte = LE.particion(len(datos))
    ini = np.array([x for x, _ in J])
    j0 = int(np.searchsorted(ini, W)); jc = int(np.searchsorted(ini, corte))
    m = ModeloTripleta(a.reaj, a.tau, a.lam)
    t0 = time.time()
    P = m.predecir(X, Y, j0)
    print(f"jornadas: {len(J)} | desarrollo {j0}-{jc} | prueba {jc}-{len(J)} | {time.time()-t0:.1f}s")
    print("coeficientes:", {n: round(float(c), 3) for n, c in zip(["const"] + nombres, m.th)})
    tramos = [("desarrollo", slice(0, jc - j0))] + ([("prueba", slice(jc - j0, None))] if a.final else [])
    res = {}
    for nombre, sl in tramos:
        res[nombre] = {"calibracion": calibracion(P[sl], Y[j0:][sl])}
        cal = res[nombre]["calibracion"]
        print(f"\n== {nombre}: {cal['mbits_por_animal_dia']:+.2f} mbits/animal-día | P(sale) por rango 1..6: "
              f"{[round(x, 3) for x in cal['P_sale_por_rango_1a6']]} (base {cal['tasa_base_animal']:.3f})")
        for e in ESTRATEGIAS:
            r = evaluar_tramo(P[sl], Y[j0:][sl], D[j0:][sl], e)
            res[nombre][e] = r
            print(f"  {e:<11} {r['tripletas']:>4} tripletas  aciertos {r['aciertos']:>3} = {r['tasa']*100:5.2f}% "
                  f"[{r['ic95_tasa'][0]*100:.2f}-{r['ic95_tasa'][1]*100:.2f}]  azar {r['tasa_azar']*100:.2f}%  "
                  f"umbral 2.22%  z={r['z_vs_azar']:+.2f} p={r['p_valor']:.3f}  EV 45x {r['ev_45x']*100:+.1f}% "
                  f"[{r['ic95_ev'][0]*100:+.0f}, {r['ic95_ev'][1]*100:+.0f}]")
    if a.final:
        with open(REGISTRO, "a", encoding="utf-8") as f:
            f.write(json.dumps({"cuando": time.strftime("%Y-%m-%d %H:%M:%S"), "modelo": "tripleta_logit",
                                "config": vars(a), "prueba": res["prueba"]}, ensure_ascii=False) + "\n")
    return res


if __name__ == "__main__":
    main()
