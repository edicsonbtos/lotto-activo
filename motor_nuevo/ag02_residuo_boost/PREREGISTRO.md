# ag02_residuo_boost — prerregistro (escrito antes de correr el experimento principal)

Fecha: 2026-09-25. Rama `motor-nuevo`. Solo filas de desarrollo [2000, 9357) vía `arnes`.

## Hipótesis
El ensamble_v2 modela la supresión intradía y el reciclaje por huecos (tiempo desde la última
salida), pero NO mira el *contenido* de los sorteos recientes. Si el operador (o su RNG) deja
huella en las relaciones entre ganadores consecutivos, una corrección residual
`logit_final = log P_ens + X·w` sobre la elección condicional (softmax de los 38 por sorteo)
debería subir la log-verosimilitud.

## Mecanismo candidato
Operador humano o semi-manual que "mira el tablero": evita/prefiere vecinos numéricos del último
ganador, repite el orden de ayer, retoma el último animal de la noche anterior, o repite pares.

## Variables (x_i para el candidato i en el sorteo t; todas usan solo seq[:t])
Tablero numérico (v = número 1..36; 0 y 00 no tienen vecinos), respecto de s1 = seq[t-1],
s2 = seq[t-2] y s3 = seq[t-3]:
- s1 y s2: |v_i − v_s| = 1; |v_i − v_s| ∈ {2,3}; misma columna (v mod 3) ; misma fila (⌈v/3⌉);
  mismo último dígito; misma decena (i ≠ s en todas). -> 12 variables.
- s3: |Δv| = 1; |Δv| ∈ {2,3}. -> 2 variables.
Secuencias / pares:
- i siguió a s1 la última vez que salió s1 (sucesor); i precedió a s1 esa vez (predecesor).
- i siguió al par exacto (s2, s1) la última vez que ese par salió consecutivo.
- i salió en la misma jornada que la ocurrencia anterior de s1 (jornada distinta de hoy).
Ayer (jornada anterior del historial):
- i fue el último sorteo de ayer × (sorteo actual es el primero de hoy / no) -> 2 variables.
- i salió ayer a la misma hora; i salió ayer a la hora ±1.
- i salió ayer en la posición 0-2 / 3-5 / 6-8 / 9-11 del orden de ayer -> 4 variables.
- i siguió ayer a s1 (en ayer, el sorteo posterior al de s1).
Total: 28 variables binarias. Sin interacciones con hora (salvo las indicadas). El ensamble
entra con peso fijo 1 (no se recalibra: la temperatura ya se cerró como ruido).

## Ajuste
- Primario (V1): g lineal, L2 fija λ = 30 sobre la suma de log-verosimilitudes (elegida antes
  de correr; es el valor de la variante exploratoria del hilo 9, no se ajusta aquí).
- Secundario (V2): g = árboles de gradiente (LightGBM, objetivo propio: softmax condicional con
  init log P_ens), fuertemente regularizado: 150 rondas, lr 0,03, num_leaves 4,
  min_data_in_leaf 3000, lambda_l2 50, mismas 28 variables + hora + posición en la jornada.
- Cross-fitting: 5 bloques CONTIGUOS de jornadas del tramo de desarrollo; cada fila se predice
  con parámetros ajustados en los otros 4 bloques. Semillas fijas.
- Sensibilidad (informativa, no elige nada): V1 con λ = 10 y λ = 100.
- Modelo congelado (modelo.py): V1 ajustado con todo el desarrollo (filas < 9357).

## Qué la falsaría
V1 no pasa la barra de desarrollo (Δ ≥ +3 mbits, IC95 inferior > 0, ambas mitades > 0).
Esperado a priori: Δ ≈ 0 (Markov 38×38 y Turing ya dieron ruido). Si V2 pasa y V1 no,
se informa como resultado secundario (2 variantes pre-registradas), con Bonferroni en mente.

## Desviaciones
- (antes de correr) Error de conteo: las variables listadas son 27, no 28 (12 + 2 + 4 + 2 + 2 + 4 + 1).
  La lista no cambia.
