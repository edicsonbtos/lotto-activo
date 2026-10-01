# PRE-REGISTRO — Ronda 5 (lazo "mejorar el Top-15": ampliar la única veta viva)

Escrito el 2026-10-01 ANTES de medir. Script: `ronda5.py`. Tramos de la ronda 1: dev-A [2000,5688) elige/descarta,
dev-B [5688,9357) mide una vez. NO se toca el tramo de prueba (>=9357), ni producción.

## Idea
La única fuente nueva hallada (ronda 2): el operador esquiva el animal cuyo número es el día del mes (O/E 0,51) y,
más débil, la hora de 12 h. Hipótesis: esquiva números "populares" (fechas). Se prueban otros números derivables
de la fecha/hora ANTES del sorteo (LA, h:00), O/E contra la probabilidad del ensamble, IC de bootstrap por jornada.

Familia (8 hipótesis, Bonferroni 8 -> IC 99,375 %):
- C1 mes (1..12)            C2 día de la semana (lun=1..dom=7)    C3 día + mes (si <=38)
- C4 suma de dígitos del día   C5 número de sorteo del día (1..14)   C6 día + hora12 (si <=38)
- C7 año dos dígitos (25, 26)    C8 día invertido (mes-día: 12-día... se usa 38-día; espejo)

PASA (cada una): O/E < 1 en dev-A Y en dev-B con IC 99,375 % < 1. Los candidatos con valor repetido por día
(muchos sorteos el mismo animal) se agrupan por jornada en el bootstrap.
Placebos: para cada candidata que pase se mide también la misma regla con desplazamiento +-1 (esperado ~1).
Si alguna pasa, se mide cuánto mueve el Top-15 en dev-B sacándola (relleno con el 16.º) frente a B1.

## Falsación del lazo
Si ninguna pasa: la veta fecha/hora está agotada en LA y se declara el techo; la siguiente confirmación es solo
la sombra en vivo de exposición. No se prueban más hipótesis sobre estos mismos datos sin razón nueva.

## Réplica (escrita ANTES de medir, mismo día)
`ronda5_replica.py`: C4 = animal cuyo número es la suma de dígitos del día, probado (a) con todos los días y
(b) solo días >= 10 (donde suma != día). Datos: RD Internacional dev (esperado = B1 de RD), LARD, La Granjita,
Selva Plus, Guácharo (esperado = frecuencia). Réplica en RD: O/E < 1 con IC 98,75 % (Bonferroni 2) < 1 en (b).
Los demás juegos son descriptivos. Si RD no replica, C4 se archiva como ruido.
