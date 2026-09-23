# -*- coding: utf-8 -*-
"""Regla de cambio (PREREGISTRO_cambio_rd_top5.md): si el animal de RD (h−1):30 está en el Top-5
del ensamble para LA h:00, sacarlo y subir al #6. Reutiliza la caché del ensamble de reciproca_la.

Uso: python herramientas/rdint/cambio_top5.py   -> resultados/hilo7_cambio_top5.md
"""
import os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import reciproca_la as RL
import datos as DT
LE = RL.LE

FICHAS = [2, 2, 2, 1, 1]
VENTANAS = [("PRINCIPAL", "2025-12-17", "2026-09-23"),
            ("  sub: 2025-12-17..2026-04-12", "2025-12-17", "2026-04-13"),
            ("  sub: 2026-04-13..2026-09-22", "2026-04-13", "2026-09-23"),
            ("desarrollo (ya visto)", "2024-03-01", "2025-12-17")]
SALIDA_MD = os.path.join(RL.HERR, "resultados", "hilo7_cambio_top5.md")


def retorno(top, y):
    return sum(30 * FICHAS[i] for i, a in enumerate(top) if a == y) - sum(FICHAS)


def main():
    la = LE.cargar(RL.HIST)
    n = int(np.searchsorted(np.array(la.fecha), RL.FIN, side="right"))
    la = la.prefijo(n)
    P = RL.ensamble(la)
    y = np.asarray(la.seq)[LE.W:]; f = np.array(la.fecha[LE.W:]); h = np.asarray(la.hora)[LE.W:]
    rd, *_ = DT.cargar()
    rdd = {(a, int(b)): int(c) for a, b, c in zip(rd.fecha, rd.hora, rd.seq) if a <= RL.FIN}
    orden = LE.rankings(P)[:, :6]
    s0 = np.zeros(len(y)); s1 = np.zeros(len(y)); cambio = np.zeros(len(y), bool)
    gana_rd = np.zeros(len(y), bool); gana6 = np.zeros(len(y), bool)
    for t in range(len(y)):
        top = [int(a) for a in orden[t]]
        r = rdd.get((f[t], int(h[t]) - 1)) if h[t] > 0 else None   # solo RD anterior a LA h:00
        t2 = top[:5]
        if r is not None and r in t2:
            t2 = [a for a in t2 if a != r] + [top[5]]
            cambio[t] = True; gana_rd[t] = y[t] == r; gana6[t] = y[t] == top[5]
        s0[t] = retorno(top[:5], y[t]); s1[t] = retorno(t2, y[t])
    dia = np.asarray(la.dia)[LE.W:]
    rng = np.random.default_rng(20260923)
    L = ["# Regla de cambio RD → Top-5 de Lotto Activo (pre-registro: PREREGISTRO_cambio_rd_top5.md)\n",
         "| ventana | n | cambios | ganó el de RD | ganó el #6 | sin cambio | con cambio | diferencia pp/ficha [IC95] |",
         "|---|---|---|---|---|---|---|---|"]
    ver = None
    for nom, a, b in VENTANAS:
        s = (f >= a) & (f < b)
        d = (s1[s] - s0[s]) / sum(FICHAS) * 100
        u, g = np.unique(dia[s], return_inverse=True)
        D = np.bincount(g, d); N = np.bincount(g)
        bs = []
        for _ in range(2000):
            k = rng.integers(0, len(u), len(u)); bs.append(D[k].sum() / N[k].sum())
        lo, hi = np.percentile(bs, [2.5, 97.5])
        L.append("| %s | %d | %d | %d | %d | %+.1f %% | %+.1f %% | %+.2f [%+.2f, %+.2f] |"
                 % (nom, s.sum(), cambio[s].sum(), gana_rd[s].sum(), gana6[s].sum(),
                    100 * s0[s].mean() / 8, 100 * s1[s].mean() / 8, d.mean(), lo, hi))
        if nom == "PRINCIPAL":
            ver = "CONFIRMADA" if d.mean() > 0 and lo > 0 else ("SE ADOPTA (sin confirmar)" if d.mean() > 0 else "SE DESCARTA")
    L.append("\n**VEREDICTO: %s**" % ver)
    txt = "\n".join(L)
    print(txt, flush=True)
    with open(SALIDA_MD, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    main()
