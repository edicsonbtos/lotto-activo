# r2_a03_rd_produccion — prerregistro (2026-09-26, escrito ANTES de correr experimento.py)

## Ángulo
Modelo para PRODUCCIÓN que sí usa RD Internacional (h:30), que existe en todo el desarrollo LA
(filas [2000, 9357) = 2024-03-07..2025-12-17; RD desde 2023-09-04). Base a batir: ag12 V1 (`ag12_transiciones/P_V1.npy`).

## Historia previa (honesto: NO es una idea a ciegas)
- H4 (LA usando RD) pasó en desarrollo de hilo 7 y FALLÓ en su prueba ciega (2025-07-01..2026-04-12, +3 mbits, IC cruza 0).
  Ese tramo se SOLAPA con el desarrollo de aquí (2025-07-01..2025-12-17). H4b (2ª mirada) +9,7 mbits sin dinero.
- L3 (LA evita RD (h−2):30): real pero +1,4 mbits sobre el ensamble (hilo 9).
- `ag12_transiciones/sondeo_rd.py`: sobre ag12 V1, LA h:00 repite el animal de RD (h−1):30 70 veces contra 185,8 esperadas
  (O/E 0,38, z −8,5). Pares repetidos en la secuencia intercalada LA/RD: nada (O/E 0,85-1,13).
- Regla de cambio RD→Top-5 ya en vivo (solo lo mostrado).
Por eso el desarrollo aquí es reutilizado: lo que pase solo se confirma con sorteos FUTUROS.

## Variables nuevas (fila t = LA h:00 del día d; solo RD de horas anteriores del MISMO día y pares de días anteriores)
- L1 `rd_h1`: [i == animal de RD (h−1):30 del mismo día] (0 si h = 0 o falta el dato).
- L3 `rd_h2`: [i == animal de RD (h−2):30 del mismo día] (0 si h < 2 o falta).
- PF `par_rdla_1a30`: log1p(nº de días hace 1-30 jornadas en que el par a→i salió como RD (h'−1):30 → LA h':00), a = RD (h−1):30.
- PR `par_lard_1a30`: log1p(nº de días hace 1-30 en que salió LA h':00 = i seguido de RD h':30 = a) (par inverso).
La noche (RD 19:30 → LA 8:00 del día siguiente) NO se usa (descartada en hilo 7).

## Modelo y evaluación (fijados)
Softmax por sorteo, L2 λ = 30 (mismo valor fijo de ag02/ag12), L-BFGS de `ag02_residuo_boost/experimento.py`.
Cross-fit en los MISMOS 5 bloques contiguos de jornada (`bloques_jornada`). Forward-chaining informativo (bloque 0 = referencia).
Métrica: Δ mbits frente a ag12 V1 con `arnes.evaluar(P, P_ref=P_V1, y=y)`, más Top-3/5/15 y Top-5 escalonado.
Barra: Δ ≥ +3 mbits, IC95 inferior > 0, las dos mitades > 0, forward informativo > 0.

## Variantes (máximo 3)
- **VA (primaria):** offset log P_V1 + las 4 variables (L1, L3, PF, PR).
- VB: offset log P_V1 + solo L1 y L3 (los dos mecanismos con razón clara).
- VC: reajuste conjunto desde el ensamble: 33 variables de ag12 + las 4 (control de la pequeña fuga que implica usar
  P_V1 cross-fit como offset, y forma natural para producción).
Diagnóstico (no son variantes): O/E de L1 frente a ag12 V1 antes y después de 2025-07-01 (el tramo donde H4 falló).

## Qué la falsa
Si VA no pasa la barra, RD no aporta sobre ag12 en desarrollo. Si pasa sólo por L1, el resultado es el ya conocido H4b y
lo que decide es el marcador en vivo (la regla de cambio RD→Top-5 ya lo mide).
