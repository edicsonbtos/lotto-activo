VEREDICTO: NULO

# ag08: logit condicional solo para el primer sorteo, apilado sobre P_aj

**Hipótesis.** Un modelo especializado en el primer sorteo, con offset log P_aj, extrae más información. Usa softmax sobre
los 38 animales con 49 rasgos por animal y su copia × era 8:00 (98 en total), con L2 elegida por validación anidada.
Pre-registro: `PREREGISTRO.md`. Script: `modelo.py`. Exploración: `explorar_lambda.py`.

**Rasgos.** A: posición 1..12 de ayer. B: posición 1..12 de anteayer. C: primer sorteo de hace 3..10 días.
D: hueco en sorteos (8 bins). E: hueco en días (6 bins). F: nº de apariciones en 1/3/7 días. G: interacción con la era.
Rasgos que ya se habían probado: A completo, B1 y C3/C4/C7 (barrido de producción) y "salió ayer" (informe 2026-10-03).
C2 es la versión con solo los rasgos nuevos.

**Validación.** Rolling-origin en 6 bloques por fecha dentro de dev. Fuera de pliegue (OOF) = bloques 2..6, n = 529
(157 de la era 9:00 y 372 de la era 8:00). λ ∈ {1..1000} se eligió dentro de cada pliegue con un rolling-origin interno
de 5 sub-bloques.

**Cosas miradas en dev: unas 93.** Son 49 O/E crudos de rasgos (sanidad), 2 candidatos anidados, 7 ablaciones y
35 combinaciones exploratorias de λ fijo × subconjunto. **No se miró prueba ni vivo.**

## Dev: OOF anidado (mbits por primer sorteo contra P_aj, IC 95 % bootstrap de días)
| candidato | OOF total | era 9:00 (n = 157) | era 8:00 (n = 372) | λ por pliegue |
|---|---|---|---|---|
| C1 (98 rasgos) | **−19,4 [−32,9; −6,5]** | +3,3 [+0,7; +5,9] | −28,9 [−48,0; −10,3] | 1000, 1000, 100, 1000, 30 |
| C2 (66, solo nuevos) | **−17,7 [−30,6; −4,7]** | +3,1 [+0,5; +5,7] | −26,5 [−44,9; −8,3] | ídem |

- Por pliegue (C1): −1,6, +4,6, −2,7, +2,9 y **−100,9** (2025-08-26..12-19). En el último pliegue la λ interna eligió 30
  y el modelo se sobreajustó. Es el mismo semestre "excepcional" (+178 mbits) del motor.
- Top-5 / Top-15 a las 8:00, OOF de C1: 90 → 96 y 232 → 230. En la era 9:00: 24 → 26 y 74 → 72. Sin mbits que lo
  respalden, ese +6 del Top-5 es ruido.
- Ablación (C1 sin un bloque, OOF): sin A −8,2, sin B −8,6, sin C −19,5, sin D −15,0, sin E −17,3, sin F −5,1,
  sin G −1,5. Todas son ≤ 0 o tienen un IC que cruza 0. Las que más dañan son las interacciones con la era y los conteos F.

## Exploración con λ fijo (descriptiva, sin anidar: el mejor de 35 es optimista)
| subconjunto | λ = 10 | λ = 100 | λ = 1000 | λ = 3000 | λ = 10000 |
|---|---|---|---|---|---|
| C1 (98) | −35,4 | −6,3 | +0,1 [−2,5; +2,5] | +0,3 [−0,7; +1,3] | +0,1 |
| C1 sin era (49) | −16,5 | −0,4 | +1,3 [−1,2; +4,0] | +0,7 | +0,2 |
| solo E (días de hueco) | +0,6 | **+2,5 [−3,0; +7,7]** | +0,5 | +0,2 | 0,0 |
| solo F (conteos) | −6,2 | −1,1 | +0,8 [−1,4; +3,2] | +0,5 | +0,2 |
| D+E+F | −13,0 | −0,4 | +1,2 [−1,3; +3,9] | +0,7 | +0,2 |
| A+B (posiciones) | +1,4 | +0,7 [−0,8; +2,2] | +0,1 | 0,0 | 0,0 |
| C (hace 3..10) | −2,5 | −0,2 | 0,0 | 0,0 | 0,0 |

Ningún λ ni subconjunto, ni elegido a posteriori, da un OOF con IC por encima de 0. El techo es ≈ +2,5 mbits, y para
alcanzarlo los coeficientes deben quedar casi en cero.

## Coeficientes más grandes
- **Modelo final (λ = 1000, la que se elige en todo dev).** Todos |β| ≤ 0,016, es decir, multiplicadores de ×0,99 a ×1,02.
  Los mayores son F_n_7d (+0,016), F_n_3d (+0,013), hueco de 2 días (+0,012) y hueco de 13-18 sorteos (+0,009).
  En la práctica el modelo es P_aj.
- **Con λ = 30 (sobreajuste, solo para ver qué "quiere" el modelo):**

  | rasgo | multiplicador |
  |---|---|
  | hueco de 2 días | ×1,15 |
  | era 8:00 × apariciones en 3 días | ×0,89 |
  | 7.º de ayer | ×1,11 (ya descartado por inestable) |
  | 8.º de anteayer | ×0,92 |
  | hueco de 3 días | ×0,92 |
  | primero de hace 6 días | ×0,93 |

- **O/E crudo contra P_aj en dev (sanidad, en muestra).** Los animales que salieron hace 1-2 días dan O/E 1,17-1,18, y
  los de hace 3-4 días dan 0,81-0,84. Es el "salió ayer = 1,12" del informe del 2026-10-03 (ya conocido y cerrado).
  Fuera de pliegue no se sostiene: el pliegue 3 lo invierte.

## Prueba / vivo
**No se midieron.** Ningún candidato cumplió la regla pre-registrada (OOF > 0 con IC que no cruce 0). Los 3 cupos de
prueba quedan sin usar, y la prueba queda intacta para otros agentes.

## Conclusión y recomendación
- Lo que aporta de verdad es ≈ 0. Un logit flexible sobre P_aj con la historia de 1-10 días solo reaprende ruido:
  con poca L2 pierde de −6 a −35 mbits, y con L2 fuerte se encoge a P_aj (±1 mbit).
- Las interacciones con la era son lo más dañino. La era 9:00 tiene poca muestra y no anticipa la de 8:00.
- El ajuste de dos factores que ya está en producción (×0,272 y ×1,736) parece capturar toda la señal explotable del
  primer sorteo con estos datos.
- **No se recomienda nada para producción.** Coincide con el hilo 9: un modelo de 91 variables tampoco superaba al ensamble.
