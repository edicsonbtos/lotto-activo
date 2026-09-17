# -*- coding: utf-8 -*-
"""Forense Tarea A (v2): usa la ruta EXACTA de producción (prediccion.Predictor)
para recomputar el top servido en cada sorteo del 16 y compararlo con lo que
muestra la página viva. También recomputa con pesos UNIFORMES para probar la
hipótesis del fallback. Solo lee; no toca modelos ni pesos."""
import os, sys, json
import numpy as np

RUTA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RUTA)
import prediccion  # noqa: E402  (lee PESOS de RUTA en local = mismo archivo del repo)

P = prediccion.Predictor()
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}

# Sorteos servidos (tabla histórica de la página viva, 2026-09-17 ~00:20 UTC).
# hora = índice 0-based (0=8AM ... 11=7PM)
SERVIDOS = [
    ("2026-09-16", 0,  ["23", "24", "4"],  "30"),   # 8 AM
    ("2026-09-16", 1,  ["7", "2", "13"],   "29"),   # 9 AM
    ("2026-09-16", 2,  ["24", "23", "4"],  "15"),   # 10 AM
    ("2026-09-16", 3,  ["24", "4", "23"],  "34"),   # 11 AM
    ("2026-09-16", 4,  ["24", "4", "23"],  "12"),   # 12 PM
    ("2026-09-16", 5,  ["24", "23", "4"],  "12"),   # 1 PM
    ("2026-09-16", 6,  ["23", "24", "4"],  "30"),   # 2 PM
    ("2026-09-16", 7,  ["23", "24", "4"],  "32"),   # 3 PM
    ("2026-09-16", 8,  ["2", "13", "25"],  "10"),   # 4 PM
    # 5 PM (idx 9): sin fila en el histórico
    ("2026-09-16", 10, ["25", "7", "13"],  "9"),    # 6 PM
    ("2026-09-16", 11, ["2", "7", "25"],   "12"),   # 7 PM
    ("2026-09-17", 0,  ["2", "22", "13"],  None),   # próximo (slot vivo)
]

# filas que el volumen tiene y la copia local no (strip de la página viva)
EXTRA = [("2026-09-16", 8, "10"), ("2026-09-16", 9, "31"),
         ("2026-09-16", 10, "9"), ("2026-09-16", 11, "12")]

HIST_TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_hist_tmp.txt")
with open(os.path.join(RUTA, "historial.txt"), encoding="utf-8") as f:
    lineas = f.readlines()
with open(HIST_TMP, "w", encoding="utf-8") as f:
    f.writelines(lineas)
    for fe, h, num in EXTRA:
        f.write(f"{fe} {h} {num}\n")

import lotto_eval as LE  # noqa: E402
datos_full = LE.cargar(HIST_TMP)
indice = {(f, h): i for i, (f, h) in enumerate(zip(datos_full.fecha, datos_full.hora))}

def top_de(p, k=3):
    orden = np.argsort(-p)
    return [POS[j] for j in orden[:k]], orden

def recompute(fecha, h, uniforme=False):
    """Reproduce prediccion.Predictor.calcular sobre el estado previo al sorteo."""
    i = indice[(fecha, h)]
    d = LE.Datos(datos_full.seq[:i], datos_full.hora[:i], datos_full.dow[:i],
                 datos_full.dia[:i], list(datos_full.fecha[:i]))
    n = len(d)
    ext = prediccion._extender(d, fecha, h)
    logs = []
    for nombre in P.ens.base:
        sub = LE.cargar_modelo(os.path.join(prediccion.HERR, "modelos", nombre + ".py"))
        R = getattr(sub, "R", None) or 250
        T = prediccion._frontera(n, P.ens.arranque, R)
        Pm = LE.normalizar(sub.predecir(ext, T))[-1]
        logs.append(np.log(np.clip(Pm, 1e-9, None)))
    L = np.stack(logs); L -= np.log(np.exp(L).sum(1, keepdims=True))
    w = np.full(len(P.ens.base), 1.0 / len(P.ens.base)) if uniforme else np.array(json.load(open(os.path.join(RUTA, "pesos_ensamble.json"), encoding="utf-8"))["pesos"])
    z = w @ L
    p = np.exp(z - z.max()); p /= p.sum()
    return p

print(f"{'slot':<16}{'salio':<6}{'servido':<13}{'recomp(pesos)':<13}{'recomp(unif)':<13}")
print("-" * 62)
for fecha, h, servido, salio in SERVIDOS:
    p1 = recompute(fecha, h, uniforme=False)
    p2 = recompute(fecha, h, uniforme=True)
    t1, _ = top_de(p1); t2, _ = top_de(p2)
    m1 = "OK" if set(t1) == set(servido) else "!!"
    m2 = "OK" if set(t2) == set(servido) else "!!"
    print(f"{fecha} h{h:<3}{str(salio or '-'):<6}{' '.join(servido):<13}{' '.join(t1)+' '+m1:<13}{' '.join(t2)+' '+m2:<13}")
    if m1 == "!!":
        probs = [(POS[j], round(float(p1[j]) * 100, 2)) for j in np.argsort(-p1)[:6]]
        print(f"     pesos reales top6: {probs}")
os.remove(HIST_TMP)
