# Pre-registro A1 — validación estadística día por día del efecto "mié-vie" (2026-10-06)
Escrito ANTES de calcular nada en esta carpeta. Ya se conoce (del INFORME de reciclaje) el resultado exploratorio:
2026 mié/jue/vie Top-15 O/E 0,85/0,82/0,84; dev sin efecto (domingo 0,82). Este pre-registro no puede ser ciego respecto a
eso; lo que fija es CÓMO se juzga la búsqueda que lo produjo.

## Datos y tramos
- `prod_0605.npz` (walk-forward de producción). dev = t < 9357 (2024-03-07..2025-12-19); 2026 = f ≥ 2026-01-01;
  vivo = f ≥ 2026-09-15 (subconjunto de 2026, solo descriptivo).
- Unidad de remuestreo: la jornada (fecha). Día de la semana por fecha del sorteo.

## Métricas (por día de la semana y tramo)
1. Top-15 O/E = Σ aciertos Top-15 / Σ masa del Top-15 del motor (principal).
2. mbits del ganador = 1000·mean(log2(38·P[y])).
3. Top-5: tasa de acierto y O/E contra la masa del Top-5.
4. Retorno Top-5 escalonado 2-2-2-1-1 (8 fichas, pago 30), por ficha.
IC 95 % por bootstrap de jornadas (4.000 réplicas).

## Test de la búsqueda (solo 2026)
Se barajan las etiquetas de día de la semana ENTRE jornadas de 2026 (se conserva cuántas jornadas tiene cada día),
20.000 permutaciones. Estadísticos (todos de Top-15 O/E del grupo):
- S1: peor bloque de 3 días consecutivos (7 bloques cíclicos: lun-mié .. dom-mar), mínimo O/E.
- S2: peor subconjunto de 3 días cualquiera (35 subconjuntos), mínimo O/E.
- S3: χ² de los 7 días: Σ_d (O_d−E_d)²/V_d, V_d = Σ m15(1−m15) del motor (binomial de Poisson).
- S4 (el más conservador, búsqueda amplia): máximo |z| sobre todos los subconjuntos de 1 a 3 días (63), dos colas.
p = fracción de permutaciones con estadístico tan extremo como el observado.

## Umbrales (fijados ahora)
- Búsqueda: PASA si p(S2) < 0,01 y p(S4) < 0,05. RUIDO si p(S2) ≥ 0,05.
- Estabilidad mensual (ene..oct 2026, 10 meses): PASA si ≥ 8/10 meses tienen O/E mié-vie < O/E resto.
  RUIDO si ≤ 6/10.
- Robustez: tras excluir jornadas con < 12 sorteos y feriados nacionales venezolanos 2026, el O/E mié-vie sigue ≤ 0,90 y
  el IC 95 % por jornadas de la diferencia (mié-vie − resto) no toca 0. Por hora: ≥ 9/12 horas con O/E mié-vie < resto.
  Además se mide la diferencia estratificada por hora (media ponderada por E de las diferencias por hora).
- Vivo (≥ 2026-09-15): solo descriptivo (≈ 9 jornadas mié-vie, sin potencia). Se reporta la dirección.
- dev: si en dev mié-vie tampoco difiere (|diferencia| < 0,05), el efecto no es estacionario. Esto no tumba la
  existencia en 2026, pero sí limita el veredicto.

## Veredicto
- REAL: pasan búsqueda, estabilidad y robustez.
- RUIDO: falla la búsqueda (p(S2) ≥ 0,05) o la estabilidad (≤ 6/10).
- DUDOSO: cualquier otro caso (incluido pasar todo pero con un precedente de efectos de día de la semana que aparecen y
  desaparecen entre eras, como el domingo de dev).
