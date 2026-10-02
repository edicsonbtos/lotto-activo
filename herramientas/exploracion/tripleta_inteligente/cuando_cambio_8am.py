# -*- coding: utf-8 -*-
"""¿Cuándo dejó de funcionar la regla de las 8:00? Mes a mes: O/E de "salió ayer" a las 8:00 y Top-15 de las 8:00.
Descriptivo. Antes: reentreno/sub.py todo I|S|H. Uso: python .../cuando_cambio_8am.py -> salida_cuando_cambio_8am.txt"""
import io, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
RE = os.path.join(RAIZ, "herramientas", "exploracion", "enjambre_2026-09-30", "reentreno"); sys.path.insert(0, RE)
import comun as C  # noqa: E402
LE = C.LE; SAL = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)
D = LE.cargar(os.path.join(RE, "historial_la.txt")); seq = np.asarray(D.seq); dia = np.asarray(D.dia); hora = np.asarray(D.hora); n = len(seq)
L = C.cargar_L("todo", ["I", "S", "H"]); P = C.combinar(L, seq[C.ARRANQUE:], LE.W, **C.COMB["base"])
pdia = {}
for t in range(n):
    pdia.setdefault(dia[t], set()).add(int(seq[t]))
ocho = [t for t in range(LE.W, n) if hora[t] == 0]
log("mes      madrugadas  'salió ayer' O/E   Top-15 8:00   (O/E < 1 = la regla está activa)")
for m in sorted({D.fecha[t][:7] for t in ocho}):
    ts = [t for t in ocho if D.fecha[t][:7] == m]
    o = sum(seq[t] in pdia.get(dia[t] - 1, ()) for t in ts); e = sum(len(pdia.get(dia[t] - 1, ())) / 38 for t in ts)
    t15 = np.mean([np.where(np.argsort(-P[t - LE.W], kind="stable") == seq[t])[0][0] < 15 for t in ts])
    log(f"{m}   {len(ts):4d}        {o/e:5.2f} ({o:2d}/{e:4.1f})    {100*t15:5.1f} %")
for a, b in (("2024-11", "2025-11"), ("2025-12", "2026-09"), ("2026-09-14", "2026-09-30")):
    ts = [t for t in ocho if a <= D.fecha[t] <= b + "-31"]
    o = sum(seq[t] in pdia.get(dia[t] - 1, ()) for t in ts); e = sum(len(pdia.get(dia[t] - 1, ())) / 38 for t in ts)
    log(f"tramo {a}..{b}: O/E {o/e:.2f} (n={len(ts)})")
io.open(os.path.join(AQUI, "salida_cuando_cambio_8am.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
