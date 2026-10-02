# -*- coding: utf-8 -*-
"""Las 8:00 desde que el modelo está en vivo (2026-09-14) hasta el último dato local (2026-09-29), con el ensamble
RECONSTRUIDO walk-forward (puede diferir un poco del congelado de la web, que es el oficial). Descriptivo.
Antes: reentreno/sub.py todo I|S|H. Uso: python .../vivo_8am.py -> salida_vivo_8am.txt"""
import io, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
RE = os.path.join(RAIZ, "herramientas", "exploracion", "enjambre_2026-09-30", "reentreno"); sys.path.insert(0, RE)
import comun as C  # noqa: E402
LE = C.LE; SAL = []
NOM = ["Delfín", "Ballena", "Carnero", "Toro", "Ciempiés", "Alacrán", "León", "Rana", "Perico", "Ratón", "Águila", "Tigre",
       "Gato", "Caballo", "Mono", "Paloma", "Zorro", "Oso", "Pavo", "Burro", "Chivo", "Cochino", "Gallo", "Camello", "Cebra",
       "Iguana", "Gallina", "Vaca", "Perro", "Zamuro", "Elefante", "Caimán", "Lapa", "Ardilla", "Pescado", "Venado", "Jirafa", "Culebra"]
def log(*a):
    s = " ".join(str(x) for x in a); print(s); SAL.append(s)
D = LE.cargar(os.path.join(RE, "historial_la.txt")); seq = np.asarray(D.seq); n = len(seq)
L = C.cargar_L("todo", ["I", "S", "H"]); P = C.combinar(L, seq[C.ARRANQUE:], LE.W, **C.COMB["base"])
ult = np.full(38, -10**6); GD = np.zeros((n, 38), int)
for t in range(n):
    GD[t] = D.dia[t] - ult; ult[seq[t]] = D.dia[t]
idx = {(D.dia[t], int(D.hora[t])): t for t in range(n)}
def grupo(g):
    return "salió ayer" if g == 1 else ("hace 2-3 d" if g <= 3 else "frío (4+ d)")
log("Las 8:00 en vivo (motor reconstruido)")
log("fecha       ganador          puesto  Top-5  Top-15  hueco   grupo         prob. motor  ¿8:00 de ayer?  ¿núm. del día?")
for t in [t for t in range(n) if D.hora[t] == 0 and D.fecha[t] >= "2026-09-14"]:
    p = P[t - LE.W]; o = np.argsort(-p, kind="stable"); a = int(seq[t]); pos = int(np.where(o == a)[0][0]) + 1
    a8 = idx.get((D.dia[t] - 1, 0)); dnum = int(D.fecha[t][8:10])
    log(f"{D.fecha[t]}  {LE.POS[a]:>2} {NOM[a]:<10}  {pos:5d}   {'sí' if pos <= 5 else '—':^5}  {'sí' if pos <= 15 else 'NO':^6}  {GD[t][a]:3d} d  "
        f"{grupo(GD[t][a]):<12}  {100*p[a]:5.1f} %       {'sí' if a8 is not None and seq[a8] == a else 'no':^6}         {'sí' if LE.POS[a] == str(dnum) else 'no'}")
log("\nCuando FALLA el Top-15 a las 8:00, ¿qué tipo de animal sale? (época actual, nov-2025..sep-2026)")
cnt = {"aciertos": {}, "fallos": {}}
for t in [t for t in range(LE.W, n) if D.hora[t] == 0 and D.fecha[t] >= "2025-11-01"]:
    p = P[t - LE.W]; a = int(seq[t]); pos = int(np.where(np.argsort(-p, kind="stable") == a)[0][0])
    k = "aciertos" if pos < 15 else "fallos"; gr = grupo(GD[t][a]); cnt[k][gr] = cnt[k].get(gr, 0) + 1
for k in ("aciertos", "fallos"):
    tot = sum(cnt[k].values())
    log(f"  {k}: " + ", ".join(f"{g} {100*v/tot:.0f} %" for g, v in sorted(cnt[k].items())) + f"  (n={tot})")
io.open(os.path.join(AQUI, "salida_vivo_8am.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
