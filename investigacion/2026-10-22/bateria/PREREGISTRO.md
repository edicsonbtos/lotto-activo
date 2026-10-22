# Preregistro — batería 2026-10-22 (ideas no probadas + pruebas del motor por otras vías)

Escrito ANTES de mirar ningún resultado. Protocolo `lotto-nueva-idea`.

## Datos
- **Desarrollo**: `verificacion/hilo9/datos/calor_cache.npz` (P walk-forward del ensamble, filas [2000, 9357) de
  `verificacion/hilo9/datos/historial.txt`, 2024-03-07..2025-12-17, 7.357 sorteos). dev-A = primera mitad de los días,
  dev-B = segunda mitad.
- **El tramo de prueba ≥ 9357 NO se toca.**
- **Ciega nueva (una sola mirada)**: pronósticos congelados en vivo leídos de `/api/mesa` el 2026-10-22:
  ensamble (`modelo=la`, 2026-09-14..10-22) y motor principal ag12+RD (`modelo=principal`, 2026-09-26..10-22).
  Los ganadores anteriores del día salen de `/api/mesa`, `oficial_multi.csv` y `historial.txt`.

## Hipótesis (familia de 7; ninguna figura en la lista de ideas cerradas)
Para cada sorteo t, `prev` = ganador del sorteo anterior del MISMO día (las 8:00 no cuentan).
- H1 Rueda: el candidato es vecino inmediato de `prev` en la rueda americana (distancia 1).
- H2 Color: mismo color (rojo/negro) que `prev` (0 y 00 fuera).
- H3 Docena: misma docena (1-12, 13-24, 25-36) que `prev`.
- H4 Consecutivo: |n − prev| = 1 (1..36).
- H5 Mes: número = mes del sorteo (todas las horas).
- H6 Día de semana: número = día de la semana (lunes=1..domingo=7) (todas las horas).
- H7 Familia aves: candidato ave {7, 9, 14, 17, 21, 25, 28} y `prev` ave.

Métrica: O/E = (ganadores con el rasgo) / Σ_t P_t(rasgo), con P del ensamble. IC por bootstrap de jornadas.

**Pasa desarrollo** si: mismo sentido en dev-A y dev-B con |z| ≥ 2 en cada mitad, y |z| combinado ≥ 2,73
(Bonferroni 0,05/7, bilateral).
**Pasa ciega** (solo los que pasen desarrollo): la corrección P×(O/E de desarrollo) en el rasgo, renormalizada, da
Δmbits > 0 en el ensamble en vivo con p unilateral < 0,05 (bootstrap por jornada), y mismo sentido en ag12+RD.
Si nada pasa desarrollo, la ciega de hipótesis no se corre y se reporta así.

## Pruebas del motor por otras vías (diagnóstico, no deciden nada)
Sobre los pronósticos congelados en vivo (ensamble y ag12+RD):
1. Calibración por puesto (1-5, 6-10, 11-15, 16-25, 26-38): esperado vs observado.
2. O/E del ganador por: hora, día de semana, hueco (sorteos desde su última salida: 1-12, 13-36, 37-84, 85+),
   "ya salió hoy", número = día del mes, número = hora en reloj de 12 h.
3. Prueba de permutación: barajar ganadores entre sorteos de la misma hora (1.000 veces) para comprobar que la señal
   en mbits no es un artefacto.
4. Probabilidad, según el modelo, de rachas como la de los últimos 13 sorteos (3 en el Top-15).
