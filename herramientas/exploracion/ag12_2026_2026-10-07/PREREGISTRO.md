# PREREGISTRO — ag12 en 2026: réplica de estabilidad + tramo fresco (escrito 2026-10-07 ANTES de calcular nada de lo nuevo)

## Qué se pide y qué NO es esto
El usuario no puede esperar 6 meses de sombra y quiere una respuesta ya, centrada en 2026.
- **Réplica de estabilidad (NO es prueba virgen):** 2026-01-01..2026-09-16 de LA = filas 9357..12510 de `historial.txt`
  (ya fueron la 2.ª prueba ciega de ag12, PASÓ +19,4 [8,9; 29,9]). Aquí solo se mira si el efecto es estable en el tiempo
  (mes, trimestre, día de la semana). **Nada se reajusta con ella.**
- **Tramo fresco:** filas >= 12511 = 2026-09-16 8:00 .. 2026-10-07 (hoy, 5 sorteos), bajadas de la fuente oficial
  (`bajar_fresco.py`, contrastadas contra `oficial_multi.csv` y el historial local en el solape). n = 249 sorteos.
  Ningún modelo se construyó ni se afinó mirando estas filas.

## Qué ya se había visto (declarado)
- Resultados publicados de las pruebas ciegas de ag12 (sellada −1,17; reciente +19,4), réplica 6 meses +16,4 (enjambre).
- La auditoría 2026-10-07 midió mié-vie SOLO en desarrollo (filas 2000..9356), y `/api/sombra` (n=135 desde 2026-09-26:
  ag12 113,1 vs ensamble 112,6 mbits). **Esas 135 filas se solapan con el tramo fresco (09-26..10-07): no son independientes del tramo
  fresco; se muestran aparte y solo como dato descriptivo.**
- NO se ha visto: ningún desglose mensual/trimestral/por día de la semana de 2026, ni el tramo fresco, ni ag12_rd ni la regla RD en
  Top-15 en estas ventanas fuera de lo ya publicado, ni los placebos.

## Modelos (congelados, sin reajuste)
- Ensamble: `ensamble_v2` walk-forward con los pesos de producción (`pesos_ensamble.json`), idéntico al de la 2.ª ciega.
- ag12 V1: `parametros_V1.json` (λ=30, pesos ajustados solo con filas [2000, 9357)), commit c4a2b17. V0 se reporta como secundaria.
- Réplica: se reutilizan las matrices ya calculadas de la 2.ª ciega (`motor_nuevo/reciente/P_*.npy`). Fresco: se calculan con el mismo
  código (`calcular_fresco.py`) y se verifica que las filas viejas recalculadas coinciden con las guardadas.
- Fechas: se corrigen en memoria con `herramientas/correccion_historial_2026-09-29.json` y se EXCLUYEN los días tocados (fecha vieja o nueva),
  como en `enjambre_2026-09-30/ag12_top15/medir.py`.

## Medidas
- Δ mbits por sorteo = 1000·log2(P_ag12[ganador]/P_ens[ganador]); IC95 e IC90 por bootstrap de bloques de jornada (fecha), 4.000 réplicas, semilla 20261007.
- Top-3/5/15 (empates con la misma semilla que `lotto_eval.rankings`), Top-5 escalonado 2-2-2-1-1 (pp de retorno por ficha, paga 30),
  Top-15 ponderado 3-3-3-2-2-1×10 y plano.
- Desgloses (descriptivos): por mes, por trimestre (T1 ene-mar, T2 abr-jun, T3 jul-sep16), por día de la semana.
- **Hipótesis única declarada de día de la semana: mié-vie (3 días) rinde más que el resto**; se reporta contraste con IC95 y p de permutación por
  jornada. Los otros 7 días se reportan solo como descripción, sin inferencia.
- Potencia: efecto mínimo detectable (EMD) del tramo fresco = (z_{0,95}+z_{0,80})·SE con z=1,645 y 0,842 y SE = error típico por bloques de jornada
  (IC90 unilateral 5 %, potencia 80 %); además potencia con efecto +5, +10 y +19,4.

