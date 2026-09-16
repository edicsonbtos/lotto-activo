# -*- coding: utf-8 -*-
"""Valida el Top-3 del ensamble para 2026-09-15 h0 y responde: cuando el Top-3
suma probabilidad alta (>=14%), ¿acierta mas? Recalcula walk-forward todo el
bloque actual (T=12250..n) y agrupa aciertos por nivel de suma Top-3.
NO modifica ningun archivo.
"""
import json, os, sys
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE
from datetime import date

FECHA_OBJ, HORA_OBJ = "2026-09-15", 0
datos = LE.cargar()
n = len(datos)
d0 = date.fromisoformat(datos.fecha[0])
fobj = date.fromisoformat(FECHA_OBJ)
ext = LE.Datos(np.r_[datos.seq, 0], np.r_[datos.hora, HORA_OBJ],
               np.r_[datos.dow, fobj.weekday()], np.r_[datos.dia, (fobj - d0).days],
               list(datos.fecha) + [FECHA_OBJ])
pj = json.load(open(os.path.join(RAIZ, "pesos_ensamble.json"), encoding="utf-8"))
w = np.array(pj["pesos"])
ARRANQUE, R = 1000, 250
T = ARRANQUE + ((n - ARRANQUE) // R) * R
print(f"n={n}  bloque T={T}  pesos={np.round(w,3)}  base={pj['base']}", flush=True)

logs = []
for nombre in pj["base"]:
    sub = LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", nombre + ".py"))
    P = LE.normalizar(sub.predecir(ext, T))
    logs.append(np.log(np.clip(P, 1e-9, None)))
    print(f"  {nombre}: {P.shape[0]} filas ok", flush=True)
L = np.stack(logs, axis=1)
L -= np.log(np.exp(L).sum(2, keepdims=True))
z = np.einsum("nmk,m->nk", L, w)
z -= z.max(1, keepdims=True)
P = np.exp(z); P /= P.sum(1, keepdims=True)

POS = LE.POS
# ---- filas reales del bloque (T..n-1), la ultima fila es el sorteo futuro ----
y = datos.seq[T:]
Preal = P[:-1]
pobj = P[-1]
orden_o = np.argsort(-pobj)

print("\n== PREDICCION (codigo de produccion) para", FECHA_OBJ, "h", HORA_OBJ, "==")
for r, i in enumerate(orden_o[:10], 1):
    marca = " <<< TOP-3" if r <= 3 else ""
    print(f"  #{r:>2} {POS[i]:>3}  {pobj[i]*100:5.2f}%{marca}")
s3 = pobj[orden_o[:3]].sum()
s5 = pobj[orden_o[:5]].sum()
s10 = pobj[orden_o[:10]].sum()
print(f"  suma Top-3 = {s3*100:.2f}%  | suma Top-5 = {s5*100:.2f}% | suma Top-10 = {s10*100:.2f}%")

# ---- validacion: aciertos por nivel de suma Top-3 en el bloque ----
top3sum = np.sort(Preal, axis=1)[:, ::-1][:, :3].sum(1)
orden = np.argsort(-Preal, axis=1)
rango = np.argmax(orden == y[:, None], axis=1)
hit3 = rango < 3
print(f"\n== VALIDACION en el bloque actual ({len(y)} sorteos, walk-forward) ==")
print(f"  Global: Top-3 {hit3.mean()*100:.1f}% (azar 7.9%) | suma Top-3 media {top3sum.mean()*100:.2f}%")
print(f"\n  {'suma Top-3':>12} {'n':>4} {'aciertos':>8} {'tasa':>7} {'azar':>6}")
for lo, hi in [(0, 12), (12, 13), (13, 14), (14, 15), (15, 100)]:
    m = (top3sum * 100 >= lo) & (top3sum * 100 < hi)
    if m.sum() == 0:
        continue
    print(f"  {f'{lo}-{hi}%':>12} {int(m.sum()):>4} {int(hit3[m].sum()):>8} {hit3[m].mean()*100:>6.1f}% {'7.9%':>6}")
me = np.argsort(-top3sum)
print(f"\n  Los 20 sorteos con mayor suma Top-3 del bloque: aciertos {int(hit3[me[:20]].sum())}/20 = {hit3[me[:20]].mean()*100:.0f}%")
print(f"  Los 20 con menor suma Top-3:                    aciertos {int(hit3[me[-20:]].sum())}/20 = {hit3[me[-20:]].mean()*100:.0f}%")
print(f"\n  Manana entra en el tramo 14-15% (suma={s3*100:.2f}%).")
