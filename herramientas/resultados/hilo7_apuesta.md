# Hilo 7 — H3 (E2, apuesta por valor) y E3 (mesa doble)

Generado por `herramientas/rdint/apuesta.py`. Pre-registro: `herramientas/exploracion/PREREGISTRO_rdint_cruzado.md` (criterios sin cambios). **Solo desarrollo; la prueba ciega no se miró.**

- RD Int: `rdint/cache_dev.npz` (P1 = B1, P0 = B0 = secuencia_v3), 5784 sorteos, 2024-03-01 .. 2025-06-30.
- Lotto Activo: `exploracion/calor_cache.npz` (ensamble_v2 walk-forward), solo filas con fecha en los días dev de RD: 5405 sorteos, 2024-03-07 .. 2025-06-30 (la caché empieza el 2024-03-07).
- Mitades por fecha (la misma que `hilo7_modelo.md`): 1ª ≤ 2024-10-29 < 2ª. Retorno por ficha = neto / fichas apostadas; IC95 por bootstrap de jornadas (2000). Pago 30x.
- E2: v = (30p−1)/29 en los animales con 30p ≥ 1.10; fichas = redondeo(3·v/v_máx del sorteo) acotado a 1..3 (lectura de «proporcionales, redondeadas a 1-3»: el mejor lleva 3). Se muestra también la variante de 1 ficha plana por animal como sensibilidad, no decide.

## RD Int (P1)

| estrategia | dev | 1ª mitad | 2ª mitad |
|---|---|---|---|
| Top-3 plano | +9.3 % [+2.0, +17.6] · 17352 f · neto +1608 | +2.7 % [-8.0, +13.1] · 8676 f · neto +234 | +15.8 % [+5.1, +26.9] · 8676 f · neto +1374 |
| Top-5 escalonado 2-2-2-1-1 | +7.8 % [+1.3, +14.2] · 46272 f · neto +3588 | +0.8 % [-8.8, +9.4] · 23136 f · neto +174 | +14.8 % [+5.7, +24.2] · 23136 f · neto +3414 |
| E2 valor (1..3 fichas) | +9.9 % [+2.0, +17.7] · 40023 f · neto +3957 | -0.3 % [-11.3, +11.3] · 17448 f · neto -48 | +17.7 % [+6.7, +28.8] · 22575 f · neto +4005 |
| E2 valor, 1 ficha plana | +9.7 % [+2.6, +17.0] · 18182 f · neto +1768 | +1.8 % [-8.5, +12.8] · 7723 f · neto +137 | +15.6 % [+5.6, +25.8] · 10459 f · neto +1631 |

- E2 dev: sorteos sin jugar 775 de 5784 (13.4 %); animales por sorteo jugado: media 3.63, mediana 3, máx 15; fichas por sorteo jugado: media 7.99.

- E2 1ª mitad: sorteos sin jugar 588 de 2892 (20.3 %); animales por sorteo jugado: media 3.35, mediana 3, máx 12; fichas por sorteo jugado: media 7.57.

- E2 2ª mitad: sorteos sin jugar 187 de 2892 (6.5 %); animales por sorteo jugado: media 3.87, mediana 4, máx 15; fichas por sorteo jugado: media 8.35.
- Distribución de animales por sorteo (0,1,..,7,8+): 775, 843, 914, 949, 793, 590, 379, 257, 284.
- Diferencia pareada E2 − Top-5 escalonado (pp de retorno por ficha): dev +2.1 [-3.3, +7.7]; 1ª mitad -1.0 [-10.4, +8.2]; 2ª mitad +3.0 [-3.7, +9.8].

## RD Int (P0, referencia)