## CRITERIO DE VEREDICTO (fijado antes de calcular)
1. **PASA** si, a la vez: (a) en el tramo fresco, Δ mbits (ag12 V1 − ensamble) > 0 con límite inferior del IC90 por jornadas > 0, y
   (b) Δ mbits > 0 en los tres trimestres T1, T2, T3 de la réplica 2026.
2. **NO PASA** si: (a') en la réplica 2026 (n≈3.000) el límite inferior del IC90 es ≤ 0 (la estabilidad ni siquiera se sostiene sobre la muestra que
   antes pasó), o (b') en el tramo fresco el IC90 queda entero por debajo de 0.
3. **NO CONCLUYENTE** en cualquier otro caso. Se escribe de antemano: con n=249 el EMD será ~35-40 mbits, mucho mayor que el efecto esperado (+10 a +19),
   así que lo más probable es NO CONCLUYENTE salvo que el signo y los trimestres hablen claro. Eso NO se tratará como "pasa".
4. Validez: si cualquiera de los placebos (signos aleatorios por jornada; coeficientes de par invertidos; rasgos de par barajados entre
   jornadas de la misma hora) da "pasa" con el mismo criterio, el veredicto se invalida (sospecha de fuga o de artefacto).
5. No se cambian pesos, λ, umbrales ni variantes con nada de esto. Mié-vie solo informa; no se convierte en regla.

## ag12_rd y regla RD en Top-15
- **ag12_rd (definición de la sombra):** ag12 × 0,50 al animal de RD (h−1):30 y × 0,75 al de (h−2):30 (`SOMBRA_RD_MULT`), reportado contra el ensamble
  (como el marcador en vivo) y contra el ensamble con los MISMOS multiplicadores (base justa: aísla lo que aporta ag12).
- **Regla de cambio_rd sobre el Top-5 (la que se juega):** si el animal de RD (h−1):30 está en el Top-5, sale y entra el 6.º. Se mide
  ag12+regla contra ensamble+regla en Top-5 escalonado (pp/ficha) — la base real de la jugada.
- **Regla RD en Top-15 (enjambre_2026-09-30):** si el animal de RD (h−1):30 está en el Top-15, sale y entra el 16.º. Se mide Δ retorno Top-15 ponderado
  (con − sin) en el ensamble y en ag12, IC95/IC90 por jornadas; réplica 2026 y tramo fresco por separado. Mismo criterio de 3 vías (PASA = Δ>0, IC90>0 en
  fresco y signo igual en trimestres; NO PASA si réplica IC90 inferior ≤ 0 o fresco IC90 < 0).
- RD fresco: `fresco_rd.csv` (fuente oficial, id 2) + `rdint_hist.csv` hasta 09-22.

## Placebos (control de validez)
1. Volteo aleatorio de signo del Δ por jornada (10.000): p exacta de Δ≠0 bajo H0 de simetría.
2. ag12 con los coeficientes de los 6 rasgos de par (T1-T3, R1-R3) con el signo invertido: debe dar Δ muy negativo si el mecanismo es real.
3. Rasgos de par barajados: cada fila toma los rasgos de par de otra fila al azar de la misma hora (otro día): debe dar Δ≈0 o negativo.
4. RD: el animal de RD de cada sorteo se sustituye por el de otra jornada al azar de la misma hora (1.000 permutaciones): el Δ de la regla debe caer a ~0.

## Si no concluye
Se calcula n necesario con la σ medida y se discute qué es legítimo: (i) prueba directa del mecanismo (O/E de las repeticiones de par bajo las
probabilidades del ensamble, más potente que comparar log-scores), (ii) agrupar RD con el mismo mecanismo (ya medido: RD Int Δ +0,5 → no ayuda),
(iii) seguir la sombra. Sin atajos nuevos ni variantes nuevas.
