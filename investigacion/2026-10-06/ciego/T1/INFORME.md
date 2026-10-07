# T1: pruebas ciegas C1 y C2 del motor S2 (pre-registro `../PREREGISTRO.md`, criterios sin cambios)

**Veredicto.**
- **C1 PASA, con margen escaso.** La mezcla S2+PROD (w = 0,75) da +7,4 mbits [+1,5; +13,4] en ANTIGUO. En plata, el
  Top-5 escalonado con la regla RD da Δ +1,0 pp, que cumple el umbral de ≥ 0, pero su IC es [−4,5; +6,4].
- **C2 NO PASA.** S2 entrenado con RD da −4,2 mbits [−10,8; +2,4] contra el motor de RD.
- Según el pre-registro, S2 es REAL solo si pasan C1 y C3; C2 es un apoyo, y ese apoyo falta. El veredicto global
  depende de C3, a cargo de T2.

## Archivos
Están todos en esta carpeta. Las matrices quedaron en el scratchpad con prefijo `T1_`.

| tarea | archivos |
|---|---|
| C1 | `c1_correr.py` (log `c1_correr.log`), `c1_eval.py`, salida en `c1_salida.txt` y `c1.json` |
| C2 | `PLAN_C2.md` (decisiones fijadas antes de correr), `c2_datos.py`, `c2_motor_rd.py`, `c2_rasgos.py` (con prueba de fuga), `c2_correr.py`, `c2_eval.py`, salida en `c2_salida.txt` y `c2.json` |

## C1: S2 congelado en ANTIGUO (2024-03..2025-06), reentreno MENSUAL exacto
**Configuración.**
- Se usó `motor_s2.correr("C", 90, desde="2024-03", paso=1, hasta="2025-06")` sin cambios, sobre la misma matriz
  `s2_rasgos.npz` del motor congelado. La mezcla es p ∝ PROD^0,25 · S2^0,75.
- Nada se reajustó.
- **Control.** Con la matriz trimestral de orientación se reproducen exactamente −11,05 y +0,77.

**`A.evaluar(..., tramos=("ANTIGUO",))`** (n = 5440)

| variante | Δ mbits vs PROD [IC 90 %] | Top-5 (PROD) | Top-15 (PROD) | ret. Top-5 (PROD) |
|---|---|---|---|---|
| S2 solo, mensual | −1,6 [−9,5; +6,3] | 18,7 (19,6) | 51,7 (52,3) | +13,6 % (+20,4 %) |
| **S2+PROD w = 0,75, mensual** | **+7,4 [+1,5; +13,4]** | 19,8 (19,6) | 52,7 (52,3) | +20,6 % (+20,4 %) |
| S2+PROD w = 0,75, trimestral (orientación) | +0,8 [−5,3; +6,8] | 19,3 | 52,4 | +15,1 % |

**Por semestre.** Mezcla w = 0,75, mensual. Δ mbits con ranking directo. Plata con la regla de cambio RD (h−1):30,
pareada contra PROD con la misma regla. IC 90 % por jornadas.

| semestre | Δ mbits | Top-5 (PROD) | Top-15 (PROD) | T5 escalonado RD (PROD) | Δ T5 esc. en pp | Δ Top-15 RD en pp |
|---|---|---|---|---|---|---|
| 2024-S1 (mar-jun) | +8,4 [−4,9; +21,7] | 20,4 (19,5) | 52,3 (51,6) | +24,4 % (+24,1 %) | +0,3 [−10,1; +10,7] | −0,08 |
| 2024-S2 (jul-dic) | +9,1 [−0,4; +18,5] | 19,3 (19,2) | 51,4 (51,6) | +20,7 % (+16,5 %) | +4,2 [−4,7; +13,1] | −0,44 |
| 2025-S1 (ene-jun) | +5,3 [−4,1; +14,6] | 19,9 (20,2) | 54,1 (53,3) | +22,0 % (+23,8 %) | −1,7 [−10,8; +7,3] | +1,16 |
| **ANTIGUO** | **+7,4 [+1,5; +13,4]** | 19,8 (19,7) | 52,7 (52,3) | **+22,1 % (+21,1 %)** | **+1,0 [−4,5; +6,4]** | +0,28 [−0,7; +1,2] |

**S2 solo, mensual, en ANTIGUO.**
- Δ T5 escalonado con la regla RD: −6,1 pp [−12,4; +0,3].
- Δ Top-15: −0,48 pp.
- No hay ningún semestre en positivo de forma clara.

**Lectura.**
1. C1 pasa con la regla escrita: el IC de mbits es > 0 y la diferencia en plata, ≥ 0. Pero la plata pasa solo por la
   estimación puntual: el IC va de −4,5 a +6,4.
