# Prerregistro ag09_multi_escala (escrito ANTES de correr el experimento principal, 2026-09-25)

## Hipótesis
La curva de reciclaje del operador (evita repetir el mismo día, recicla con 1-2,5 días de hueco) se puede
estimar como una función SUAVE y multi-escala de la historia de cada animal, con menos varianza que los
bins/submodelos del ensamble_v2. Si el ensamble deja residuo en esa curva, una corrección log-lineal
penalizada sobre log P_ens lo recoge y sube los mbits.

## Mecanismo / modelo
Logit condicional sobre los 38 animales:  z[t,a] = log P_ens[t,a] + f(x[t,a]),  P = softmax(z).
f es aditiva, con bases penalizadas (P-splines / efectos aleatorios gaussianos = ridge):
1. `gap`: B-spline cúbica (12 bases, nudos uniformes) de log(sorteos desde la última salida), tope log(300);
   nunca visto = tope. Penalización de 2.ª diferencia.
2. `sup1`: superficie 12×12 (hora de la última salida × hora actual) activa solo si la última salida fue AYER
   (hueco de 1 día de calendario). Penalización de 1.ª diferencia en filas y columnas.
3. `sup2`: igual para hueco de 2 días.
4. `gd`: hueco en días de calendario, one-hot 0..7 y 8+ (9), ridge (efecto aleatorio).
5. `c3`: veces que salió en los 3 días anteriores (0,1,2,3+), ridge.
6. `hoy`: ya salió hoy (1 parámetro; la regla del mismo día; el ensamble ya la aplica, aquí se recalibra).
7. `animal`: intercepto por animal (efecto aleatorio, ridge).
Total ≈ 352 parámetros. Además ridge mínimo 1e-3 en todo (identificabilidad).
Una sola escala de penalización λ multiplica todas las penalizaciones (ridge + diferencias).

## Ajuste (anti-fuga)
- Variables de la fila t: solo seq[:t] (y hora/día de t, que son calendario).
- Parámetros: CROSS-FITTING en 5 bloques CONTIGUOS de jornadas del tramo [2000, 9357): la fila de un bloque se
  predice con w ajustado en los otros 4. λ ∈ {0.3, 3, 30, 300} elegido DENTRO de los 4 bloques de entrenamiento
  (CV interna por bloques contiguos, log-verosimilitud). Nada in-sample.
- Robustez (secundaria): forward-chaining en 10 bloques contiguos (bloque k usa w ajustado con bloques < k;
  el bloque 0 queda = ensamble).
- Modelo congelado: w ajustado con TODO el desarrollo (filas < 9357), λ por CV de 5 bloques.

## Variantes (pre-registradas, máximo 2)
- **V1 (primaria):** corrección sobre el ensamble, cross-fit, descrita arriba.
- V2 (informativa): el mismo f SIN el ensamble (offset = uniforme), para ver si la curva suave sola se
  acerca al ensamble ("menos varianza"). No es candidato.

## Métrica y barra
arnes.evaluar(P_V1): Δmbits >= +3, IC95 por jornadas con límite inferior > 0, positivo en ambas mitades.

## Qué la falsaría
Δmbits de V1 < +3 o IC95 que toca 0 o una mitad <= 0 => la curva de reciclaje suave no añade nada al ensamble
(ya la captura). También se reporta el forward-chaining; si da <= 0 mientras el cross-fit pasa, se trata como
señal no robusta.
