# Hilo 7 — H4, sonda inversa: ¿gana Lotto Activo al saber lo que salió en RD Int?

Generado por `herramientas/rdint/sonda_inversa.py`. Criterio fijado en `herramientas/exploracion/PREREGISTRO_rdint_cruzado.md` (H4): **PASA si Δ ≥ +5 mbits con IC95 > 0 en ambas mitades del desarrollo**. Se esperaba que FALLE.

## Datos y anti-fuga

- Lotto Activo: filas 2000..7439 de `lotto_eval.cargar()` con fecha < 2025-07-01 → **5440 sorteos**, 2024-03-07 .. 2025-06-30 (todo en tramo desarrollo). Base = P de ensamble_v2 congelado (`calor_cache.npz`).
- RD Int truncado antes del primer sorteo del tramo 'test' (último RD usado: 2025-06-30).
- Para LA de h:00 se usa RD de (h−1):30 y anteriores del MISMO día; RD de h:30 (posterior) nunca. LA de 8:00 no tiene RD previo (features = 0).
- Sorteos LA con algún RD ese día: 5405 de 5440 (99.4 %); con RD en (h−1):30 marcado: 5195.
- Prueba de fuga (300 sorteos, se cambia al azar todo RD desde h:30): **SIN FUGA**; control (cambiar RD de (h−1):30 sí mueve las features): 291 casos movidos.
- Métrica: mbits por sorteo = 1000·log2(38·p(ganador)). IC95 por bootstrap de bloques de jornada (2000 remuestreos). Mitades cortadas en cambio de día.

## Descriptivo: ¿LA repite lo que acaba de sacar RD? (O/E contra el ensamble, por hora)

| indicador | observados | esperados (ensamble) | O/E | z |
|---|---|---|---|---|
| RD (h-1):30 | 49 | 138.9 | 0.35 | -7.7 |
| RD antes hoy | 610 | 699.7 | 0.87 | -3.4 |

Por hora (RD (h−1):30 → LA h:00): 9:00 5/12.5, 10:00 6/12.7, 11:00 1/12.5, 12:00 6/12.9, 13:00 5/12.8, 14:00 3/13.0, 15:00 2/12.6, 16:00 3/12.7, 17:00 5/12.4, 18:00 5/12.3, 19:00 8/12.3

## Diagnóstico de alineación horaria (descriptivo, no entra al modelo)

Repeticiones LA h:00 == RD (h+k):30 en desarrollo, contra 1/38. k=0 es RD de h:30 (posterior a LA h:00): aquí solo se mira para ubicar el hueco, nunca se usa para predecir.

| k | RD | n | observados | esperados | z |
|---|---|---|---|---|---|
| -3 | (h-3):30 | 4251 | 91 | 111.9 | -2.0 |
| -2 | (h-2):30 | 4723 | 88 | 124.3 | -3.3 |
| -1 | (h-1):30 | 5195 | 49 | 136.7 | -7.6 |
| +0 | (h+0):30 | 5405 | 30 | 142.2 | -9.5 |
| +1 | (h+1):30 | 4932 | 71 | 129.8 | -5.2 |
| +2 | (h+2):30 | 4459 | 93 | 117.3 | -2.3 |

El hueco se centra entre k=−1 y k=0 (los dos sorteos RD a 30 min de LA h:00) y decae hacia los lados: compatible con horas bien alineadas y con un operador que evita repetir lo reciente de la otra lotería en ambos sentidos. Ojo: en la ventana de descubrimiento (test B, 2026) la dirección RD → LA (lag −1) no apareció en el top 25 (|z| < 1,8): el efecto podría haberse debilitado; la prueba ciega lo dirá.

## Coeficientes

| ajuste | b[RD (h-1):30] | b[RD antes hoy] |
|---|---|---|
| sin cuarto 1 | -1.124 | -0.192 |
| sin cuarto 2 | -0.930 | -0.177 |
| sin cuarto 3 | -1.115 | -0.169 |
| sin cuarto 4 | -1.067 | -0.215 |
| todo dev (descriptivo, dentro de muestra) | -1.064 | -0.188 |

(Referencia: exp(b) es el factor sobre la probabilidad del animal; b = −∞ sería 'nunca repite'.)

## H4 — Δ mbits por sorteo, sonda − ensamble (fuera de muestra)

| esquema | tramo | n | Δ mbits | IC95 | ¿Δ ≥ +5 e IC>0? |
|---|---|---|---|---|---|
| cuartos (principal) | dev completo | 5440 | +12.60 | [+8.13, +16.72] | sí |
| cuartos (principal) | 1ª mitad | 2720 | +14.69 | [+8.60, +20.11] | sí |
| cuartos (principal) | 2ª mitad | 2720 | +10.50 | [+4.20, +16.66] | sí |
| walk-forward | dev completo | 5440 | +11.51 | [+7.59, +15.28] | sí |
| walk-forward | 1ª mitad | 2720 | +12.59 | [+8.00, +16.87] | sí |
| walk-forward | 2ª mitad | 2720 | +10.43 | [+4.21, +16.39] | sí |

Por cuarto (principal): Q1 +10.18, Q2 +19.17, Q3 +11.14, Q4 +9.87
Walk-forward: las primeras 500 filas usan b = 0 (Δ = 0 por construcción).

**H4: PASA** (criterio: Δ ≥ +5 mbits y límite inferior del IC95 > 0 en AMBAS mitades; esquema principal = cuartos).
