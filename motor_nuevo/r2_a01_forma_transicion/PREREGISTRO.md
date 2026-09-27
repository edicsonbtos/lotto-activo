# r2_a01_forma_transicion — prerregistro (2026-09-26, escrito ANTES de correr nada en esta carpeta)

## Pregunta
ag12 V1 mide "el operador evita repetir un par consecutivo reciente" con 6 ventanas fijas en JORNADAS
(s1->i y i->s1 hace 1, 2-7, 8-30). ¿Queda señal si la forma se refina: edad en SORTEOS, decaimiento
exponencial continuo, número de repeticiones del par, y hora en que ocurrió?

Antecedente honesto: la V2 exploratoria de ag12 (8 ventanas más finas, 16 variables) dio −2,1 mbits frente a V1.
Eso sugiere que refinar la forma de la ventana aporta poco. Expectativa previa: Δ entre 0 y +3 mbits.

## Base y métrica
- Referencia: P_ref = ag12_transiciones/P_V1.npy (cross-fit, 7357x38), y = arnes.base()[1].
- Métrica primaria: arnes.evaluar(P_cand, P_ref=P_V1, y) → Δmbits frente a ag12 V1, IC95 por bootstrap de jornadas.
- Barra: Δ >= +3 mbits, IC95 inferior > 0, las dos mitades > 0, forward-chaining (informativo) > 0.
- Datos: solo filas [2000, 9357) (datos().prefijo(CORTE)). Nada del sellado ni de filas >= 9357.

## Modelo (sin fuga)
Para no depender del offset cross-fit de P_V1 (que usa el bloque de prueba al entrenar las otras filas), el candidato
se reajusta ENTERO con los mismos 5 bloques de jornada (ag02 bloques_jornada) y el mismo λ=30:
logit = log P_ens + x·w, softmax por sorteo, L2 λ = 30, x = las 33 variables de ag12 V1 + variables nuevas.
Como anida a V1, solo puede ganar lo que las ventanas no capturan.

Variables nuevas (fila t usa solo seq[:t]; solo si s1 = seq[t-1] es del mismo día que t, si no valen 0):
- EF(h) = log1p( Σ_{ocurrencias pasadas de s1->i dentro del día} 2^(−a/h) ), a = edad en SORTEOS (t − índice del
  segundo elemento de la ocurrencia).
- ER(h) = lo mismo para la inversa i->s1.
- Vidas medias h_f (para EF) y h_r (para ER) elegidas DENTRO de cada pliegue de entrenamiento por verosimilitud
  penalizada de entrenamiento, rejilla {6, 12, 24, 48, 96, 192} sorteos (≈ 0,5 a 17 jornadas). 36 pares.
  El pliegue de prueba no interviene en la elección.

## Variantes (máximo 3; la primaria es la única que decide)
- **A (PRIMARIA):** 33 de V1 + EF(h_f) + ER(h_r), edad en sorteos, h por pliegue.
- B (sensibilidad, repeticiones y hora): A + 2 variables:
  N2 = log1p(max(0, nº de ocurrencias de s1->i en las últimas 30 jornadas − 1)) (¿pesa más un par repetido varias veces?),
  HM = log1p(Σ 2^(−a/h_f) solo sobre ocurrencias de s1->i cuyo segundo elemento fue a la MISMA hora que t).
- C (sensibilidad, reemplazo): 27 de ag02 + EF + ER (sin las 6 ventanas): ¿la forma continua sustituye a las ventanas?
  (edad en sorteos, h por pliegue igual que A).

Se reporta además: forward-chaining de A (bloque 0 = P_V1), Top-3/5/15 y retorno del Top-5 escalonado, las h elegidas
por pliegue y los pesos.

## Qué la falsa
Si A no cumple la barra, la forma de ventanas de ag12 V1 se queda y el ángulo se cierra. B y C no pueden rescatar el
resultado (solo informan); si B o C superan la barra y A no, se declaran exploratorias.
