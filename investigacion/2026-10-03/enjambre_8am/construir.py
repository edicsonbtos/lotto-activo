# Caché compartida para la investigación de las 8:00 (2026-10-03)
import os, sys, numpy as np
RAIZ = "/home/user/lotto-activo"
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE
AQUI = os.path.dirname(os.path.abspath(__file__))
D = LE.cargar(os.path.join(AQUI, "hist_la.txt"))
S = np.asarray(D.seq); H = np.asarray(D.hora); DI = np.asarray(D.dia); F = np.array(D.fecha); DOW = np.asarray(D.dow)
ens = LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", "ensamble_v2.py"))
P = LE.normalizar(ens.predecir(D, LE.W))
n = len(S)
Pfull = np.full((n, 38), np.nan); Pfull[LE.W:] = P
first = {}
for t in range(n): first.setdefault(int(DI[t]), t)
es_primero = np.zeros(n, bool)
for d, t in first.items(): es_primero[t] = True
# ajuste en producción (prediccion.AJUSTE_PRIMER = {1: 0.272, 3: 1.736})
Paj = Pfull.copy()
for d, t in first.items():
    if t < LE.W: continue
    m = np.ones(38)
    for k, mult in {1: 0.272, 3: 1.736}.items():
        tp = first.get(d - k)
        if tp is not None and H[tp] == H[t]: m[S[tp]] *= mult
    q = Pfull[t] * m; Paj[t] = q / q.sum()
tramo = np.array(["cal" if t < LE.W else ("dev" if t < LE.CORTE_FIJO else ("vivo" if F[t] >= "2026-09-15" else "prueba")) for t in range(n)])
np.savez_compressed(os.path.join(AQUI, "base8.npz"), seq=S, hora=H, dia=DI, fecha=F, dow=DOW, P=Pfull, P_aj=Paj, es_primero=es_primero, tramo=tramo)
for tr in ("dev", "prueba", "vivo"):
    for h in (0, 1):
        m = (tramo == tr) & es_primero & (H == h)
        print(tr, "primer sorteo hora", h, "n=", m.sum(), F[m][:1], F[m][-1:])
print("filas", n, "ultima", F[-1])
