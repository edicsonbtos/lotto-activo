# -*- coding: utf-8 -*-
"""Descriptivo (2026-10-01, a pedido): ¿cuánto acierta y cuánto deja jugar el Top-21 en 2026?
El N = 21 salió de mirar 2026 (D4 de la ciega), así que 2026 está sesgado a favor: el control es 2024-25.
Top-21 plano: 21 fichas, paga 30 -> gana +9 o pierde -21; empata con acierto 70 %.
Top-21 escalonado (solo ilustrativo): 3-3-3-2-2 y 1 ficha del 6º al 21º = 29 fichas."""
import os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
import top15_tarde as T
K = 38; N = 21
ESC = np.array([3, 3, 3, 2, 2] + [1] * (N - 5) + [0] * (K - N), float)
rng = np.random.default_rng(21)


def racha_max(fallo, fe):
    m = c = 0
    for f in fallo:
        c = c + 1 if f else 0; m = max(m, c)
    return m


def resumen(nombre, d, sel):
    P, y, fe, h = d["P"][sel], d["y"][sel], d["fecha"][sel], d["hora"][sel]
    o = T.LE.rankings(P); pos = np.argmax(o == y[:, None], 1)
    hit = (pos < N).astype(float); masa = np.take_along_axis(P, o[:, :N], 1).sum(1)
    ret = (30 * hit - N) / N; rete = (30 * ESC[pos] - ESC.sum()) / ESC.sum()
    a, (_, ica) = T.boot(hit, fe, rng); r, (_, icr) = T.boot(ret, fe, rng); e, (_, ice) = T.boot(rete, fe, rng)
    print(f"  {nombre:24s} n {len(y):5d} | acierta {a*100:5.1f} % [{ica[0]*100:.1f}; {ica[1]*100:.1f}] (el modelo dice {masa.mean()*100:.1f} %)"
          f" | plano {r*100:+5.1f} % por ficha [{icr[0]*100:+.1f}; {icr[1]*100:+.1f}] | escalonado {e*100:+5.1f} % [{ice[0]*100:+.1f}; {ice[1]*100:+.1f}]"
          f" | peor racha de fallos {racha_max(hit == 0, fe)}")
    return hit, fe, h, pos


for j, d in [("RD", T.juego_rd()), ("LA", T.juego_la())]:
    print(f"\n## {j}: Top-{N}")
    dev = d["dev"]; a26 = (d["fecha"] >= "2026-01-01") & (d["fecha"] <= "2026-09-29")
    tarde = np.isin(d["hora"], (10, 11))
    resumen("2024-25 todas las horas", d, dev)
    resumen("2024-25 horas 10-11", d, dev & tarde)
    hit, fe, h, pos = resumen("2026 todas las horas", d, a26)
    resumen("2026 horas 10-11", d, a26 & tarde)
    for k in (10, 11):
        resumen(f"2026 solo hora {k}", d, a26 & (d["hora"] == k))
    print("  2026 por mes (todas las horas): " + "  ".join(f"{m[5:]}: {hit[np.char.startswith(fe.astype(str), m)].mean()*100:.0f}"
                                                         for m in sorted({f[:7] for f in fe})))
    print("  2026 por hora (todas): " + "  ".join(f"{k + 8}h: {hit[h == k].mean()*100:.0f}" for k in range(12)))
    curva = [(pos < n).mean() for n in range(1, K + 1)]
    print("  2026 acierto por tamaño (todas las horas): " + "  ".join(f"T{n}: {curva[n-1]*100:.0f}" for n in (15, 18, 20, 21, 22, 24, 26)))

# Control post-hoc: la hora 18:30 de RD destaca en 2026; ¿también en otros años?
d = T.juego_rd()
o = T.LE.rankings(d["P"]); acierto = np.argmax(o == d["y"][:, None], 1) < N
print(f"\n## Control: Top-{N} de RD por hora y por año (18:30 = hora 10)")
for nom, s in [("2024", (d["fecha"] >= "2024-03-01") & (d["fecha"] < "2025-01-01")),
               ("2025", (d["fecha"] >= "2025-01-01") & (d["fecha"] < "2026-01-01")), ("2026", d["fecha"] >= "2026-01-01")]:
    print("  " + nom + " " + " ".join(f"{k + 8}:30 {acierto[s & (d['hora'] == k)].mean()*100:.0f}%" for k in range(12))
          + f" | todas {acierto[s].mean()*100:.1f}%")
