# Tarea 2 (corregida) y Tarea 4 - que mira la politica f

Generado por `herramientas/exploracion/politica_f2.py`.

- Desarrollo `[2000, 9357)` = **7357 sorteos**. Tramo de prueba **intacto**.

## 2.0 Por que la Tarea 2 de la primera pasada estaba mal

1. `hora` y `posicion en la jornada` coinciden en el **61%** de las filas y sus tablas de interaccion salieron casi identicas: son **la misma variable**, no dos hallazgos.
2. Mas grave: `ya salio hoy` es una **funcion determinista** de (hueco, posicion) -- se cumple `salio_hoy <=> hueco <= posicion` en el **100.00%** de las celdas. Asi que «f(hueco) con interaccion de hora» y «f(hueco, salio_hoy)` son **el mismo modelo**.
3. La tabla de `veces-hoy` de la v1 normalizaba contra celdas **estructuralmente imposibles** (hueco>=28 **y** salio hoy: 0 casos en 279566). De ahi salian los multiplicadores de 8.8x. **Eran un artefacto, como el `gcd` del Vector 3.**

Lo que sigue reemplaza esa seccion.

---

## 2.1 El experimento decisivo: f(hueco) contra f(DIA)

Todas son logit condicional sobre los mismos 7357 sorteos. AIC menor gana.

| parametrizacion | que asume | parametros | logver | AIC | delta AIC |
|---|---|---|---|---|---|
| B) f(DIA): salio hoy hace d, si no hueco grueso | la politica tiene estado POR JORNADA | 19 | -26390.5 | 52818.9 | +0.0 |
| C) f(hueco grueso) x momento del dia | modelo saturado de la v1 | 60 | -26372.8 | 52865.6 | +46.7 |
| D) f(DIA) + hueco fino fuera del dia | estado por jornada + recencia entre dias | 72 | -26380.1 | 52904.1 | +85.2 |
| A) f(hueco) 1..60 + 61+ | la politica mira el hueco global | 61 | -26475.2 | 53072.3 | +253.4 |

**Gana: B) f(DIA): salio hoy hace d, si no hueco grueso** (1.0s).  

### 2.2 Las dos curvas de la politica

**(a) El animal YA salio hoy**, hace `d` sorteos:

| d | n pares | tasa | IC95 | multiplicador |
|---|---|---|---|---|
| 1 | 6722 | 0.536% | 0.387-0.741% | **0.20** | 
| 2 | 6059 | 0.941% | 0.727-1.217% | **0.35** | 
| 3 | 5397 | 1.167% | 0.913-1.491% | **0.43** | 
| 4 | 4735 | 0.993% | 0.747-1.317% | **0.36** | 
| 5 | 4093 | 1.051% | 0.781-1.412% | **0.38** | 
| 6 | 3447 | 1.102% | 0.804-1.509% | **0.40** | 
| 7 | 2809 | 1.424% | 1.047-1.933% | **0.51** | 
| 8 | 2181 | 1.651% | 1.195-2.277% | **0.58** | 
| 9 | 1560 | 1.859% | 1.297-2.657% | **0.65** | 
| 10 | 950 | 1.895% | 1.202-2.975% | **0.66** | 
| 11 | 353 | 0.850% | 0.289-2.468% | **0.29** | 

**Cualquier d**: 410 de 38306 = **1.070%** (IC95 0.972-1.178%) = **0.41x** el azar.

**(b) El animal NO salio hoy**, segun su hueco global:

| hueco | n pares | tasa | IC95 | vs azar |
|---|---|---|---|---|
| 1-7 | 16344 | 2.662% | 2.426-2.920% | **1.01x** |
| 8-12 | 26196 | 2.855% | 2.661-3.064% | **1.09x** |
| 13-19 | 36370 | 3.552% | 3.367-3.748% | **1.35x** |
| 20-27 | 31691 | 3.354% | 3.162-3.558% | **1.27x** |
| 28-44 | 46596 | 2.756% | 2.611-2.908% | **1.05x** |
| 45-69 | 39262 | 2.583% | 2.430-2.744% | **0.98x** |
| 70-109 | 26689 | 2.863% | 2.669-3.070% | **1.09x** |
| 110-179 | 12369 | 2.062% | 1.826-2.327% | **0.78x** |
| 180-inf | 5743 | 1.602% | 1.308-1.961% | **0.61x** |

### 2.3 La prueba que separa las dos hipotesis

Para un **mismo hueco corto**, comparar los casos en que esa aparicion previa cae DENTRO de la jornada contra los que caen FUERA (el animal salio ayer al final). Si la politica mirara el hueco, las dos columnas serian iguales.

| hueco | salio HOY: tasa (n) | NO salio hoy: tasa (n) | razon |
|---|---|---|---|
| 1 | 0.536% (6722) | 1.732% (635) | **0.31** |
| 2 | 0.941% (6059) | 3.038% (1251) | **0.31** |
| 3 | 1.167% (5397) | 2.750% (1818) | **0.42** |
| 4 | 0.993% (4735) | 2.155% (2367) | **0.46** |
| 5 | 1.051% (4093) | 2.989% (2911) | **0.35** |
| 6 | 1.102% (3447) | 2.685% (3427) | **0.41** |
| 7 | 1.424% (2809) | 2.694% (3935) | **0.53** |
| 8 | 1.651% (2181) | 2.921% (4417) | **0.57** |
| 9 | 1.859% (1560) | 3.530% (4873) | **0.53** |
| 10 | 1.895% (950) | 2.916% (5282) | **0.65** |
| 11 | 0.850% (353) | 2.453% (5707) | **0.35** |

**Agregado (huecos 1-11)**: salio hoy **1.070%** (n=38306) contra no salio hoy **2.812%** (n=36623). Razon **0.38**, z = **-17.2**, p = 1.69e-66.

---

## Tarea 4 - Oraculo de la politica, walk-forward

f se reajusta cada 250 sorteos **solo con el pasado** y se evalua en el bloque siguiente. Nada de ajustar y evaluar en los mismos datos.

| oraculo (walk-forward) | n | Top-1 | Top-3 | IC95 Top-3 | mbits |
|---|---|---|---|---|---|
| A) f(hueco) | 6857 | 3.51% | 10.31% | 9.61-11.05% | +32.7 |
| D) f(DIA) + hueco fuera del dia | 6857 | 3.51% | 10.35% | 9.66-11.10% | +33.0 |
| E) f(DIA) x cuarto de jornada | 6857 | 3.81% | 10.38% | 9.68-11.13% | -251.9 |

Referencias sobre los mismos sorteos de desarrollo:

| modelo | Top-1 | Top-3 | mbits |
|---|---|---|---|
| azar puro | 2.63% | 7.89% | 0.0 |
| oraculo tabular de la fase anterior (ajustado en los mismos datos) | 4.13% | 11.66% | - |
| `hazard_actual` (produccion) | 3.41% | 10.74% | +47.6 |
| **`ensamble_v2` (produccion)** | **4.53%** | **12.89%** | **+120.1** |

**Techo del oraculo de politica: 10.38% de Top-3.**

El oraculo de f **NO supera** al ensamble (10.38% contra 12.89%). El ensamble ya capturo la politica medible: no queda jugo por este lado.

