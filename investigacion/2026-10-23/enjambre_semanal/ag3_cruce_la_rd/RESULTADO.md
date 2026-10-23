# RESULTADO ag3 — repelencias cruzadas LA h:00 / RD h:30

Nada pasa. Las 5 hipótesis preregistradas (Bonferroni 0,05/5, |z| >= 2,576, mismo sentido y |z| >= 2 en dev-A y dev-B) fallan.
Scripts: `cruce.py`; salida: `salida_cruce.txt`, `resultado.json`. Prerregistro: `PREREGISTRO.md` (escrito antes de correr).

| Hipótesis | Objetivo / base | n | O/E [IC95] | z total | z dev-A / dev-B | Veredicto |
|---|---|---|---|---|---|---|
| C1 LA h:00 vs vecinos de rueda del RD (h-1):30 | LA, ensamble | 6.922 | 1,04 [0,94; 1,14] | +0,78 | -0,36 / +1,46 | NO PASA |
| C2 RD h:30 vs vecinos de rueda del LA h:00 | RD, uniforme | 5.229 | 0,975 [0,86; 1,08] | -0,43 | +0,02 / -0,62 | NO PASA |
| C3 LA vs día del mes si RD ya lo sacó hoy | LA, ensamble | G1=816 | obs 10 vs 14,6 esp. (O/E 0,44 sin ajuste) | -1,21 | -0,61 / -1,12 | NO PASA (sin potencia: esp. < 30) |
| C4 LA vs número (h-1) en reloj 12 h | LA, ensamble | 6.922 | 0,97 [0,83; 1,12] | -0,37 | -1,10 / +0,58 | NO PASA |
| C5 LA vs opuesto en rueda (d19) del RD (h-1):30 | LA, ensamble | 6.922 | 0,89 [0,76; 1,03] | -1,51 | -0,69 / -1,45 | NO PASA |

Sensibilidad (no decide): quitando el animal RD (h-1):30 de la base (regla de cambio ya en producción) C1 da 1,01 (z +0,24) y
C5 0,87 (z -1,86); tampoco pasan. Placebo número h+1: 1,00.

Controles que sí salen como se sabe (el método funciona): número de la propia hora en LA 0,77 (z -3,1; dev-A 0,93, dev-B 0,61);
día del mes en RD 0,73 [0,60; 0,88] (z -3,25; A/B -2,6/-2,0) con esta base uniforme, es decir la repelencia de fecha ya conocida
se replica dentro de RD, pero no se acopla con LA.

Réplica: no corresponde, porque nada pasó desarrollo. Por completitud se corrieron los espejos en RD (dev y oficial
2025-07-01..2025-12-17; ese tramo no está gastado para rueda cruzada, hilo 7 lo usó solo para el animal exacto): C2 0,95, C4r 1,06,
C5r 1,21 (z +1,55, sentido contrario), C3r 1,10 con 4 casos. Todo nulo. El espejo C2 es además la réplica temporal de C1, y ambos son nulos.

Lectura llana: la rueda y el número de fecha/hora se esquivan solo dentro del MISMO juego. Entre LA y RD no hay repelencia nueva
por rueda, ni por número de hora, ni por opuesto (d19 mejor candidato, 0,89, no distinguible de azar). C3 no tiene potencia
(unos 15 eventos esperados) y su dirección (menos de lo esperado) no se puede separar del ruido.
Filas de LA >= 9357 no se tocaron.

Qué haría falta para confirmarlo en vivo: nada que merezca sombra; solo C5 (d19) queda como curiosidad, y necesitaría unos
8.000+ pares adicionales para detectar un 0,89 con z=2,6, es decir años de datos. No se recomienda.
