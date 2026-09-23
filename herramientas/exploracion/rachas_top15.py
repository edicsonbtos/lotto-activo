# -*- coding: utf-8 -*-
"""¿Se pueden predecir las rachas de fallos del Top-15?

Pregunta del usuario (2026-09-22). Solo tramo de DESARROLLO [2000, 9357), con
la caché walk-forward del ensamble. No toca el tramo de prueba.

CRITERIO FIJADO ANTES DE CORRER:
  A. Tras k fallos seguidos (k = 1..6), ¿el siguiente sorteo acierta distinto
     que tras un acierto? Contraste Mantel-Haenszel estratificado por HORA
     (el crudo da ~88 % de falsos positivos aquí). Hay 6 contrastes: se exige
     |z| >= 3 en alguno para decir que la racha informa.
  B. ¿Las rachas largas salen más a menudo de lo que daría una moneda con la
     misma tasa de acierto por hora? Comparación de la racha máxima y del nº
     de rachas >= 4 contra 2.000 simulaciones independientes. Se exige que lo
     real quede fuera del 95 % central.
  Si A y B no se cumplen: las rachas NO se pueden predecir; son azar.
"""
import os, sys, math, random
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE        # noqa: E402

z = np.load(os.path.join(AQUI, "calor_cache.npz"))
P, y = z["P"], z["y"]
d = LE.cargar(os.path.join(RAIZ, "historial.txt"))
fin = LE.CORTE_FIJO - LE.W
hora = np.asarray(d.hora[LE.W:LE.W + fin])
puesto = np.argmax(np.argsort(-P, axis=1) == y[:, None], axis=1) + 1
acierto = (puesto <= 15).astype(int)
n = len(acierto)
print(f"desarrollo n={n} · Top-15 acierta {acierto.mean()*100:.2f} %\n")

# racha de fallos en curso ANTES de cada sorteo (se conoce antes de jugar)
racha = np.zeros(n, int)
for i in range(1, n):
    racha[i] = 0 if acierto[i - 1] else racha[i - 1] + 1

print("A. ¿Acierta distinto el sorteo que viene tras k fallos seguidos? (estratificado por hora)")
print(f"{'tras':<16}{'casos':>7}{'acierta':>9}{'tras acierto':>14}{'z (MH)':>9}")
for k in range(1, 7):
    grupo = racha >= k if k == 6 else racha == k
    base = racha == 0
    num = var = 0.0; kk = nn = 0
    for h in np.unique(hora):
        m = hora == h
        a = acierto[m & grupo]; b = acierto[m & base]
        n1, n0 = len(a), len(b)
        if n1 == 0 or n0 == 0:
            continue
        N = n1 + n0; t = a.sum() + b.sum()
        num += a.sum() - n1 * t / N
        var += n1 * n0 * t * (N - t) / (N * N * (N - 1)) if N > 1 else 0
        kk += a.sum(); nn += n1
    zmh = num / math.sqrt(var) if var > 0 else 0.0
    etiqueta = f"{k}{'+' if k == 6 else ''} fallo(s)"
    print(f"{etiqueta:<16}{nn:>7}{kk/nn*100:>8.1f}%{acierto[racha == 0].mean()*100:>13.1f}%{zmh:>+9.2f}")

print("\nB. ¿Hay más rachas largas de las que daría el azar puro (misma tasa por hora)?")
tasa_h = {h: acierto[hora == h].mean() for h in np.unique(hora)}
def resumen(sec):
    mx = r = largas = 0
    for x in sec:
        if x:
            if r >= 4: largas += 1
            r = 0
        else:
            r += 1; mx = max(mx, r)
    if r >= 4: largas += 1
    return mx, largas
real = resumen(acierto)
rng = random.Random(20260922)
sims = [resumen([1 if rng.random() < tasa_h[h] else 0 for h in hora]) for _ in range(2000)]
for j, nombre in ((0, "racha más larga"), (1, "nº de rachas de 4+")):
    v = sorted(s[j] for s in sims)
    lo, hi = v[50], v[1949]
    print(f"  {nombre:<20} real {real[j]:>4} · azar puro: 95 % entre {lo} y {hi}"
          f" -> {'FUERA (hay estructura)' if not lo <= real[j] <= hi else 'normal'}")

print("\nC. Solo descriptivo: acierto del Top-15 por hora del sorteo")
for h in sorted(tasa_h):
    print(f"  hora {h:>2}: {tasa_h[h]*100:5.1f} %")
