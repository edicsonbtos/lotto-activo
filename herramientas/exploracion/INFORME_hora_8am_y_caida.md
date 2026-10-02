# Las 8:00, la tarde y la caída del Top-15: validación del motor (2026-10-02)

Pre-registro: `PREREGISTRO_hora_8am_ciega.md` (commit d454a40, antes de calcular). Script: `hora_8am_ciega.py`
(~2 min; salida completa en `hora_8am_ciega_salida.txt`). Mirada al tramo de prueba anotada en
`herramientas/registro_final.jsonl`. No se tocó producción ni Railway: el proxy de este equipo bloquea la web,
así que el vivo se reconstruyó con datos oficiales hasta el 29-sep.

## La respuesta corta

1. **El 51-53 % que "ofrece" el motor en el Top-15 es su propia estimación, y en 2026 promete unos 3 puntos de más.**
   A ciegas en 2026 (3.122 sorteos, 2025-12-19..2026-09-13) esperaba 52,5 % y dio **49,4 %** (z = −3,5).
   En el Top-3 y el Top-5 sí cumple (12,2 % y 19,4 %; esperaba 12,7 % y 20,2 %). El desfase está en los puestos 6-15.
2. **Lo que el motor debe dar hoy:** Top-3 ~12 %, Top-5 ~19 %, Top-15 ~49 %, ~90 mbits. El 45 % del vivo cabe
   en el ruido de eso: con 250 sorteos, un Top-15 real de 49,4 % sale entre 43 % y 56 % el 95 % de las veces.
3. **No es el servidor ni los datos.** El historial coincide con la API oficial en 5.071 de 5.071 sorteos. El motor
   recalculado fuera de Railway da los mismos aciertos por día que el marcador en vivo, y no mira el futuro
   (prueba de fuga en 3 cortes).
4. **La caída la causó el operador.** En 2025 casi no repetía animal el mismo día (0,25-0,37 veces lo del azar).
   En 2026 repite el doble (~0,50), y en jul-sep 2026 dejó de reciclar los animales de ayer. El motor aprendió con
   un 2025 "fácil".
5. **Las 8:00 no son una hora mejor.** La racha en vivo existe (11 de 16 madrugadas, 9 seguidas del 21 al 29-sep),
   pero en las 260 madrugadas a ciegas de 2026 las 8:00 acertaron el Top-15 el **49,2 %**, igual que el resto
   (49,4 %). **H8: FALSADA.** Ninguna hora es buena de forma estable: el perfil por horas no se repite entre
   tramos (correlación −0,12).
6. **Saber más resultados del día no sube el Top-15.** La pendiente es −0,37 puntos por sorteo [−0,92; +0,19].
   **H-día: FALSADA.** Lo que aporta el día es saber quién NO va a salir, no quién sí.
7. **Qué hacer:** no cambiar la jugada. Leer el marcador contra el 49 %, no contra lo que dice el motor. Las 8:00
   se siguen juzgando en vivo con la H1 de `PREREGISTRO_manana_8am.md` (30 madrugadas desde el 02-10).

## 1. De 53 % a 49 % (y 45 % en vivo): qué pasó

Top-15 por trimestre. "Esperado" es la suma de las probabilidades del Top-15 del motor. La estructura del operador
se mide sobre los resultados crudos, sin modelo: "repite hoy" es el O/E de que salga un animal que ya salió ese día
(1,00 = azar; cuanto más bajo, más fácil para el motor) y "de ayer" es el O/E de que salga uno del día anterior.

| Trimestre | Tramo | Top-15 obs / esperado | mbits obs / esperado | Repite hoy | De ayer |
|---|---|---|---|---|---|
| 2024-T2 | desarrollo | 50,9 / 54,2 | 86 / 125 | 0,43 | 1,04 |
| 2024-T3 | desarrollo | 51,1 / 51,9 | 91 / 95 | 0,42 | 1,04 |
| 2024-T4 | desarrollo | 51,5 / 52,1 | 113 / 106 | 0,43 | 1,15 |
| 2025-T1 | desarrollo | 50,7 / 52,0 | 73 / 103 | 0,60 | 1,08 |
| 2025-T2 | desarrollo | 55,1 / 52,6 | 130 / 101 | 0,37 | 1,09 |
| 2025-T3 | desarrollo | **57,2** / 54,9 | **196** / 142 | **0,25** | 1,10 |
| 2025-T4 | desarrollo y prueba | 54,1 / 56,6 | 157 / 178 | 0,31 | 1,09 |
| 2026-T1 | prueba | **49,3** / 54,7 | **78** / 147 | 0,51 | 1,08 |
| 2026-T2 | prueba | 48,4 / 51,6 | 79 / 100 | 0,49 | 1,05 |
| 2026-T3 | prueba y vivo | 50,3 / 50,7 | 109 / 94 | 0,38 | **1,00** |
| Vivo 14-29 sep (192) | vivo reconstruido | 45,8 / 51,9 | 103 / 105 | | |

