VEREDICTO: NULO

# ag07 — ¿La regla del primer sorteo es cruzada entre juegos? (2026-10-03)
Hipótesis: el ganador del primer sorteo de Lotto Activo (LA) esquiva o favorece el animal del PRIMER sorteo de hace
k días de RD Internacional (8:30), de LARD (8:00) o de Granjita, Selva Plus y Guácharo. Métrica: O/E contra `P_aj`
(motor con el ajuste ×0,272/×1,736 de producción). Pre-registro en `PREREGISTRO.md`. Script: `analizar.py dev|desc|escala`.
Datos: RD = `rdint_hist.csv` por nombre (`ANIMALES` de `herramientas/rdint/datos.py`), 0 discrepancias con el juego 2 de la
API oficial. LARD = juego 3 de `oficial_multi.csv`. LA de base8 = juego 1 oficial (0 discrepancias). Otros juegos: mapeados
por nombre, y se descarta el animal que no está entre los 38.

## Cuánto se miró en dev
6 rasgos de selección (RD k = 1, 2, 3 y LARD k = 1, 2, 3), cada uno por era (9:00 / 8:00 / total) y además contra P sin ajuste
(18 celdas). Umbral de selección: p < 0,05/6. Descriptivo, sin que cuente como candidato: 12 conteos "propio de ayer o de
hace 3 días", 6 del reverso, 6 de Granjita/Selva/Guácharo y 6 de RD/LARD propio por tramo.

## DEV: primer sorteo de LA == primer sorteo del otro juego hace k días (contra P_aj)
| rasgo | era 9:00 (n 261) | era 8:00 dev | total dev | p unilateral (mejor lado) |
|---|---|---|---|---|
| RD k=1 | 5 / 7,0 = 0,71 | 12 / 10,0 = 1,20 | 17 / 17,0 = **1,00** [0,58; 1,60] | 0,53, signo cambia |
| RD k=2 | 9 / 6,9 = 1,31 | 10 / 9,3 = 1,08 | 19 / 16,2 = 1,17 [0,71; 1,83] | 0,27 |
| RD k=3 | 4 / 6,8 = 0,59 | 15 / 9,7 = 1,54 | 19 / 16,5 = 1,15 [0,69; 1,80] | 0,30, signo cambia |
| LARD k=1 | — | 1 / 4,4 = **0,23** [0,01; 1,26] (n 159) | idem | 0,066 |
| LARD k=2 | — | 5 / 4,4 = 1,14 | idem | 0,45 |
| LARD k=3 | — | 7 / 4,4 = 1,60 [0,64; 3,30] | idem | 0,15 |
Conteo crudo en 'cal' (RD, sin motor): k=1 3/4,7; k=2 6/4,7; k=3 3/4,7. Contra P sin ajuste sale lo mismo (±0,03).

Ningún rasgo pasa ni siquiera p < 0,05. RD k=1 y k=3 cambian de signo entre eras. Con eso, y siguiendo la regla escrita
antes de mirar, **se envían 0 candidatos a PRUEBA**, así que la prueba ciega de RD y LARD queda sin gastar. LARD k=1 es lo
único sugerente: O/E 0,23, aunque son 1 contra 4,4 con n = 159 en una sola era. Con 6 rasgos en la familia, p = 0,066 es
ruido esperable. Escala del efecto, medida dentro de dev (optimista): +4,4 mbits por primer sorteo [−1,6; +8,0], Top-5
134→135 y Top-15 358→363. Los demás rasgos dan entre 0 y +1,6 mbits. No hay nada que llevar a plata.

## Descriptivo (solo muestra de 2026-04-13 en adelante, todo en prueba/vivo de LA, no decide nada)
| LA primero vs primero de ayer de… | k=1 O/E (O/E_motor) | k=3 |
|---|---|---|
| La Granjita (n ≈ 149) | 0,48 (2 / 4,2) | 1,49 (6 / 4,0) |
| Selva Plus (n ≈ 140) | 2,05 (8 / 3,9), p(alta) = 0,045 | 1,87 (7 / 3,7) |
| Guácharo (n = 72 con animal en los 38) | 1,07 (2 / 1,9) | 0,98 |
Son 6 miradas y no muestran ningún patrón consistente: Selva sale de más y Granjita de menos.

## Reverso (descriptivo, crudo contra 1/38): RD 8:30 de hoy == primer sorteo de LA de hace k días
k=1: era 9:00 9/11,6 (0,78); era 8:00 19/16,6 (1,14); RD-dev 2024-03..2025-06 10/12,6 (0,80). k=3: 0,78 / 1,27 / 1,12.
RD no esquiva el primer sorteo de LA de ayer.

## Contexto: ¿cada juego esquiva SU PROPIO primer sorteo de ayer? (crudo contra 1/38)
| juego | k=1 | k=3 |
|---|---|---|
| LA (todo) | 3 / 28,4 = 0,11 | 50 / 28,2 = 1,77 |
| **RD Internacional** | **9 / 28,2 = 0,32** | 28 / 28,0 = 1,00 |
| LARD | 13 / 11,8 = 1,10 | 9 / 11,7 = 0,77 |
| Granjita / Selva / Guácharo | 1/3,9 · 0/3,6 · 0/0,9 | 5/3,8 · 2/3,5 · 0/0,9 |
RD por tramo (k=1): cal 2023-09..2024-02 4/4,5 (0,88); **RD-dev 2024-03..2025-06 4/12,6 (0,32, p = 0,005)**;
**RD-test 2025-07..2026-04-12 0/7,0 (p = 0,0009)**; desde 2026-04-13 1/4,2 (0,24). LARD dev 0,67 y después 1,37: no esquiva,
igual que no esquiva el número de la fecha.

## Conclusión
- La regla es **intra-juego, no cruzada**. LA solo esquiva su propio primer sorteo de ayer, y no el de RD, LARD ni los
  demás. Las O/E cruzadas quedan en ≈ 1, lo mismo que dio el hilo 9 para el reciclaje general entre juegos.
- Hallazgo lateral (fuera de mi objetivo, solo descriptivo): **RD Internacional también esquiva su propio primer sorteo
  de ayer** (O/E 0,32 crudo, 0 de 265 en su tramo de prueba). LARD no lo hace. Parece que el operador de LA y RD aplica la
  misma regla en sus dos juegos y que LARD es otra cosa, lo que es coherente con el hilo 8 y con el "número de la fecha".
  `rdint_vivo.py` no tiene ajuste de primer sorteo. Antes de tocar nada hay que medirlo **contra el motor de RD**, que
  quizá ya lo capture a medias como pasó en LA, siguiendo el protocolo de RD (dev 2024-03..2025-06; la confirmación
  vendría del marcador en vivo, porque el tramo de prueba de RD ya está usado). Ese análisis queda propuesto, no hecho.
- Recomendación para producción en LA: **ninguna**. Para RD: abrir un hilo "primer sorteo de RD" contra su motor.
