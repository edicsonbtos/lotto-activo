# M1 · Pre-registro: detector en línea de "modo relajado" del operador (2026-10-06, antes de medir)

## Idea
Cada día d tiene un modo oculto z_d ∈ {normal, relajado}. En modo normal el operador se comporta como el motor de
producción (PROD). En modo relajado deja de evitar repetir el animal del día y se parece más al azar. Antes de cada
sorteo t se estima q_t = P(z_d = relajado | pasado) y se predice con la mezcla bayesiana
    P_t = (1 − q_t)·PROD_t + q_t·PR_t,
    PR_t ∝ [(1 − u)·PROD_t^τ / Σ + u/38] · r^{1[ya salió hoy]}    (r ≥ 1 quita la penalización; τ ≤ 1 aplana; u mezcla uniforme)

## Detector (filtro bayesiano por día, sin calendario fijo)
- Prior del día: π_d = σ(a0 + a1·logit(Msem_d) + a2·logit(Mrec_d)).
  - Msem_d: media con olvido exponencial (vida media h_s semanas) de la evidencia de los días anteriores con el MISMO día
    de la semana, encogida hacia la media global con un pseudo-peso. Solo sabe que hay periodicidad semanal; nunca se le
    dice qué día es el relajado.
  - Mrec_d: media con olvido exponencial (vida media h_r días) de la evidencia de los días anteriores, sin día de semana.
  - Evidencia de un día pasado: e_d = σ(κ·LLR_d), con LLR_d = Σ_t log(PR_t(y)/PROD_t(y)) sobre sus sorteos (prior plano).
- Dentro del día: q_t = σ(logit π_d + κ·Σ_{t'<t, mismo día} log(PR_t'(y)/PROD_t'(y))). Esto incluye las repeticiones y el
  reciclaje ya vistos hoy (señal a), porque PR premia el animal ya salido.
- Todo usa solo sorteos anteriores. Se demuestra con A.chequear_fuga.

## Variantes (se ajustan en AJUSTE por máxima verosimilitud de la mezcla; se elige en ELECCION)
- V0: solo dentro del día (a1 = a2 = 0).
- V1: V0 + días recientes (a1 = 0). Sin ninguna información del día de la semana.
- V2: V0 + mismo día de la semana (a2 = 0).
- V3: completo.
- Además, para la elegida, mezcla log-lineal p ∝ PROD^(1−w)·M1^w con w ∈ {0,25; 0,5; 0,75; 1; 1,25; 1,5} elegido en ELECCION.
Parámetros: r, τ, u, κ, a0, a1, a2, h_s, h_r. Optimización numérica (Powell/Nelder-Mead) solo con filas de AJUSTE.

## Criterios (fijados antes de mirar)
- Elección: mayor Δmbits contra PROD en ELECCION.
- PRUEBA26 solo si la elegida tiene IC 90 % (por jornadas) > 0 en ELECCION. Una sola vez, con todo congelado.
- VEREDICTO: MEJORA si en PRUEBA26 el IC 90 % > 0; DUDOSO si la media es > 0 y el IC toca 0; NO MEJORA si la media ≤ 0
  o si no se llega a PRUEBA26.
- Validación fuerte (informativa, no decide el veredicto): con V3, (i) en 2024-07..2025-06 el domingo es el día con mayor
  π medio; (ii) en 2026-01..2026-10 los tres días con mayor π medio son mié, jue y vie. Con V1 (que no conoce el día de la
  semana) se repite el ranking con la evidencia e_d media por día de la semana.
- Hora a la que "sabe": por hora h, AUC y Brier de q_h contra el modo real a posteriori del día
  (etiqueta = σ(LLR_d completo con prior plano y κ=1) > 0,5) y contra "el día tuvo ≥ 2 repeticiones". También
  calibración de q por tramos.
- Adversarial: comparar contra GL (factor global de "salió hoy", +1-2 mbits en `../../adaptativo`) para saber si el
  detector aporta algo más que un factor medio, y mirar Δmbits por día de la semana y por mes en ELECCION.