- El 53 % del desarrollo es la media de 2024-2025, empujada por el segundo semestre de 2025, el mejor periodo
  registrado. En ese tramo el motor está bien calibrado: esperaba 53,4 % y dio 53,1 %.
- En enero de 2026 el operador volvió a repetir en el día (0,51, más que en todo 2024) y el Top-15 bajó a ~49 %. El motor tarda
  en notarlo y sigue esperando 52-55 %. Eso es el "51-53 %" que muestra.
- Ya se probó que reentrenar más rápido u olvidar antes lo viejo no ayuda (`enjambre_2026-09-30/reentreno`: −3,3
  y −3,8 mbits en desarrollo). Bajar la confianza del motor con una "temperatura" ajustada en los 1.500 sorteos
  anteriores tampoco: +0,3 mbits [−2,9; +3,5] en prueba. Además, la temperatura no cambia el orden, así que no
  cambia ni un acierto.
- El vivo va algo por debajo en todo (Top-3 8,3 %, Top-5 15,1 %, Top-15 45,8 %; z ≈ −1,6 en cada uno), pero con
  192 sorteos eso es ruido. Hacen falta ~1.000 para concluir (regla de `lotto-marcador`).

## 2. Las 8:00

| Tramo | n | Top-15 a las 8:00 | Esperado por el motor | Resto de horas |
|---|---|---|---|---|
| dev-A (mar-2024..feb-2025; las 8:00 existen desde el 28-nov-2024) | 66 | 60,6 % | 50,9 % | 51,3 % |
| dev-B (feb..dic-2025) | 306 | 60,8 % | 59,1 % | 54,3 % |
| **Prueba 2026 (ciega por hora)** | **260** | **49,2 % [43,1; 55,4]** | 53,6 % | 49,4 % |
| Vivo reconstruido 14-29 sep | 16 | 68,8 % (11/16) | 54,5 % | 43,8 % |

- En 2025 las 8:00 fueron buenas porque el motor estaba muy seguro a esa hora (esperaba 59 %) y acertó. Era el
  mismo reciclaje fuerte del 2025, no algo propio de la mañana. En 2026 ese reciclaje se debilitó y las 8:00
  volvieron a la media.
- Las 8:00 en vivo, día a día (puesto del ganador): 14-sep 20, 15-sep 30, 16-sep 24, 17-sep **4**, 18-sep 23,
  19-sep **11**, 20-sep 31, y desde el 21-sep todas dentro: **2, 11, 8, 12, 6, 1, 6, 10, 12**.
- ¿Es rara esa racha? 11 de 16 sale el 10-19 % de las veces por azar. Nueve aciertos seguidos en una hora concreta
  sale el ~1-2 %. Pero el día tiene 12 horas, y que alguna de ellas muestre una racha así pasa ~9 % de las veces.
  Es la misma memoria selectiva de `top15_otra_hora.md`: se mira la hora que acierta.
- No hay "horas buenas" estables. El Top-15 por hora no se correlaciona entre tramos: desarrollo contra prueba
  −0,12, dev-A contra dev-B +0,12, dev-B contra prueba −0,21. Las 18:00 pasan de 55,6 % a 42,5 %; las 9:00, de
  45,9 % a 60,8 % y luego a 54,6 %.

## 3. "Más información del día debería dar más certeza"

Es razonable, pero los datos dicen otra cosa (prueba 2026):

