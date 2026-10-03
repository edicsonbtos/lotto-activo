# -*- coding: utf-8 -*-
"""¿El primer sorteo del día repite el primer sorteo de ayer? (2026-10-03)

Uso:  python investigacion/2026-10-03/primer_sorteo_ayer/analizar.py RUTA_AL_HISTORIAL
      (una COPIA del historial del volumen de Railway; ~35 s, necesita numpy y scipy)

1. Conteo crudo: ganador del primer sorteo == ganador del primer sorteo de ayer.
2. Observado contra lo que daba el ensamble walk-forward (ensamble_v2, mismo código
   que lotto_eval), por tramo: dev [2000, 9357), prueba [9357, 2026-09-15), vivo.
   Controles: último sorteo de ayer, hace 2 y 3 sorteos, "salió ayer", misma hora
   de ayer en las demás horas.
3. Corrección: multiplicar por m (ajustado SOLO en dev) la prob. de ese animal en
   el primer sorteo; mbits y Top-5/Top-15 por tramo.
"""
import os, sys
import numpy as np
from scipy.stats import chi2, poisson

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE  # noqa: E402

D = LE.cargar(sys.argv[1])
S = np.asarray(D.seq); DI = np.asarray(D.dia); H = np.asarray(D.hora); F = D.fecha
ens = LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", "ensamble_v2.py"))
P = LE.normalizar(ens.predecir(D, LE.W))          # fila t -> P[t - LE.W], solo usa seq[:t]
win = {(int(d), int(h)): int(s) for d, h, s in zip(DI, H, S)}
first = {}
for t in range(len(S)):
    first.setdefault(int(DI[t]), t)


def tramo(t):
    return "dev" if t < LE.CORTE_FIJO else ("vivo" if F[t] >= "2026-09-15" else "prueba")


def oe(nombre, filas):
    """filas: lista de (t, conjunto de animales)."""
    print(f"\n== {nombre} ==")
    for tr in ("dev", "prueba", "vivo", "todo"):
        R = [(t, a) for t, a in filas if t >= LE.W and (tr == "todo" or tramo(t) == tr)]
        if not R:
            continue
        O = sum(S[t] in a for t, a in R); E = sum(P[t - LE.W][list(a)].sum() for t, a in R)
        lo = 0 if O == 0 else 0.5 * chi2.ppf(0.025, 2 * O); hi = 0.5 * chi2.ppf(0.975, 2 * O + 2)
        print(f"  {tr:7s} N={len(R):4d} obs={O:4d} motor={E:6.1f} O/E={O / E:4.2f} "
              f"[{lo / E:4.2f}, {hi / E:4.2f}]  P(obs<=O)={poisson.cdf(O, E):.2g}")


# 1. crudo
pares = [(first[d], first[d - 1]) for d in first if d - 1 in first and H[first[d]] == H[first[d - 1]]]
for era, cond in (("primer sorteo 9:00 (hasta nov-2024)", lambda t: H[t] == 1),
                  ("primer sorteo 8:00 (desde nov-2024)", lambda t: H[t] == 0)):
    R = [(t, tp) for t, tp in pares if cond(t)]
    k = sum(S[t] == S[tp] for t, tp in R)
    print(f"{era}: repite el primero de ayer {k}/{len(R)} = {k / len(R) * 100:.2f}%  (azar {len(R) / 38:.1f})")
print("excepciones:", [F[t] for t, tp in pares if S[t] == S[tp]])

# 2. contra el motor
oe("primer sorteo = primer sorteo de ayer", [(t, {S[tp]}) for t, tp in pares])
h0 = [t for t in range(LE.W, len(S)) if H[t] == 0 and (int(DI[t]) - 1, 11) in win]
for hh, txt in ((11, "último sorteo (7 PM)"), (10, "hace 2 sorteos (6 PM)"), (9, "hace 3 sorteos (5 PM)")):
    oe(f"control 8:00 = {txt} de ayer", [(t, {win[(int(DI[t]) - 1, hh)]}) for t in h0 if (int(DI[t]) - 1, hh) in win])
oe("control 8:00 = salió ayer (cualquier hora)",
   [(t, {win[(int(DI[t]) - 1, h)] for h in range(12) if (int(DI[t]) - 1, h) in win}) for t in h0])
oe("control demás horas = misma hora de ayer",
   [(t, {win[(int(DI[t]) - 1, int(H[t]))]}) for t in range(LE.W, len(S))
    if H[t] != 0 and t != first[int(DI[t])] and (int(DI[t]) - 1, int(H[t])) in win])

# 3. corrección ajustada en dev
dev = [(t, S[tp]) for t, tp in pares if LE.W <= t < LE.CORTE_FIJO]
O = sum(S[t] == a for t, a in dev); E = sum(P[t - LE.W][a] for t, a in dev)
m = (O + 0.5) / (E + 0.5)
print(f"\nmultiplicador ajustado en dev: m = {m:.3f} (O={O}, E={E:.2f})")
for tr in ("dev", "prueba", "vivo"):
    R = [(t, S[tp]) for t, tp in pares if t >= LE.W and tramo(t) == tr]
    ll = 0.0; c = np.zeros(4, int); dentro = 0
    for t, a in R:
        p = P[t - LE.W]; q = p.copy(); q[a] *= m; q /= q.sum(); w = S[t]
        ll += np.log2(q[w] / p[w])
        o = np.argsort(-p, kind="stable"); oc = np.argsort(-q, kind="stable")
        c += [w in o[:5], w in oc[:5], w in o[:15], w in oc[:15]]; dentro += a in o[:15]
    print(f"  {tr:7s} n={len(R):4d} {ll / len(R) * 1000:+6.1f} mbits/primer sorteo  "
          f"Top-5 {c[0]}->{c[1]}  Top-15 {c[2]}->{c[3]}  animal de ayer en el Top-15: {dentro / len(R) * 100:.0f}%")
