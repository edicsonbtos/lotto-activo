# -*- coding: utf-8 -*-
"""ag03 — ajuste de los candidatos SOLO en dev. Imprime multiplicadores y mbits en dev (primer sorteo, por era)."""
import numpy as np, json
from scipy import stats
from comun import *
dd = np.array([int(f[8:10]) for f in fecha])
h12 = ((8 + hora - 1) % 12) + 1
OBJ = {"dia": dd + 1, "dia+1": dd + 2, "dia-1": dd, "hora12": h12 + 1}   # índice POS del código (código k -> índice k+1)
dev = tramo == "dev"
res = {}
for nom, idx in OBJ.items():
    for etiqueta, mask in (("dev_todas", dev), ("dev_demas", dev & ~prim), ("dev_primer", dev & prim)):
        F = np.where(mask & (idx >= 2) & (idx <= 37))[0]
        O = int((seq[F] == idx[F]).sum()); E = float(Paj[F, idx[F]].sum())
        lo, hi = poisson_ic(O)
        print(f"{nom:7s} {etiqueta:10s} n={len(F):5d} O={O:4d} E={E:6.1f} O/E={O/E:.2f} [{lo/E:.2f};{hi/E:.2f}] p={p_dos_colas_poisson(O,E):.4f}")
        res[(nom, etiqueta)] = (O, E)
    # por era en las demás horas (estabilidad)
    for era, c in (("9:00", fecha <= "2024-11-27"), ("8:00", fecha >= "2024-11-28")):
        F = np.where(dev & c & (idx >= 2) & (idx <= 37))[0]
        O = int((seq[F] == idx[F]).sum()); E = float(Paj[F, idx[F]].sum()); print(f"        era {era} todas O/E={O/E:.2f}")
# multiplicadores (ajustados en dev, todas las horas, suavizado +0,5)
M = {k: (res[(k, "dev_todas")][0] + 0.5) / (res[(k, "dev_todas")][1] + 0.5) for k in OBJ}
print("multiplicadores dev todas:", {k: round(v, 3) for k, v in M.items()})


def aplicar(rows, usar):
    q = Paj[rows].copy()
    for k in usar:
        idx = OBJ[k][rows]
        ok = (idx >= 2) & (idx <= 37)
        q[np.where(ok)[0], idx[ok]] *= M[k]
    return q / q.sum(1, keepdims=True)


CANDS = {"C1_fecha": ["dia", "dia+1"], "C2_fecha_hora": ["dia", "dia+1", "hora12"]}
for c, usar in CANDS.items():
    for era, cond in (("dev", np.ones(n, bool)), ("9:00", hora == 1), ("8:00", hora == 0)):
        F = np.where(dev & prim & cond)[0]
        m, lo, hi = mbits_boot(aplicar(F, usar), F)
        print(f"{c:14s} {era:5s} n={len(F)} mbits/primer={m:+.1f} [{lo:+.1f};{hi:+.1f}]")
    F = np.where(dev & ~prim)[0]
    q = aplicar(F, usar); y = seq[F]
    print(f"{c:14s} demás horas dev (control) mbits/sorteo={1000*np.mean(np.log2(q[np.arange(len(F)),y]/Paj[F,y])):+.1f}")
json.dump({"M": M, "CANDS": CANDS}, open("multiplicadores_dev.json", "w"), indent=1)
