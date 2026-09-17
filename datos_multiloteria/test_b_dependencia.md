# TEST B — Dependencia cruzada entre loterias

Alineacion por hora del dia; nula empirica por transformacion
(parejas del mismo dia sin alinear, captura solapamiento de
tableros). Combinaciones: 10 pares x 9 lags x 3 transforms = 270.
Umbral duro: z > 4 tras FDR (BH q=0.05).

## Sin alertas: ninguna combinacion supera z > 4 tras FDR.

## Top 25 por |z|
| par | lag_h | transform | n | hits | p_hat | p0 | z | p_fdr |
|---|---|---|---|---|---|---|---|---|
| lottoactivo -> lottoactivordint | +1 | id | 1800 | 9 | 0.0050 | 0.0266 | -5.70 | 3.27e-06 |
| lottoactivo -> lottoactivordint | +0 | id | 1800 | 13 | 0.0072 | 0.0266 | -5.11 | 4.29e-05 |
| lottoactivo -> selvaplus | +6 | pm1 | 865 | 64 | 0.0740 | 0.0504 | +3.16 | 0.14 |
| lottoactivo -> lagranjita | +6 | id | 900 | 43 | 0.0478 | 0.0315 | +2.79 | 0.323 |
| lagranjita -> selvaplus | +0 | id | 1716 | 69 | 0.0402 | 0.0293 | +2.68 | 0.323 |
| lagranjita -> guacharoactivo | +2 | id | 1500 | 10 | 0.0067 | 0.0148 | -2.60 | 0.323 |
| lottoactivordint -> lagranjita | -1 | pm1 | 1800 | 112 | 0.0622 | 0.0490 | +2.59 | 0.323 |
| lottoactivordint -> selvaplus | +1 | id | 1580 | 23 | 0.0146 | 0.0247 | -2.59 | 0.323 |
| lagranjita -> guacharoactivo | +6 | id | 900 | 22 | 0.0244 | 0.0148 | +2.41 | 0.483 |
| lottoactivo -> selvaplus | +0 | id | 1716 | 65 | 0.0379 | 0.0286 | +2.30 | 0.584 |
| lottoactivordint -> lagranjita | +2 | espejo | 1500 | 55 | 0.0367 | 0.0276 | +2.13 | 0.658 |
| lottoactivo -> lottoactivordint | -6 | espejo | 900 | 13 | 0.0144 | 0.0254 | -2.09 | 0.658 |
| lottoactivordint -> guacharoactivo | +0 | id | 1800 | 12 | 0.0067 | 0.0119 | -2.05 | 0.658 |
| lagranjita -> selvaplus | +0 | pm1 | 1716 | 107 | 0.0624 | 0.0516 | +2.02 | 0.658 |
| lottoactivordint -> guacharoactivo | +0 | pm1 | 1800 | 31 | 0.0172 | 0.0246 | -2.02 | 0.658 |
| lottoactivo -> guacharoactivo | -2 | espejo | 1500 | 28 | 0.0187 | 0.0128 | +2.01 | 0.658 |
| selvaplus -> guacharoactivo | -3 | id | 1294 | 27 | 0.0209 | 0.0143 | +2.00 | 0.658 |
| lottoactivordint -> guacharoactivo | +1 | pm1 | 1650 | 28 | 0.0170 | 0.0246 | -2.00 | 0.658 |
| lottoactivo -> lottoactivordint | -2 | pm1 | 1500 | 57 | 0.0380 | 0.0491 | -1.99 | 0.658 |
| lagranjita -> selvaplus | -1 | pm1 | 1573 | 64 | 0.0407 | 0.0516 | -1.95 | 0.691 |
| lottoactivordint -> selvaplus | +6 | pm1 | 865 | 32 | 0.0370 | 0.0514 | -1.91 | 0.695 |
| lottoactivordint -> lagranjita | +0 | espejo | 1800 | 63 | 0.0350 | 0.0276 | +1.91 | 0.695 |
| lottoactivo -> guacharoactivo | +6 | pm1 | 900 | 31 | 0.0344 | 0.0248 | +1.87 | 0.695 |
| lagranjita -> selvaplus | -2 | id | 1430 | 30 | 0.0210 | 0.0293 | -1.87 | 0.695 |
| lottoactivordint -> lagranjita | -6 | pm1 | 1050 | 39 | 0.0371 | 0.0490 | -1.78 | 0.714 |

