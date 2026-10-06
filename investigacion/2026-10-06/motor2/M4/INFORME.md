# M4: LightGBM con softmax por sorteo, apilado sobre producción, reentrenado cada mes

Pre-registro: `PREREGISTRO.md` (no se tocó). Scripts: `rasgos.py` (rasgos), `hacer_rasgos.py` (y la prueba de fuga de
los rasgos), `motor.py` (walk-forward mensual), `elegir.py` (variantes, mezcla e importancias), `rd_simple.py`
(control adversarial), `fuga.py` (chequear_fuga con el reentrenamiento real), `final.py` (versión congelada).
Matriz: `<scratchpad>/motor2_M4.npz` (P 10744×38). Resultados: `resultados.json`.

## Qué es
- 38 filas por sorteo y 34 rasgos del pasado, más log PROD y su puesto. `init_score = log PROD`, así que el árbol
  solo aprende la corrección. El objetivo es propio: softmax dentro de cada sorteo (logit condicional, grad = p − y).
  No es binario ni lambdarank, que fueron los fallos del intento previo (top15_70, planes 4 y 5).
- Reentreno cada mes con las filas de antes del día 1. La parada temprana usa los últimos 60 días de ese pasado (300
  árboles como máximo, paciencia 30). Después se reajusta con todo el pasado y ese número de árboles. 7 hojas,
  mínimo 400 filas por hoja, L2 = 10, tasa 0,05.
- **Desviación:** no se reentrenó en ANTIGUO (antes de 2025-07), para ahorrar CPU. Ahí P = PROD y Δ = 0 por
  construcción. En total se usaron unos 55 min de CPU, por encima de los 40 previstos (V1 tardó 11 min de reloj, sin
  causa clara).
- **Sin fuga:** al alterar `seq[c:]` en 3 cortes, los rasgos de las filas ≤ c no cambian. `A.chequear_fuga`, con
  rasgos, etiquetas y modelo reentrenados sobre la secuencia alterada (cortes 8285, 10709 y 12185, uno por tramo),
  da OK.

## Variantes (Δ mbits contra prod, w = 1)
| variante | AJUSTE | ELECCION [IC 90] |
|---|---|---|
| V1 todo el pasado | +31,2 | +27,1 [+16,9; +37,2] |
| V2 ventana de 365 d | +32,1 | +14,4 [+6,0; +22,9] |
| **V3 todo el pasado, vida media 180 d** | **+35,3** | **+27,4 [+17,2; +37,6]** |
| V4 vida media 90 d | +28,9 | +24,8 [+13,4; +36,1] |
| V5 = V1 sin RD | +26,5 | +7,3 [−0,4; +14,9] |
| Control: solo RD (h−1) ×0,42 y (h−2) ×0,77 log-lineal sobre PROD | +8,4 | +15,1 [+10,9; +19,4] |

Mezcla p ∝ PROD^(1−w)·M4^w: w = 1 y w = 1,25 son casi iguales (+27,41 y +27,48). La regla pre-registrada elige
**V3 con w = 1,25**.

## Final congelado y PRUEBA26 (una sola mirada, registrada)
| tramo | mbits | Δ contra prod [IC 90] | Top-5 (prod) | Top-15 (prod) | ret. Top-5 (prod) |
|---|---|---|---|---|---|
| AJUSTE | +195,5 | **+34,7 [+24,0; +45,4]** | 22,1 (21,2) | 57,2 (54,6) | +35,5 % (+29,1) |
| ELECCION | +106,5 | **+27,5 [+14,8; +40,2]** | 20,0 (20,1) | 51,4 (48,6) | +20,4 % (+23,4) |
| PRUEBA26 | +128,2 | **+19,1 [+5,7; +32,6]** | 19,9 (18,6) | 52,2 (49,6) | +22,4 % (+14,4) |

Δ de mié a vie frente al resto de la semana: AJUSTE +35,7 / +34,0, ELECCION +39,2 / +19,5, PRUEBA26 +28,6 / +11,9.
El modelo recupera sobre todo los días "relajados" de 2026, gracias a los rasgos de régimen.

## Importancia de los rasgos (V3, último modelo, % de la ganancia)
rd1 9,9 · reps_dow8 9,0 · gap2 8,7 · puestoPROD 8,2 · logPROD 6,9 · gap1 6,1 · recic_hoy 5,9 · hora 4,5 · hora_ult 4,5 ·
k_hoy 3,3 · gapdias 3,3 · recic_dow8 3,2 · dia_mes 2,9 · frec120 2,9 · dow 2,6 · frec360 2,3 · recic_7d 1,7 · hora_ult_ayer 1,7 ·
num_fecha1 1,7 · rd2 1,6. Los rasgos de régimen (repeticiones de este día de la semana en 8 semanas y reciclaje de hoy)
entran combinados con log PROD y con los retrasos. Eso es justo la no linealidad que no tiene el término log-lineal.

## Lectura adversarial
1. **Buena parte de la ganancia es RD (h−1).** Sin RD, ELECCION baja a +7 [−0,4; +15]. Solo con RD log-lineal ya
   da +15. Lo que aporta de verdad el árbol, por encima de RD simple, es unos +12 mbits en ELECCION y +26 en AJUSTE.
   En el juego real, producción ya aplica la regla de cambio RD sobre el Top-5. Por eso la ganancia en plata del
   Top-5 es menor de lo que dicen los mbits.
2. **El Top-5 no mejora de forma consistente.** En ELECCION baja (20,0 contra 20,1; retorno +20 % contra +23 %) y en
   PRUEBA26 sube (+22 % contra +14 %). El Top-15 sube unos 2,6 puntos en los tres tramos. La mejora está en la
   probabilidad y en el Top-15, no en el Top-5.
3. El CSV de RD termina el 2026-09-22. Las dos últimas semanas de PRUEBA26 van sin RD (NaN) y el resultado lo incluye.
   En producción haría falta RD (h−1):30 en vivo antes de cada h:00.
4. w = 1,25 y V3 se eligieron en ELECCION, así que ELECCION es optimista. PRUEBA26 es la medida limpia: +19 [+6; +33].

## VEREDICTO: MEJORA
Cumple el criterio pre-registrado: Δ > 0 en los tres tramos, con el IC 90 % por encima de 0. La ganancia es más
pequeña en PRUEBA26 que en AJUSTE, y depende en parte de RD. Antes de producción conviene ponerlo en sombra en vivo,
con RD (h−1) alimentado en tiempo real, y revisarlo con `revisor-sesgo`.
