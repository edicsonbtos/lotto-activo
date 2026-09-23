# -*- coding: utf-8 -*-
"""Escenario: ¿cómo habría ido cada forma de jugar, mes a mes, con 300 $?

Reproduce la historia REAL (sorteos que salieron y lo que el modelo dijo
antes de cada uno, walk-forward) del tramo de desarrollo [2000, 9357). La
parte en 30 días seguidos y juega cada tramo desde 300 $ con cada política.
No toca el tramo de prueba. Ojo: en prueba ciega el modelo rindió unos
5 puntos de retorno menos que en desarrollo, así que esto es algo optimista.

Las reglas de "Mi gestión" se fijaron ANTES de correr esto (no se ajustaron
al resultado):
  * jugada Top-5 escalonado (2-2-2-1-1 fichas);
  * ficha = banca // 400, mínimo 1 $ (con 300 $ -> 8 $ por sorteo);
  * freno del día: si hoy ya perdí el 15 % de la banca con que empecé el
    día, no juego más hasta mañana;
  * al llegar a 600 $ retiro los 300 $ iniciales y sigo jugando solo con
    la ganancia (ya no puedo terminar el mes perdiendo);
  * si la banca no alcanza para una jugada, me retiro.

Uso: python escenario_gestion.py
"""
import os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import lotto_eval as LE        # noqa: E402

PAGO, INICIAL, DIAS = 30, 300.0, 30
CACHE = os.path.join(AQUI, "exploracion", "calor_cache.npz")
HIST = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or RAIZ, "historial.txt")

datos = LE.cargar(HIST)
fin = LE.CORTE_FIJO - LE.W
if os.path.exists(CACHE):
    z = np.load(CACHE); P, y = z["P"], z["y"]
else:
    print("primera vez: calculando el ensamble walk-forward (varios minutos)...", flush=True)
    modelo = LE.cargar_modelo(os.path.join(AQUI, "modelos", "ensamble_v2.py"))
    P = modelo.predecir(datos, LE.W)[:fin]; y = datos.seq[LE.W:][:fin]
    np.savez_compressed(CACHE, P=P, y=y)
dia = np.asarray(datos.dia[LE.W:LE.W + fin])
puesto = np.argmax(np.argsort(-P, axis=1) == y[:, None], axis=1) + 1   # 1..38


def plan(tramos):
    f = [0] * 39
    for a, b, n in tramos:
        for p in range(a, b + 1):
            f[p] = n
    return f


ESC = plan([(1, 3, 2), (4, 5, 1)])
POLITICAS = {
    "Top-15 plano, 1 $/animal": (plan([(1, 15, 1)]), None),
    "Top-15 ponderado 3-2-1, 1 $/ficha": (plan([(1, 3, 3), (4, 5, 2), (6, 15, 1)]), None),
    "Top-3, 3 $/animal": (plan([(1, 3, 3)]), None),
    "Top-5 escalonado, 1 $/ficha": (ESC, None),
    "Mi gestión (Top-5 esc. + frenos)": (ESC, "gestion"),
}


def jugar(idx, fichas, modo):
    banca, retirado, maxv, llego = INICIAL, 0.0, INICIAL, False
    diario, d_act, inicio_dia = [], None, banca
    for i in idx:
        if dia[i] != d_act:
            if d_act is not None:
                diario.append(banca + retirado)
            d_act, inicio_dia = dia[i], banca
        ficha = max(1, int(banca // 400)) if modo else 1
        coste = sum(fichas) * ficha
        if banca < coste:
            continue
        if modo and inicio_dia - banca >= 0.15 * inicio_dia:
            continue                                   # freno del día
        banca += fichas[puesto[i]] * ficha * PAGO - coste
        if banca + retirado >= 2 * INICIAL:
            llego = True
            if modo and retirado == 0:
                banca -= INICIAL; retirado = INICIAL    # recupero lo invertido
        maxv = max(maxv, banca + retirado)
    diario.append(banca + retirado)
    return banca + retirado, llego, diario


dias_unicos = np.unique(dia)
tramos = [dias_unicos[k:k + DIAS] for k in range(0, len(dias_unicos) - DIAS + 1, DIAS)]
print(f"{len(tramos)} meses reales de {DIAS} días (desarrollo), cada uno empieza con {INICIAL:.0f} $.\n")
print(f"{'política':<36}{'final típico':>13}{'mes malo':>10}{'mes bueno':>11}{'meses ganando':>15}{'tocó 600':>10}")
res_gestion = []
for nombre, (fichas, modo) in POLITICAS.items():
    finales, llegos = [], 0
    for t in tramos:
        idx = np.where(np.isin(dia, t))[0]
        f, ll, diario = jugar(idx, fichas, modo)
        finales.append(f); llegos += ll
        if modo:
            res_gestion.append((f, t, diario))
    fs = sorted(finales); n = len(fs)
    print(f"{nombre:<36}{fs[n // 2]:>12.0f}${fs[n // 10]:>9.0f}${fs[(9 * n) // 10]:>10.0f}$"
          f"{sum(x > INICIAL for x in fs) / n * 100:>14.0f}%{llegos / n * 100:>9.0f}%")

# Diario del mes TÍPICO de mi gestión (el de la mediana, no el mejor).
res_gestion.sort(key=lambda r: r[0])
f, t, diario = res_gestion[len(res_gestion) // 2]
print(f"\nDIARIO DEL MES TÍPICO de 'Mi gestión' (el de la mitad, no el mejor): termina en {f:.0f} $")
print("día: " + "  ".join(f"{k + 1}:{v:.0f}" for k, v in enumerate(diario)))
peor = res_gestion[0]
print(f"El PEOR mes de 'Mi gestión' terminó en {peor[0]:.0f} $; el mejor en {res_gestion[-1][0]:.0f} $.")
print("\n'final típico' = mitad de los meses termina por encima; 'mes malo' = 1 de cada 10 meses")
print("termina por debajo; 'tocó 600' = llegó a doblar la plata en algún momento del mes.")
