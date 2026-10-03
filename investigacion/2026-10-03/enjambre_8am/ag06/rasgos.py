# ag06 — rasgos por (primer sorteo, animal) para medir calibración del motor en el primer sorteo
import os, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
d = np.load(os.path.join(AQUI, "..", "base8.npz"), allow_pickle=True)
S, H, DI, F = d["seq"], d["hora"], d["dia"], d["fecha"]
P, PAJ, EP, TR = d["P"], d["P_aj"], d["es_primero"], d["tramo"]
n = len(S)
filas = np.where(EP & (TR != "cal"))[0]
ERA = np.where(F[filas] < "2024-11-28", 9, 8)  # 9 = primer sorteo 9:00, 8 = primer sorteo 8:00

# para cada fila de primer sorteo y animal: horas exactas desde la última aparición, hueco en días,
# apariciones en últimos 3 y 7 días calendario, franja en que salió ayer
NA = 38
ult_t = np.full(NA, -1)
horas = np.full((len(filas), NA), np.inf)
hdias = np.full((len(filas), NA), 99)
c3 = np.zeros((len(filas), NA), int); c7 = np.zeros((len(filas), NA), int)
fr_ayer = np.full((len(filas), NA), -1)  # -1 no salió ayer; 0 mañana (8-11), 1 tarde (12-15), 2 noche (16-19)
idx = {t: k for k, t in enumerate(filas)}
for t in range(n):
    if t in idx:
        k = idx[t]
        for a in range(NA):
            j = ult_t[a]
            if j < 0: continue
            horas[k, a] = (DI[t] - DI[j]) * 24 + (H[t] - H[j])
            hdias[k, a] = DI[t] - DI[j] - 1
        # conteos
        lo = np.searchsorted(DI, DI[t] - 7)
        for j in range(lo, t):
            dd = DI[t] - DI[j]
            c7[k, S[j]] += 1
            if dd <= 3: c3[k, S[j]] += 1
            if dd == 1: fr_ayer[k, S[j]] = H[j] // 4
    ult_t[S[t]] = t

Y = S[filas]
PA = PAJ[filas]; P0 = P[filas]
RANK = np.argsort(np.argsort(-PA, axis=1), axis=1) + 1  # 1 = favorito
np.savez(os.path.join(AQUI, "rasgos.npz"), filas=filas, ERA=ERA, TR=TR[filas], F=F[filas], Y=Y, PA=PA, P0=P0,
         RANK=RANK, horas=horas, hdias=hdias, c3=c3, c7=c7, fr_ayer=fr_ayer, DI=DI[filas])
print("ok", len(filas))
