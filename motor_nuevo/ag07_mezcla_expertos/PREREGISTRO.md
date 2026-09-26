# Prerregistro ag07: mezcla de expertos con compuerta dependiente del contexto

Escrito ANTES de correr el experimento principal (2026-09-25). Solo se ha mirado: forma de las cachés,
recuento de `hora` y de sorteos por día (11 o 12). Ningún resultado de mbits.

## Hipótesis
El ensamble_v2 combina intradia_v2, secuencia_v3 y haz_v1 con pesos log-lineales **iguales en todos los
sorteos**. Si la fiabilidad relativa de cada experto cambia con el contexto (p. ej. intradia pesa más tarde en
el día, cuando ya hay muchos animales "quemados"; o cuando el día ya tuvo repeticiones, el operador se
comporta distinto; o cuando la distribución está muy concentrada), una compuerta que haga depender los pesos
del contexto debería ganar verosimilitud.

## Expertos (todos walk-forward, la fila t solo usa seq[:t])
1. intradia_v2, 2. secuencia_v3, 3. haz_v1: predicciones del repo (caché copiada de ag04, calculada sobre
   `prefijo(9357)` desde la fila 1000; ag04 comprobó que reconstruye el ensamble del arnés con |dif| 6e-6).
4. recencia: p_i ∝ h[g_i], g_i = sorteos desde la última salida del animal i (tope 120), h[g] = tasa de
   acierto por hueco con Laplace (+1 / +38), acumulada solo con filas < t (forward, sin parámetros ajustados).

## Contexto x (fijo, sin estandarizar con datos)
- k = nº de sorteos ya celebrados hoy (0..11): x1 = k/11, x2 = (k/11)^2
- r = nº de repeticiones intra-día ya ocurridas hoy (sorteos de hoy cuyo animal ya había salido hoy), x3 = min(r,3)/3
- dispersión: x4 = (log 38 − H)/1, H = entropía (nats) de la combinación geométrica igualitaria de los 3 expertos del repo.

## Variantes (máximo 3, fijadas de antemano)
- **V1 (primaria): log-lineal con pesos por contexto.** z_i = Σ_m (a_m + b_m·x) log p_m(i); P = softmax(z).
  4 expertos × (1 + 4) = 20 parámetros. Penalización L2: λ=5 de a hacia 1/4 (como ensamble.py), λ=20 de b hacia 0.
  Incluye el ensamble (b=0) como caso particular.
- **V2: mezcla lineal verdadera (MoE).** P = Σ_m g_m(x) p_m, g = softmax(c_m + d_m·x) (regresión multinomial
  pequeña, 4 × 5 parámetros, m=1 como referencia), L2 λ=5 sobre todo. Máxima verosimilitud.
- **V3: control de ablación** = V1 sin el experto de recencia (3 expertos × 5).

## Ajuste (anti-fuga)
Cross-fitting en 5 bloques CONTIGUOS de jornadas del tramo [2000, 9357) (bloques por día, ~igual nº de filas).
La fila de un bloque se predice con parámetros ajustados con las filas de los otros 4 bloques más las filas
[1000, 2000) (anteriores al desarrollo, walk-forward). Optimizador L-BFGS, arranque en el ensamble igualitario.
Nada in-sample. Semillas fijas (no hay aleatoriedad salvo el desempate de rankings del arnés).

## Métrica y falsación
`arnes.evaluar(P_V1)`. PASA si Δ ≥ +3 mbits, IC95 inferior > 0 y ambas mitades > 0. Si V1 no pasa, la idea queda
**falsada** (los pesos óptimos no dependen del contexto de forma aprovechable), aunque V2 o V3 pasaran por azar
(se reportarían como exploratorias). Se informan los coeficientes b para ver qué contexto mueve los pesos.

## Modelo congelado
modelo.py: parámetros de V1 ajustados con todas las filas [1000, 9357); corre los 3 submodelos del repo + recencia.
