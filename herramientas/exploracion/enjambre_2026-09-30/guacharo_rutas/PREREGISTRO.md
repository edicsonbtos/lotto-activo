# PREREGISTRO — Camino 4: Guácharo + rutas nuevas (enjambre 2026-09-30)

Escrito ANTES de calcular ninguna cifra de este camino. No se cambia después de ver resultados.
Lo único visto antes: reglamentos (Guácharo: 77 figuras, 60x, el 75 paga 120x, cierre 5 min antes;
Lotto Activo: tradicional 30x, DUPLETA 1.000x por acertar la combinación de dos sorteos distintos,
ejemplo "1.ª dupleta = 9:00 y 10:00"), y en el dev de Guácharo (2022-02..2024-11, ya usado por b07)
la frecuencia del 75: 64 de 11.296 (0,44 veces lo normal).

## Parte A — Guácharo M2, últimos 6 meses (re-precio, NO es una prueba nueva)
- Fuente: `lotto-activo-motor/motor_nuevo/ronda3/b07_guacharo/ciega/salida.npz` (predicciones ya
  congeladas y ya puntuadas UNA vez en la ciega del 2026-09-28; registro.jsonl de ronda3).
  No se reajusta nada, no se elige nada: solo se cambia el precio.
- Ventana: 2026-04-01..2026-09-27 (última fecha disponible en el sellado).
  Este tramo YA SE MIRÓ en la ciega de b07; esto es descripción, no confirmación.
- Pagos: escenario oficial 60x y el 75 a 120x. Sensibilidad: 55x y 50x parejos (agencias que pagan menos).
- Métricas: Top-15 (M2, N0, azar 15/77); retorno por ficha del Top-15 plano (1 ficha a cada uno) y del
  Top-5 escalonado 2-2-2-1-1; mbits M2−N0. IC 95 % por bootstrap de jornadas (2000, semilla 7).
- No hay umbral de "pasa": la decisión sigue siendo la del INFORME_RONDA3 (sombra en vivo).

## Parte B — cribado en DESARROLLO de las 2 rutas nuevas más prometedoras (solo LA)
Datos: `herramientas/exploracion/calor_cache.npz` (ensamble walk-forward, filas [2000, 9357) =
2024-03-07..2025-12-17). Nada de filas ≥ 9357 en el cribado.

### B1 — Dupleta de Lotto Activo (1.000x)
- Apuesta: antes del sorteo h (5 min antes), con la distribución P_h del ensamble (que solo sabe lo
  salido hasta h−1), lista T = Top-k de P_h. Se compran TODOS los pares ordenados (a, b) con a ≠ b,
  a, b ∈ T, para la dupleta (h, h+1) del mismo día: k·(k−1) fichas. Para h+1 se usa la MISMA lista
  (no se usa P_{h+1}, que ya conoce el resultado de h: sería fuga).
- Gana si y_h ∈ T, y_{h+1} ∈ T e y_h ≠ y_{h+1}: cobra 1.000 fichas.
- Pares: todos los consecutivos del mismo día (8-9, 9-10, …, 18-19).
- Métrica primaria: retorno por ficha de k = 15 (210 fichas) con pago 1.000x, contra el equilibrio.
  Secundarias: k = 5 (20 fichas), k = 10 (90 fichas); pago de equilibrio; escenario 100x
  (una web dice "10 Bs dan 1.000 Bs"); mbits del par contra el azar sin repetición (1/(38·37)).
  Comparación: Top-15 plano y Top-5 escalonado del animal suelto (30x) en las mismas filas.
- IC 95 % por bootstrap de jornadas (12 sorteos). Mitades del dev.
- PASA_DEV (k = 15, 1.000x): retorno medio > 0, límite inferior del IC 95 % > 0 y media > 0 en las
  dos mitades. Si no, NO PASA.
- Confirmación (una sola mirada, pre-registrada): si pasa en dev, se mide igual en
  2026-04-01..2026-09-16 con `lotto-activo-motor/motor_nuevo/reciente/P_ens_reciente.npy`
  (ensamble walk-forward ya calculado). AVISO: las filas ≥ 9357 de LA ya se miraron varias veces
  (registro_final.jsonl + reciente de ag12), así que es una réplica DÉBIL, no prueba limpia.
  Si no pasa en dev, no se mira.

### B2 — Fuerza de la "no repetición" estimada en línea (cambio de régimen)
- Para cada sorteo t: R_t = animales ya salidos hoy antes de t. Con los últimos 30 días ANTERIORES
  al día de t: O = sorteos cuyo ganador estaba en R, E = suma de P(R) del ensamble.
  θ_t = (O + 2) / (E + 2), recortado a [0,25; 4]. P'(i) = P(i)·θ_t si i ∈ R_t; se renormaliza.
- Métrica: Δmbits = mbits(P') − mbits(P), IC 95 % por bloques de jornada, por hora (12 horas) y por
  mitades. Secundarias: Δ Top-5 y Δ Top-15 (puntos).
- PASA_DEV: Δ ≥ +3 mbits, límite inferior del IC > 0 y > 0 en las dos mitades. Si no, NO PASA.
- Confirmación (si pasa): igual que B1, una mirada a 2026-04-01..09-16 (réplica débil).

## Lo que no se hace
No se toca historial.txt, predicciones.json, servidor.py ni producción. Sin commit, sin push.
