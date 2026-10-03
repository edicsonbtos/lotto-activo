# PRERREGISTRO ciego — `gap_bin × gap_prev_ult` (2026-10-02, escrito después del barrido 2 y ANTES de tocar el tramo ciego)

Único sobreviviente del barrido 2 fuera de la familia del control positivo (`eq_fecha`): 366 hipótesis, compuerta 4/4 OOF + q_BH<0,05.
En desarrollo: +3,98 mbits (a=8), IC95 [+1,50; +6,33], OOF por cuartos [+3,7, +4,4, +3,7, +4,1], q_BH = 0,011, peso ajustado w = 0,26903.
(a=1: +3,89 mbits, q 0,027, w 0,26361. Se fija a=8 por tener el mayor aporte en desarrollo.)

## Definición exacta (Lotto Activo, filas globales t = 0..11; índices de animal 0..37 con "0"=0, "00"=1, 1..36 = 2..37)
- `gap` del animal i en la fila t = t − (última fila anterior a t donde salió i); 9999 si nunca. `gap_bin = digitize(gap, [2,3,4,6,9,13,21,38,61,110])` (valores 0..10).
- `gprev[t]` = para el ganador w = seq[t−1]: (t−1) − (fila de la salida anterior de w antes de t−1); 999 si w no había salido antes (0 en t=0).
  `gprev_bin = digitize(gprev, [6,20,50])` (valores 0..3).
- Bucket (fila t, animal i) = `gap_bin[t,i]*4 + gprev_bin[t]`.
- Feature: tasa empírica CAUSAL por bucket: rate(b,t) = (W_b(<t) + 8·(1/38)) / (E_b(<t) + 8), donde E_b(<t) = nº de pares (fila<t, animal) en el bucket b
  (38 por fila) y W_b(<t) = nº de filas<t cuyo ganador cayó en b. F[t,i] = log rate(bucket[t,i], t), restado el promedio de la fila sobre los 38 animales.
  Las cuentas incluyen TODAS las filas desde 0 hasta t−1 (también las del tramo ciego ya ocurridas antes de t).
- Modelo: logit = log P_base[t] + w·F[t], w = **0,26903 FIJO (no se reajusta)**, softmax sobre los 38.

## Prueba ciega (cada agente, UNA vez)
- LA filas [9357, 12511), P_base = `../lotto-activo-motor/motor_nuevo/reciente/P_ens_reciente.npy` (relativo a la raíz del proyecto), y = seq[t].
  Se excluyen del conteo de la métrica los días tocados por `herramientas/correccion_historial_2026-09-29.json` (antes y después).
- Métrica: aporte en mbits = 1000 · media_filas(log2 p_con[y] − log2 p_base[y]); IC por bootstrap de bloques por día (5000 réplicas, semilla 20261002, 95 %).
- **PASA si** mbits > 0 **y** el límite inferior del IC95 > 0 **y** el aporte es > 0 en las dos mitades del tramo (por fechas únicas).
  Si el aporte es positivo pero el IC cruza 0: NO CONCLUYENTE. Si ≤ 0: FALSADA.
- Descriptivo sin veredicto: aporte con a=1 (w=0,26361); diferencia de retorno por ficha del Top-5 escalonado 2-2-2-1-1 (30 por ficha, costo 8) con y sin la feature;
  mismo cálculo en RD Internacional con w fijo 0,26903, P1 de `herramientas/rdint/cache_todo.npz` (tramos 'test'+'desc'), mismas definiciones sobre la secuencia de RD.
- Dos agentes independientes; la hipótesis solo se acepta si PASA en ambos. Aun así, la confirmación definitiva sería el marcador en vivo.
