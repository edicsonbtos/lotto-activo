# r2_a05_anti_patron_numerico — prerregistro (2026-09-26, escrito ANTES de correr nada)

## Pregunta
¿El operador evita patrones en los NÚMEROS (1..36) que ag02/ag12 no miden? ag02 ya tiene, para s1 y s2 por separado:
vecino ±1, ±2-3, columna, fila, dígito final, decena (y vecinos de s3). Aquí solo entran relaciones que ag02 NO tiene.

## Números
Índice 0 = "0", 1 = "00", 2..37 = 1..36. Igual que ag02, 0 y 00 no tienen número: toda variable numérica vale 0 si
el candidato i o el animal de referencia (s1, s2, s3) es 0/00. s1, s2, s3 = sorteos t−1, t−2, t−3, **exigidos del mismo
día que t** (la noche corta la secuencia). Fila t usa solo seq[:t].

## Variables (11, fijadas aquí)
1. `prog_arit`: v_i − v_s1 = v_s1 − v_s2 (≠ 0): i continúa una progresión aritmética (mismo salto con signo).
2. `mono3`: s2 < s1 < i o s2 > s1 > i (i alarga una racha creciente/decreciente de 3).
3. `mono4`: s3 < s2 < s1 < i o al revés (racha de 4).
4. `dif_hoy`: log1p(nº de pares consecutivos de HOY, antes de t, con el mismo salto con signo v_b − v_a = v_i − v_s1).
5. `difabs_hoy`: igual con el salto absoluto |v_i − v_s1|.
6. `dif_30d_z`: pares consecutivos (dentro del día) de las jornadas 1-30 anteriores con el mismo salto con signo:
   (observado − esperado)/sqrt(esperado), esperado = N_pares · (36 − |d|)/(36·35) (corrige que los saltos cortos son
   más comunes por construcción).
7. `term_s1s2`: v_i, v_s1 y v_s2 con el mismo dígito final (interacción; ag02 solo tiene los dos efectos sueltos).
8. `term_hoy`: log1p(nº de sorteos de hoy anteriores a t−2 con el mismo dígito final que i) (terminaciones repetidas
   en el día, sin s1 y s2 que ya mide ag02).
9. `paridad3`: i, s1 y s2 con la misma paridad.
10. `color3`: i, s1 y s2 del mismo color de ruleta (rojos 1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36). ag02 usa la
    disposición de ruleta (columna, fila), así que el color es la relación de tablero que falta.
11. `espejo`: v_i + v_s1 = 37.

## Etapa 1 — barrido (solo sobre ag12 V1)
Para cada variable f, en la mitad 1 de desarrollo (primeras n//2 filas, igual que arnes): u_t = x[t, y_t, f] − Σ_i P_V1[t,i]·x[t,i,f];
z = Σu / sqrt(Σ_jornada (Σu)^2) (varianza robusta por jornada). p bilateral normal. **Benjamini-Hochberg q = 0,05** sobre
las 11. Las que sobrevivan se confirman en la mitad 2: mismo signo y p unilateral < 0,05. Se reporta O/E = Σx[t,y]/ΣE_P[x].

## Etapa 2 — modelo (Δ mbits FRENTE A ag12 V1)
logit = log P_V1 + x·w, softmax, L2 λ = 30 (fijo, como ag02/ag12), cross-fit en los MISMOS 5 bloques contiguos de jornada
(`ag02_residuo_boost/experimento.py: bloques_jornada`), y forward-chaining informativo (bloque 0 = P_V1).
- **VA (primaria):** solo las variables que sobreviven el BH de la mitad 1 (y se confirman en la mitad 2). Si ninguna
  sobrevive, VA = P_V1 (Δ = 0) y el ángulo queda cerrado.
- **VB (sensibilidad):** las 11 variables, λ = 30.
Máximo estas 2 variantes (una tercera solo como exploratoria, anunciada como tal).

## Barra (VA)
Δ ≥ +3 mbits sobre ag12 V1, IC95 inferior > 0, las dos mitades positivas, forward-chaining positivo. Se imprimen Top-5,
Top-15 y el Top-5 escalonado.

## Limitaciones conocidas de antemano
- P_V1 es cross-fit; corregirlo con los mismos bloques deja una fuga menor (los pesos de V1 en el bloque j vieron el bloque k).
- La selección se hace con la mitad 1 y el cross-fit incluye esas filas: la mitad 2 es la parte limpia.
- No queda tramo ciego histórico: lo que pase solo se confirma con sorteos futuros.
