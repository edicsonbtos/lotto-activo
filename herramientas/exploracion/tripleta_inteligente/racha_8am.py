# -*- coding: utf-8 -*-
"""Anexo 2 del PREREGISTRO: la racha de las 8:00 (descriptivo). Usa el historial con fechas corregidas
(reentreno/historial_la.txt, hasta 2026-09-29) y el ensamble walk-forward recalculado (reentreno/cache/todo_*.npy).
Antes: cd herramientas/exploracion/enjambre_2026-09-30/reentreno && for k in I S H; do python sub.py todo $k; done
(~1 min, crea cache/ que no va al repo).
Uso: python herramientas/exploracion/tripleta_inteligente/racha_8am.py -> salida_racha_8am.txt"""
import io, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
RE = os.path.join(RAIZ, "herramientas", "exploracion", "enjambre_2026-09-30", "reentreno")
sys.path.insert(0, RE)
import comun as C  # noqa: E402
LE = C.LE
NOMBRE = ["Delfín", "Ballena", "Carnero", "Toro", "Ciempiés", "Alacrán", "León", "Rana", "Perico", "Ratón", "Águila",
          "Tigre", "Gato", "Caballo", "Mono", "Paloma", "Zorro", "Oso", "Pavo", "Burro", "Chivo", "Cochino", "Gallo",
          "Camello", "Cebra", "Iguana", "Gallina", "Vaca", "Perro", "Zamuro", "Elefante", "Caimán", "Lapa", "Ardilla",
          "Pescado", "Venado", "Jirafa", "Culebra"]
SAL = []


def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); SAL.append(s)


D = LE.cargar(os.path.join(RE, "historial_la.txt")); seq = np.asarray(D.seq); n = len(seq)
L = C.cargar_L("todo", ["I", "S", "H"]); y = seq[C.ARRANQUE:]
desde = LE.W
P = C.combinar(L, y, desde, **C.COMB["base"])          # filas desde..n-1
orden = np.argsort(-P, axis=1, kind="stable")
# hueco en días y "salió ayer" para cada sorteo
ultdia = np.full(38, -10**6); gap = np.zeros(n, int); ayer = np.zeros(n, bool)
por_dia = {}
for t in range(n):
    gap[t] = D.dia[t] - ultdia[seq[t]]
    ultdia[seq[t]] = D.dia[t]
for t in range(n):
    por_dia.setdefault(D.dia[t], set()).add(int(seq[t]))
for t in range(n):
    ayer[t] = seq[t] in por_dia.get(D.dia[t] - 1, set())
ocho = [t for t in range(n) if D.hora[t] == 0]

log("R1 — ganadores de las 8:00 desde 2026-09-14 (datos hasta 2026-09-29)")
vivos = [t for t in ocho if D.fecha[t] >= "2026-09-14"]
pos = {}
for t in vivos:
    j = t - desde; p = int(np.where(orden[j] == seq[t])[0][0]) + 1; pos[t] = p
    log(f"  {D.fecha[t]}  {LE.POS[seq[t]]:>2} {NOMBRE[seq[t]]:<9} hueco {gap[t]:2d} d  salió ayer {'sí' if ayer[t] else 'no'}"
        f"  puesto {p:2d}{'  ← Top-15' if p <= 15 else ''}{'  ← Top-5' if p <= 5 else ''}")
g13 = [1 <= gap[t] <= 3 for t in vivos]
log(f"  hueco 1-3 d: {sum(g13)}/{len(vivos)};  Top-15: {sum(pos[t] <= 15 for t in vivos)}/{len(vivos)};  "
    f"Top-5: {sum(pos[t] <= 5 for t in vivos)}/{len(vivos)};  salió ayer: {sum(ayer[t] for t in vivos)}/{len(vivos)}")
# masa del modelo en hueco 1-3 a las 8:00 en vivo
m13 = []
for t in vivos:
    g_all = D.dia[t] - np.array([max([D.dia[s] for s in range(t) if seq[s] == a] or [-10**6]) for a in range(38)])
    m13.append(P[t - desde][(g_all >= 1) & (g_all <= 3)].sum())
log(f"  el ensamble le daba a los animales con hueco 1-3 d: {100*np.mean(m13):.0f} % de media "
    f"(cuántos animales había con hueco 1-3 d: ~{np.mean([np.sum((lambda gg: (gg>=1)&(gg<=3))(D.dia[t]-np.array([max([D.dia[s] for s in range(max(0,t-60),t) if seq[s]==a] or [-10**6]) for a in range(38)]))) for t in vivos]):.0f} de 38)")

log("\nR2 — rachas de madrugadas seguidas con hueco 1-3 d, en desarrollo (8:00 desde nov-2024, filas < 9357)")
dev = [t for t in ocho if t < LE.CORTE_FIJO]
x = np.array([1 <= gap[t] <= 3 for t in dev], int); p0 = x.mean()
runs = []; r = 0
for v in x:
    if v: r += 1
    else:
        if r: runs.append(r)
        r = 0
if r: runs.append(r)
log(f"  madrugadas: {len(dev)}; tasa de hueco 1-3 d: {100*p0:.1f} %")
for N in (5, 8, 11):
    obs = sum(1 for rr in runs if rr >= N)
    esp = (len(x) - N + 1) * (1 - p0) * p0 ** N + p0 ** N      # rachas que empiezan (aprox.)
    log(f"  rachas de ≥ {N:2d}: {obs} observadas, ~{esp:.1f} esperadas por azar con esa tasa; prob. de una racha de {N} = {100*p0**N:.2f} %")
log(f"  racha más larga en desarrollo: {max(runs)}")

log("\nR3 — ¿la racha predice la siguiente? (desarrollo)")
for k in (1, 3, 5):
    sel = [i for i in range(k, len(x)) if x[i - k:i].all()]
    log(f"  tras {k} seguidas con hueco 1-3 d: la siguiente también {100*x[sel].mean():.1f} % (n={len(sel)}) vs general {100*p0:.1f} %")
io.open(os.path.join(AQUI, "salida_racha_8am.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")

log("\nR4 — la racha de Top-15 a las 8:00 (desarrollo, ensamble recalculado)")
hit = np.array([int(np.where(orden[t - desde] == seq[t])[0][0]) < 15 for t in dev], int); q = hit.mean()
runs = []; r = 0
for v in hit:
    if v: r += 1
    else:
        if r: runs.append(r)
        r = 0
if r: runs.append(r)
log(f"  Top-15 a las 8:00 en desarrollo: {100*q:.1f} %; rachas de ≥ 9 seguidas: {sum(rr >= 9 for rr in runs)} "
    f"(prob. de 9 seguidas {100*q**9:.1f} %); racha más larga {max(runs)}")
for k in (1, 3, 5):
    sel = [i for i in range(k, len(hit)) if hit[i - k:i].all()]
    log(f"  tras {k} aciertos seguidos a las 8:00, el siguiente acierta {100*hit[sel].mean():.1f} % (n={len(sel)}) vs {100*q:.1f} %")
io.open(os.path.join(AQUI, "salida_racha_8am.txt"), "w", encoding="utf-8").write("\n".join(SAL) + "\n")