## Prioridad mision: lottoactivo -> lagranjita

| lag_h | transform | n | hits | p_hat | p0 | z | p_fdr |
|---|---|---|---|---|---|---|---|
| +6 | id | 900 | 43 | 0.0478 | 0.0315 | +2.79 | 0.323 |
| +3 | id | 1350 | 54 | 0.0400 | 0.0315 | +1.78 | 0.714 |
| +2 | id | 1500 | 58 | 0.0387 | 0.0315 | +1.58 | 0.714 |
| -6 | espejo | 900 | 17 | 0.0189 | 0.0272 | -1.54 | 0.714 |
| -2 | id | 1500 | 37 | 0.0247 | 0.0315 | -1.52 | 0.714 |
| +0 | pm1 | 1800 | 110 | 0.0611 | 0.0531 | +1.51 | 0.714 |
| -1 | id | 1650 | 42 | 0.0255 | 0.0315 | -1.41 | 0.776 |
| +3 | pm1 | 1350 | 63 | 0.0467 | 0.0531 | -1.06 | 0.871 |
| -1 | espejo | 1650 | 38 | 0.0230 | 0.0272 | -1.05 | 0.871 |
| -3 | id | 1350 | 36 | 0.0267 | 0.0315 | -1.02 | 0.871 |
| +1 | pm1 | 1650 | 97 | 0.0588 | 0.0531 | +1.02 | 0.871 |
| -3 | pm1 | 1350 | 79 | 0.0585 | 0.0531 | +0.88 | 0.888 |
| -6 | id | 900 | 24 | 0.0267 | 0.0315 | -0.83 | 0.888 |
| -2 | espejo | 1500 | 46 | 0.0307 | 0.0272 | +0.82 | 0.888 |
| -3 | espejo | 1350 | 33 | 0.0244 | 0.0272 | -0.63 | 0.908 |
| -1 | pm1 | 1650 | 82 | 0.0497 | 0.0531 | -0.62 | 0.908 |
| +1 | espejo | 1650 | 41 | 0.0248 | 0.0272 | -0.59 | 0.908 |
| +2 | pm1 | 1500 | 84 | 0.0560 | 0.0531 | +0.49 | 0.908 |
| +1 | id | 1650 | 49 | 0.0297 | 0.0315 | -0.43 | 0.943 |
| -2 | pm1 | 1500 | 83 | 0.0553 | 0.0531 | +0.38 | 0.967 |
| +3 | espejo | 1350 | 39 | 0.0289 | 0.0272 | +0.38 | 0.967 |
| +2 | espejo | 1500 | 39 | 0.0260 | 0.0272 | -0.29 | 0.976 |
| +0 | espejo | 1800 | 47 | 0.0261 | 0.0272 | -0.29 | 0.976 |
| +6 | pm1 | 900 | 49 | 0.0544 | 0.0531 | +0.17 | 0.976 |
| +0 | id | 1800 | 58 | 0.0322 | 0.0315 | +0.17 | 0.976 |
| -6 | pm1 | 900 | 47 | 0.0522 | 0.0531 | -0.12 | 0.976 |
| +6 | espejo | 900 | 25 | 0.0278 | 0.0272 | +0.10 | 0.976 |

### Verificacion anecdota 2026-09-13 (Lotto Activo -> La Granjita)
Coincidencias numero exacto observadas ese dia: numero 16 a las 10:00 -> 11:00 (lag 1h); numero 1 a las 09:00 -> 12:00 (lag 3h); numero 7 a las 15:00 -> 18:00 (lag 3h); numero 27 a las 08:00 -> 14:00 (lag 6h)
Conteo por lag ese dia (0,1,2,3,6h): {0: 1, 1: 1, 2: 0, 3: 2, 6: 1}

Contexto: con 12 sorteos/dia en cada loteria y N=37, el numero
esperado de coincidencias por azar en un dia es ~12*(12/37)≈3.9
por lag util. Ver test_b_dependencia.json para el z global.
