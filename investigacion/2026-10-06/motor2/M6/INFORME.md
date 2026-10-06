# M6: reglas del operador que PROD no modela (residuo O/E contra PROD), 2026-10-06

Archivos: `PREREGISTRO.md` (escrito antes de mirar), `rasgos.py` (539 rasgos walk-forward), `barrido.py` → `barrido.tsv`
(O/E y z por rasgo en AJUSTE, ELECCION y ANTIGUO), `confirmados.json`, `placebo.py`, `correccion.py`, `descomp.py`,
`final.py` (prueba de fuga, matriz final y la única mirada a PRUEBA26). Matriz: `<scratchpad>/motor2_M6.npz` (P 10744×38).

## Barrido (AJUSTE, BH 10 % sobre 539 rasgos) → confirmación (ELECCION, Bonferroni 0,05/15)
15 supervivientes del BH; se confirman 2:
| rasgo | O/E AJUSTE | O/E ELECCION | O/E ANTIGUO |
|---|---|---|---|
| **RD1:igual**: LA h:00 = RD (h−1):30 del mismo día | 0,43 (z −4,75) | 0,21 (z −4,62) | 0,36 (z −7,7) |
| **par_evita**: animal del decil de pares que menos coinciden en el día (lift de 365 días previos) con algo que ya salió hoy | 0,92 (z −3,81) | 0,88 (z −3,88) | 0,92 (z −4,5) |

`par_evita` es lo nuevo: marca unos 13,7 animales (40 % de la masa de PROD) y les quita el 12-15 %. Es estable por mes
(mar-jun 2026: 0,86/0,90/0,83/0,95) y más fuerte de miércoles a viernes (0,84 y 0,83 frente a 0,97 y 0,92 el resto).
`RD1:igual` NO es nuevo: es la "regla de cambio RD (h−1):30" que la jugada en vivo ya aplica al Top-5 (quitar y subir), pero
PROD no la lleva en las probabilidades. Por eso suma mbits contra PROD aunque el Top-5 en vivo ya tenía parte de ese efecto.

Lo que NO pasó, por familia:
- (a) h−1/h−2/h−3: varias relaciones con h−1 salen < 1 en las tres eras (misma columna 0,87/0,91/0,93; último dígito
  0,80/0,83/0,89; suma de dígitos 0,73/0,80/0,89; vecino de rueda 0,79/0,77/0,81), pero ninguna confirma con Bonferroni.
  Quedan para vigilancia, no para el motor. Espejo, ±1, ±2, suma y diferencia: nada.
- (b) tablero: `tableros.json/md` no trae la disposición física. Se probaron el paño de ruleta y la rueda americana: no hay
  señal (máx |z| 2,6).
- (c) misma hora de ayer y último de ayer (también solo a las 8:00): nada (máx |z| 2,8, no replica).
- (d) RD (h−2):30 igual: 0,79/0,75/0,70 (es la L3 conocida), no pasa el BH en AJUSTE. "Salió en RD hoy": 0,96/0,85/0,79.
  Relaciones numéricas con RD: nada.
- (e) transiciones h−1→h "prohibidas" (Markov de 365 días): 0,74-0,80 en AJUSTE y ELECCION, pero ~1 en ANTIGUO; no confirman.
- (f) **no hay tope de ausencia**: los que más tiempo llevan sin salir dan O/E 0,77-0,95 en AJUSTE y 1,1-1,5 en ELECCION
  (rango 1: 0,95 y 1,28), sin dirección estable ni el exceso que daría un tope.
- (g) 342 parejas de horas (hoy-hoy y ayer-hoy): 8 con p < 0,01 en AJUSTE (3,4 esperadas); ninguna replica. Es ruido.
- (z) fecha y hora fuera de las 8:00 (conocidas, PROD no las aplica a h ≥ 1): día 0,55/0,79, hora12 0,58/0,77; pasan el BH
  pero no Bonferroni en ELECCION. Sumarlas (V2) no mejora ELECCION (+21,3 contra +21,4).
- Placebo por permutación de jornadas: NO es válido aquí (máx |z| nulo 13-17), porque PROD condiciona en la secuencia
  real y el ganador permutado rompe su calibración. La referencia es el BH con la varianza martingala.

## Corrección y evaluación (`evaluar`, Δ contra PROD con IC 90 % por jornadas)
p ∝ PROD·exp(β1·RD1 + β2·par_evita), β por máxima verosimilitud (ridge λ = 2) reajustada cada mes con las filas
anteriores (walk-forward). β en AJUSTE: ×0,47 para RD1 y ×0,85 para par_evita. `chequear_fuga` OK (rasgos y β se
recalculan desde la secuencia alterada) y la matriz guardada coincide con ese pipeline.
| variante | AJUSTE Δ | ELECCION Δ | ELECCION Top-5 / Top-15 / ret Top-5 |
|---|---|---|---|
| RD1 sola (wf) | +7,4 [+3,0; +11,8] | +14,5 [+10,3; +18,7] | 20,4 / 50,1 / +25,0 % |
| par_evita sola (wf) | +3,7 [+1,0; +6,4] | +6,8 [+2,5; +11,2] | 20,4 / 51,6 / +25,0 % |
| **V1 final = RD1 + par_evita (wf)** | **+11,2 [+5,9; +16,5]** | **+21,4 [+15,5; +27,4]** | 20,5 / 52,2 / +26,3 % (PROD 20,1 / 48,6 / +23,4 %) |
| V2 = V1 + fecha/hora (wf) | +21,4 | +21,3 [+12,6; +30,1] | 20,4 / 50,8 / +26,3 % |
| V3 exploratoria (+ rasgos NO confirmados) | +31,0 | +29,6 | descartada: usa rasgos que fallaron la confirmación |
| mezcla log-lineal w = 0,5 / 1,2 / 1,5 | | +14,0 / +23,0 / +24,1 | w > 1 sube mbits pero baja el Top-5; se queda w = 1 |
Con la regla de cambio RD ya aplicada al Top-5 de ambos, ELECCION: PROD 20,40 % / 50,07 % / +25,0 %; V1 20,47 % / 52,23 % / +26,3 %.

**PRUEBA26 (una vez, V1 congelada):** mbits +122,3, **Δ +13,20 [+6,46; +19,94]**, Top-5 20,2 % (PROD 18,6 %),
Top-15 51,4 % (PROD 49,6 %), ret Top-5 +24,4 % (PROD +14,4 %). Ojo: el historial de RD llega a 2026-09-22, así que los
últimos 13 días de PRUEBA26 van sin RD1 (sin corrección de ese rasgo).

## VEREDICTO: MEJORA
Para llevarlo a producción hacen falta: RD en vivo (`rdint_vivo.py`) para RD1, y la tabla de pares del mes (365 días previos)
para par_evita. Una parte de la ganancia (RD1) ya está en la jugada en vivo como la regla de cambio del Top-5. Lo
genuinamente nuevo es par_evita: +3,7 / +6,8 mbits sola en AJUSTE / ELECCION. V1 sobre PROD con la regla de cambio ya
aplicada: +2,2 pp de Top-15 y +1,3 pp de retorno en ELECCION, aunque parte de ese Top-15 es RD1 fuera del Top-5.
Debe pasar por `revisor-sesgo` y por la sombra en vivo antes de entrar en la jugada.
