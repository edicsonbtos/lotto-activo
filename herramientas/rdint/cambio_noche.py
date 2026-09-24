# -*- coding: utf-8 -*-
"""Regla de cambio de noche (PREREGISTRO_cambio_rd_noche.md): si el animal de RD de las 19:30 del
día ANTERIOR está en el Top-5 del ensamble para LA 8:00, sacarlo, subir a los de abajo y meter al #6
de 5º. Mide también la señal: ¿LA 8:00 repite RD 19:30 de la víspera menos de lo que espera el ensamble?

Uso: python herramientas/rdint/cambio_noche.py   -> resultados/hilo7_cambio_noche.md
"""
import os, sys
from datetime import date, timedelta
from math import exp, factorial
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import reciproca_la as RL
import datos as DT
from cambio_top5 import FICHAS, retorno
LE = RL.LE

VENTANAS = [("PRINCIPAL", "2025-12-17", "2026-09-23"),
            ("desarrollo", "2024-11-25", "2025-12-17")]
SALIDA_MD = os.path.join(RL.HERR, "resultados", "hilo7_cambio_noche.md")


def poisson_cdf(k, mu):
    return sum(exp(-mu) * mu ** i / factorial(i) for i in range(int(k) + 1))


def main():
    la = LE.cargar(RL.HIST)
    n = int(np.searchsorted(np.array(la.fecha), RL.FIN, side="right"))
    la = la.prefijo(n)
    P = RL.ensamble(la)
    y = np.asarray(la.seq)[LE.W:]; f = np.array(la.fecha[LE.W:]); h = np.asarray(la.hora)[LE.W:]
    dia = np.asarray(la.dia)[LE.W:]
    rd, *_ = DT.cargar()
    rdd = {(a, int(b)): int(c) for a, b, c in zip(rd.fecha, rd.hora, rd.seq) if a <= RL.FIN}
    orden = LE.rankings(P)[:, :6]
    idx = [t for t in range(len(y)) if h[t] == 0]
    filas = []   # (t, r, s0, s1, cambio, gana_rd, gana6, p_ens)
    for t in idx:
        ayer = (date.fromisoformat(f[t]) - timedelta(days=1)).isoformat()
        r = rdd.get((ayer, 11))
        if r is None:
            continue
        top = [int(a) for a in orden[t]]
        t2 = top[:5]; cam = r in t2
        if cam:
            t2 = [a for a in t2 if a != r] + [top[5]]
        filas.append((t, r, retorno(top[:5], y[t]), retorno(t2, y[t]), cam,
                      cam and y[t] == r, cam and y[t] == top[5], float(P[t, r])))
    rng = np.random.default_rng(20260924)
    L = ["# RD 19:30 de la víspera → LA 8:00 (pre-registro: PREREGISTRO_cambio_rd_noche.md)\n",
         "| ventana | n 8:00 | repitió RD 19:30 | azar | ensamble | p (menos que ensamble) | cambios | ganó el de RD | ganó el #6 | diferencia pp/ficha [IC95] |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    res = {}
    for nom, a, b in VENTANAS:
        sel = [x for x in filas if a <= f[x[0]] < b]
        if not sel:
            L.append("| %s | 0 | | | | | | | | |" % nom); continue
        rep = sum(y[x[0]] == x[1] for x in sel)
        mu = sum(x[7] for x in sel)
        p = poisson_cdf(rep, mu)
        d = np.array([(x[3] - x[2]) / sum(FICHAS) * 100 for x in sel])
        dd = np.array([dia[x[0]] for x in sel])
        u, g = np.unique(dd, return_inverse=True)
        D = np.bincount(g, d); N = np.bincount(g)
        bs = [D[k].sum() / N[k].sum() for k in (rng.integers(0, len(u), len(u)) for _ in range(2000))]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        cam = sum(x[4] for x in sel)
        L.append("| %s | %d | %d | %.1f | %.1f | %.3f | %d | %d | %d | %+.2f [%+.2f, %+.2f] |"
                 % (nom, len(sel), rep, len(sel) / 38, mu, p, cam, sum(x[5] for x in sel),
                    sum(x[6] for x in sel), d.mean(), lo, hi))
        res[nom] = (d.mean(), lo, p)
    dm, lo, p = res.get("PRINCIPAL", (0, 0, 1))
    dv = res.get("desarrollo", (0, 0, 1))[0]
    ver = ("CONFIRMADA" if dm > 0 and lo > 0 and p < 0.05 else
           "SE ADOPTA (sin confirmar)" if dm > 0 and dv > 0 else "SE DESCARTA")
    L.append("\n**VEREDICTO: %s**" % ver)
    txt = "\n".join(L)
    print(txt, flush=True)
    with open(SALIDA_MD, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    main()
