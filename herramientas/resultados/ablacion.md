# Tarea 3 - Ablacion del ensamble

Generado por `herramientas/exploracion/ablacion.py`.

- Historial completo **12502 sorteos**; aqui se lee solo hasta la fila 9357: **el tramo de prueba no se abre**.
- Evaluacion en **desarrollo**: 7357 sorteos (2024-03-07 a 2025-12-17).
- Mismos sorteos para todas las variantes (comparacion **pareada**).
- Intervalos por bootstrap de **bloques de dia** (2000 remuestreos, 636 dias).

## 3.1 Linea base: reproduce el ensamble de produccion?

| medida | esta corrida | produccion (`pagina_sorteo.txt`) | coincide |
|---|---|---|---|
| Top-1 | 4.53% | 4.53% | SI |
| Top-3 | 12.89% | 12.89% | SI |
| mbits | +120.07 | +120.07 | SI |


## 3.2 Aporte de cada componente (delta vs linea base)

| variante | Top-1 | Top-3 | delta Top-3 (IC95 bootstrap) | mbits | delta mbits (IC95) |
|---|---|---|---|---|---|
| ensamble completo (linea base) | 4.53% | 12.89% | - | +120.1 | - |
| SIN secuencia_v3 | 4.34% | 12.72% | -0.16 pts [-0.72, +0.39] | +113.3 | -6.7 [-9.5, -4.0] |
| SIN haz_v1 (hazard) | 4.50% | 12.82% | -0.07 pts [-0.25, +0.11] | +120.3 | +0.3 [-0.1, +0.6] |
| SIN intradia_v2 | 4.31% | 12.63% | -0.26 pts [-0.86, +0.35] | +113.1 | -7.0 [-10.3, -3.6] |
| solo secuencia_v3 | 4.27% | 12.65% | -0.23 pts [-0.85, +0.34] | +113.1 | -7.0 [-10.3, -3.5] |
| solo intradia_v2 | 4.23% | 12.45% | -0.43 pts [-1.02, +0.12] | +110.6 | -9.5 [-12.9, -6.2] |
| solo haz_v1 | 4.42% | 12.49% | -0.39 pts [-1.16, +0.35] | +80.4 | -39.7 [-47.3, -31.6] |

## 3.3 Veredicto por componente

**El veredicto se decide con mbits, no con Top-3.** Top-3 tira el 97% de la informacion de cada sorteo (solo mira si el ganador cayo en 3 de 38 casillas) y con n=7357 su error estandar es de ~0.4 puntos: no distingue nada. La log-verosimilitud usa la distribucion completa. Abajo se ve que con Top-3 los tres componentes salen «no significativo», y con mbits dos de ellos se separan con claridad.

| componente | quitarlo cuesta (mbits) | IC95 | quitarlo cuesta (Top-3) | IC95 | por cuarto (mbits) | veredicto |
|---|---|---|---|---|---|---|
| `secuencia_v3` | +6.7 | [+4.0, +9.5] | +0.16 pts | [-0.72, +0.39] | +9.4 +2.4 +4.8 +10.3 | **APORTA** |
| `haz_v1 (hazard)` | -0.3 | [-0.6, +0.1] | +0.07 pts | [-0.25, +0.11] | -0.3 -0.4 -0.0 -0.3 | **NO APORTA** |
| `intradia_v2` | +7.0 | [+3.6, +10.3] | +0.26 pts | [-0.86, +0.35] | -1.4 +9.5 +9.9 +10.0 | **APORTA** |

(«por cuarto» = mbits que se pierden al quitarlo, en cada cuarto del periodo de desarrollo. Signos mezclados = aporte inestable.)

## 3.4 Atribucion de los ~1.2 puntos que el oraculo tabular no explicaba

| modelo | Top-3 | mbits |
|---|---|---|
| mejor oraculo tabular de la fase anterior (con ventaja: ajustado en los mismos datos) | 11.66% | - |
| ensamble completo (linea base) | 12.89% | +120.1 |
| SIN secuencia_v3 | 12.72% | +113.3 |
| SIN haz_v1 (hazard) | 12.82% | +120.3 |
| SIN intradia_v2 | 12.63% | +113.1 |
| solo secuencia_v3 | 12.65% | +113.1 |
| solo intradia_v2 | 12.45% | +110.6 |
| solo haz_v1 | 12.49% | +80.4 |

**La conclusion incomoda: Top-3 no puede atribuir nada.** Cualquier submodelo SOLO ya saca entre 12.45%% y 12.65%%, contra 12.89%% del ensamble completo, y todos los intervalos se solapan. Con este tamano de muestra el Top-3 no distingue el ensamble de sus piezas sueltas.

**Con mbits si se separa:**

- `secuencia_v3`: quitarlo cuesta **+6.7 mbits** -> **APORTA**.
- `haz_v1 (hazard)`: quitarlo cuesta **-0.3 mbits** -> **NO APORTA**.
- `intradia_v2`: quitarlo cuesta **+7.0 mbits** -> **APORTA**.

- `solo haz_v1` se queda en **+80.4 mbits** contra **+120.1** del ensamble: la curva de recencia sola predice el ganador casi igual de bien en Top-3, pero **calibra mucho peor**.

Los pesos que el propio ensamble le asigna a cada submodelo en el ultimo bloque lo dicen igual:

| variante | pesos ajustados |
|---|---|
| ensamble completo (linea base) | `intradia_v2`=0.573, `secuencia_v3`=0.62, `haz_v1`=0.038 |
| SIN secuencia_v3 | `intradia_v2`=0.864, `haz_v1`=0.307 |
| SIN haz_v1 (hazard) | `intradia_v2`=0.579, `secuencia_v3`=0.645 |
| SIN intradia_v2 | `secuencia_v3`=1.08, `haz_v1`=0.139 |
| solo secuencia_v3 | `secuencia_v3`=1.19 |
| solo intradia_v2 | `intradia_v2`=1.049 |
| solo haz_v1 | `haz_v1`=1.081 |