| estrategia | dev | 1ª mitad | 2ª mitad |
|---|---|---|---|
| Top-3 plano | +5.3 % [-2.5, +12.7] · 17352 f · neto +918 | -3.9 % [-13.6, +6.2] · 8676 f · neto -336 | +14.5 % [+3.0, +25.9] · 8676 f · neto +1254 |
| Top-5 escalonado 2-2-2-1-1 | +4.3 % [-2.0, +10.5] · 46272 f · neto +1968 | -2.4 % [-10.4, +6.3] · 23136 f · neto -546 | +10.9 % [+1.9, +19.8] · 23136 f · neto +2514 |
| E2 valor (1..3 fichas) | +4.5 % [-5.2, +14.3] · 31023 f · neto +1407 | -6.2 % [-18.7, +7.1] · 14260 f · neto -880 | +13.6 % [+0.2, +27.5] · 16763 f · neto +2287 |
| E2 valor, 1 ficha plana | +3.5 % [-4.8, +11.9] · 13365 f · neto +465 | -6.3 % [-18.3, +6.8] · 6147 f · neto -387 | +11.8 % [-0.1, +23.9] · 7218 f · neto +852 |

- E2 dev: sorteos sin jugar 1233 de 5784 (21.3 %); animales por sorteo jugado: media 2.94, mediana 2, máx 12; fichas por sorteo jugado: media 6.82.

- E2 1ª mitad: sorteos sin jugar 800 de 2892 (27.7 %); animales por sorteo jugado: media 2.94, mediana 2, máx 12; fichas por sorteo jugado: media 6.82.

- E2 2ª mitad: sorteos sin jugar 433 de 2892 (15.0 %); animales por sorteo jugado: media 2.94, mediana 3, máx 11; fichas por sorteo jugado: media 6.82.
- Distribución de animales por sorteo (0,1,..,7,8+): 1233, 1191, 1133, 848, 551, 342, 200, 132, 154.
- Diferencia pareada E2 − Top-5 escalonado (pp de retorno por ficha): dev +0.3 [-6.6, +7.1]; 1ª mitad -3.8 [-15.6, +7.2]; 2ª mitad +2.8 [-5.9, +11.6].

## Lotto Activo

| estrategia | dev | 1ª mitad | 2ª mitad |
|---|---|---|---|
| Top-3 plano | +26.7 % [+17.9, +35.5] · 16215 f · neto +4335 | +26.3 % [+13.8, +39.9] · 7698 f · neto +2022 | +27.2 % [+15.7, +39.7] · 8517 f · neto +2313 |
| Top-5 escalonado 2-2-2-1-1 | +21.1 % [+14.5, +28.2] · 43240 f · neto +9140 | +19.5 % [+9.6, +29.4] · 20528 f · neto +4012 | +22.6 % [+13.2, +32.2] · 22712 f · neto +5128 |
| E2 valor (1..3 fichas) | +23.6 % [+16.1, +31.2] · 48282 f · neto +11418 | +21.5 % [+11.2, +32.3] · 23401 f · neto +5039 | +25.6 % [+14.9, +36.5] · 24881 f · neto +6379 |
| E2 valor, 1 ficha plana | +19.1 % [+12.8, +25.5] · 25255 f · neto +4835 | +16.7 % [+7.9, +25.8] · 12496 f · neto +2084 | +21.6 % [+12.0, +31.1] · 12759 f · neto +2751 |

- E2 dev: sorteos sin jugar 70 de 5405 (1.3 %); animales por sorteo jugado: media 4.73, mediana 5, máx 13; fichas por sorteo jugado: media 9.05.

- E2 1ª mitad: sorteos sin jugar 35 de 2566 (1.4 %); animales por sorteo jugado: media 4.94, mediana 5, máx 12; fichas por sorteo jugado: media 9.25.

- E2 2ª mitad: sorteos sin jugar 35 de 2839 (1.2 %); animales por sorteo jugado: media 4.55, mediana 4, máx 13; fichas por sorteo jugado: media 8.87.
- Distribución de animales por sorteo (0,1,..,7,8+): 70, 294, 602, 860, 911, 752, 727, 550, 639.
- Diferencia pareada E2 − Top-5 escalonado (pp de retorno por ficha): dev +2.5 [-0.8, +5.8]; 1ª mitad +2.0 [-2.7, +7.0]; 2ª mitad +3.1 [-1.7, +7.9].

