# Camino 3: Lotto Activo República Dominicana (LARD) con su propio modelo — NO PASA

Fecha: 2026-09-30. Carpeta: `herramientas/exploracion/enjambre_2026-09-30/lard_propio/`.
Archivos: `PREREGISTRO.md` (escrito antes de medir), `lard_propio.py`, `dev.json`, `ciega.json`,
`ciega_salida.txt`, `registro.jsonl` (deja constancia de la ÚNICA mirada a la prueba ciega).

## Qué se probó
LARD es el tercer juego del mismo operador: 14 sorteos al día, a las h:00 de 8 a 21. Ya sabíamos que no
"copia" ni "evita" a Lotto Activo ni a RD. Faltaba ver si LARD se puede adivinar con SU PROPIO pasado,
usando el mismo motor que funciona en Lotto Activo: no repetir el animal el mismo día y reciclarlo a los 1-2 días.

Hubo cinco candidatos, todos elegidos solo con datos viejos (desarrollo, 2025-09-19..2026-01-31, 1890 sorteos):
- U: azar puro (1/38 para cada animal).
- H: probabilidad según "cuánto tiempo lleva sin salir", aprendida de LARD.
- B: el motor de Lotto Activo (`secuencia_v3`) aprendido de nuevo con LARD.
- C: el motor con lo que aprendió en Lotto Activo (datos de LA hasta 2025-06-30), aplicado tal cual a LARD.
- M: mitad B y mitad C.

## Resultado en desarrollo
Todos quedaron POR DEBAJO del azar (mbits: H −10,9; B −16,2; M −31,1; C −126,2). H "ganó" solo porque
perdió menos. El dato más claro es que C pierde muchísimo. Es decir, **LARD no se comporta como Lotto Activo**:
en LARD, un animal que ya salió hoy vuelve a salir casi tanto como por azar (93 % de lo esperado, diferencia no
significativa), mientras que en Lotto Activo eso casi nunca pasa. El patrón que da ventaja en LA aquí no existe.

## Prueba ciega (se miró UNA sola vez: 2026-02-01..2026-09-22, 3276 sorteos)
| Modelo | mbits [IC 95 %] | Top-3 | Top-5 escalonado, retorno por ficha | Top-15: acierto / retorno por ficha |
|---|---|---|---|---|
| Azar | 0 | 7,88 % | −20,3 % | 38,4 % / −23,1 % |
| H (elegido) | −4,1 [−6,7; −1,3] | 8,03 % | −22,7 % [−29,9; −15,3] | 38,7 % / −22,6 % [−26,2; −19,2] |
| B | −9,0 [−14,7; −2,9] | 8,21 % | −19,0 % | 40,4 % / −19,3 % |
| C | −123,9 | 7,81 % | −19,6 % | 40,1 % / −19,9 % |

Esperado por puro azar: Top-3 7,89 %, Top-15 39,5 %, retorno −21 % por ficha.

En los últimos 6 meses (2026-04-01..09-22, dentro de la misma y única mirada, 2450 sorteos), H dio −2,6 mbits [−5,4; +0,2],
un Top-3 de 7,59 %, un Top-5 escalonado de −22,4 % y un Top-15 con 39,6 % de acierto y −20,7 % por ficha. Es lo mismo que el azar.

El criterio fijado antes de mirar era: mbits > 0 con IC > 0 y z ≥ 3. H dio −4,1 mbits y z −1,4. **NO PASA.**

## ¿Cuánto paga LARD?
Según elbrujodelosanimalitos.com (fuente NO oficial), paga 30 veces lo apostado, con 14 sorteos de 8:00 a 21:00.
Con 30x, apostar sin ventaja pierde ~21 % por ficha. Para no perder con el Top-15 habría que acertar el 50 %
de las veces, y en LARD se acierta ~39-40 % (lo mismo que al azar). El pago necesario para empatar está en ~37-39x, muy por encima de 30.

## Qué significa
- LARD no se puede adivinar con su propio historial: ni con el Top-3 ni con el Top-15, ni en ninguna hora.
- No cambia nada del Top-5 ni del Top-15 de Lotto Activo / RD, porque LARD no entra en la jugada.
- No se puede "asegurar el Top-15" en LARD: acierta lo mismo que elegir 15 animales al azar.
- No se tocó producción, ni el historial del marcador, ni el CSV compartido. No se bajaron datos nuevos: la ventana
  ciega ya terminaba el 22-09 y 7 días más (98 sorteos) no cambian nada.
