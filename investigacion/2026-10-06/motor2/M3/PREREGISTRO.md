# M3: pre-registro (escrito ANTES de mirar resultados), 2026-10-06

## Modelo: generativo del operador, logit condicional con β dinámicos
log P(a | pasado) = Σ_j β_j · x_j(a, t) − log Z_t, sobre los 38 animales. Rasgos x_j (todos del pasado del sorteo t):
- **hoy**: a ya salió hoy (indicador); **ant1**: a salió en el sorteo inmediatamente anterior (aunque sea de ayer).
- **día k** (k = 1..7): a salió el día natural d−k (indicador).
- **hueco**: sorteos desde su última salida, en tramos [1-3], [4-12], [13-24], [25-36], [37-60], [61-90], [91-130], [131-200], >200
  (un tramo de referencia omitido: 37-60).
- **primero** (solo en el primer sorteo del día): a = primero de ayer, a = primero de hace 2 días, a = primero de hace 3 días.
- **fecha/hora**: a = número del día del mes, del día+1, del día−1; a = hora en reloj de 12 h; a ∈ {d−1, d, d+1} en el primer sorteo.
- **misma hora ayer**; **frecuencia reciente**: (nº de salidas en 7 días − esperado) y (en 30 días − esperado), escaladas.
- **hoy × avance del día**: hoy · (nº de sorteos ya hechos hoy / 12).

Dinámica: cada día d, β_d = argmax Σ_{t < día d} 0,5^{(d − día_t)/vm} · log P(y_t) − ridge común·|β|²/2 − λ·Σ_dow |δ_dow|²/2.
Se reajusta cada día con solo el pasado (inicio en caliente desde β_{d−1}, pasos de Newton con gradiente exacto).
Efecto por día de la semana: los rasgos **hoy, día 1, día 2, día 3** tienen β = β_común + δ_dow, con contracción λ hacia el común.

## Rejilla (cerrada)
- vida media vm ∈ {30, 60, 120, 240} días; λ ∈ {∞ (sin día de semana), 300, 30, 3}; ridge común fijo = 1.
- Elección de (vm, λ): mayor mbits medio en AJUSTE ∪ ELECCION (agrupados). Se informa cada tramo.
- Mezcla log-lineal p ∝ PROD^(1−w)·M3^w, w ∈ {0, 0,1, …, 1}: w elegido en ELECCION.

## Criterio para gastar PRUEBA26 (una vez)
Candidato final = el mejor en ELECCION entre M3 solo y la mezcla con w elegido. Solo se mira PRUEBA26 si en ELECCION
Δmbits contra PROD > 0 con IC 90 % inferior > 0 y en AJUSTE Δ ≥ 0 (estimación puntual).
- MEJORA: PRUEBA26 Δ > 0 con IC 90 % inferior > 0. DUDOSO: Δ > 0 con IC que cruza 0. NO MEJORA: Δ ≤ 0 o no pasó ELECCION.
- Nota adversarial: w se elige en ELECCION, así que su Δ en ELECCION está inflado; por eso se exige también AJUSTE ≥ 0.

## Predicción descriptiva (no decide nada)
Si el modelo aprende el cambio de régimen solo, δ_dow de "hoy" (menos castigo a repetir en el día) debería subir el
domingo en 2024-07..2025-07 y en mié-vie desde 2025-12. Se mostrará la evolución de β_hoy y β_1..β_3 por día de la semana.
