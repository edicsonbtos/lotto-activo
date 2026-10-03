# -*- coding: utf-8 -*-
"""ag03 — C3 (multiplicadores de fecha ajustados SOLO con primeros sorteos de dev) y efecto Top-5/Top-15 en dev."""
import numpy as np
from comun import *
from ajuste_dev import OBJ, M, aplicar   # re-ejecuta ajuste_dev (barato)
dev = tramo == "dev"
F = np.where(dev & prim)[0]
M3 = {}
for k in ("dia", "dia+1"):
    idx = OBJ[k][F]; ok = (idx >= 2) & (idx <= 37)
    O = (seq[F][ok] == idx[ok]).sum(); E = Paj[F[ok], idx[ok]].sum()
    M3[k] = (O + 0.5) / (E + 0.5)
print("C3 multiplicadores (solo primer sorteo dev):", {k: round(v, 3) for k, v in M3.items()})
# contraste C3 en dev por era: objetivos dia, dia+1 contra q_C1
for era, c in (("9:00", hora == 1), ("8:00", hora == 0)):
    G = np.where(dev & prim & c)[0]
    q1 = aplicar(G, ["dia", "dia+1"])
    O = E = 0
    for k in ("dia", "dia+1"):
        idx = OBJ[k][G]; ok = (idx >= 2) & (idx <= 37)
        O += (seq[G][ok] == idx[ok]).sum(); E += q1[np.where(ok)[0], idx[ok]].sum()
    print(f"  C3 dev era {era}: O={O} E(q_C1)={E:.1f} O/E={O/E:.2f}")
    O = E = 0
    for k in ("dia", "dia+1"):
        idx = OBJ[k][G]; ok = (idx >= 2) & (idx <= 37)
        O += (seq[G][ok] == idx[ok]).sum(); E += Paj[G[ok], idx[ok]].sum()
    print(f"  C1 dev era {era}: O={O} E(P_aj)={E:.1f} O/E={O/E:.2f}")
    O3 = O
    E += 0
    idx = OBJ["hora12"][G]; O += (seq[G] == idx).sum(); E += Paj[G, idx].sum()
    print(f"  C2 dev era {era}: O={O} E(P_aj)={E:.1f} O/E={O/E:.2f}")


def topk(q, rows, k):
    r = np.argsort(-q, 1)[:, :k]
    return int((r == seq[rows][:, None]).any(1).sum())


for nom, q in (("P_aj", Paj[F]), ("C1", aplicar(F, ["dia", "dia+1"])), ("C2", aplicar(F, ["dia", "dia+1", "hora12"]))):
    print(f"  dev primer {nom}: Top-5 {topk(q, F, 5)}  Top-15 {topk(q, F, 15)}")
