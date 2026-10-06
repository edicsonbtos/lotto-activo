# M5: las mismas bases de ensamble_v2, combinadas de forma que se adapten más rápido (pre-registro, 2026-10-06)

Escrito ANTES de mirar resultados de combinaciones nuevas.

## Datos y bases
- Submodelos de `ensamble_v2`: intradia_v2, secuencia_v3, haz_v1. Cada uno se predice walk-forward con su propio
  `predecir(A.D, desde)` (el mismo código que usa el ensamble) y se guarda en el scratchpad (`M5_bases.npz`).
- Las combinaciones nuevas usan SOLO filas de las bases anteriores al sorteo (o al día) que se predice.

## Familias candidatas (rejilla fija)
1. **EXP**: pesos log-lineales (L-BFGS, L2 hacia el peso global de ensamble_v2) reajustados cada DÍA sobre el pasado con
   olvido exponencial; vida media de 2, 4, 8 y 16 semanas (84 sorteos por semana); lam ∈ {5, 20}.
2. **DOW/HORA**: pesos por día de la semana y por hora = pesos comunes (EXP) + desviación contraída (L2 κ ∈ {20, 100}).
3. **HEDGE**: fixed-share sobre las 3 bases y la combinación global (expertos que cambian), η ∈ {0,5, 1, 2},
   α ∈ {0,001; 0,01; 0,05}; mezcla de probabilidades y también versión log-lineal.
4. **TEMP**: temperatura dinámica p ∝ q^τ, con τ ajustada cada día sobre una ventana reciente exponencial
   (vida media 2, 4 u 8 semanas), acotada en [0,5; 1,5], encima de la mejor de 1-3 y de la propia combinación global.

## Comparación en igualdad
- Encima de cada candidata se aplican los mismos ajustes que en PROD: `ajuste_primer_sorteo` (×0,272 al primero de ayer,
  ×1,736 al de hace 3 días, si fue a la misma hora) y `ajuste_8am` (exposicion.aplicar_8am) en las filas donde
  PROD los tiene aplicados (lo compruebo reproduciendo PROD desde el ensamble base).
- Métrica: Δmbits contra PROD de `A.evaluar`, IC 90 % por jornadas.

## Elección y umbral de falsación
- Parámetros elegidos SOLO en AJUSTE; en ELECCION se elige la familia (máx. Δmbits medio).
- Se gasta PRUEBA26 solo si la elegida cumple en ELECCION: Δ ≥ +3 mbits con IC 90 % > 0, y Δ ≥ 0 en AJUSTE.
  Si no, veredicto NO MEJORA sin mirar PRUEBA26.
- También se prueba la mezcla p ∝ PROD^(1−w)·M5^w, w ∈ {0,25; 0,5; 0,75; 1}, con w elegido en ELECCION.
- PRUEBA26: MEJORA si Δ > 0 con IC 90 % > 0; DUDOSO si Δ > 0 y el IC cruza 0; NO MEJORA si Δ ≤ 0.
- Fuga: `A.chequear_fuga` sobre la combinación final (función de predicción de una fila).
