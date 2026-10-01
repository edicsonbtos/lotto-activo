# PRERREGISTRO — "filtros de la tarde" (2026-09-29)

Idea del usuario: en los **dos últimos sorteos de la tarde** (Lotto Activo 18:00 y 19:00 = hora 10 y 11;
RD Internacional 18:30 y 19:30 = hora 10 y 11) se descartan:
1. **Hoy**: los animales que ya salieron hoy en ese mismo juego.
2. **Gemelo**: el último resultado del otro juego (para LA h:00 → RD (h−1):30 del mismo día; para RD h:30 → LA h:00 del mismo día).
3. **Fríos**: los animales que llevan **más de 7 días de calendario** sin salir en ese juego.
Lo que queda es el conjunto C. La idea es que "el panorama se reduce" y se puede explotar.

Ningún parámetro se ajusta: las tres reglas y el umbral de 7 días los fijó el usuario.
Quedan fuera los días tocados por la corrección de fechas del 2026-09-29 (antes y después), porque el cruce LA↔RD sería erróneo.

## Hipótesis y umbrales (por juego; 4 pruebas → IC 98,75 %, bootstrap por jornada, 5000 réplicas)
- **H1, jugar plano todo C** (1 ficha a cada animal de C, paga 30): retorno por ficha.
  PASA si el IC 98,75 % queda entero por encima de 0.
- **H2, filtros sobre el ensamble** (se quitan del ranking los excluidos y suben los siguientes): diferencia de retorno
  por ficha del Top-5 escalonado (2-2-2-1-1) filtrado menos el normal.
  PASA si el IC 98,75 % queda entero por encima de 0.
- Descriptivo, sin veredicto: por grupo excluido (hoy / gemelo que no está en hoy / frío que no está en los anteriores), las salidas
  observadas contra las esperadas por el azar (1/38) y por el ensamble (suma de P). También el Top-15 ponderado 3-2-1 filtrado,
  y el acierto de C contra |C|/38.

## Tramos
- Desarrollo (exploratorio, se mira primero, sin veredicto): LA filas [2000, 9357) con `calor_cache.npz`; RD `rdint/cache_dev.npz` (P1).
- **Ciego (UNA vez, `python filtros_tarde.py ciega`)**: LA filas [9357, 12511) con `motor_nuevo/reciente/P_ens_reciente.npy`
  (worktree lotto-activo-motor); RD `rdint/cache_todo.npz` (P1), tramos 'test' + 'desc' (2025-07-01..2026-09-13).
  Estos tramos se usaron para otras ideas, **nunca para esta**. La confirmación definitiva sería el marcador en vivo.
- Se informa por mitades del tramo ciego (sin veredicto aparte).
