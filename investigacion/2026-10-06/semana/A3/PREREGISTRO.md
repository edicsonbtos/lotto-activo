# A3 · Pre-registro (2026-10-06, escrito ANTES de calcular cualquier resultado de esta carpeta)

Pregunta: ¿qué hace distinto el operador miércoles-viernes (MVF) en 2026, y es corregible?
Grupos: MVF = dow 2,3,4; SM = sáb-mar (dow 5,6,0,1). Eras: dev = t < 9357 (2024-03-07..2025-12-19); 2026 = f ≥ 2026-01-01.
Fuente: $SP/prod_0605.npz (motor de producción walk-forward) + $SP/hist_0605.txt. Ya conozco (del informe que motiva
esto) el Top-15 O/E por día y el O/E de "reciclados ayer/anteayer"; NO he mirado nada de lo que sigue.

Todo O/E = (ganadores en la categoría) / (Σ P del motor sobre la categoría), sorteo a sorteo, así que ya está
condicionado a la hora y al estado. Contrastes MVF vs SM: además, por hora (12 estratos) con suma de O y E por estrato.
IC 95 % por bootstrap de jornadas (2.000 réplicas, bloque = día). "Ratio" = O/E(MVF) / O/E(SM).

## M1. Perfil del ganador (la métrica principal)
Categorías (estado antes del sorteo): retraso G en sorteos 1-12, 13-24, 25-36, 37-60, 61-120, >120; salió hoy antes;
salió ayer (día calendario −1, no hoy); salió anteayer y no ayer (ni hoy); ≥ 4 días sin salir (ni hoy, ni d−1..d−3).
- Una categoría "es distinta en MVF-2026" si el IC 95 % del ratio excluye 1 en 2026. "Nueva de 2026" si además en dev el
  IC del ratio incluye 1.
- Descomposición: déficit de aciertos Top-15 MVF-2026 = O − E. Contrafactual: reponderar los ganadores MVF por
  categoría de reciclaje {hoy, ayer, anteayer-no-ayer, resto} para que cada una tenga el O/E de SM-2026, y recalcular el
  Top-15. Si eso recupera ≥ 50 % del déficit → el mecanismo "recicla menos" EXPLICA el déficit. < 25 % → no lo explica.

## M2. Por hora
Top-15 O/E MVF vs SM en 2026 para cada hora, mañana (8-13) y tarde (14-19), y 8:00 sola.
"Concentrado en una franja" solo si la diferencia de ratios mañana vs tarde tiene |z| ≥ 3. Si no, "difuso".

## M3. Concentración
Por día: animales distintos, repeticiones (12 − distintos), entropía de los 12 ganadores. Referencias: lo que espera el
motor (repeticiones esperadas = Σ P sobre "ya salió hoy"), y el azar puro (repeticiones = 1,60/día).
Hipótesis alternativa "MVF-2026 es casi azar puro": se acepta si (a) repeticiones/día MVF-2026 ≥ 1,30 y (b) la
ganancia del motor sobre el uniforme (mbits por sorteo) en MVF-2026 tiene IC que incluye 0, mientras en SM-2026 no.
Además: frecuencia de cada animal MVF vs SM en 2026 (chi² 37 gl, permutación por días) por si cambia el "bombo".

## M4. ¿El motor usa el día de la semana?
Revisión de código (grep dow en ensamble_v2 y submodelos). Si algún rasgo depende del calendario semanal, mido su
residuo (valor del rasgo en el ganador − Σ P·rasgo) por grupo y era. Cuenta como "el motor arrastra un patrón semanal
viejo" solo si el residuo MVF-2026 difiere del SM-2026 con |z| ≥ 3 y en dev no.

## Controles adversariales (fijados de antemano)
- Selección post-hoc: z del Top-15 O/E para las 7 ternas de días consecutivos en 2026; el p del máximo se corrige ×7
  (y se recuerda que también se eligió "la terna" entre otras formas de agrupar).
- Datos: concordancia del historial con datos_multiloteria/oficial_multi.csv (juego 1 = LA) y lottoactivo.csv en
  2026, por día de la semana. Si los desacuerdos se concentran en MVF, el hallazgo es un artefacto de datos.
- Otras loterías (sin motor): repeticiones dentro del día y "salió ayer" por grupo en 2026 vs antes. Solo descriptivo.

## Veredicto (regla fijada)
REAL si: el déficit 2026 se reproduce en ≥ 2 de 3 trimestres (ya sabido), M1 identifica un mecanismo que explica
≥ 50 % y que es nuevo de 2026, y no hay artefacto de datos. RUIDO si el control de selección deja p corregido > 0,05
o hay artefacto. DUDOSO en otro caso. "Corregible con regla simple" solo se afirma como hipótesis para el vivo; aquí no
se ajusta nada que se mida en el mismo 2026.
