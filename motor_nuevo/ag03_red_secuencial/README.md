# ag03_red_secuencial: red neuronal secuencial equivariante (ronda 1)

**Veredicto: NO pasa la barra de desarrollo.** La red apilada sobre el ensamble da +2,05 mbits con un IC95
que cruza el 0 y la mitad 1 no es significativa. Sola, pierde 50 mbits contra el ensamble. La red no
ve nada robusto que el ensamble_v2 no tenga ya. No es candidato.

## Qué se probó (prerregistro en `PREREGISTRO.md`, escrito antes de correr)
MLP compartido por los 38 animales (1 capa oculta de 32 ReLU → logit, softmax sobre 38). Los mismos pesos
sirven para todos, así que la identidad del animal no importa. Entradas por animal (116): one-hot del
ganador en los retardos 1..72, esa marca solo si es del mismo día (retardos 1..11), días desde su última
aparición {0,1,2,3,4+,nunca}, si fue sucesor o predecesor de s1 en la ocurrencia anterior de s1, nº de
veces que siguió a s1 en la ventana, y la hora y la posición en la jornada (one-hot, globales).
Adam lr 1e-3, lotes de 256, L2 1e-4, semilla 0, parada temprana con el último 15 % del entrenamiento.
Cross-fitting en 5 bloques contiguos de jornadas de [2000, 9357).

## Resultados (salida exacta de `experimento.py`, n=7357)
```
== ag03 V_apilado (primaria) ==
mbits: cand +122.1 · ensamble +120.1
Delta mbits +2.05 [-0.30, +4.50] · mitad1 +1.11 [-2.12, +4.38] · mitad2 +3.00 [-0.40, +6.44]
Top-3 13.31% vs 12.89% · Top-5 20.88% vs 20.25% · Top-15 53.05% vs 53.07%
Top-5 escalonado por ficha: +28.19% vs +24.27% · delta +0.04 [+0.01, +0.07]
PASA BARRA DEV: False

== ag03 V_solo ==
mbits: cand +70.0 · ensamble +120.1
Delta mbits -50.04 [-59.63, -40.35] · mitad1 -39.26 [-52.93, -25.77] · mitad2 -60.82 [-74.69, -47.34]
Top-3 10.52% vs 12.89% · Top-5 17.67% vs 20.25% · Top-15 50.01% vs 53.07%
Top-5 escalonado por ficha: +5.72% vs +24.27% · delta -0.19 [-0.25, -0.12]
PASA BARRA DEV: False

== ag03 V_apilado forward-chaining (informativa; bloque 0 = ensamble) ==
mbits: cand +119.1 · ensamble +120.1
Delta mbits -0.99 [-4.24, +2.38] · mitad1 -0.94 [-4.91, +2.84] · mitad2 -1.04 [-6.18, +4.17]
Top-3 12.71% vs 12.89% · Top-5 19.95% vs 20.25% · Top-15 53.13% vs 53.07%
Top-5 escalonado por ficha: +22.49% vs +24.27% · delta -0.02 [-0.06, +0.02]
PASA BARRA DEV: False
```
Épocas de la parada temprana (apilado): 5, 6, 8, 7, 6.

Lectura: el Δ retorno Top-5 de +0,04 [+0,01, +0,07] en el cross-fit **no** se sostiene en forward-chaining
(−0,02), y la métrica primaria (mbits) no pasa. No lo tomo como señal. Lo más probable es que el poco
efecto que queda venga de la variable "sucesor de s1" (el ganador es sucesor de s1 en el 1,66 % de los
sorteos, contra 2,6 % esperado), que ag02 ya captura mejor con variables explícitas.

Variantes: 2 pre-registradas (V_apilado, V_solo) y 1 diagnóstica (forward-chaining). No se ajustó nada
después de ver el resultado. No hubo desviaciones del prerregistro, salvo el nº de variables: 116 y no 118.

## Modelo congelado y fuga
- `congelar.py`: entrena V_apilado con todo [2000, 9357), 6 épocas (la mediana del cross-fit), y guarda
  `parametros.npz`.
- `modelo.py`: `Modelo` = ensamble_v2 walk-forward del repo más la red congelada. Admite jornadas de 11 o 12 sorteos.
- `prueba_fuga.py`: `lotto_eval.prueba_fuga(prefijo(2600), desde 2000)` da `(True, None, 0.0)`. El ensamble
  recalculado difiere de la caché en 1,2e-6 como máximo (la caché es float32).

## Reproducir
```
cd motor_nuevo/ag03_red_secuencial
set PYTHONIOENCODING=utf-8 & set OPENBLAS_NUM_THREADS=1
python experimento.py    # ~2 min, escribe resultados.json, salida_experimento.txt y P_apilado.npy
python congelar.py       # parametros.npz
python prueba_fuga.py
```
