# Pre-registro: tramos mañana y tarde (2026-09-29)

Idea del usuario: "evaluar en tramos mañana y tarde, debe haber algo allí".

## Qué es nuevo (y qué no)
- Ya cerrado: **hora por hora** (estrategias_v2: ninguna hora mejor se repite entre mitades) y **la mañana predice la tarde** (dia_sin_reciclaje, ag04 de la ronda 3). No se repiten.
- Nuevo: agrupar en **dos tramos fijos** y preguntar si la jugada rinde distinto en uno y otro. Hay una razón mecánica previa: el motor descarta a los que ya salieron hoy, así que por la tarde elige entre menos animales disponibles. Si eso hace que el Top-15 (o el Top-5) pase el equilibrio solo por la tarde, jugar solo por la tarde sería una regla sencilla.

## Definición (fija antes de mirar)
- Mañana: LA 08:00-13:00 (h 0..5); RD 08:30-13:30 (h 0..5). Tarde: LA 14:00-19:00 (h 6..11); RD 14:30-19:30.
- Datos: solo desarrollo. LA: `calor_cache.npz` (ensamble walk-forward, filas [2000, 9357)). RD: `herramientas/rdint/cache_dev.npz`, P1 = modelo en vivo B1 (2024-03..2025-06).
- Estrategias, que no se eligen después: (a) **Top-15 plano**, 1 ficha por animal, retorno por ficha = 30·acierto/15 − 1; (b) **Top-5 escalonado** 2-2-2-1-1 (8 fichas), retorno = 30·fichas en el ganador/8 − 1.
- Estadísticos: retorno por ficha de cada tramo y **diferencia tarde − mañana**, con IC95 por bootstrap de jornadas (B = 5000, semilla 20260929), en el tramo entero y por mitades (primera y segunda mitad de jornadas).
- Informativo: acierto del Top-15 por tramo frente al azar (15/38) y mbits del modelo frente al uniforme por tramo.

## Umbral de falsación
Para decir "hay algo en tramos" en un juego, con una estrategia:
1. la diferencia tarde − mañana tiene IC95 que excluye 0 en el tramo entero, **y**
2. tiene el mismo signo en las dos mitades.

Para proponer "jugar solo en un tramo", además el retorno de ese tramo debe tener IC95 > 0 en el tramo entero y ser > 0 en las dos mitades. Son 4 contrastes (2 juegos × 2 estrategias): Bonferroni, así que el IC que manda es el de 98,75 %.

Si pasa, **no se cambia nada en vivo**: se mide en el marcador en vivo desde hoy (el tramo de prueba ≥ 9357 ya se miró 5 veces y no se usa).
