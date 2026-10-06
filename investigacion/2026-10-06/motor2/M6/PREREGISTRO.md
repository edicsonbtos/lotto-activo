# M6: pre-registro (escrito ANTES de mirar resultados), 2026-10-06

## Pregunta
¿Hay reglas del operador que producción (PROD = ensamble_v2 + primer sorteo + fecha a las 8:00) NO modela, visibles
en el régimen actual como residuo O/E del ganador contra PROD?

## Métrica por rasgo
Cada rasgo es un conjunto S_i de animales marcado para la fila i usando SOLO sorteos anteriores (mismo día, ayer, RD
de horas anteriores, historia pasada). O = Σ 1[y_i ∈ S_i]; E = Σ q_i con q_i = Σ_{a∈S_i} PROD[i,a];
V = Σ q_i(1−q_i). O/E y z = (O−E)/√V (si PROD está calibrado, O−E es suma de diferencias martingala, así que V es la
varianza correcta). p bilateral normal. Filas donde el rasgo no está definido (falta el sorteo de referencia) no cuentan.

## Familias (barrido en AJUSTE = 2025-07-01..2026-02-28)
- (a) ganador de h−1, h−2, h−3 del mismo día: igual (control), ±1, +1, −1, ±2, mismo último dígito, misma decena,
  espejo (12↔21), misma suma de dígitos, complemento (n+p = 36 y = 37), suma y diferencia de h−1 y h−2 (mod 37),
  mismo color de ruleta, misma docena, misma columna, misma paridad, misma mitad.
- (b) vecinos en el tablero: tableros.json/md NO trae disposición física, así que se usan dos hipótesis declaradas:
  paño de ruleta (3 columnas × 12 filas: vecino horizontal, vertical, diagonal) y rueda americana (vecino ±1 y ±2
  en el orden de la rueda), contra h−1 y h−2.
- (c) misma hora de ayer y último sorteo de ayer: igual, ±1, último dígito, espejo, vecino de paño, vecino de rueda,
  color; el último de ayer en todas las horas y aparte en las 8:00.
- (d) RD Internacional (h−1):30 y (h−2):30 (rdint_historial.txt, hasta 2026-09-22; h ≥ 1): igual (L3, control),
  ±1, último dígito, espejo, vecinos de paño y rueda, color; y "salió en RD hoy antes de h:00".
- (e) pares que se evitan: lift de co-ocurrencia en el mismo día de cada par (a,b) aprendido en los 365 días previos
  al mes de la fila (con encogimiento); rasgo = b está en el decil más evitado de algún animal que ya salió hoy (y en
  el decil más buscado, como espejo). Secuencias prohibidas: transición h−1→h con cero apariciones en la ventana de
  365 días y en el decil más bajo de lift (Markov reciente, NO la 38×38 global cerrada).
- (f) ausencia: hueco en sorteos desde la última salida por tramos (≥48, ≥72, ≥96, ≥120, ≥150, ≥200) y el animal
  de mayor ausencia (rango 1 y rangos 1-3). Si hay un tope que el operador respeta, O/E ≫ 1 en los extremos.
- (g) parejas de horas: para cada par (h1<h2) del mismo día, igual, ±1 y mismo último dígito; y para cada par
  (hora de ayer h1, hora de hoy h2), igual.
- (z) controles conocidos fuera de las 8:00 (PROD solo los aplica a las 8:00): número del día, día±1, hora en 12 h.
  Se reportan aparte; si pasan, entran en la corrección (es regla no modelada en h ≥ 1).

## Corrección por multiplicidad y confirmación
1. AJUSTE: Benjamini-Hochberg al 10 % sobre TODOS los rasgos del barrido (familias juntas). Robustez: permutación de
   jornadas (barajar las fechas de los PROD/y por bloques de día no aplica a rasgos intradía; se usa en su lugar
   la máscara de rasgo de otra jornada de la misma hora como placebo y se calcula el máximo |z| nulo) informativa.
2. ELECCION: un superviviente se confirma si su O/E va en la misma dirección y p unilateral < 0,05/k (Bonferroni
   sobre los k supervivientes).
3. ANTIGUO solo informativo.

## Corrección y evaluación
- Con los confirmados: p ∝ PROD · exp(Σ β_k x_k), β por máxima verosimilitud en AJUSTE (logit condicional con
  desplazamiento log PROD, ridge leve). Para la matriz final (walk-forward estricto) β se reajusta cada mes con las
  filas anteriores (desde 2024-03).
- Se evalúa con A.evaluar en AJUSTE y ELECCION. Variantes permitidas: rasgos confirmados solos, más los de familia
  (z), y la mezcla log-lineal con w elegida en ELECCION.
- **Gana en ELECCION** si Δmbits vs PROD > 0 con IC90 inferior > 0, o Δ > +2 mbits con Top-5 y Top-15 sin caer.
  Solo entonces se mira PRUEBA26 UNA vez con la versión congelada.
- Si nada sobrevive AJUSTE→ELECCION: veredicto NO MEJORA, P final = PROD (o la mejor variante, declarada), y NO se
  usa PRUEBA26.
