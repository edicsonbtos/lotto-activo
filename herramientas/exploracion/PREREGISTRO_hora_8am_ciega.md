# Pre-registro: ¿el motor rinde mejor a ciertas horas? (8:00 y "más información del día") — 2026-10-02

Escrito ANTES de mirar el tramo de prueba por hora. Script: `herramientas/exploracion/hora_8am_ciega.py`.

## Por qué
El usuario ve en vivo que el Top-15 de las 8:00 acierta casi todos los días desde que arrancó el marcador, y que
el Top-15 global bajó de ~53 % a ~45 %. Pregunta si el motor funciona mejor a alguna hora, si se puede replicar y
si los sorteos de la tarde (con más resultados del día ya conocidos) deberían acertar más.

## Lo que ya se sabía (desarrollo, ya mirado; NO es evidencia nueva)
- Top-15 a las 8:00 en desarrollo (`hora == 0`, n = 372): 60,5 %; en dev-B 61,1 % (n = 306). Top-15 global del desarrollo: 53,1 %.
- En dev-A, cuando el primer sorteo del día era a las 9:00, las 9:00 dieron 45,6 % (la peor hora). Las 17:00, elegidas
  en dev-A como "hora buena", no replicaron en dev-B (plan 7 de `top15_70`).
- El vivo (2026-09-15..10-01) originó la idea, así que no cuenta como prueba.

## Datos
Walk-forward del `ensamble_v2` de producción (mismo código, pesos cada 250) sobre `verificacion/hilo9/datos/historial.txt`
+ la corrección de fechas del 2026-09-29 + los resultados de la API oficial (juego 1) hasta el 2026-09-22. Comprobado:
los 5.071 sorteos comunes entre historial y API coinciden (0 diferencias); el desarrollo reproduce Top-15 53,1 %
y la prueba Top-3 12,2 % / 90 mbits (cifras ya publicadas, no por hora).

Tramo de prueba = filas >= 9357 hasta el 2026-09-13 (3.122 sorteos, 2025-12-19..2026-09-13). Esta es una mirada
más al tramo de prueba y queda anotada en `herramientas/registro_final.jsonl`. Nada de ese tramo se ha mirado por hora.

## H8 (principal): "a las 8:00 el Top-15 acierta más que el resto de horas, y por encima del equilibrio"
- Métrica: acierto Top-15 (orden del ensamble, desempate `LE.rankings`) en los sorteos de las 8:00 del tramo de prueba,
  contra los de las otras 11 horas del mismo tramo.
- **PASA** si (a) la diferencia 8:00 − resto es > 0 con p unilateral < 0,01 (bootstrap por jornada, 10.000 réplicas,
  semilla 20261002) **y** (b) el límite inferior del IC95 de la tasa de las 8:00 supera el 50 % (equilibrio del
  Top-15 plano con pago 30x).
- **FALSADA** si la diferencia es < +3 pp. Entre medias: sin concluir.
- Si pasa, la decisión de jugar distinto a las 8:00 sigue esperando al vivo (H1 de `PREREGISTRO_manana_8am.md`,
  leída con su fe de erratas) y a la regla de `gestion_banca.VIGILANCIA`.

## H8-cal (mecanismo): ¿el motor ya "sabe" que a las 8:00 acierta más?
- Comparar el Top-15 observado a las 8:00 con el esperado por el propio motor (suma de las probabilidades de su Top-15).
- Si |z| < 2 en el tramo de prueba, la ventaja de las 8:00 ya está en las probabilidades del motor (calibrado por hora):
  no hay nada oculto que "replicar", solo que a esa hora el motor está más seguro. Si z >= +2, hay estructura a las
  8:00 que el motor no captura (y se abre un hilo nuevo, solo con desarrollo).

## H-día: "con más resultados del día, el Top-15 acierta más"
- Métrica: pendiente de la regresión del acierto Top-15 sobre el número de sorteo del día (0 = 8:00 … 11 = 19:00)
  en el tramo de prueba, con IC por bootstrap por jornada.
- **PASA** si la pendiente es > 0 con p unilateral < 0,01. **FALSADA** si la pendiente es <= 0.

## Descriptivo (no decide nada)
- Top-15 y mbits por trimestre, observado contra esperado por el motor, en desarrollo, prueba y vivo reconstruido
  (2026-09-14..09-22): para explicar el paso de ~53 % a ~49 % y luego ~45 %.
- Top-15, mbits y esperado por hora en desarrollo y en prueba.
- Si H8 pasa: retorno por ficha del Top-15 plano y del ponderado 3-2-1 solo a las 8:00, con IC por jornada.
