# Prerregistro ag01_gbm_ranker (ronda 1, 2026-09-25)

Escrito ANTES de correr el experimento principal. Cambios posteriores van en "Desviaciones".

## Hipótesis
El ensamble_v2 es log-lineal (y el techo del hilo 9 fue una elección condicional LINEAL en tramos).
Un modelo de árboles potenciados puede encontrar INTERACCIONES no lineales entre hueco, hora,
veces hoy/ayer y conteos (p. ej. "hueco corto sólo penaliza a primera hora", "reciclaje a 1-2,5 días
depende de cuántas repeticiones lleva el día") que el log-lineal no ve.
Razón nueva frente a lo cerrado: el techo M-A/M-B del hilo 9 era lineal en one-hots, sin interacciones
de orden > 2 salvo hueco × franja y veces-hoy × franja. Aquí los árboles eligen las interacciones.

## Mecanismo / modelo
- Unidad: (sorteo t, animal i), 38 filas por sorteo. Objetivo: **softmax condicional por sorteo**
  (logit condicional) implementado como objetivo propio de LightGBM: grad = p − 1[y], hess = p(1−p),
  con p = softmax de la puntuación dentro del sorteo.
- Variables (todas con seq[:t] solamente): hueco en sorteos desde la última y la penúltima salida
  (tope 400), hueco en días desde la última salida (tope 30), veces hoy / ayer / anteayer, hora,
  posición k dentro del día, sorteos hoy ya jugados, repeticiones del día (sorteos hoy − animales
  distintos hoy), conteos en ventanas 12/24/36/60/120, sorteos desde que salió el animal HOY (o tope).
- Variante A ("solo"): sólo esas variables, puntuación inicial 0.
- Variante B ("apilado", CANDIDATO PRINCIPAL): además log P_ens y rango del animal en el ensamble como
  variables, y puntuación inicial (init_score) = log P_ens: los árboles aprenden una corrección
  sobre el ensamble.
- P_ens = caché walk-forward del ensamble_v2 (arnes.base()).

## Ajuste (anti-fuga)
- Datos: sólo filas [2000, 9357) (7357 sorteos). Nada >= 9357, nada anterior a 2023-09-04 ni RD.
- Cross-fitting en 5 bloques CONTIGUOS de jornadas (días enteros). La fila del bloque b se predice
  con un modelo entrenado sólo con los otros 4 bloques, dejando fuera además 2 días de embargo a cada
  lado del bloque b.
- Número de árboles: dentro del entrenamiento, el último bloque de entrenamiento en el tiempo (sin el
  bloque b) hace de validación con early stopping (paciencia 50, máx. 1000); luego se reentrena con
  los 4 bloques con ese número de árboles.
- Hiperparámetros FIJOS de antemano: num_leaves 15, learning_rate 0.03, min_data_in_leaf 400,
  feature_fraction 0.8, bagging_fraction 0.8 (freq 1), lambda_l2 10, max_bin 63, semilla 20260925,
  num_threads 1.
- Modelo congelado (modelo.py): variante B entrenada con TODAS las filas de desarrollo con el nº de
  árboles = mediana de los 5 del cross-fitting.

## Métrica y barra
- Primaria: arnes.evaluar(P_cand): Δmbits vs ensamble. Pasa si Δ >= +3, IC95 inferior > 0 y ambas
  mitades > 0 (barra del prerregistro común).
- Secundarias: Top-5, Top-5 escalonado, Top-3, Top-15.
- Se prueban 2 variantes pre-registradas (A y B). Sólo B puede ser candidato; A es diagnóstico.

## Qué la falsaría
- B con Δ < +3 mbits o IC que cruza 0 o una mitad <= 0 => no hay interacciones no lineales útiles
  más allá del ensamble; se reporta "no pasa".
- A muy por debajo del ensamble (como M-A del hilo 9) confirma que el ensamble ya captura lo aprendible.

## Desviaciones
1. (antes de la corrida principal) Se corrió una prueba de tubería `--rapido` (máx. 60 árboles,
   paciencia 10) y SE VIERON sus números: A −27,95 mbits; B +6,15 [+3,62, +8,64], mitades +6,61 / +5,68.
   No se cambió ningún hiperparámetro ni variable por ello. La corrida principal usa exactamente lo
   pre-registrado arriba (máx. 1000 árboles, paciencia 50).
2. Por lo sospechoso de ese +6, se añaden ANTES de la corrida principal dos diagnósticos (no son
   variantes candidatas, no se elige nada con ellos):
   a) forward-chaining: los bloques 1..4 se predicen con modelos B entrenados SÓLO con bloques
      anteriores (el bloque 0 queda con el ensamble, Δ=0) — descarta fuga por entrenar con el futuro;
   b) control de recalibración: B sin variables propias (sólo log P_ens y rango, init_score = log P_ens),
      mismo cross-fitting — mide cuánto del efecto es mera recalibración del ensamble.
   Se comprobó además que las variables son causales (barajar seq[c:] no cambia filas <= c).
