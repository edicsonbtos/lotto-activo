# ag01_gbm_ranker: LightGBM con softmax por sorteo, solo y apilado sobre el ensamble_v2

## Qué se probó
Árboles potenciados (LightGBM 4.7, objetivo propio = logit condicional por sorteo: grad p−1[y],
hess p(1−p)) sobre 15 variables causales por (sorteo, animal): hueco en sorteos (última y penúltima
salida), hueco en días, veces hoy/ayer/anteayer, hora, posición en el día, repeticiones del día,
sorteos desde que salió hoy, conteos en ventanas 12/24/36/60/120 (`variables.py`).
- **A (solo)**: sólo esas variables.
- **B (apilado, candidato)**: + log P_ens y rango en el ensamble como variables, e init_score = log P_ens
  (los árboles aprenden una corrección multiplicativa sobre el ensamble).

Ajuste: cross-fitting en 5 bloques contiguos de jornadas de [2000, 9357), 2 días de embargo a cada lado;
nº de árboles por early stopping en el último bloque de entrenamiento y reentreno con los 4 bloques.
Hiperparámetros fijados antes (PREREGISTRO.md). Semilla 20260925, 1 hilo. Corrida completa: 76 s.

## Resultados (copiados de `salida_experimento.txt`; `resultados.json` tiene arnes.evaluar completo)
```
== ag01 A_solo (desarrollo n=7357) ==
mbits: cand +98.2 · ensamble +120.1
Delta mbits -21.85 [-29.63, -13.93] · mitad1 -15.01 [-27.17, -3.49] · mitad2 -28.68 [-39.85, -18.01]
Top-3 11.50% vs 12.89% · Top-5 18.78% vs 20.25% · Top-15 50.22% vs 53.07%
Top-5 escalonado por ficha: +13.57% vs +24.27% · delta -0.11 [-0.17, -0.04]
PASA BARRA DEV: False

== ag01 B_apilado (desarrollo n=7357) ==
mbits: cand +125.9 · ensamble +120.1
Delta mbits +5.87 [+2.95, +8.78] · mitad1 +6.27 [+2.03, +10.55] · mitad2 +5.47 [+1.44, +9.52]
Top-3 12.83% vs 12.89% · Top-5 20.63% vs 20.25% · Top-15 53.13% vs 53.07%
Top-5 escalonado por ficha: +25.49% vs +24.27% · delta +0.01 [-0.02, +0.04]
PASA BARRA DEV: True

== ag01 diag B forward-chaining (bloque 0 = ensamble) (desarrollo n=7357) ==
Delta mbits +3.37 [+1.54, +5.21] · mitad1 +0.86 [-0.28, +2.04] · mitad2 +5.88 [+2.34, +9.38]
Top-5 20.50% vs 20.25%

== ag01 diag recalibración (sólo log P_ens y rango) (desarrollo n=7357) ==
Delta mbits +0.03 [-1.01, +1.05] · mitad1 +0.59 [-0.96, +2.21] · mitad2 -0.52 [-1.84, +0.67]
```
Árboles por bloque (B): 44, 92, 96, 56, 60 → congelado con la mediana, 60 árboles, todas las filas de desarrollo.
Importancia (ganancia) del congelado: hueco1 16 %, hueco2 16 %, ens_logp 14 %, ens_rango 11 %, hora 11 %,
k_dia 10 %, c120 6 %, hueco_dias 5 %, resto < 3 % cada una.

## Lectura
- **B pasa la barra de desarrollo** (+5,87 mbits, IC95 [+2,95, +8,78], ambas mitades > 0 con IC > 0).
- No es recalibración: el control con sólo log P_ens y rango da +0,03. La ganancia viene de
  interacciones de hueco (última y penúltima salida) con hora/posición en el día y con el ensamble.
- El forward-chaining (sólo pasado) también da positivo (+3,37 total; el bloque 0 vale 0 por
  construcción y el bloque 1 se entrena con ~1400 sorteos y sale casi plano); la señal no depende de
  entrenar con el futuro.
- **Pero el dinero casi no se mueve**: Top-5 20,63 % vs 20,25 %, Top-5 escalonado +0,01 [−0,02, +0,04]
  por ficha, Top-3 igual, Top-15 igual. Mismo patrón que el hilo 9: afina probabilidades (mbits)
  más que el orden de arriba.
- A (solo) queda −21,85 mbits: los árboles sin el ensamble no llegan (confirma M-A del hilo 9).
- Sobreajuste in-sample: el modelo congelado evaluado sobre sus propias filas de entreno da +29,6 mbits;
  el número honesto es el cross-fit (+5,87). Espérese en el sellado algo del orden de +3 a +6, o menos.
- Riesgo de era: hora y k_dia pesan 21 %; en el tramo sellado (11 sorteos/día) su distribución cambia
  (no hay hora 11) y los huecos en sorteos equivalen a más tiempo. Puede degradar la corrección.

## Veredicto
Candidato (variante B) que **pasa la barra de desarrollo en mbits** sin mejora significativa en
Top-5 ni en retorno. 2 variantes pre-registradas (A, B) + 2 diagnósticos añadidos antes de la
corrida principal; una prueba de tubería `--rapido` se vio antes (desviación 1 del prerregistro), no
cambió nada. No exploratorio.

## Archivos y reproducción
- `experimento.py` (imprime arnes.informe, guarda `resultados.json`, `P_*.npy`, `modelo_B.txt`)
- `variables.py` (variables causales; verificado: barajar seq[c:] no cambia filas <= c)
- `modelo.py` (class Modelo: ensamble_v2 walk-forward + `modelo_B.txt`); `lotto_eval.prueba_fuga`
  sobre `datos.prefijo(2600)`, desde 2000: (True, None, 0.0). También probado sobre un historial con
  días de 11 sorteos (sin fuga). El ensamble_v2 que carga reproduce la caché (dif. máx. 2,8e-17).

```
cd C:\Users\edics\Downloads\lotto-activo\lotto-activo-motor
$env:PYTHONIOENCODING="utf-8"; python motor_nuevo\ag01_gbm_ranker\experimento.py
```
