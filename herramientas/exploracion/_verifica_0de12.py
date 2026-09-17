# -*- coding: utf-8 -*-
"""Tarea B: verifica el '0/12 en top-15' del 2026-09-16 usando los top-15
recomputados (que coinciden con los servidos, demostrado en _forense_top16)."""
import os, sys, json
import numpy as np

RUTA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RUTA)
import prediccion  # noqa: E402
import lotto_eval as LE  # noqa: E402

POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}

SLOTS = [  # (fecha, hora_idx, salio)  -- 5PM (idx 9) no tiene predicción
    ("2026-09-16", 0, "30"), ("2026-09-16", 1, "29"), ("2026-09-16", 2, "15"),
    ("2026-09-16", 3, "34"), ("2026-09-16", 4, "12"), ("2026-09-16", 5, "12"),
    ("2026-09-16", 6, "30"), ("2026-09-16", 7, "32"), ("2026-09-16", 8, "10"),
    ("2026-09-16", 10, "9"), ("2026-09-16", 11, "12"),
]
EXTRA = [("2026-09-16", 8, "10"), ("2026-09-16", 9, "31"),
         ("2026-09-16", 10, "9"), ("2026-09-16", 11, "12")]

HIST_TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_hist_tmp.txt")
with open(os.path.join(RUTA, "historial.txt"), encoding="utf-8") as f:
    lineas = f.readlines()
with open(HIST_TMP, "w", encoding="utf-8") as f:
    f.writelines(lineas)
    for fe, h, num in EXTRA:
        f.write(f"{fe} {h} {num}\n")

datos_full = LE.cargar(HIST_TMP)
indice = {(f, h): i for i, (f, h) in enumerate(zip(datos_full.fecha, datos_full.hora))}

P = prediccion.Predictor()
aciertos = 0
print(f"{'slot':<14}{'salio':<6}{'en top-15?':<11}{'rank de lo que salio'}")
for fecha, h, salio in SLOTS:
    i = indice[(fecha, h)]
    d = LE.Datos(datos_full.seq[:i], datos_full.hora[:i], datos_full.dow[:i],
                 datos_full.dia[:i], list(datos_full.fecha[:i]))
    ext = prediccion._extender(d, fecha, h)
    logs = []
    for nombre in P.ens.base:
        sub = LE.cargar_modelo(os.path.join(prediccion.HERR, "modelos", nombre + ".py"))
        R = getattr(sub, "R", None) or 250
        T = prediccion._frontera(len(d), P.ens.arranque, R)
        Pm = LE.normalizar(sub.predecir(ext, T))[-1]
        logs.append(np.log(np.clip(Pm, 1e-9, None)))
    L = np.stack(logs); L -= np.log(np.exp(L).sum(1, keepdims=True))
    w = np.array(json.load(open(os.path.join(RUTA, "pesos_ensamble.json"), encoding="utf-8"))["pesos"])
    z = w @ L
    p = np.exp(z - z.max()); p /= p.sum()
    orden = np.argsort(-p)
    s = IDX[salio]
    rank = int(np.where(orden == s)[0][0]) + 1
    hit = rank <= 15
    aciertos += hit
    print(f"{fecha} h{h:<3}{salio:<6}{str(hit):<11}rank {rank} de 38 (p={p[s]*100:.2f}%)")
print(f"\naciertos top-15: {aciertos}/{len(SLOTS)}  (con predicción)")
print(f"P(0/11) si h=53.07%: {(1-0.5307)**11:.5f}")
os.remove(HIST_TMP)
