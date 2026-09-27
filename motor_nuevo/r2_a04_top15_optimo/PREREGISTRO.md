# r2_a04_top15_optimo — prerregistro (2026-09-26, escrito ANTES de correr nada)

## Pregunta
Con la P de ag12 V1 fija, ¿se puede armar un Top-15 que acierte más que los 15 animales de mayor probabilidad?

## Razonamiento previo (lo que se espera)
1. En cada sorteo sale exactamente UN animal. La probabilidad de que el Top-15 acierte es la SUMA de las
   probabilidades de sus 15 animales: P(acierto S) = Σ_{i∈S} p_i. No hay término de correlación entre animales
   (los sucesos "sale i" y "sale j" son excluyentes). Por eso, si la P es correcta, los 15 de mayor p son el
   Top-15 óptimo, y "tener en cuenta la correlación entre animales" no puede ayudar.
2. Una transformación monotónica de p aplicada igual a los 38 animales de un sorteo (temperatura, isotónica,
   Platt, etc.) NO cambia el orden, así que deja el Top-15 idéntico. Solo lo pueden cambiar correcciones que
   reordenen: dependientes del puesto de forma no monótona, del animal, o de otra fuente (el ensamble).
3. Por tanto, cualquier ganancia de Top-15 solo puede venir de que la P de ag12 esté mal ordenada en algún eje.

## Diagnósticos (no son variantes, no cuentan para la barra)
- D1: Top-15 esperado (media de Σ de las 15 p mayores) contra observado, con IC por jornadas.
- D2: acierto por puesto 1..38 (observado contra Σ p del puesto) y en la frontera (puestos 11-20).
- D3: fiabilidad por deciles de p.
- D4: control de identidad: temperatura T = 0,7 y 1,5 sobre P_V1 → ΔTop-15 debe ser EXACTAMENTE 0.

## Variantes (máximo 3; fijadas aquí)
- **V1 (primaria) — recalibración por puesto:** P ∝ P_V1 · c(puesto), c(r) = (O_r + 20)/(E_r + 20), donde O_r son los
  aciertos observados en el puesto r y E_r = Σ p del puesto r en entrenamiento (encogido hacia 1 con 20 aciertos
  de pseudo-cuenta). Puede reordenar si c no es monótona.
- **V2 — mezcla geométrica con el ensamble:** log P = a·log P_V1 + b·log P_ens (+ normalizar), (a, b) por máxima
  verosimilitud en entrenamiento. Reordena si el ensamble tiene información que ag12 ordena mal.
- **V3 — sesgo por animal:** log P = log P_V1 + β_animal (38 interceptos, L2 λ = 30 como ag02/ag12), máxima verosimilitud.

## Anti-fuga
- Cross-fit en los MISMOS 5 bloques de jornada (ag02 `bloques_jornada`). Como P_V1 de una fila de entrenamiento se
  ajustó usando el bloque de prueba, se hace **cross-fit anidado**: para el bloque de prueba k, las filas de
  entrenamiento (bloques j ≠ k) llevan predicciones de ag12 reajustadas SIN k ni j (mismo código, λ = 30, 33 variables).
  La corrección aprendida se aplica a P_V1 del bloque k. Control: el reajuste reproduce P_V1 (diferencia máxima impresa).
- Forward informativo: base = ag12 V1 forward (bloque 0 = ensamble). La corrección del bloque k (k ≥ 2) se aprende con
  los bloques 1..k−1 (sus P forward, que no ven k). Bloques 0 y 1 quedan sin corrección.
- Solo filas [2000, 9357). Nada de filas >= 9357 ni del sellado.

## Métricas y barra
- Primaria del ángulo: ΔTop-15 (aciertos por sorteo, candidato − ag12 V1) con IC95 por bootstrap de jornadas,
  mitades y forward. Éxito del ángulo: IC95 inferior > 0, las dos mitades > 0 y forward > 0.
- Barra común: Δ mbits ≥ +3 sobre P_V1, IC95 inferior > 0, mitades > 0, forward > 0 (arnes.evaluar con P_ref = P_V1).
- Si ninguna variante pasa: el Top-15 por probabilidad de ag12 V1 se queda como el óptimo, con los diagnósticos
  como demostración numérica.
