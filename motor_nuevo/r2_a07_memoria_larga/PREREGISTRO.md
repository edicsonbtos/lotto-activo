# r2_a07_memoria_larga — prerregistro (2026-09-26, escrito ANTES de correr nada)

## Pregunta
Con la base ag12 V1, ¿tiene el operador una memoria SEMANAL (calendario) más allá de lo que ya capturan las ventanas
de pares de ag12 (1, 2-7, 8-30 jornadas)?
- (a) Pares del mismo día de la semana: ¿evita formar el par consecutivo s1→i (o i→s1) que salió EXACTAMENTE hace
  7, 14, 21 o 28 días naturales (el "mismo día de la semana") más que el de desfases vecinos?
- (b) Misma hora, mismo día de la semana: ¿evita el animal que ganó a la misma hora hace 7 días (y 14/21/28)?
- (c) Composición del día: ¿evita completar un par que "copiaría" un día de hace 1-4 semanas con el que hoy ya comparte pares?

Lo ya cerrado que roza esto (no se repite, se usa como contexto): ag08 F1b (misma hora hace 1..7 días frente al
ensamble: |z| < 1,8), sondeo2 de ag12 (misma hora 1/2-7/8-30 frente a ag12: O/E ≈ 1), ag10 (co-ocurrencia del día: nada),
r2_a01 (hora del par: peso ≈ 0), r2_a02 (pares no adyacentes 8-30: nada). Lo nuevo aquí es el alineamiento EXACTO al
día de la semana y su contraste con desfases no naturales (placebo), y la interacción de composición.

## Datos y anti-fuga
Solo filas [2000, 9357) vía arnes. Nada >= 9357, nada de `sellado/`. Fila t usa solo seq[:t] (días pasados completos y
sorteos previos del día). Desfase L = diferencia de `dia` (días naturales, lotto_eval).

## Variables nuevas (por candidato i en el sorteo t; s1 = sorteo anterior del MISMO día; si t es el primero del día,
las de pares valen 0)
- PS  = nº de L ∈ {7,14,21,28} con el par adyacente s1→i o i→s1 en el día d−L (cuenta, 0..8).
- HS1 = [i ganó a la misma hora en el día d−7].
- HS2 = nº de L ∈ {14,21,28} con i ganador a la misma hora en d−L.
Placebo (desfases no naturales, vecinos, misma distribución de edades):
- PP  = igual que PS con L ∈ {6,8,13,15,20,22,27,29} (dividido entre 2 para igualar exposición).
- HP1 = ([misma hora en d−6] + [misma hora en d−8]) / 2.
- HP2 = nº de L ∈ {13,15,20,22,27,29} con i a la misma hora, /2.
Composición:
- CS = suma sobre L ∈ 1..28 de [s1–i adyacentes (cualquier orden) en d−L] × (nº de pares adyacentes no ordenados que
  hoy (hasta t−1) comparte con el día d−L). Se usa log1p(CS).

## Modelo
Reajuste completo como r2_a01: logit = log P_ens + [33 variables de ag12 V1 + nuevas]·w, softmax, L2 λ = 30, cross-fit
en los MISMOS 5 bloques contiguos de jornada (E2.bloques_jornada). Control: el mismo código sin nuevas reproduce P_V1.
Métrica: Δ mbits frente a P_V1 (arnes.evaluar con P_ref = P_V1), Top-15, Top-5, retorno Top-5 escalonado.

## Variantes (3, una sola corrida)
- V1 (PRIMARIA): 33 + PS + HS1 + HS2.
- V2 (PLACEBO, control): 33 + PP + HP1 + HP2. Esperado Δ ≈ 0.
- V3: 33 + log1p(CS).
Informativo: forward-chaining de V1 frente al forward de ag12 V1 (mismo procedimiento); pesos por bloque; y un sondeo
descriptivo O/E frente a P_V1 por desfase exacto L = 1..35 (par s1–i y misma hora), para ver si 7/14/21/28 destacan
sobre sus vecinos.

## Barra y decisión
Candidato solo si V1: Δ >= +3 mbits, IC95 inferior > 0, las dos mitades > 0, forward informativo > 0, **y** además
Δ(V1) − Δ(V2 placebo) con IC95 > 0 (si el placebo da lo mismo, no es memoria semanal sino edad del par, que ag12 ya
mide). V3 se juzga con la misma barra. Si nada pasa: ángulo cerrado.
