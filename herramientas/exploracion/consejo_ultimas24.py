# -*- coding: utf-8 -*-
"""Ranking del resultado real dentro de la prediccion del ensamble (produccion)
para los ultimos 24 sorteos del historial. Mismo camino que prediccion.py:
submodelos en frontera de bloque + pesos de pesos_ensamble.json. Walk-forward:
la fila t solo usa datos[:t]. NO modifica ningun archivo.
"""
import json, os, sys
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

ULT = 24
datos = LE.cargar()
n = len(datos)
ARRANQUE, R = 1000, 250
T0 = ARRANQUE + ((n - ULT - ARRANQUE) // R) * R
# verificar que los 24 sorteos estan en el mismo bloque
assert ARRANQUE + ((n - 1 - ARRANQUE) // R) * R == T0, "los ultimos 24 cruzan frontera de bloque"

base = json.load(open(os.path.join(RAIZ, "pesos_ensamble.json"), encoding="utf-8"))
w = np.array(base["pesos"])
nombres = base["base"]
print(f"historial n={n}  bloque T0={T0}  pesos={np.round(w,3)}  base={nombres}")

logs = []
for nombre in nombres:
    sub = LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", nombre + ".py"))
    P = LE.normalizar(sub.predecir(datos, T0))
    logs.append(np.log(np.clip(P, 1e-9, None)))
    print(f"  {nombre}: {P.shape[0]} filas ok", flush=True)
L = np.stack(logs, axis=1)                     # (n-T0, M, 38)
L -= np.log(np.exp(L).sum(2, keepdims=True))
z = np.einsum("nmk,m->nk", L, w)
z -= z.max(1, keepdims=True)
P = np.exp(z); P /= P.sum(1, keepdims=True)

filas = P[-ULT:]
ys = datos.seq[-ULT:]
POS = LE.POS
print(f"\n{'fecha':<11}{'hora':>4} {'salio':>6} {'rango':>6} {'p(real)':>8}  top3 del modelo")
rangos = []
for i in range(ULT):
    orden = np.argsort(-filas[i])
    y = int(ys[i])
    rango = int(np.where(orden == y)[0][0]) + 1
    rangos.append(rango)
    top3 = " ".join(f"{POS[o]}({filas[i][o]*100:.1f})" for o in orden[:3])
    marca = {True: "SI", False: "--"}
    print(f"{datos.fecha[-ULT+i]:<11}{int(datos.hora[-ULT+i]):>4} {POS[y]:>6} {rango:>6} {filas[i][y]*100:>7.2f}%  {top3}")

rangos = np.array(rangos)
print("\n== RESUMEN ultimos 24 sorteos (ensamble produccion) ==")
for k in (1, 3, 5, 10):
    hits = int((rangos <= k).sum())
    print(f"Top-{k:<2}: {hits:>2}/24 = {hits/24*100:5.1f}%   azar {k/38*100:5.1f}%   "
          f"suma p modelo media {np.mean([filas[i][np.argsort(-filas[i])[:k]].sum() for i in range(ULT)])*100:5.1f}%")
print(f"rango medio del resultado: {rangos.mean():.1f}  (azar 19.5)")
print("\n== matematica del margen (pago 30x) ==")
for k in (1, 3, 5, 10):
    hits = int((rangos <= k).sum())
    roi = (30 * hits - k * ULT) / (k * ULT)
    print(f"apostar Top-{k:<2}: necesitas >{k/30*100:5.1f}% para no perder | estas 24h: {hits/24*100:5.1f}% -> ROI {roi*100:+6.1f}%")
