# M5: las mismas bases de ensamble_v2, combinadas para que se adapten antes. VEREDICTO: DUDOSO
Pre-registro: `PREREGISTRO.md`. Scripts: `bases.py` (paso 1), `comb.py` (biblioteca), `paso2.py`-`paso5.py`, `fuga.py`, `final.py`.
Scratchpad: `M5_bases.npz` (las 3 bases walk-forward desde la fila 1000), `M5_ens.npz` (ensamble_v2 reproducido y sus
pesos), `M5_exp.npz`, `M5_otras.npz` y la matriz final **`motor2_M5.npz`** (P 10744×38).

## Comprobaciones
- ensamble_v2 reproducido desde las bases: máx |dif| 6·10⁻⁶. ajuste_primer_sorteo + aplicar_8am (como multiplicadores
  por fila, la misma lógica que prediccion.py/calib.py) reproducen PROD con dif 0. Todas las candidatas llevan esos ajustes.
- Fuga: las bases son los submodelos de producción (auditados con lotto_eval.prueba_fuga). En la capa de combinación,
  al cambiar el futuro desde 3 cortes, las filas anteriores no cambian (`fuga.py`).

## Resultados (Δ mbits contra PROD, IC 90 % por jornadas). Parámetros elegidos en AJUSTE; familia elegida en ELECCION
| candidata (mejor de su familia en AJUSTE) | AJUSTE | ELECCION |
|---|---|---|
| bases solas: intradia_v2 / secuencia_v3 / haz_v1 | −14,0 / −7,4 / −43,7 | −1,2 / −8,2 / −33,5 |
| EXP: pesos diarios, vida media 2 sem, lam 20 | +3,0 [+0,6; +5,5] | +3,0 [−1,3; +7,4] |
| **DOW: pesos por día de la semana, vida media 2 sem, κ 20** | +4,0 [+0,9; +7,1] | **+4,9 [−0,4; +10,2]** |
| HORA: pesos por hora, vida media 2 sem, κ 20 | +5,1 [+2,0; +8,2] | +1,8 [−3,0; +6,7] |
| HEDGE fixed-share (geo, η 0,5, α 0,001) | +0,6 | −0,9 (todas ≤ 0 en ELECCION) |
| TEMP dinámica sobre ensamble_v2 (vida media 2 sem) | +3,2 [−0,4; +6,8] | +2,3 [−3,5; +8,1] |
| mezcla PROD^0,25·DOW^0,75 (w elegido en ELECCION) | +3,8 [+1,5; +6,2] | +4,7 [+0,7; +8,7] |

- Con olvido más lento (16 semanas) el IC se estrecha, pero la ganancia baja a +0,7/+1,4. Olvidar rápido ayuda poco.
- En ELECCION, DOW gana sobre todo de mié a vie (+8,9 / +18,9 / +32,3), donde el motor falla en 2026.
- Desviación del pre-registro (la declaro): DOW con w=1 no cumple el umbral (el IC cruza 0). Congelé la mezcla w=0,75,
  la única de la rejilla de w que lo cumple. Elegir w así favorece al candidato.

## PRUEBA26 (una vez, versión congelada `final.py`)
| tramo | mbits | Δ vs PROD | Top-5 (prod) | Top-15 (prod) | ret Top-5 (prod) |
|---|---|---|---|---|---|
| AJUSTE | +164,6 | +3,81 [+1,45; +6,17] | 21,2 (21,2) | 54,5 (54,6) | +29,1 % (+29,1 %) |
| ELECCION | +83,7 | +4,67 [+0,68; +8,67] | 20,6 (20,1) | 49,6 (48,6) | +25,8 % (+23,4 %) |
| PRUEBA26 | +111,3 | **+2,21 [−0,13; +4,54]** | 18,9 (18,6) | 50,2 (49,6) | +16,0 % (+14,4 %) |
| ANTIGUO (informativo) | +104,8 | +3,37 [+1,71; +5,04] | 20,1 (19,6) | 52,4 (52,3) | +21,4 % (+20,4 %) |

En PRUEBA26 el mecanismo de mié-vie NO se repite (por día: lun +1,8, mar +3,3, mié +3,1, jue −5,0, vie −1,3, sáb +6,1,
dom +7,5). La ganancia es positiva y parecida en los cuatro tramos (+2 a +5 mbits), pero pequeña, y su IC en PRUEBA26
toca el 0. No recupera la caída de mar-jun (prod +79 → +84 mbits).

## Veredicto: DUDOSO
Δ > 0 con el IC cruzando 0 en PRUEBA26 (regla pre-registrada). Es una mejora menor y consistente (+2 a +4 mbits, Top-5 y
plata casi iguales), del orden de la "GL" anotada en `../adaptativo/`. No justifica cambiar producción por sí sola. Es
candidata a sombra en vivo o a combinarse con otra mejora del enjambre.
