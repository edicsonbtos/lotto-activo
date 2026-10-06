# S2 (motor 0): motor nuevo desde cero para el Top-15. PRE-REGISTRO (escrito antes de mirar resultados)
Fecha: 2026-10-06. Arnés: `../../motor2/arnes.py`. Tramos: AJUSTE (jul-25..feb-26) para ajustar, ELECCION
(mar-jun-26) para elegir. PRUEBA26 está contaminada: como mucho una mirada al final, con la versión congelada.

## Motor
- Sin PROD dentro (ni como rasgo ni como init_score). PROD solo para comparar y para la mezcla log-lineal final.
- Sin RD dentro del modelo. RD (h−1):30 se aplica después, al jugar: "quitar y subir" en el Top-N (no a las 8:00).
- Rasgos (todos de sorteos anteriores): los 31 de M4 sin rd1/rd2/hay_rd (retrasos, hoy, ayer, anteayer, d−3,
  frecuencias 12/36/120/360, primer sorteo de ayer y de d−3, número de fecha/fecha+1/hora/mes, hora, dow, día del mes,
  régimen reps/recic de hoy, de este dow en 8 semanas y de 7 días), más: número de fecha−1; par_evita (conteo de
  animales de hoy con los que el candidato está en el decil bajo de lift de pares, 365 días previos al mes, como M6) y
  log-lift medio con los de hoy; q_prior (prior de modo relajado del día, congelado antes de las 8:00) y q_post
  (actualización bayesiana con las repeticiones de hoy).
- Modo relajado: etiqueta blanda por día = P(relajado | repeticiones del día), modelo generativo de dos modos:
  normal (peso de repetir ρ < 1, calibrado con 2025-07..12, AJUSTE) y relajado (azar, ρ = 1), prior 0,2.
  q_prior = logística walk-forward (reajuste mensual) sobre medias con olvido de la etiqueta en este dow (vida 4 sem.)
  y en todos los días (vida 7 días). q_post = Bayes exacto con la secuencia de hoy.
- Walk-forward: reentreno el día 1 de cada mes con las filas anteriores; parada temprana con los últimos 60 días;
  reajuste con todo el pasado y ese nº de árboles. Pesos con olvido 0,5^(edad/vida).
- Hiperparámetros fijos (no se barren): lr 0,05, 15 hojas, min 400 filas por hoja, L2 10, feature_fraction 0,7,
  bagging 0,8, máx. 500 árboles, paciencia 40.

## Objetivos a comparar (todos con vida 180 días)
- (a) A: softmax por sorteo (logit condicional, grad p − y).
- (b) B1: lambdarank con NDCG@15 (truncation 15); P = softmax(a·score), con a ajustado por MV en la ventana de validación.
- (b) B2: pérdida de cobertura del Top-15: ajuste fino de A con una pérdida suave de "el ganador fuera de mis 15"
  (rango suave con sigmoides), pocos árboles, con parada temprana en NDCG/acierto Top-15 de validación.
- (c) C: mezcla de expertos por régimen: experto N (pesos 1 − etiqueta) y experto R (pesos etiqueta), ambos softmax;
  P = (1 − q_post)·P_N + q_post·P_R.
- Después, para el objetivo elegido: vida 90 y 365 (y 180) → se elige en ELECCION.

## Regla de elección (ELECCION)
1. Objetivo y vida: mayor mbits en ELECCION; si dos difieren < 3 mbits, el de mayor Top-15 (con regla RD).
2. Mezcla log-lineal con PROD p ∝ PROD^(1−w)·S2^w, w ∈ {0; 0,25; 0,5; 0,75; 1; 1,25}: el de mayor mbits en ELECCION.
   Se reporta S2 solo (w = 1) y la mezcla.

## Métricas (AJUSTE y ELECCION, IC 90 % por jornadas, diferencias pareadas contra PROD)
- Top-15 (acierto) con la regla RD; mbits y Δ contra PROD.
- Plata, con la regla RD en todas: Top-15 plano (15 fichas), Top-15 ponderado 3-3-3-2-2 + 1×10 (23 fichas),
  Top-5 escalonado 2-2-2-1-1 (8 fichas). Retorno por ficha y fichas netas por día. Comparado con PROD y con M4.

## Veredicto (fijado ahora)
- MEJORA: la versión elegida supera a PROD (ambos con la regla RD) en acierto Top-15 con IC 90 % pareado > 0 en AJUSTE
  y en ELECCION, y además Δ mbits > 0 en los dos tramos.
- DUDOSO: Top-15 por encima de PROD en los dos tramos pero algún IC cruza 0, o mejora solo en la mezcla con PROD.
- NO MEJORA: en otro caso (en particular si en ELECCION el Top-15 queda ≤ PROD).
- PRUEBA26: una sola mirada al final, reportada como "contaminada"; no cambia el veredicto hacia MEJORA por sí sola.
- Si S1 dejó `selector_S1.npz`, se prueba al final con el motor congelado, sin reajustar el selector.
