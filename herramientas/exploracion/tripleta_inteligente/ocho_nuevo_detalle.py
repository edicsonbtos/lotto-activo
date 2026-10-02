# -*- coding: utf-8 -*-
"""Detalle descriptivo tras el anexo 6 (no es prueba): "hace 2-3 días" por hora en las dos épocas, y el animal
de las 8:00 de ayer en toda la época nueva. Uso: python .../ocho_nuevo_detalle.py -> salida_ocho_nuevo_detalle.txt"""
import io, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas")); import lotto_eval as LE  # noqa: E402
D = LE.cargar(os.path.join(RAIZ, "herramientas", "exploracion", "enjambre_2026-09-30", "reentreno", "historial_la.txt"))
seq = D.seq; n = len(seq); SAL = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s); SAL.append(s)
ult = np.full(38, -10**6); G = np.zeros((n, 38), int)
for t in range(n):
    G[t] = D.dia[t] - ult; ult[seq[t]] = D.dia[t]
log("O/E de 'salió hace 2-3 días' por hora (1 = azar)")
log("hora   2024-11..2025-10   2025-11..2026-09")
for h in range(12):
    row = []
    for a, b in (("2024-11-01", "2025-10-31"), ("2025-11-01", "2026-09-29")):
        ts = [t for t in range(n) if D.hora[t] == h and a <= D.fecha[t] <= b]
        m = (G[ts] >= 2) & (G[ts] <= 3)
        o = m[np.arange(len(ts)), seq[ts]].sum(); e = m.sum() / 38
        row.append(f"{o/e:.2f} ({o}/{e:.0f})")
    log(f"{h+8:2d}:00  {row[0]:<18} {row[1]}")
ts = [t for t in range(n) if D.hora[t] == 0 and D.fecha[t] >= "2025-11-01"]
o = e = 0
for t in ts:
    s = [u for u in range(t - 24, t) if D.dia[u] == D.dia[t] - 1 and D.hora[u] == 0]
    if s: o += seq[t] == seq[s[0]]; e += 1 / 38
log(f"\nEl animal de las 8:00 de AYER, a las 8:00 de hoy (época nueva): sale {o} veces, esperado {e:.1f} → O/E {o/e:.2f}")
ts = [t for t in range(n) if D.hora[t] == 0 and D.fecha[t] < "2025-11-01"]
o = e = 0
for t in ts:
    s = [u for u in range(t - 24, t) if D.dia[u] == D.dia[t] - 1 and D.hora[u] == 0]
    if s: o += seq[t] == seq[s[0]]; e += 1 / 38
log(f"Lo mismo en la época vieja (nov-2024..oct-2025): sale {o} veces, esperado {e:.1f} → O/E {o/e:.2f}")
io.open(os.path.join(AQUI, "salida_ocho_nuevo_detalle.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")

# ¿El motor ya sabe que el de las 8:00 de ayer no se repite a las 8:00? ¿Pasa en otras horas ("misma hora de ayer")?
RE = os.path.join(RAIZ, "herramientas", "exploracion", "enjambre_2026-09-30", "reentreno"); sys.path.insert(0, RE)
import comun as C  # noqa: E402
L = C.cargar_L("todo", ["I", "S", "H"]); P = C.combinar(L, np.asarray(seq)[C.ARRANQUE:], LE.W, **C.COMB["base"])
idx = {(D.dia[t], int(D.hora[t])): t for t in range(n)}
log("\n'El animal de la MISMA HORA de ayer' en cada hora (desde nov-2024): sale / esperado al azar / esperado por el motor")
for h in range(12):
    o = ea = em = 0; top5 = 0
    for t in range(LE.W, n):
        if D.hora[t] != h or D.fecha[t] < "2024-11-01": continue
        s = idx.get((D.dia[t] - 1, h))
        if s is None: continue
        a = seq[s]; o += seq[t] == a; ea += 1 / 38; em += P[t - LE.W][a]
        top5 += a in np.argsort(-P[t - LE.W], kind="stable")[:5]
    log(f"  {h+8:2d}:00  sale {o:3d} | azar {ea:5.1f} (O/E {o/ea:.2f}) | motor {em:5.1f} (O/E {o/em:.2f}) | estaba en el Top-5 del motor {top5} veces")
io.open(os.path.join(AQUI, "salida_ocho_nuevo_detalle.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")

# ¿Cuántas veces estaba el de las 8:00 de ayer en el Top-15 de las 8:00, y qué pasa si se saca?
t8 = [t for t in range(LE.W, n) if D.hora[t] == 0 and D.fecha[t] >= "2024-11-01" and (D.dia[t] - 1, 0) in idx]
en15 = 0; base = 0; nuevo = 0
for t in t8:
    a = seq[idx[(D.dia[t] - 1, 0)]]; o = list(np.argsort(-P[t - LE.W], kind="stable"))
    base += seq[t] in o[:15]
    if a in o[:15]:
        en15 += 1; o.remove(a); o.append(a)
    nuevo += seq[t] in o[:15]
log(f"\nTop-15 de las 8:00 (nov-2024..sep-2026, {len(t8)} madrugadas): el de las 8:00 de ayer estaba dentro {en15} veces; "
    f"Top-15 {100*base/len(t8):.1f} % → sacándolo {100*nuevo/len(t8):.1f} %")
io.open(os.path.join(AQUI, "salida_ocho_nuevo_detalle.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
