# -*- coding: utf-8 -*-
"""¿Cuántos animales conviene jugar? Economía por puesto y calibración.

Lee la matriz walk-forward del ensamble en DESARROLLO [2000, 9357) que dejó
calor_lista_real.py en calor_cache.npz (no recalcula el modelo y NO toca el
tramo de prueba). Imprime:

  1. Acierto por puesto del orden (1º, 2º, ...) contra el 3,33 % que exige
     el pago 30x. Un puesto por debajo pierde plata aunque "acierte a veces".
  2. Calibración: cuando el modelo dice p, ¿sale con frecuencia p?
  3. Estrategias (Top-N plano, Top-5 escalonado 2-2-2-1-1) por mitades del
     tramo, con IC95 por bootstrap de bloques de 12 sorteos (una jornada).

Uso:  python herramientas/exploracion/estrategia_top5.py
"""
import os
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
PAGO = 30

CACHE = os.path.join(AQUI, "calor_cache.npz")
if not os.path.exists(CACHE):
    # La caché no se versiona (se regenera). En un servidor recién desplegado
    # se calcula aquí, una sola vez: el ensamble walk-forward tarda varios minutos.
    import sys
    RAIZ = os.path.dirname(os.path.dirname(AQUI))
    sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
    import lotto_eval as LE
    print("primera vez: calculando el ensamble walk-forward en desarrollo (varios minutos)...", flush=True)
    datos = LE.cargar(os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or RAIZ, "historial.txt"))
    modelo = LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", "ensamble_v2.py"))
    fin = LE.CORTE_FIJO - LE.W                  # solo desarrollo: no toca el tramo de prueba
    M = modelo.predecir(datos, LE.W)[:fin]
    np.savez_compressed(CACHE, P=M, y=datos.seq[LE.W:][:fin])
z = np.load(CACHE)
P, y = z["P"], z["y"]
P = P / P.sum(1, keepdims=True)
n = len(y)
R = np.argsort(-P, axis=1)
H = (np.arange(P.shape[1])[None, :] == y[:, None]).astype(float)
puesto = np.argmax(R == y[:, None], axis=1) + 1

print(f"desarrollo walk-forward: n = {n}\n")
print("1. ACIERTO POR PUESTO (equilibrio a 30x = 3,33 % por animal)")
print(f"{'puestos':<9}{'acierto':>9}{'modelo dice':>13}{'retorno/ficha':>15}")
for a, b in [(1, 1), (2, 3), (4, 5), (6, 8), (9, 12), (13, 15), (16, 20), (21, 30), (31, 38)]:
    w = b - a + 1
    tasa = ((puesto >= a) & (puesto <= b)).mean() / w
    dice = np.take_along_axis(P, R[:, a - 1:b], 1).mean()
    print(f"{a:>2}-{b:<6}{tasa*100:>8.2f}%{dice*100:>12.2f}%{(PAGO*tasa-1)*100:>+14.1f}%")

print("\n2. CALIBRACIÓN (probabilidad individual de cada animal)")
p, h = P.ravel(), H.ravel()
cortes = [0, .01, .02, .025, .03, 1/30, .037, .04, .045, .05, .06, 1]
print(f"{'dice':<16}{'casos':>8}{'promete':>9}{'sale':>8}  IC95")
for lo, hi in zip(cortes[:-1], cortes[1:]):
    m = (p >= lo) & (p < hi)
    N = int(m.sum())
    if N < 100:
        continue
    r = h[m].mean(); e = 1.96 * np.sqrt(r * (1 - r) / N)
    print(f"{lo*100:5.2f}-{hi*100:<9.2f}{N:>8}{p[m].mean()*100:>8.2f}%{r*100:>7.2f}%  [{(r-e)*100:.2f}, {(r+e)*100:.2f}]")


def plan(fichas):
    S = np.zeros_like(P)
    np.put_along_axis(S, R[:, :len(fichas)], np.array(fichas, float)[None, :].repeat(n, 0), 1)
    return S


def roi_ic(S, sl, B=2000, blk=12, seed=1):
    st = S[sl].sum(1); pr = PAGO * (S[sl] * H[sl]).sum(1) - st
    nb = len(pr) // blk
    pb = pr[:nb * blk].reshape(nb, blk).sum(1); sb = st[:nb * blk].reshape(nb, blk).sum(1)
    idx = np.random.default_rng(seed).integers(0, nb, (B, nb))
    lo, hi = np.percentile(pb[idx].sum(1) / sb[idx].sum(1), [2.5, 97.5])
    return st.mean(), pr.mean(), pr.sum() / st.sum(), lo, hi


print("\n3. ESTRATEGIAS (1 ficha = 1 unidad; ganancia por sorteo y retorno)")
estr = {"Top-3 plano": [1] * 3, "Top-5 plano": [1] * 5, "Top-5 2-2-2-1-1": [2, 2, 2, 1, 1],
        "Top-8 plano": [1] * 8, "Top-15 plano": [1] * 15}
print(f"{'estrategia':<17}{'tramo':<7}{'fichas':>7}{'gana/sorteo':>13}{'retorno':>9}   IC95")
for nombre, f in estr.items():
    S = plan(f)
    for t, sl in (("1a mit", slice(0, n // 2)), ("2a mit", slice(n // 2, n)), ("todo", slice(0, n))):
        st, g, roi, lo, hi = roi_ic(S, sl)
        print(f"{nombre:<17}{t:<7}{st:>7.0f}{g:>+13.3f}{roi*100:>+8.1f}%   [{lo*100:+.1f}, {hi*100:+.1f}]")