2. Los tres semestres van en la misma dirección en mbits (+5 a +9), aunque ninguno tiene por sí solo un IC > 0.
3. En el régimen antiguo, **S2 solo no supera a PROD** (−1,6 mbits). Lo que aporta es complementario a PROD.
4. El reentreno mensual vale unos 7-10 mbits frente al trimestral. La orientación de −11 / +0,8 se debía sobre todo a
   modelos viejos.

## C2: transferencia a RD Internacional (2025-07-01..2026-09-22; n = 5145 sorteos)
**Configuración.** Las decisiones de `PLAN_C2.md` se fijaron antes de correr.
- **Rasgos de S2-RD.** Son los mismos 37 de S2, calculados con la secuencia de RD, más los 3 rasgos de LA que usa el
  motor de RD: LA h:00, LA (h−1):00 y "salió hoy en LA". Así el conjunto de información es idéntico.
- **ρ del modo normal.** Se calibró con RD de 2025-01..06, antes del tramo, con el mismo procedimiento: ρ = 0,265,
  frente a 0,240 en LA.
- **Entrenamiento.** `motor_s2.correr("C", 90)` sin cambios, con reentreno mensual.
- **Prueba de fuga de rasgos.** Se alteró RD desde c y LA desde c+1, en los cortes 9500 y 12000: **OK**.
- **Rival.** El motor de RD walk-forward, corrido de verdad (2 min de CPU) igual que en `prueba_ciega.py`:
  - B0 = secuencia_v3 desde la fila 2000, con reajuste cada 250;
  - B1 = `modelo.cruzado`, con b walk-forward (R = 250, mínimo 500, λ = 1).
  - El b final, [−1,65; −0,45; +0,16], es casi el congelado de producción.

**Resultados.** Todo es pareado contra B1, con IC 90 % por jornadas.

| variante | tramo | Δ mbits vs B1 | Top-5 (B1) | Top-15 (B1) | T5 esc. (B1) | Δ T5 esc. en pp |
|---|---|---|---|---|---|---|
| **S2-RD solo (criterio C2)** | 2025-07..2026-09 | **−4,2 [−10,8; +2,4]** | 18,9 (19,3) | 53,7 (52,9) [−0,4; +2,0] | +14,3 % (+16,9 %) | −2,6 [−9,7; +4,5] |
| S2-RD solo | 2025-S2 | −3,1 [−13,8; +7,6] | 20,5 (20,9) | 56,9 (55,3) | +23,7 % (+24,3 %) | −0,5 |
| S2-RD solo | 2026 (ene-sep) | −4,9 [−13,2; +3,5] | 17,9 (18,2) | 51,6 (51,4) | +8,0 % (+12,0 %) | −4,0 |
| S2-RD ⊗ B1, w = 0,75 (informativo) | 2025-07..2026-09 | +2,7 [−2,2; +7,7] | 19,8 (19,3) | 53,7 (52,9) | +17,6 % (+16,9 %) | +0,7 [−6,8; +5,5] |
| B0 sin LA (control) | 2025-07..2026-09 | −24,5 [−29,4; −19,5] | 18,1 | 50,8 | +9,5 % | −7,4 |

**Lectura.**
1. **C2 NO PASA.** Con la misma información, la arquitectura S2 queda en −4 mbits frente al motor de RD. No le gana en
   log-verosimilitud y el IC incluye 0.
2. S2-RD aprende el efecto de LA, ya que mejora 20 mbits sobre B0. También sube algo el Top-15 (+0,8 pp, con un IC que
   cruza 0). Pero no aporta nada medible por encima del logit de RD.
3. La mezcla con B1 da +2,7 mbits [−2,2; +7,7]: es la misma señal complementaria que en LA, pero aquí no es
   significativa.
4. En RD, el prior de modo relajado es plano por día de la semana (q_prior de 0,10 a 0,11). El régimen mié-vie de LA
   2026 no existe en RD, así que el componente "mezcla de expertos" no tiene en qué apoyarse.

## Desviaciones y avisos (declarados)
- **ρ de C1.** La matriz congelada usa ρ = 0,24, calibrado con jul-dic-25, que es posterior a ANTIGUO. Se mantuvo
  porque es parte de la configuración congelada. Es una pequeña mirada al futuro dentro de C1, y por eso C1 queda algo
  optimista. El resto de los rasgos (q_prior, par_evita, M4) es walk-forward.
- **CPU.** El total fue de unos 53 min, algo por encima de los 50 previstos. C1 tomó 38 min de CPU porque compartió los
  núcleos con otro proceso. Por eso **no se corrió** la variante secundaria de C2 con solo LA h:00, que era
  informativa. El criterio C2 no depende de ella.
- **Datos.** El historial de RD termina el 2026-09-22, así que C2 cubre hasta esa fecha.
- **Pasada interrumpida.** La sesión se cortó a mitad de trabajo. C1 y el motor de RD ya habían terminado y se
  reutilizaron sin cambios. Los rasgos y el entrenamiento de C2 se corrieron después del reinicio.
