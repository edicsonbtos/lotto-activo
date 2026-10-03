# Top-15: 8:00 contra el resto del día, con y sin los ajustes (2026-10-03)

Simulación walk-forward (`ensamble_v2`, la misma que mide `lotto_eval`) sobre 10.708 sorteos. Cada pronóstico
usa solo el pasado. Versiones:
- **A**: motor actual.
- **B**: A + ajuste del primer sorteo (en el PR #1).
- **C**: B + corrección fecha/hora (en sombra).
- **D**: B + ventana de fecha a las 8:00 (en sombra).

Los ajustes de B, C y D se fijaron con datos de desarrollo, así que **la cifra limpia es la de prueba**.

| tramo | versión | Top-15 8:00 | Top-15 resto del día |
|---|---|---|---|
| dev (nov-24 a dic-25) | A | 60,8 % (n = 372) | 53,6 % |
| | B | 62,4 % | 53,6 % |
| **prueba (dic-25 a sep-26)** | **A** | **49,0 % [43,0; 55,1]** (n = 261) | **49,5 %** |
| | **B** | **50,6 % [44,5; 56,6]** | 49,5 % |
| | C | 51,3 % | 50,8 % |
| | D | 51,0 % | 50,8 % |
| vivo (15-sep a 3-oct) | A = B | 73,7 % (14/19) | 41,4 % (n = 198) |
| | C = D | 78,9 % (15/19) | 45,5 % |
| desde nov-24 | A | 56,4 % (n = 652) | 51,6 % (n = 7.160) |
| | B | 58,0 % | 51,6 % |

Un Top-15 al azar acierta el 39,5 %. Diferencias pareadas a las 8:00:

| comparación | tramo | diferencia [IC 95 %] |
|---|---|---|
| B − A | prueba | +1,5 pp [0,0; +3,4] |
| B − A | desde nov-24 | +1,5 pp [+0,3; +2,8] |
| D − B | prueba | +0,4 pp [−1,9; +2,7], no significativa |

Top-15 por hora desde nov-24, versión B:

| 8a | 9a | 10a | 11a | 12p | 1p | 2p | 3p | 4p | 5p | 6p | 7p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 58 % | 56 % | 53 % | 52 % | 51 % | 49 % | 52 % | 51 % | 51 % | 53 % | 50 % | 50 % |

## Lectura
- Las 8:00 son la mejor hora (≈ 58 % desde nov-24), pero en el tramo de prueba bajaron a ≈ 50 %, igual que el
  resto del día. El 73,7 % en vivo son 19 mañanas: con una tasa real del 58 %, en 30 mañanas lo normal es
  ver entre 43 % y 73 %.
- El ajuste del primer sorteo suma +1,5 pp a las 8:00 de forma consistente. La ventana de fecha a las 8:00 no
  se confirma fuera de desarrollo. La corrección fecha/hora (C) sube todas las horas en prueba (+1,3 pp) y en
  vivo: es la siguiente candidata, y la sombra ya la mide.
- Top-15 plano (15 fichas, paga 30): el equilibrio es 50 %. A las 8:00, en prueba, retorna +1,2 % por ficha;
  desde nov-24, +16 %. El resto del día, en prueba, retorna −1 %.

Reproducir: `1_walkforward.py COPIA_HIST salida.npz` (~35 s) y después `2_simular.py` y `3_tabla.py`, que
leen `hist_full.txt` y `wf_desde2000.npz` del directorio de trabajo.
