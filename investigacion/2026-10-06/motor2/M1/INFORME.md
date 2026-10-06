# M1 · Detector en línea de "modo relajado": NO MEJORA
Pre-registro: `PREREGISTRO.md` (sin cambios). Código: `m1.py`. Salidas: `aj_V*.txt`, `salida_elegir.txt`,
`salida_fuga.txt`, `salida_prueba.txt`. Congelado: `final.json`. Matriz: `<scratchpad>/motor2_M1.npz`.

## Qué es
Filtro bayesiano por día con dos modos. P = (1−q)·PROD + q·PR, con PR ∝ [(1−u)·PROD^τ + u/38]·r^{ya salió hoy}.
q_t = σ(logit π_d + κ·Σ llr de los sorteos de hoy ya salidos). π_d sale de la evidencia de días pasados: mismo día de
la semana con olvido (h_s semanas) y días recientes (h_r días). Nunca se le dice qué día es el relajado.
Final: V3 (completo) con mezcla log-lineal w = 0,5 con PROD. Parámetros (AJUSTE): r 5,3; τ 0,80; u 0,00; κ 0,49;
h_s 3,9 semanas; h_r 7,6 días; a1 = a2 = 3 (en la cota).

## Resultados (Δ mbits contra PROD, IC 90 % por jornadas)
| tramo | V3 solo | **V3, w = 0,5 (final)** | Top-15 final/prod |
|---|---|---|---|
| AJUSTE | +2,26 [+0,04; +4,48] | +1,77 [+0,45; +3,10] | 54,6 / 54,6 |
| ELECCION | +1,46 [−2,45; +5,38] | +2,54 [+0,21; +4,86] | 48,9 / 48,6 |
| ANTIGUO (info) | | +2,02 [+0,84; +3,19] | 52,3 / 52,3 |
| **PRUEBA26 (1 vez)** | | **−0,31 [−1,04; +0,41]** | 49,6 / 49,6 |
V0, V1, V2 y VC: ~0 (el optimizador quedó en PR = PROD o en las cotas). Ni el Top-5 ni la plata se mueven en ningún tramo.
En PRUEBA26 mié +1,3, jue −1,4 y vie +0,5: el detector ya no saca nada en los días relajados.

## Validación fuerte: el detector SÍ encuentra el día relajado sin que se lo digan
- V3, π medio: en 2024-07..2025-06, el domingo 0,18 (resto 0,03-0,06). En 2025-12..2026-06, vie 0,25-0,27, mié 0,13-0,15,
  jue 0,10-0,12 (resto 0,04-0,06). En 2025-07..11 (meses neutros) todo ≈ 0,01-0,02.
- V1 (sin día de la semana), evidencia del día por día de la semana: domingo en ANTIGUO (0,31 contra 0,11-0,14);
  jue, vie y mié en ELECCION (0,18-0,24 contra 0,11-0,14).
## ¿A qué hora sabe? (V3, AUC de q_h contra el modo del día medido a posteriori)
ELECCION: 0,69 a las 8:00 (solo prior) → 0,74 a las 12:00 → **0,85 a las 14:00** → 0,87 a las 19:00. ANTIGUO: 0,73 → 0,87,
y llega más tarde (0,83 a las 17:00). q queda corto: cuando dice 0,45, el día es relajado el 70 % de las veces.

## Lectura adversarial
- El fenómeno es real y se detecta. Pero cuando el detector ya está seguro (14:00), quedan pocos sorteos del día, y en
  modo relajado el operador es "casi azar": acertar el modo vale poco en bits. Así no se puede batir a PROD.
- La ganancia de AJUSTE/ELECCION (+2 mbits) es del tamaño del control GL de `../../adaptativo` (+1-2). Se eligió entre
  4 variantes y 6 valores de w, y el IC de ELECCION apenas pasaba (+0,21). En PRUEBA26 desaparece.
- Desviación declarada: la 1.ª ronda sin cotas degeneró (r → 0, a1 → 10⁵; está en `sin_cotas/`). La 2.ª acota
  r ∈ [1, 6], τ ∈ [0,3; 1], a1, a2 ∈ [0, 3] (r ≥ 1 y τ ≤ 1 ya estaban en el pre-registro).
- Walk-forward: `chequear_fuga` OK (cortes 6000, 9000, 12000 y 12743) sobre la versión final.

## VEREDICTO: NO MEJORA
No entra en el motor. Sí vale como herramienta de vigilancia: la π de V3 sigue el día relajado sin calendario y puede
servir para el pre-registro en vivo de `../../semana/INFORME.md`.
