# r2_a08_comodin — prerregistro (2026-09-26, escrito ANTES de correr cualquier cosa con resultados)

## Hipótesis: "lista negra de pares compartida entre juegos"
ag12 mostró que Lotto Activo (LA, h:00) evita repetir un par consecutivo propio reciente (s1→i visto hace 1-30 jornadas,
i→s1 hace 1-7). El hilo 7 mostró además que el operador mira el OTRO juego que opera: LA h:00 evita el animal de
RD Internacional (h−1):30 (O/E 0,38) y RD evita el de LA. Es decir, el filtro anti-repetición del operador es
**multi-juego**. Si el filtro de pares es una misma lista del operador, LA también debería evitar formar el par
s1→i cuando ese par salió como consecutivo **dentro de RD** (RD h':30 → RD (h'+1):30) en días recientes.

Razón clara: un solo operador, un solo control de "que no se repita lo que se ve en la tabla"; los apostadores
usan tablas de "qué sale después de X" que mezclan los dos juegos del mismo operador.

## Por qué es nueva (nadie la probó)
- ag02/ag10/ag12/r2_a01: pares consecutivos **de LA** solamente.
- `ag12_transiciones/sondeo_rd.py`: pares de la secuencia INTERCALADA (LA h → RD h:30 y RD h:30 → LA h+1). Los pares
  RD→RD (medio día de separación 2) quedan fuera de ese diccionario.
- r2_a03_rd_produccion: animal de RD (h−1):30 y (h−2):30, y pares cruzados RD(h'−1):30→LA h' / LA h'→RD h':30. No usa
  los pares internos de RD.
- r2_a02: pares no adyacentes de LA. Hilo 8: LARD (otro operador) independiente. Hilo 9: reciclaje de ANIMALES entre
  juegos de días anteriores (O/E 1,00), no de PARES.
Distinta de los otros 7 ángulos de la ronda (forma, no adyacentes, RD en producción = animal de RD, Top-15, numérico,
intradía, memoria larga).

## Variables (fila t = LA h:00 del día d; s1 = LA anterior del mismo día; en el primer sorteo del día valen 0)
Solo pares RD de jornadas ANTERIORES (edad >= 1 jornada, jornada = índice de día de LA como en ag12; un día RD sin
LA se ignora). Nada de RD del día d ni posterior. RD se lee solo hasta la última fecha del desarrollo (2025-12-17).
- RF1/RF2/RF3 = log1p(# veces que el par s1→i salió consecutivo en RD hace 1 / 2-7 / 8-30 jornadas)
- RR1/RR2/RR3 = log1p(# veces que i→s1 salió consecutivo en RD, mismas ventanas)
(mismas ventanas y forma que las 6 de ag12, para que la comparación sea limpia).

## Modelo
Reajuste completo (no P_V1 como offset, para no heredar fuga del cross-fit): logit = log P_ens + x·w, softmax por
sorteo, L2 λ = 30, funciones de ag02 (`ajustar_lineal`, `cross_fit`, `forward`), los MISMOS 5 bloques de jornada
(`bloques_jornada`). Control obligatorio: con las 33 variables de V1 se reproduce P_V1 (dif. máx. < 1e-6).

Variantes (3, fijadas ahora):
- **V1 (primaria):** 33 de ag12 V1 + RF1-3 + RR1-3 (39 variables).
- V2 (lista única): 27 de ag02 + 6 variables AGRUPADAS = log1p(conteo LA + conteo RD) por ventana y sentido
  (si la lista es la misma, el peso debería ser común).
- V3 (parsimoniosa): 33 de V1 + 2 variables RF(1-30) y RR(1-7) sumadas en una ventana cada una.

## Métrica y barra (frente a ag12 V1 = P_V1.npy)
arnes.evaluar(P_cand, P_ref=P_V1, y). Pasa si: Δ >= +3 mbits, IC95 inferior > 0, mitades positivas, y forward-chaining
informativo positivo (Δ del forward de la variante frente al forward de V1 con el mismo procedimiento, bloques 1-4).
Se imprime Top-3/5/15 y Top-5 escalonado.

## Diagnóstico descriptivo (no decide)
O/E crudo frente a P_V1 de las máscaras "s1→i visto en RD" y "i→s1 visto en RD" por ventana (1, 2-7, 8-30 y, como
placebo, 31-90), por mitades. Esperado bajo H0: O/E ≈ 1.

## Qué la falsa
V1 < +3 mbits o IC que cruza 0 → la lista de pares NO es compartida (o lo es con peso despreciable); el ángulo se cierra.
