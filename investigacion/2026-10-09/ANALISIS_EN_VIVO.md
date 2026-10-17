# Revisión de jornada y seguimiento del motor — 2026-10-09

## Corte

Consulta de producción a las **4:55 p. m. de Caracas**. El último resultado anotado por la app es el de las 4:00 p. m.; el sorteo de las 5:00 p. m. seguía pendiente. Se usaron los pronósticos congelados y resultados guardados en el volumen de Railway, no la copia local del histórico.

## Hoy, Lotto Activo

| Hora | Resultado | Puesto congelado |
|---|---|---:|
| 8:00 a. m. | 31 Lapa | 30 |
| 9:00 a. m. | 24 Iguana | 20 |
| 10:00 a. m. | 11 Gato | 4 |
| 11:00 a. m. | 14 Paloma | 23 |
| 12:00 p. m. | 34 Venado | 7 |
| 1:00 p. m. | 21 Gallo | 21 |
| 2:00 p. m. | 5 León | 29 |
| 3:00 p. m. | 1 Carnero | 31 |
| 4:00 p. m. | 29 Elefante | 27 |

Resultado parcial: **0/9 Top-3, 1/9 Top-5 y 2/9 Top-15**. Los pronósticos daban en conjunto aproximadamente **1,69 aciertos Top-5 esperados** para esos nueve sorteos. Con la referencia histórica del Top-5 (19,4 %), obtener como máximo un acierto en nueve sorteos tiene probabilidad aproximada de **45 %**. El mal tramo de Top-5 de hoy, por sí solo, no señala una avería ni una causa repetible. La jornada aún no estaba cerrada.

La app informa para los últimos siete días **17/81 Top-5 (21,0 %)** y **36/81 Top-15 (44,4 %)**, y clasifica la ventana como normal. La ventana a 30 días también aparece como normal.

## Qué explican los días buenos y malos

En el corte diario, “bueno” o “malo” describe sobre todo dónde cayó el ganador dentro del orden que ya estaba congelado: los días buenos concentran más ganadores en los puestos 1–5 y los días malos los dejan fuera. Eso explica el resultado después del sorteo, pero no da una regla para reconocerlo antes.

El histórico del repo ya probó varias explicaciones de ese tipo —rachas del favorito, hora, retraso y filtros de días “calientes”— con evaluación walk-forward. Los informes descartan usar esas reglas como interruptor del juego. Ajustar el motor a los días extremos que acabamos de observar convertiría ruido pasado en una predicción nueva.

## Hallazgo para seguir: `ag12` en sombra

La app ya mantiene la comparación sin afectar el marcador real. En los **163 sorteos** registrados desde el 26 de septiembre, la pantalla de sombra informa:

- Ensamble actual: **17 Top-3, 27 Top-5 y 71 Top-15**.
- `ag12`: **24 Top-3, 32 Top-5 y 79 Top-15**.
- Diferencia media de log-puntuación: **+6,32 mbits por sorteo**, con IC 90 % **[−28,00; +40,64]**.
- Con el ajuste de RD, la ventaja estimada del Top-5 sigue positiva, pero su IC también incluye cero.

Es una señal inicial que justifica seguir midiendo; todavía no valida cambiar el motor. El criterio ya fijado en producción exige que el intervalo de la diferencia de mbits quede por encima de cero. La primera revisión está configurada para **931 sorteos**; si no concluye, la app extiende el seguimiento hasta 3.500. Hoy el intervalo principal todavía cruza cero.

## Decisión

1. **No cambiar el ensamble por el día parcial de hoy ni por los días extremos.**
2. **Dejar que el seguimiento en sombra existente continúe** hasta su corte preregistrado; esa es la vía para replicar una mejora sin elegirla mirando los mismos resultados.
3. Al cierre de hoy, volver a leer el marcador diario. Una jornada completa añade solo 12 observaciones y no decide por sí sola si el motor mejoró.

Fuentes de producción consultadas: `/api/salud`, `/api/sombra_decision`, `/api/sombra` y los pronósticos/resultados congelados en `/data/predicciones.json` de Railway. La copia local de datos llega hasta el 7 de octubre y no se usó para afirmar resultados de hoy.
