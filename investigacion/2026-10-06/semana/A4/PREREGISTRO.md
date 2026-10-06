# A4 — Cronología y cambio de régimen del efecto "día de la semana" (pre-registro, 2026-10-06)

Escrito ANTES de calcular cualquier resultado de esta carpeta. Lo único visto antes: las cifras del INFORME de
`../../reciclaje/` (2026: mié 0,85, jue 0,82, vie 0,84; dev: domingo 0,82; 3 trimestres de 2026 con mié-vie 0,81-0,86).

## Datos y métrica
- `prod_0605.npz` (walk-forward de producción, filas desde 2024-03-07 hasta 2026-10-05).
- Por sorteo: acierto Top-15 (`in15`) y masa del Top-15 según el motor (`m15`). Residuo r = in15 − m15.
- O/E de un grupo = Σin15 / Σm15. Comparación entre grupos A y B **estratificada por hora**:
  Δ = Σ_h w_h (r̄_A,h − r̄_B,h) / m̄15, con w_h ∝ n_h total (por hora); se expresa en unidades de O/E.
- IC: bootstrap por bloques de jornada (día) para O/E; para contrastes en el tiempo, bloques de semana ISO
  (preserva la estructura día-de-semana dentro de la semana).
- Contrastes: C1 = (mié+jue+vie) − (lun,mar,sáb,dom); C2 = dom − (lun..sáb).

## Pasos
1. Serie mensual y trimestral (2024-03 .. 2026-10) del O/E por día de semana, C1 y C2 (tabla + barras de texto).
2. Punto de cambio. Estadístico: para cada corte mensual k (al menos 4 meses a cada lado), t_k = diferencia de la
   media de C (antes vs después) / EE, con C calculado por semana. Máximo |t_k| sobre k. p-valor por permutación del
   ORDEN de las semanas (2000 permutaciones; bajo H0 de estacionariedad las semanas son intercambiables).
   Se hace por separado para C1 y C2. Además CUSUM de C por semana (texto).
   Rango plausible del corte: cortes con |t_k| ≥ max|t| − 1.
   "Coinciden" = los cortes óptimos de C1 y C2 están a ≤ 2 meses. Se compara con 2024-T3 (ventana de fecha),
   2024-11-28 (empieza 8:00) y 2025-T4 (8:00 deja de esquivar lo de ayer).
3. Controles: misma maquinaria con (a) tercio del mes 1-10/11-20/21-31, (b) semana del mes (1-7, 8-14, 15-21,
   22-28, 29-31). Para 7 días de semana, 3 tercios y 5 semanas: χ² de heterogeneidad (O−E)²/V en dev y en 2026,
   calibrado por permutación (días de semana barajados DENTRO de cada semana ISO; para los controles, etiquetas de
   grupo barajadas entre días del mismo mes). Además: el "peor bloque de 3 días consecutivos" de la semana (7
   posibles, circular) en cada semestre, para medir cuánto rota el día malo.
4. Estabilidad: por semestre (2024-S1 .. 2026-S2) el día de semana con peor O/E y su valor; y la tasa nula de que
   algún día salga ≤ 0,85 en un semestre (por permutación dentro de semana).

## Umbrales (fijados ahora)
- Punto de cambio de C1 "real" si p_perm < 0,01; "dudoso" si 0,01 ≤ p < 0,05; "no hay" si p ≥ 0,05.
- **Régimen estable (podría seguir)** si se cumplen TODAS:
  (i) cambio de C1 con p_perm < 0,01 y desde el corte cada trimestre completo tiene C1 ≤ −0,08;
  (ii) dentro del tramo posterior al corte no hay tendencia (pendiente de C1 por mes con p > 0,10);
  (iii) los controles (tercio y semana del mes) en 2026 dan χ² con p_perm > 0,01 y su peor grupo |z| < 3;
  (iv) en el tramo previo (dev) el patrón de día de semana no rota con frecuencia: a lo sumo 1 semestre de dev con
       un "peor día" ≤ 0,85 distinto del domingo.
- **Patrón cambiante (no apostable)** si falla (i) o (iv), o si el domingo-malo de dev y el mié-vie-malo de 2026
  aparecen como episodios de ≤ 3 trimestres sin continuidad.
- Si los controles salen igual de fuertes (|z| ≥ 3 en 2026 o p_perm ≤ 0,01), el hallazgo pierde valor → como mucho DUDOSO.
- Veredicto: REAL solo si "régimen estable" y C1 en 2026 sobrevive a la corrección por haberlo elegido mirando
  (permutación dentro de semana del MÁXIMO contraste de 3 días consecutivos, p < 0,01). DUDOSO si cambio real pero
  falla algún punto de estabilidad. RUIDO si no hay cambio significativo o los controles igualan al efecto.
