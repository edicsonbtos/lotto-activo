# -*- coding: utf-8 -*-
"""Agente hazard / retraso (gap): puntua segun el riesgo estimado de que cada
animal salga AHORA, dado cuantos sorteos lleva sin aparecer.

Idea:
  * El "gap" de un animal = sorteos consecutivos sin salir. Se discretiza en
    contenedores (bins).
  * Walk-forward sobre el pasado: cada aparicion de un animal cierra una
    "racha" (streak) cuyo gap final cae en un bin. Esa racha es un exito
    A[i][b] y ademas una exposicion E[i][b'] para todo b' <= b (la racha paso
    por todos los gaps 0..g). La racha en curso solo suma exposicion.
  * Hazard suavizado:  h[i][b] = (A[i][b] + m*p) / (E[i][b] + m),
    con p = 1/K (uniforme) y m = pseudo-muestras. Con pocos datos el hazard
    colapsa a lo uniforme: el modelo NUNCA se congela en "los 3 mas atrasados
    siempre" (fallo del modelo anterior que este agente corrige).
  * score(i) = h[i][bin(gap_actual_i)] + minusculo desempate por frecuencia
    global.

Propiedad clave: los gaps extremos tienen poca exposicion empirica, asi que su
hazard se suaviza hacia 1/K (nunca hacia el techo). "Muy atrasado" sube solo
hasta donde los datos lo respaldan.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import Agente, K  # noqa: E402

# Contenedores de gap (sorteos sin salir): g <= BORDES[b] va al bin b.
BORDES = (0, 1, 3, 6, 10, 15, 22, 32, 45, 65)   # 10 bins; >65 va al ultimo
NBINS = len(BORDES)
M_SUAV = 200.0       # pseudo-muestras de suavizado del hazard hacia uniforme
P_UNI = 1.0 / K      # prior uniforme
W_FREQ = 0.20        # peso del desempate por frecuencia global
M_HORA = 150.0        # pseudo-muestras del factor horario hacia uniforme
CAP_HORA = 1.25       # techo del factor horario (evita sobreconfianza)


def _bin_gap(g):
    for b, lim in enumerate(BORDES):
        if g <= lim:
            return b
    return NBINS - 1


class AgenteHazard(Agente):
    nombre = "hazard"
    descripcion = "Hazard del gap: P(salir ahora | sorteos sin salir), suavizado hacia uniforme"

    def predecir(self, seq, horas, dweek):
        n = len(seq)
        # ---- pasada unica: rachas cerradas por aparicion -------------------
        # S[i][b] = nÂº de rachas de i cerradas con gap final en el bin b.
        S = [[0] * NBINS for _ in range(K)]
        ultimo = [-1] * K
        for t, a in enumerate(seq):
            g = t - ultimo[a] - 1            # gap antes de este sorteo
            S[a][_bin_gap(g)] += 1           # esta racha cierra aqui
            ultimo[a] = t

        # ---- gap actual (racha en curso: solo exposicion, sin exito) -------
        gap_act = [(n - 1 - ultimo[i]) if ultimo[i] >= 0 else n
                   for i in range(K)]

        # ---- frecuencia global (desempate) ---------------------------------
        freq = [0] * K
        for a in seq:
            freq[a] += 1
        fmax = max(freq) if n else 1

        # ---- factor por hora esperada del proximo sorteo --------------------
        # El horario es ciclico (hora = (anterior+1) % 12 en >96% de los casos),
        # asi que h_next se conoce usando solo el pasado. El factor rota el
        # top-3 por franja horaria: combate el congelamiento del ranking.
        cnt_h = [[0] * 12 for _ in range(K)]
        n_h = [0] * 12
        for a, h in zip(seq, horas):
            cnt_h[a][h] += 1
            n_h[h] += 1
        h_next = (horas[-1] + 1) % 12 if horas else 0

        # ---- hazard suavizado y puntajes -----------------------------------
        scores = []
        for i in range(K):
            suf = 0
            E = [0] * NBINS
            for b in range(NBINS - 1, -1, -1):   # sufijo: rachas con bin >= b
                suf += S[i][b]
                E[b] = suf
            b_act = _bin_gap(gap_act[i])
            E[b_act] += 1                        # racha en curso tambien expone
            h = (S[i][b_act] + M_SUAV * P_UNI) / (E[b_act] + M_SUAV)
            fac = K * (cnt_h[i][h_next] + M_HORA * P_UNI) / (n_h[h_next] + M_HORA)
            fac = min(max(fac, 1.0 / CAP_HORA), CAP_HORA)
            scores.append(h * fac + W_FREQ * P_UNI * (freq[i] / fmax))
        return scores


if __name__ == "__main__":
    from base import POS, ANIM, cargar_historial
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "historial.txt")
    seq, horas, dweek, _ = cargar_historial(ruta)
    s = AgenteHazard().predecir(seq, horas, dweek)
    top = sorted(range(K), key=lambda i: -s[i])[:5]
    print("Top-5:", [(POS[i], ANIM[POS[i]], round(s[i], 5)) for i in top])
