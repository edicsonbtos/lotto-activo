# ag08 — PRE-REGISTRO (escrito antes de cualquier cálculo; prueba sin mirar)

## Hipótesis
Un logit condicional especializado SOLO en el primer sorteo del día, apilado sobre P_aj (offset log P_aj),
con rasgos por animal de la historia reciente, extrae información que P_aj (ensamble_v2 + ajuste ×0,272/×1,736) no tiene.

## Modelo
q_t(a) ∝ P_aj[t,a] · exp(β·x_{t,a}); softmax sobre los 38 animales; L2 = λ·||β||² (sin intercepto: no identificable).
Rasgos x_{t,a} (todos con datos estrictamente anteriores al sorteo t):
- A. salió en la posición j (j=1..12, orden dentro del día) de AYER (12 indicadores).
- B. ídem de ANTEAYER (12 indicadores).
- C. fue el primer sorteo de hace k días, k=3..10 (8 indicadores; k=1,2 ya están en A1/B1).
- D. hueco en sorteos desde la última aparición, bins: 1-6, 7-12, 13-18, 19-24, 25-36, 37-48, 49-72, 73-108, >108 (ref.).
- E. hueco en días naturales desde la última aparición, bins: 1, 2, 3, 4, 5-6, 7-10, >10 (ref.).
- F. nº de apariciones en los últimos 1 / 3 / 7 días naturales (numéricos).
- G. interacción con la era: copia de A–F multiplicada por (era 8:00) — el bloque compartido + diferencia de era.
Ya probado por otros (no es novedad): primero de hace k=1,2,3,4,7 días y n-ésimo de ayer (barrido de producción, 16 rasgos);
"salió ayer"/"hace 2-3 sorteos" (informe 2026-10-03). Lo nuevo: anteayer por posición, primero de hace 5,6,8,9,10,
huecos en bins, conteos, y el ajuste conjunto regularizado. Se reportará el aporte de cada bloque (ablación en dev).

## Validación (solo dev, 635 primeros sorteos)
- Orden por fecha, 6 bloques contiguos de igual tamaño. Pliegue k=1..5: entrena bloques <k, predice bloque k (rolling origin).
- λ anidado: dentro de cada pliegue externo, λ ∈ {1,3,10,30,100,300,1000} se elige con rolling-origin interno (4 sub-bloques)
  sobre su conjunto de entrenamiento. Así el mbits fuera de pliegue (OOF) es honesto respecto a λ.
- Métrica: mbits por primer sorteo = 1000·mean(log2(q[y]/P_aj[y])) en las filas OOF (bloques 1..5), IC 95 % bootstrap de días (10 000).
  Por era (9:00 / 8:00). Top-5 / Top-15 a las 8:00.

## Candidatos a prueba (máx. 3; uso previsto 1-2)
- C1: modelo completo A–G, λ elegido por rolling-origin en todo dev, entrenado en todo dev, congelado.
- C2: solo rasgos nuevos (B sin B1, C sin k=3,4,7, D, E, F, + interacción era), mismo procedimiento.
Regla de paso a prueba: OOF dev mbits > 0 con IC 95 % que no cruce 0. Si ninguno pasa → NO se mira prueba → NULO.
## Criterio en prueba (261 filas, una sola vez)
p unilateral (bootstrap de días, H0: mbits ≤ 0) < 0,0017 Y mbits OOF del mismo signo en ambas eras de dev → CONFIRMADO;
p < 0,05 → PROMETEDOR; si no → NULO. Vivo (15) solo se reporta.
