# Hilo 7 — calibración de B1 (RD Internacional)

Generado por `herramientas/exploracion/calibracion_rd.py` el 2026-09-23 a partir de `rdint/cache_todo.npz` (predicciones walk-forward ya calculadas; no se reentrenó nada). IC95 por bootstrap de días (2000 remuestreos para medias, 400 para pendiente y temperatura).

| tramo | sorteos | días | desde | hasta |
|---|---|---|---|---|
| desarrollo | 5784 | 482 | 2024-03-01 | 2025-06-30 |
| prueba (ya vista) | 3237 | 270 | 2025-07-01 | 2026-04-12 |
| réplica | 1800 | 150 | 2026-04-13 | 2026-09-13 |

## 1. ¿Está bien calibrado B1?

### Top-N: probabilidad que el modelo se asigna (esperado) contra lo que pasó (real)

| tramo | Top-N | esperado | real [IC95] | real − esperado [IC95] |
|---|---|---|---|---|
| desarrollo | Top-1 | 4,01 % | 3,56 % [3,11 %, 4,03 %] | -0,45 [-0,89, 0,01] pp |
| desarrollo | Top-3 | 11,52 % | 10,93 % [10,15 %, 11,72 %] | -0,60 [-1,36, 0,19] pp |
| desarrollo | Top-5 | 18,68 % | 17,81 % [16,82 %, 18,83 %] | -0,87 [-1,85, 0,17] pp |
| prueba (ya vista) | Top-1 | 4,39 % | 4,32 % [3,62 %, 5,07 %] | -0,07 [-0,77, 0,68] pp |
| prueba (ya vista) | Top-3 | 12,49 % | 12,05 % [10,90 %, 13,18 %] | -0,45 [-1,58, 0,69] pp |
| prueba (ya vista) | Top-5 | 20,14 % | 19,96 % [18,60 %, 21,35 %] | -0,18 [-1,54, 1,20] pp |
| réplica | Top-1 | 4,26 % | 3,50 % [2,67 %, 4,39 %] | -0,76 [-1,59, 0,11] pp |
| réplica | Top-3 | 12,18 % | 11,39 % [9,94 %, 12,94 %] | -0,79 [-2,25, 0,75] pp |
| réplica | Top-5 | 19,67 % | 17,67 % [15,89 %, 19,39 %] | -2,00 [-3,80, -0,27] pp |
| **prueba + réplica** | Top-1 | 4,35 % | 4,03 % [3,47 %, 4,60 %] | -0,32 [-0,88, 0,26] pp |
| **prueba + réplica** | Top-3 | 12,38 % | 11,81 % [10,91 %, 12,71 %] | -0,57 [-1,47, 0,33] pp |
| **prueba + réplica** | Top-5 | 19,97 % | 19,14 % [18,03 %, 20,26 %] | -0,83 [-1,93, 0,28] pp |
| **los tres juntos** | Top-1 | 4,17 % | 3,78 % [3,45 %, 4,15 %] | -0,39 [-0,72, -0,02] pp |
| **los tres juntos** | Top-3 | 11,92 % | 11,34 % [10,78 %, 11,94 %] | -0,58 [-1,15, 0,02] pp |
| **los tres juntos** | Top-5 | 19,28 % | 18,43 % [17,67 %, 19,17 %] | -0,85 [-1,60, -0,11] pp |

### Pendiente de calibración y temperatura

- **Pendiente logística**: regresión de y (el animal salió o no) sobre logit p, con los 38 pares sorteo × animal. 1 = bien calibrado; < 1 = sobreconfiado (las p extremas deberían estar más cerca de 1/38).
- **Temperatura T (MLE)**: el exponente que maximiza la verosimilitud de P ∝ P1^T. Es la versión multinomial de la misma pendiente; T < 1 = sobreconfiado.

| tramo | pendiente logística [IC95] | T MLE [IC95] | mbits vs uniforme [IC95] |
|---|---|---|---|
| desarrollo | 1,043 [0,957, 1,136] | 1,044 [0,957, 1,138] | 128,0 [114,0, 141,9] |
| prueba (ya vista) | 1,088 [1,007, 1,189] | 1,090 [1,008, 1,194] | 192,4 [174,7, 209,1] |
| réplica | 0,899 [0,800, 1,023] | 0,899 [0,799, 1,023] | 140,5 [113,5, 166,5] |

### Fiabilidad por deciles de p (pares sorteo × animal)

