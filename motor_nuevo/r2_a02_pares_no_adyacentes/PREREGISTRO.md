# r2_a02_pares_no_adyacentes — prerregistro (2026-09-26, escrito ANTES de correr nada)

## Pregunta
ag12 V1 captura "el operador evita repetir un par CONSECUTIVO reciente" (s1→i en 1-30 días, i→s1 en 1-7).
¿Se generaliza a (a) la misma posición relativa (mismas horas), (b) pares con un sorteo en medio
(desfase 2), (c) la pareja (s1, i) en el mismo día aunque no sea consecutiva (desfase >= 3), con ventanas largas?

## Datos y anti-fuga
Solo desarrollo, filas [2000, 9357) vía arnes (`datos().prefijo(CORTE)`). Nada >= 9357, nada del sellado.
Fila t usa solo seq[:t] (y hora/día de t). Días por índice de jornada (np.unique(dia)), como ag12.
Solo pares dentro de un mismo día pasado; el animal condicionante (s1 o s2) debe ser del mismo día que t.

## Barrido: 6 familias × 4 ventanas de días (1, 2-7, 8-30, 31-90) = 24 pruebas
Conteo por candidato i de veces que el patrón ocurrió en un día pasado con antigüedad en la ventana:
- A  s2→i con un sorteo en medio (desfase exacto 2), mismo sentido.
- B  i→s2 desfase 2 (inverso).
- C  s1 antes que i en el mismo día, desfase >= 3 (no adyacente).
- D  i antes que s1 en el mismo día, desfase >= 3 (inverso no adyacente).
- E  s1→i consecutivo EN LAS MISMAS HORAS (hora(s1)=hora[t-1] y hora(i)=hora[t]): posición relativa idéntica.
- F  s1→i consecutivo en OTRAS horas (complemento de E; E∪F = familia T de ag12).
Estadístico: máscara = conteo >= 1; obs = aciertos del ganador en la máscara; esp = Σ P_V1(máscara);
var = Σ p(1−p); z = (obs−esp)/√var; p bilateral normal. Todo frente a P_V1 (predicción cross-fit de ag12 V1).
Mitad 1 = primeras n//2 filas (como arnes). Benjamini-Hochberg q = 0,05 sobre las 24 en la mitad 1.
Confirmación en mitad 2: mismo signo y p unilateral < 0,05. Sobreviven solo las que cumplen ambas.

## Modelo (solo con sobrevivientes)
- V1 (primaria): logit = log P_V1 + x·w, x = log1p(conteo) de los sobrevivientes, L2 λ = 30, softmax,
  cross-fit con los MISMOS 5 bloques de jornada de ag02 (`bloques_jornada`).
- V2: reajuste conjunto ag12 (33 variables) + sobrevivientes desde log P_ens, cross-fit 5 bloques, λ = 30.
  Su forward-chaining (bloques 1-4) se compara con el forward de ag12 V1 recalculado igual = forward informativo.
- V3 (sensibilidad, siempre se calcula aunque no haya sobrevivientes): V1 con las 24 variables.
  Se reporta como exploratoria; no puede ser candidata si ninguna variable sobrevive al barrido.
Si no sobrevive ninguna: el veredicto es NO (V1 = V2 = ag12 V1, Δ = 0 por definición) y se informa V3.

## Barra (frente a ag12 V1)
Δ >= +3 mbits, IC95 inferior > 0, las dos mitades positivas, forward informativo positivo. Se imprime Top-15.
Máximo 3 variantes (V1, V2, V3).