## Veredicto H3

Criterio: retorno por ficha de E2 > el del Top-5 escalonado en AMBAS mitades, en RD Int (con B1) y/o en Lotto Activo, por separado (estimación puntual).

- RD Int (P1): E2 -0.3 % / +17.7 % contra Top-5 +0.8 % / +14.8 % (1ª / 2ª mitad) → **FALLA**.
- Lotto Activo: E2 +21.5 % / +25.6 % contra Top-5 +19.5 % / +22.6 % (1ª / 2ª mitad) → **PASA**.

**H3: PASA** (RD Int (P1) falla, Lotto Activo pasa).

## E3 — mesa doble (Top-5 escalonado)

Horas con ambas loterías en dev: 5405 (473 días). La decisión se toma antes de las h:00 con EV5 = Σ máx(0, 30p−1) del Top-5: LA con su caché, RD con **P0** (no puede conocer LA h:00 al decidir si apostar LA h:00). Si gana RD, el boleto RD se arma con P1 después de las h:00.
Se elige RD en 9.3 % de las horas (1ª mitad 5.7 %, 2ª 12.5 %).

| estrategia | dev | 1ª mitad | 2ª mitad |
|---|---|---|---|
| Solo LA | +21.1 % [+14.6, +28.0] · 43240 f · neto +9140 | +19.5 % [+9.7, +30.1] · 20528 f · neto +4012 | +22.6 % [+13.3, +32.3] · 22712 f · neto +5128 |
| Solo RD (P1) | +6.8 % [+0.2, +13.2] · 43240 f · neto +2930 | -2.5 % [-11.9, +7.0] · 20528 f · neto -518 | +15.2 % [+6.6, +24.7] · 22712 f · neto +3448 |
| Mesa doble: mayor EV5 | +22.9 % [+16.3, +29.4] · 43240 f · neto +9890 | +19.0 % [+9.2, +28.4] · 20528 f · neto +3892 | +26.4 % [+16.7, +35.9] · 22712 f · neto +5998 |
| Ambas | +14.0 % [+9.0, +18.7] · 86480 f · neto +12070 | +8.5 % [+2.1, +15.4] · 41056 f · neto +3494 | +18.9 % [+12.1, +25.8] · 45424 f · neto +8576 |

- Solo RD (P1) − Solo LA (pp): dev -14.4 [-24.1, -5.5]; 1ª mitad -22.1 [-36.9, -8.7]; 2ª mitad -7.4 [-19.1, +4.8].

- Mesa doble: mayor EV5 − Solo LA (pp): dev +1.7 [-1.2, +4.7]; 1ª mitad -0.6 [-4.2, +2.6]; 2ª mitad +3.8 [-0.8, +8.6].

- Ambas − Solo LA (pp): dev -7.2 [-11.7, -2.6]; 1ª mitad -11.0 [-18.0, -4.4]; 2ª mitad -3.7 [-9.8, +2.8].

Diagnóstico, NO válido para jugar (decide con P1, que ya conoce LA h:00):

| estrategia | dev | 1ª mitad | 2ª mitad |
|---|---|---|---|
| Mesa doble decidida con P1 | +20.7 % [+13.9, +27.7] · 43240 f · neto +8960 | +17.1 % [+7.2, +27.1] · 20528 f · neto +3502 | +24.0 % [+14.7, +33.3] · 22712 f · neto +5458 |

## Calibración


### Calibración de P1 (RD Int) por deciles de p (5784 sorteos × 38 animales)