| decil | p media dev | frec. real dev | p media test | frec. real test | p media desc | frec. real desc |
|---|---|---|---|---|---|---|
| 1 | 0,62 % | 0,50 % | 0,42 % | 0,27 % | 0,41 % | 0,42 % |
| 2 | 1,23 % | 1,08 % | 0,89 % | 0,70 % | 0,99 % | 1,04 % |
| 3 | 2,27 % | 2,44 % | 2,05 % | 2,41 % | 2,23 % | 2,41 % |
| 4 | 2,62 % | 2,74 % | 2,52 % | 2,66 % | 2,60 % | 2,50 % |
| 5 | 2,82 % | 3,00 % | 2,82 % | 2,89 % | 2,82 % | 3,17 % |
| 6 | 2,98 % | 3,15 % | 3,04 % | 2,94 % | 3,01 % | 3,14 % |
| 7 | 3,13 % | 3,06 % | 3,25 % | 3,18 % | 3,19 % | 3,36 % |
| 8 | 3,29 % | 3,18 % | 3,45 % | 3,42 % | 3,38 % | 3,08 % |
| 9 | 3,48 % | 3,54 % | 3,70 % | 3,82 % | 3,62 % | 3,52 % |
| 10 | 3,87 % | 3,63 % | 4,18 % | 4,02 % | 4,07 % | 3,65 % |

Cada decil de cada tramo tiene ~12.301 pares. La frecuencia real de un decil tiene un error típico de ~0,1–0,2 pp, así que solo importan diferencias mayores.

### Por puesto (lo que de verdad se juega)

| puesto | p media dev | acierto dev | p media test | acierto test | p media desc | acierto desc |
|---|---|---|---|---|---|---|
| 1º | 4,01 % | 3,56 % | 4,39 % | 4,32 % | 4,26 % | 3,50 % |
| 2º | 3,81 % | 3,46 % | 4,12 % | 3,80 % | 4,03 % | 3,94 % |
| 3º | 3,70 % | 3,91 % | 3,98 % | 3,92 % | 3,89 % | 3,94 % |
| 4º | 3,61 % | 3,44 % | 3,87 % | 4,05 % | 3,79 % | 2,89 % |
| 5º | 3,54 % | 3,44 % | 3,78 % | 3,86 % | 3,70 % | 3,39 % |

## 2. Corrección por temperatura

- **T fijo** ajustado solo en desarrollo (MLE): **T = 1,0445**.
- **T walk-forward** (reajuste cada 250 filas con todo el pasado, mínimo 500 filas): 2024-02-21 → 1,000; 2024-06-26 → 1,071; 2024-10-30 → 1,056; 2025-03-06 → 1,016; 2025-07-10 → 1,046; 2025-11-13 → 1,128; 2026-03-31 → 1,064; 2026-08-09 → 1,026; 2026-08-30 → 1,029.

| tramo | versión | Δ mbits vs P1 [IC95] | pendiente logística [IC95] | T residual [IC95] | Top-3 esp. / real | Top-5 esp. / real |
|---|---|---|---|---|---|---|
| prueba (ya vista) | B1 sin corregir | — | 1,088 [1,007, 1,189] | 1,090 [1,008, 1,194] | 12,49 % / 12,05 % | 20,14 % / 19,96 % |
| prueba (ya vista) | T fijo (dev) | 0,62 [-0,26, 1,38] | 1,042 [0,963, 1,131] | 1,044 [0,964, 1,134] | 12,68 % / 12,05 % | 20,42 % / 19,96 % |
| prueba (ya vista) | T walk-forward | 0,28 [-1,56, 2,07] | 0,993 [0,913, 1,073] | 0,994 [0,913, 1,075] | 12,89 % / 12,05 % | 20,72 % / 19,96 % |
| réplica | B1 sin corregir | — | 0,899 [0,800, 1,023] | 0,899 [0,799, 1,023] | 12,18 % / 11,39 % | 19,67 % / 17,67 % |
| réplica | T fijo (dev) | -1,15 [-2,33, 0,07] | 0,861 [0,753, 0,974] | 0,861 [0,751, 0,974] | 12,36 % / 11,39 % | 19,92 % / 17,67 % |
| réplica | T walk-forward | -1,56 [-2,72, -0,47] | 0,869 [0,748, 0,988] | 0,869 [0,747, 0,989] | 12,30 % / 11,39 % | 19,85 % / 17,67 % |

La temperatura es monótona: **no cambia el orden de los animales**, así que el Top-1/3/5 que se juega y su acierto real son idénticos. Lo que cambia es todo lo que usa el valor de p:

| tramo | versión | regla E2 (30p ≥ 1,10): fichas/sorteo | sorteos sin jugar | retorno E2 esperado | retorno E2 real |
|---|---|---|---|---|---|
| prueba (ya vista) | B1 | 6,04 | 0,7 % | 20,6 % | 20,6 % |
| prueba (ya vista) | T fijo | 6,50 | 0,3 % | 21,4 % | 20,3 % |
| prueba (ya vista) | T walk-forward | 6,93 | 0,2 % | 22,3 % | 18,8 % |
| réplica | B1 | 4,93 | 1,6 % | 19,8 % | 12,7 % |
| réplica | T fijo | 5,35 | 0,8 % | 20,5 % | 11,1 % |
| réplica | T walk-forward | 5,23 | 1,1 % | 20,3 % | 10,5 % |

