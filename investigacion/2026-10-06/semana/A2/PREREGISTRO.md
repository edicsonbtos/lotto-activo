# A2 — Pre-registro: réplica SIN motor de "mié-vie recicla menos" (escrito 2026-10-06, antes de calcular la métrica)

Lo único mirado antes de escribir esto: formato y completitud de los archivos (días, horas, nombres), nunca la métrica.
Hallazgos estructurales que fijan decisiones:
- hist_0605 (LA): hasta 2024-11 hubo 11 sorteos/día (sin 8:00); desde 2024-12, 12. Se usa hist_0605 para LA.
  `lottoactivo.csv` NO se usa: funde 0 (Delfín) y 00 (Ballena) (53 discrepancias, todas 0↔00).
- RD: `oficial_multi` juego 2 desde 2025-07-01 (fuente oficial); antes, `rdint_hist.csv` (coincide con la oficial salvo ~10 filas).
  Identidad del animal = código (rdint: nombre normalizado sin acentos → código).
- Selva Plus: identidad = `numero` (el nombre "Chivo" aparece con números 19 y 87). Solo se usan las horas 8:15..19:15
  (la de 20:15 aparece en 7 días). Solo se observan 82 números de 100.
- La Granjita 37, Guácharo 76 (sin anomalías). LARD (juego 3): 14 sorteos/día 8:00..21:00.

## Métrica (sin modelo)
Para cada sorteo i del día d: S = animales distintos salidos en los días de calendario d−1 y d−2 del MISMO juego
(todos sus sorteos); T = animales distintos ya salidos hoy antes de i. O_i = 1[ganador ∈ S].
- E principal (E1, "azar sin repetir en el día"): |S \ T| / (N − |T|).  E0 ingenuo = |S| / N (se reporta también).
- N = tamaño del tablero efectivo = códigos distintos observados en toda la serie del juego (LA/RD/LARD 38,
  Granjita 37, Guácharo 76, Selva 82; con N=100 en Selva el RR entre grupos casi no cambia, se reporta).
- Elegibles: día d completo y d−1, d−2 completos (completo = todas las horas estándar del juego en esa fecha).
- Control: repetición dentro del mismo día, O = 1[ganador ∈ T], E = |T|/N, por grupo y por día de semana.

## Contraste
Grupo A = miércoles, jueves, viernes (del sorteo); B = resto. RR = razón de tasas O/E de Mantel-Haenszel
estratificada por hora: RR = Σ_h O_Ah·E_Bh/(E_Ah+E_Bh) ÷ Σ_h O_Bh·E_Ah/(E_Ah+E_Bh).
p unilateral (RR < 1) por permutación de etiquetas A/B entre jornadas (5000). IC 95 % por bootstrap de jornadas (2000).
También O/E por cada día de la semana.

## Tramos
- LA: dev 2024-01-01..2025-12-31; 2026 = 2026-01-01..2026-10-05; y ventana común 2026-04-13..2026-09-13.
- RD: 2024-01-01..2025-12-31 y 2026-01-01..2026-09-22.  LARD: 2025-07-01..12-31 y 2026-01-01..09-22.
- La Granjita, Selva Plus, Guácharo: 2026-04-13..2026-09-13 (solo hay eso).

## Qué cuenta (fijado antes de ver nada)
Efecto de referencia (LA 2026, con motor): reciclaje O/E ≈ 0,91 mié-vie contra ≈ 1,04 resto → RR ≈ 0,88.
1. Reproducción en LA (no ciega): LA 2026 con RR < 1 y p < 0,05. Si no, la métrica sin modelo no ve el mecanismo
   ni siquiera donde se descubrió (apuntaría a un artefacto de la expectativa del motor).
2. Réplica ciega: juegos 2026 = RD, LARD, La Granjita, Selva Plus, Guácharo (5).
   - REAL: RR < 1 con p < 0,05 unilateral en ≥ 2 de los 5 Y RR combinado (inverso de la varianza en log) < 1 con p < 0,01.
   - RUIDO: ≤ 1 juego pasa y el RR combinado ≥ 0,97 o su p > 0,10.
   - DUDOSO: cualquier otro caso.
   (Con 5 juegos nulos, P(≥ 2 pasan por azar) ≈ 2 %.)
3. Secundario: si RD 2024-25 también da RR < 1 (p < 0,05), el patrón no es "de 2026" sino propio de RD.
   El control (repetición en el mismo día) no debe mostrar diferencia A/B; si la muestra, se avisa.
Nota: LARD 2026 era tramo ciego del hilo 8 (otra pregunta); aquí se usa para esta hipótesis y queda consumido para ella.
