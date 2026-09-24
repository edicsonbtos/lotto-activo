# Hilo 8 — LARD cruzado: señal en desarrollo (pre-registro: PREREGISTRO_lard_cruzado.md)

Ventana 2025-07-01..2026-02-01: 215 días  (desarrollo)
| par | n | repite | esperado n/38 | ratio | p (menos) | pasa dev (p<0,0025) |
|---|---|---|---|---|---|---|
| P1: LA h:00 <- LARD (h-1):00 | 2211 | 58 | 58.2 | 1.00 | 0.53 |  |
| P2: RD h:30 <- LARD h:00 | 2412 | 69 | 63.5 | 1.09 | 0.78 |  |
| P3: LARD h:00 <- RD (h-1):30 | 2412 | 66 | 63.5 | 1.04 | 0.65 |  |
| P4: LARD h:00 <- LA (h-1):00 | 2412 | 63 | 63.5 | 0.99 | 0.51 |  |
| desc: LA h:00 = LARD h:00 (simultaneos) | 2412 | 68 | 63.5 | 1.07 | 0.74 |  |
| control hilo 7: RD h:30 <- LA h:00 | 2412 | 8 | 63.5 | 0.13 | 2e-18 |  |
| control hilo 7: LA h:00 <- RD (h-1):30 | 2211 | 27 | 58.2 | 0.46 | 4e-06 |  |

**VEREDICTO: ningún par pasa en desarrollo → LARD no aporta. Fin del hilo 8; la prueba ciega (2026-02-01..09-22) NO se miró.**

Los controles del hilo 7 salen fuertes en los mismos datos (RD h:30 repite LA h:00 8 veces contra 63,5 esperadas), así que el método detecta el efecto cuando existe. LARD se comporta como un sorteo independiente de LA y de RD (ratios 0,99-1,09).

_Corrido el 2026-09-23 en la PC (python puro), datos: datos_multiloteria/oficial_multi.csv (API oficial, 449 días)._