## 3. ¿Cuánto es realista ganar por ficha?

Retorno por ficha (0 % = ni se gana ni se pierde). 'Esperado' = lo que promete cada versión de p; 'real' = lo que pasó, con IC95 por días.

| tramo | plan | esperado B1 | esperado T fijo | esperado T walk-fwd | real [IC95] |
|---|---|---|---|---|---|
| desarrollo | Top-3 plano | 15,2 % | — | — | 9,3 % [1,7 %, 17,4 %] |
| desarrollo | Top-5 escalonado 2-2-2-1-1 | 13,2 % | — | — | 7,8 % [1,7 %, 13,9 %] |
| prueba (ya vista) | Top-3 plano | 24,9 % | 26,8 % | 28,9 % | 20,5 % [9,7 %, 31,5 %] |
| prueba (ya vista) | Top-5 escalonado 2-2-2-1-1 | 22,4 % | 24,1 % | 26,0 % | 20,0 % [11,7 %, 28,4 %] |
| réplica | Top-3 plano | 21,8 % | 23,6 % | 23,0 % | 13,9 % [-1,1 %, 28,3 %] |
| réplica | Top-5 escalonado 2-2-2-1-1 | 19,4 % | 21,0 % | 20,6 % | 9,0 % [-1,7 %, 20,2 %] |
| prueba + réplica | Top-3 plano | 23,8 % | 25,7 % | 26,8 % | 18,1 % [9,6 %, 26,9 %] |
| prueba + réplica | Top-5 escalonado 2-2-2-1-1 | 21,3 % | 23,0 % | 24,1 % | 16,1 % [9,1 %, 22,6 %] |

## Veredicto

- **Calibración global: bien, sin sobreconfianza demostrada.** La pendiente logística y la temperatura MLE dan 1,04 (dev), 1,09 (prueba) y 0,90 (réplica); ningún IC95 excluye 1 por debajo. En prueba incluso es > 1 (algo *sub*confiado). La hipótesis 'pendiente < 1 con IC que excluye 1' **no se confirma**.
- **Pero la cola alta sí está inflada, un poco.** En los 9 casilleros tramo × Top-N el acierto real queda por debajo de lo esperado; juntando los tres tramos: Top-1 -0,39 pp, Top-3 -0,58 pp, Top-5 -0,85 pp (IC95 del Top-1 y del Top-5 excluyen 0). Es ~4,9 % relativo en el Top-3. El decil 10 de p también queda por debajo en los tres tramos, y en dev y prueba los deciles 1–2 también (los animales 'fríos' salen aún menos de lo que dice el modelo): el error está en los dos extremos en sentidos opuestos, por eso una temperatura única no lo arregla.
- **La temperatura no sirve.** T en dev = 1,044 (> 1: afila, no suaviza). En prueba Δ mbits ≈ 0 (ns); en la réplica empeora (T fijo -1,15, walk-forward -1,56 mbits) y **agranda** la brecha del Top-N (Top-3 esperado sube a ~12,3 % contra 11,39 % real). No se recomienda adoptarla.
- **¿Cambia la jugada?** No: el orden es el mismo, el Top-3 y el Top-5 escalonado son idénticos. Solo cambian las reglas que leen el valor de p (E2 30p ≥ 1,10, la elección de mesa E3 por EV5, un eventual reparto tipo Kelly) y la *expectativa* que se muestra. Con cualquier versión, la regla E2 promete ~+20 % y en la réplica dio 12,7 %: mostrar 'ganancia esperada' a partir de p exagera.
- **Ganancia realista por ficha.** El modelo promete Top-3 23,8 % y Top-5 escalonado 21,3 % (prueba + réplica). Lo realmente obtenido fuera del desarrollo: Top-3 18,1 % [9,6 %, 26,9 %], Top-5 16,1 % [9,1 %, 22,6 %]. Solo la réplica (la única prueba limpia): Top-3 13,9 % [-1,1 %, 28,3 %], Top-5 9,0 % [-1,7 %, 20,2 %]. Cifra prudente para planificar: **~+10 a +15 % por ficha** (no el +20–25 % que sugiere la suma de p), con rachas y meses negativos posibles (el IC95 de la réplica toca 0).
- Nota: 'prueba' ya se miró una vez (hilo 7); nada aquí se ajustó mirando prueba ni réplica, salvo el T walk-forward, que solo usa filas anteriores a cada bloque.
