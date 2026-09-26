# Prerregistro ag03_red_secuencial (ronda 1, 2026-09-25)

Escrito ANTES de correr el experimento principal. Si algo cambia, se anota abajo como desviación.

## Hipótesis
Una red neuronal pequeña, **equivariante a permutación de animales** (los mismos pesos para los 38),
que ve los últimos 72 ganadores codificados por animal (one-hot por retardo + hora + cambios de día),
aprende una política del operador más fina que la del ensamble_v2 (evitar el mismo día, reciclar a
1-2,5 días) y además relaciones de secuencia equivariantes (sucesor/predecesor del último ganador).

## Mecanismo / variables (fila t = sorteo t, solo seq[:t])
Para cada animal i (vector compartido, sin identidad del animal):
- `a[k] = 1[seq[t-k] == i]`, k = 1..72 (one-hot del ganador en cada retardo);
- `a_hoy[k] = a[k] · 1[dia[t-k] == dia[t]]`, k = 1..11 (marca de cambio de día);
- días desde su última aparición dentro de la ventana: one-hot {0, 1, 2, 3, 4+, no aparece} (6);
- relaciones con s1 = seq[t-1]: i fue el sucesor de s1 la última vez que salió s1; i fue su predecesor;
  nº de veces que i siguió a s1 dentro de la ventana (3);
- contexto global (igual para los 38, solo actúa por interacción): hora del sorteo one-hot (12) y
  posición en la jornada one-hot (12).
Nada de numeración del tablero, ni otras loterías, ni la identidad del animal.

## Red
logit_i = g(x_i), g = MLP compartido 1 capa oculta de 32 ReLU → escalar; softmax sobre los 38.
- **V_solo**: logit = g(x).
- **V_apilado (primaria)**: logit = log P_ens + g(x) (el ensamble con peso fijo 1; g empieza en ~0).
Entrenamiento: verosimilitud condicional (log-softmax), Adam lr 1e-3, minilotes de 256 sorteos,
L2 = 1e-4 en los pesos, semilla 0, máximo 40 épocas; parada temprana con validación interna = el
último 15 % (en el tiempo) de las filas de entrenamiento del pliegue (paciencia 4).

## Anti-fuga / ajuste
Cross-fitting en 5 bloques CONTIGUOS de jornadas del tramo [2000, 9357): la fila de un bloque se
predice con la red entrenada con los otros 4 bloques. Variables causales (solo seq[:t]).
Informativo: forward-chaining (bloque b entrenado con bloques < b; bloque 0 = ensamble).
Congelado (modelo.py): nº de épocas = mediana de las del cross-fit, entrenado con todo [2000, 9357).

## Qué la falsaría
V_apilado no cumple la barra: Δmbits >= +3, IC95 inferior > 0, positivo en las dos mitades.
Si V_solo queda muy por debajo del ensamble y V_apilado ~0, la red no ve nada que el ensamble no tenga.
Variantes previstas: 2 (V_solo, V_apilado). Cualquier otra se cuenta y se informa.