| Hora | Ganadores en el fondo (puestos 26-38) | Esperado | Ganadores en el Top-15 | Esperado |
|---|---|---|---|---|
| 8:00 | 26,2 % | 23,3 % | 49,2 % | 53,6 % |
| 14:00 | **12,7 %** | 18,7 % | 55,8 % | 52,8 % |
| 15:00 | 18,5 % | 17,1 % | 45,0 % | 53,9 % |
| 16:00 | 18,5 % | 15,5 % | 50,4 % | 55,4 % |
| 18:00 | 32,2 % | 24,1 % | 42,5 % | 50,3 % |
| Azar | 34,2 % | | 39,5 % | |

- A media tarde el motor ya sabe qué 6-8 animales salieron hoy y los manda al fondo, y casi no salen: el fondo
  recibe 13-19 % de los ganadores, frente al 34 % del azar. **La información del día funciona, pero dice quién NO
  sale.** Esos animales nunca iban a estar en el Top-15, así que quitarlos apenas sube la cabeza.
- Por eso los mbits suben por la tarde (160-210 a las 14-16 h) y el Top-15 no. A las 18:00 y 19:00 el fondo vuelve
  a recibir 28-32 % de los ganadores: a esa hora el operador repite más en el día (lo describe `intradia_v2.py`).
- "Meter más potencia" al cálculo tampoco ayuda. Ya se probaron árboles (LightGBM), 91 variables, LambdaRank, sacar
  todo lo que salió hoy en LA y en RD, y otras loterías (hilo 9 y `top15_70`). Ninguno supera al ensamble. El techo
  lo pone la información disponible, no el cálculo.

## 4. Validación del motor

| Comprobación | Resultado |
|---|---|
| Historial (con la corrección de fechas del 29-sep) contra la API oficial | 5.071 sorteos comunes, **0 diferencias**; falta 1 sorteo (2026-06-24 19:00) |
| Motor recalculado contra cifras publicadas | Desarrollo Top-15 53,13 % (publicado 53,07); prueba Top-3 12,17 % (12,27), 90,0 mbits (90) |
| Motor recalculado contra el marcador en vivo | 23-sep sorteo a sorteo (`diario_vivo.md`): el puesto del ganador coincide en 10 de 12 y se corre 1 puesto en los otros 2. Aciertos Top-5 por día iguales del 18 al 22-sep. Las pequeñas diferencias vienen de que producción aún no tenía la corrección de fechas del 29-sep y de los sorteos sin pronóstico congelado |
| Prueba de fuga (`LE.prueba_fuga`, 3 cortes al azar, semilla 7, sobre los 12.671 sorteos) | **Sin fuga**: diferencia máxima 0,0 en las filas anteriores a cada corte |
| Calibración Top-3 / Top-5 en 2026 | Cumple: 12,2 % y 19,4 % contra 12,7 % y 20,2 % prometidos |
| Calibración Top-15 en 2026 | **Promete de más:** 52,5 % contra 49,4 % (z = −3,5) |

Lo que se puede "asegurar" es esto: el motor da ~49 % de Top-15 (el azar da 39,5 % y el equilibrio del Top-15 plano
es 50 %) y ~19 % de Top-5 (azar 13,2 %, equilibrio 16,7 %). Con eso, **el Top-5 escalonado gana (+18 % por ficha en
abr-sep 2026, IC +8 a +29)**, el Top-15 ponderado queda cerca de cero (+5 %, IC −0,3 a +11) y **el Top-15 plano
pierde (−1 %)**. Ninguna hora cambia eso.

El marcador (`.claude/skills/lotto-marcador/marcador.py`) ahora imprime, junto a la calibración, la referencia ciega
de 2026, para no comparar el vivo con lo que promete el motor.

## 5. Límites
- El vivo después del 29-sep no se pudo leer (el proxy bloquea `lotto-activo-production.up.railway.app`). Con acceso,
  `en_vivo_manana_8am.py` y el marcador cubren hasta hoy.
- El tramo de prueba ya se había mirado otras veces, pero nunca por hora. H8 y H-día se fijaron antes de mirarlo.
- La racha de las 8:00 se juzga solo con sorteos desde el 2026-10-02 (H1 de `PREREGISTRO_manana_8am.md`: pasa con
  ≥ 22/30). Con la tasa de 2026 (~49 %) eso sale por azar el 0,7 % de las veces, así que si pasa sería un indicio
  serio. Aun así habría que replicarlo en otros 30 antes de tocar nada.