| decil | rango de p | p media (dice) | frecuencia (sale) | casos | sale/dice |
|---|---|---|---|---|---|
| 1 | 0.0005–0.0092 | 0.0062 | 0.0050 | 21980 | 0.81 |
| 2 | 0.0092–0.0190 | 0.0123 | 0.0108 | 21979 | 0.88 |
| 3 | 0.0190–0.0249 | 0.0227 | 0.0244 | 21979 | 1.08 |
| 4 | 0.0249–0.0273 | 0.0262 | 0.0274 | 21979 | 1.05 |
| 5 | 0.0273–0.0291 | 0.0282 | 0.0300 | 21979 | 1.06 |
| 6 | 0.0291–0.0306 | 0.0298 | 0.0315 | 21979 | 1.06 |
| 7 | 0.0306–0.0321 | 0.0313 | 0.0306 | 21979 | 0.98 |
| 8 | 0.0321–0.0338 | 0.0329 | 0.0318 | 21979 | 0.97 |
| 9 | 0.0338–0.0361 | 0.0348 | 0.0354 | 21979 | 1.02 |
| 10 | 0.0361–0.0573 | 0.0387 | 0.0363 | 21980 | 0.94 |
| p∈[0.0367, 0.0450) | — | 0.0390 | 0.0365 | 17717 | 0.94 |
| p∈[0.0450, 0.0600) | — | 0.0469 | 0.0409 | 465 | 0.87 |

### Calibración de la caché de Lotto Activo por deciles de p (5405 sorteos × 38 animales)

| decil | rango de p | p media (dice) | frecuencia (sale) | casos | sale/dice |
|---|---|---|---|---|---|
| 1 | 0.0020–0.0133 | 0.0077 | 0.0073 | 20539 | 0.94 |
| 2 | 0.0133–0.0198 | 0.0175 | 0.0170 | 20539 | 0.97 |
| 3 | 0.0198–0.0224 | 0.0212 | 0.0219 | 20539 | 1.03 |
| 4 | 0.0224–0.0245 | 0.0235 | 0.0237 | 20539 | 1.01 |
| 5 | 0.0245–0.0264 | 0.0254 | 0.0260 | 20539 | 1.02 |
| 6 | 0.0264–0.0284 | 0.0274 | 0.0280 | 20539 | 1.02 |
| 7 | 0.0284–0.0307 | 0.0295 | 0.0309 | 20539 | 1.05 |
| 8 | 0.0307–0.0335 | 0.0320 | 0.0333 | 20539 | 1.04 |
| 9 | 0.0335–0.0379 | 0.0355 | 0.0342 | 20539 | 0.96 |
| 10 | 0.0379–0.0792 | 0.0434 | 0.0409 | 20539 | 0.94 |
| p∈[0.0367, 0.0450) | — | 0.0400 | 0.0381 | 19400 | 0.95 |
| p∈[0.0450, 0.0600) | — | 0.0494 | 0.0450 | 5628 | 0.91 |
| p∈[0.0600, 1.0000) | — | 0.0635 | 0.0441 | 227 | 0.69 |

Las tres últimas filas de cada tabla miran la zona donde apuesta E2 (30p ≥ 1.10).

## Notas

- La caché de Lotto Activo NO es fuera de muestra aquí: es el tramo de desarrollo del proyecto LA (filas 2000..9356, hasta 2025-12-17), donde se eligieron los modelos y los pesos de ensamble_v2. Sus retornos (+20 % o más) son optimistas. Los de RD Int (B1 fijado en el pre-registro, coeficientes walk-forward) no tienen ese problema, aunque B0 se eligió entre 2 candidatos en este dev.
- H3 se decide por estimación puntual, como fija el pre-registro. Las diferencias pareadas E2 − Top-5 tienen IC95 que cruzan 0 en todas las mitades, en RD y en LA.
- La escala de «fichas proporcionales» (el mayor v del sorteo lleva 3) es una lectura mía: el pre-registro no la fija. La variante de 1 ficha plana se muestra solo como sensibilidad.
