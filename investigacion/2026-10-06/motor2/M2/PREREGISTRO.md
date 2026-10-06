# M2 · Pre-registro: "fugas" de calendario más allá del día de la semana (2026-10-06, ANTES de medir)

Base: `A.PROD` (ensamble_v2 + primer sorteo + fecha a las 8:00). Comprobado antes de medir, sin mirar resultados:
PROD solo difiere del ensamble crudo en la hora 0-1 (primer sorteo); **la corrección general por exposición
(número de la fecha/hora/mes, `exposicion.aplicar`) NO está en PROD en las demás horas.**

## Grupos de sorteos (todos definidos solo por el calendario)
Por día: G_pago (día del mes ∈ {1,15,16,30,31}); G_q15 (15-16); G_q30 (30, 31, 1); G_vq (viernes con día ∈
{13,14,15,28,29,30,31}); G_ini (días 1-3); G_fin (últimos 3 días del mes); G_fer (feriado nacional VE, lista abajo);
G_lw (fin de semana largo: cualquier día de una racha ≥ 3 días seguidos de sáb/dom/feriado); G_finde (sáb-dom);
G_vie (viernes); G_mvf (mié-vie).
Por sorteo: G_tarde_mvf = interacción (tarde − mañana en MVF) − (tarde − mañana en SM), tarde = 13:00-19:00.
Feriados: 2024-01-01, 02-12, 02-13, 03-28, 03-29, 04-19, 05-01, 06-24, 07-05, 07-24, 10-12, 12-24, 12-25, 12-31;
2025-01-01, 03-03, 03-04, 04-17, 04-18, 04-19, 05-01, 06-24, 07-05, 07-24, 10-12, 12-24, 12-25, 12-31;
2026-01-01, 02-16, 02-17, 04-02, 04-03, 04-19, 05-01, 06-24, 07-05, 07-24.

## Métricas (grupo contra su complemento, en el mismo tramo)
M1 Top-15 O/E contra PROD; M2 mbits de PROD (estratificado por hora: se resta la media de su hora);
M3 "ya salió hoy" O/E; M4 reciclaje "salió ayer o anteayer, no hoy" O/E; M5 fecha {d−1, d, d+1} O/E;
M6 número de la hora (reloj 12 h) O/E. Estadístico: log(O/E grupo) − log(O/E complemento) (M2: diferencia de
medias), SE por bootstrap de jornadas (2.000), z.
Para G_tarde_mvf, la interacción de log-ratios.

## Multiplicidad y confirmación
- AJUSTE (2025-07-01..2026-02-28): ~12 grupos × 6 métricas. BH-FDR q = 0,10 con p de dos colas, y además
  permutación de jornadas (se barajan las etiquetas de calendario entre los días de AJUSTE, 1.000 veces) para el
  máximo |z| de la familia.
- **Pasa a ELECCION** lo que pasa FDR en AJUSTE. **Se confirma** si en ELECCION tiene el mismo signo y p de una cola
  < 0,05. Todo lo demás de ELECCION es descriptivo.
## Corrección
Para cada patrón confirmado (grupo g, categoría c): multiplicador r = (O+5)/(E+5) sobre PROD en g, ajustado en AJUSTE
(versión fija) y versión walk-forward (r estimado con todas las filas anteriores desde 2025-07-01, con olvido de
semivida H ∈ {60, 120, ∞} días elegido en ELECCION). Para M1/M2: temperatura p ∝ PROD^τ en g.
Si no se confirma nada, se evalúa igualmente, como control, la exposición general (M5/M6 sin grupo, walk-forward,
separada hora 0 / resto), porque PROD no la lleva: es lo único "de calendario" conocido y ausente del motor.
Mezcla log-lineal con w elegido en ELECCION.
**Gana** si Δmbits contra PROD tiene IC 90 % > 0 en ELECCION y no empeora AJUSTE. Solo entonces una mirada a
PRUEBA26 con el conjunto congelado. Veredicto MEJORA si PRUEBA26 da Δ > 0 con IC 90 % > 0; DUDOSO si Δ > 0 con IC que
toca 0; NO MEJORA si no gana en ELECCION o si PRUEBA26 sale ≤ 0.
