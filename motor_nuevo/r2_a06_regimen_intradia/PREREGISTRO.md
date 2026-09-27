# r2_a06_regimen_intradia — prerregistro (2026-09-26, escrito ANTES de correr nada con resultados)

## Pregunta
¿La fuerza de la evitación de pares (las 6 transiciones de ag12 V1: s1→i y i→s1 hace 1, 2-7, 8-30 jornadas) y de la
no-repetición dentro del día cambia con (a) la posición en el día k, (b) fin de semana frente a entre semana, (c) días de
12 frente a 11 sorteos?

## Lo que ya se sabe del calendario (mirado antes, SIN resultados)
Desarrollo [2000, 9357) = 2024-03-07..2025-12-17. Días de 11 sorteos (hora 1-11) al principio (~2.900 filas, casi todo
el bloque 0 y el 1), días de 12 (hora 0-11) después. Por tanto "12 frente a 11" = época del horario; la mitad 1 es
casi toda de 11 sorteos. Se tendrá en cuenta al leer las mitades.

## Variables (todas con fila t usando solo seq[:t] y el calendario de t)
- Las 33 de ag12 V1 (rasgos12.py, sin cambios).
- REPD = log1p(nº de veces que el candidato i ya salió HOY antes de t) (no-repetición intradía).
- Grupo G = las 6 transiciones + REPD (7 columnas).
- Indicadores de régimen: MED = 1[k en 4..7], TAR = 1[k >= 8] (k = posición en la jornada, 0 = primer sorteo;
  en k = 0 las transiciones y REPD valen 0); FDS = 1[sábado o domingo]; D12 = 1[el primer sorteo de la jornada es hora 0].

## Modelo
logit = log P_ens + x·w, softmax, L2 λ = 30 (fijo, como ag02/ag12), mismos 5 bloques contiguos de jornada
(ag02 bloques_jornada) para el cross-fit. Se reajusta todo con log P_ens como offset (no se usa P_V1 como offset,
para no mezclar pliegues). Control: con las 33 columnas debe reproducir P_V1.

## Variantes (3, fijadas ahora)
- **VA (primaria)**: 33 + REPD + G×MED + G×TAR (48 variables). Tramo del día.
- VB: 33 + REPD + G×FDS (41). Día de la semana.
- VC: 33 + REPD + G×D12 (41). Días de 12 frente a 11.
Ablación (no es candidata): VR = 33 + REPD (34), para separar la aportación de REPD de la de las interacciones.
Descriptivo (no decide): O/E frente a P_V1 de los candidatos con alguna transición > 0 y de los ya salidos hoy, por régimen.

## Métrica y barra
Δ mbits frente a P_V1 (arnes.evaluar(P, P_ref=P_V1, y)). Pasa si Δ >= +3, IC95 inferior > 0, dos mitades > 0 y
forward-chaining (bloques 1-4) positivo frente a V1 forward reajustado con el mismo código.
Además, para que la interacción cuente como real: Δ(VX − VR) con IC95 > 0 y pesos de interacción con el mismo
signo en los 5 pliegues. Si solo aporta REPD y no las interacciones, el ángulo (heterogeneidad) queda NO.
