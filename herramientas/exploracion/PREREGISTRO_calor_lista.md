# PREREGISTRO — Selección de sorteos por el calor de la lista

**Fecha de congelación:** 2026-09-22
**Escrito ANTES de mirar el tramo de prueba.** `registro_final.jsonl` iba por 4 miradas.

---

> ## ⛔ RESULTADO: **FALLA**. La regla queda descartada (2026-09-22)
>
> Prueba ciega sobre `[9357, 12511)`, n = 3.154. Mirada nº 5, registrada.
>
> | Top-N | caliente | fría | diferencia | z | p |
> |---|---|---|---|---|---|
> | **3 (principal)** | **10,91 %** (119/1091) | **12,99 %** (268/2063) | **−2,08 pp** | **−1,74** | 0,959 |
> | 5 | 19,93 % | 19,26 % | +0,67 pp | 0,46 | 0,324 |
> | 15 | 50,79 % | 48,41 % | +2,38 pp | 1,33 | 0,092 |
>
> En Top-3 el efecto **se invirtió**: la mitad caliente acertó menos que la fría.
> No es que el efecto fuera menor de lo medido — es que no existía. Lo de
> desarrollo era ruido, pese a ser consistente en tres Top-N y pasar Bonferroni.
>
> Ninguno de los dos criterios se cumple. **No se reintenta con otro umbral.**
>
> ### Hallazgo secundario, no buscado
>
> El tramo ciego degrada todo, y al Top-15 lo tumba por debajo del equilibrio:
>
> | | desarrollo | prueba ciega | equilibrio |
> |---|---|---|---|
> | Top-3 | 12,89 % | 12,27 % | 10,0 % ✔ |
> | Top-5 | 20,25 % | 19,50 % | 16,7 % ✔ |
> | Top-15 | 53,07 % | **49,46 %** | 50,0 % ✘ |
>
> Es lo que la Tarea C anticipó ("~50,6 % ≈ equilibrio"), un poco peor aún.
> **El Top-15 no es rentable fuera de muestra.** Top-3 se mantiene, jugando
> todos los sorteos y sin seleccionar por calor.
>
> Lo de abajo queda tal como se escribió, antes de saber nada de esto.

---

## La hipótesis, en una frase

La masa de probabilidad que el ensamble pone en su propio Top-N —conocida
**antes** del sorteo— separa los sorteos en los que acertará de aquellos en los
que no. Jugando solo la mitad con más calor se gana más por unidad apostada.

## Por qué merece gastar una mirada

Medido walk-forward en desarrollo `[2000, 9357)`, n = 7.357. Corte en la
mediana, **fijado de antemano**, no ajustado:

| Top-N | mitad fría | mitad caliente | diferencia | z | tendencia (10 deciles) |
|---|---|---|---|---|---|
| 3 | 11,80 % | 13,97 % | +2,17 pp | 2,78 | z = 2,58 |
| 5 | 18,65 % | 21,85 % | +3,20 pp | 3,42 | z = 3,75 |
| 15 | 51,58 % | 54,55 % | +2,98 pp | 2,56 | z = 2,34→3,34 |

Los 6 contrastes pasan Bonferroni. No son independientes (es el mismo efecto
visto tres veces), pero ninguna de las 308 hipótesis de Operación Turing
sobrevivió a nada parecido.

## La regla congelada

Umbrales de calor, calculados en desarrollo y **fijos** a partir de aquí:

| Top-N | umbral (mediana de desarrollo) |
|---|---|
| 3 | **13,1055 %** |
| 5 | **20,7155 %** |
| 15 | **52,9157 %** |

Para cada sorteo: `calor = suma de las N probabilidades mayores`.
**Se juega si `calor >= umbral`. Si no, no se juega.**

Sin variantes, sin afinado, sin "probemos también otro corte".

## Lo que se va a medir (una sola vez)

Sobre el tramo de prueba `[9357, n)`, para **Top-3** como caso principal
(es el que tiene el mejor EV por unidad: +28,9 % jugando todo):

1. Tasa de acierto de la mitad caliente, con IC95.
2. Contraste caliente vs fría (z y p de una cola).
3. EV a 30x y su IC inferior.

Top-5 y Top-15 se reportan como secundarios, sin poder de decisión.

## Criterio de éxito, decidido ahora

- **Pasa** si la mitad caliente supera el equilibrio (10,0 % en Top-3) con el
  **IC95 entero por encima**, Y el contraste caliente-vs-fría da p < 0,05.
- **Falla** en cualquier otro caso, incluido "sale bien pero el intervalo
  cruza el equilibrio".

Si falla, la regla se descarta y se escribe que se descartó. No se reintenta
con otro umbral: eso convertiría la prueba en desarrollo.

## Límite conocido de antemano

Los deciles **no son monótonos**: en Top-3 el decil 6 acierta 16,17 % y el
decil 10 solo 13,86 %; en Top-5 el decil 8 (23,67 %) supera al 10 (21,60 %).
La relación sube y se aplana arriba, el mismo exceso de confianza que aparece
en la calibración del tramo alto.

Por eso la regla es **gruesa (mitad sí, mitad no)** y no "jugar solo lo más
caliente". Seleccionar el decil superior sería un error predecible.

## Lo que NO afirma este preregistro

- No dice que el modelo acierte más. Dice que sabe **cuándo** va a acertar menos.
- No hay certeza: el resultado esperado es una ventaja con intervalo, no una garantía.
- Todo lo anterior es desarrollo. Hasta que se mire la prueba, no está validado.
