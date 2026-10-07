# Auditoría independiente de ag12 y de su sombra (2026-10-07)

Alcance: solo lectura. Datos de desarrollo (filas 2000..9356). No se usó el tramo sellado ni filas >= 9357 para elegir nada
(solo se leyeron los resultados ya publicados de las pruebas ciegas). Scripts de la auditoría en el scratchpad de la sesión
(repro.py, equiv.py, dow.py, pw.py, fechas.py, cmp.py). No se tocó producción, ni el registro del marcador, ni se hizo commit.

## Veredicto: ACEPTAR CON CAMBIOS
La sombra está bien implementada y es honesta (sin fuga, congelado previo, idéntica al motor, refactor sin cambios).
Lo que NO se sostiene es la expectativa de efecto (+19,4) ni que el criterio de los 931 sorteos vaya a poder decidir. Ag12 no debe pasar a la jugada.

## Hallazgos (por gravedad)

### Importante
**I1. El efecto de ag12 no es estable entre épocas; +19,4 es el extremo optimista.**
Sellada 2019-2023 (n=15.166): Δ −1,17 [−6,02; +3,85]. Reciente (n=3.055): +19,43 [+8,91; +29,89] (IC Bonferroni k=4).
Agrupando (SE a partir de los IC): +2,6 ± 1,8 mbits; heterogeneidad z = 4,4 (script pw.py). La explicación "cambio de política en 2022" es
posterior al fallo (RETOMAR.md: "hipótesis, no evidencia"); la 2.ª prueba fue motivada por el fallo de la 1.ª y se corrigió por k=4,
pero no por "reintentar tras fallar". Vivo (n=135, /api/sombra, 2026-10-07 12:24): ag12 113,1 vs ensamble 112,6 mbits (Δ +0,5; error típico ≈ 20).
Consecuencia: planificar con +10 o menos, no con +19,4.

**I2. El criterio de 931 sorteos tiene potencia 36 % si el efecto real es +10 (16 % si +5).**
sd por sorteo de Δ en desarrollo = 236,1 (el preregistro usa 238: coincide). Potencia a n=931 (alfa 5 % unilateral): 80 % con +19,4; 36 % con +10; 16 % con +5.
Con +10 harían falta 3.503 sorteos. Efecto práctico: el resultado más probable a los 931 es "no concluyente", no "no pasa".
El preregistro no dice qué pasa en ese caso (¿se sigue hasta 3.500 o se descarta?). Definirlo ANTES de mirar. Además, el freno (n>=600, Δ<−10, "puede mirarse cada mes")
se dispara con 15 % si el efecto real es 0 y con 2 % si es +10: es prudente, pero mirar cada mes acumula falsos frenos.
Criterio intacto: git log sobre ag12_top15/PREREGISTRO.md = un solo commit (721428b, 2026-10-01); git status del archivo limpio. El número 931 no está en ningún .py.
Proyección: n=135 el 2026-10-07 (≈12,3/día, ~98 % de cobertura) → n>=931 alrededor del 2026-12-12; la regla "lo que llegue después" da 2026-12-14. Consistente.

**I3. El marcador de la sombra no calcula lo que el criterio pide, y la base no es la que ag12 reemplazaría.**
- experimentos.py (marcador_sombra, ~líneas 160-250): ic90_jornadas solo se usa para exposición y ventana 8:00. No hay IC 90 % por jornadas de Δ(ag12 − ensamble)
  ni Top-5 escalonado en pp/ficha (solo t5_neto en fichas totales). El día de la decisión habrá que calcularlo a mano: riesgo de analítica ad hoc. Añadirlo ya (no cambia ningún dato guardado).
- La base "ensamble" es el ensamble crudo; lo que se juega es ensamble + cambio_rd (Top-5). ag12_rd no es comparable (usa multiplicadores RD, no el intercambio por el 6.º).
  En vivo: ag12 Δ +0,5 mbits, ag12_rd +4,3: la parte "RD" no es mérito de ag12. La segunda condición del preregistro (Top-5 escalonado no >3 pp/ficha peor) se debería medir contra la jugada real.

**I4. La cifra de desarrollo +21,7 es la menos honesta de las tres.**
Reproducida exacta (mi script con el código de motor_nuevo, sin modificar nada): cross-fit V1 +21,71 [16,39; 27,10], P_V1.npy coincide (max|dif| 2e-13). Congelado en muestra +26,90.
Forward estricto sobre los bloques 1-4 (el bloque 0 queda = ensamble por construcción, así que el "+16,04" publicado promedia 20 % de ceros): +19,81 [14,03; 25,60].
El mecanismo (T1-T3, R1-R3) se descubrió con un sondeo sobre ese mismo desarrollo (z −7,3); ni cross-fit ni forward corrigen la selección de rasgos.
Variantes vistas en desarrollo: 11 agentes ronda 1, ag12 V0/V1/V2 y 8 agentes de ronda 2. Por eso la prueba sellada y la ciega son lo que cuenta, y ellas discrepan (I1).

### Menor
**M1. En el sorteo de las 8:00 (1/12 de los sorteos) la sombra se apoya en un ensamble distinto al validado.** prediccion.py:163-173: scores_sin_8am = ensamble × ajuste_primer_sorteo.
Ag12 se validó sobre ensamble_v2 sin ese multiplicador. Ambos brazos lo comparten, así que la comparación es limpia, pero no es exactamente el modelo medido.

**M2. Empates: sin efecto material.** Con las probabilidades redondeadas a 6 decimales (como se guardan) en las 7.357 filas de desarrollo: filas con algún empate: 159 (ag12) y 202 (ensamble);
empates justo en la frontera top3/5/15: 12 y 14 en 22.071 comprobaciones; el redondeo cambia la composición del Top-k en 9 y 6 casos. Desempate por índice en ambos brazos, sin sesgo hacia ag12. El banco usa desempate aleatorio (1e-12); la diferencia es despreciable.

**M3. Cambios de fecha (sesgo entrenamiento/servicio).** Desarrollo con fechas viejas; en vivo cargar() aplica la corrección del 2026-09-29. Medido: Δ en muestra 26,90 (viejas) vs 26,91 (corregidas); 153 de 7.357 filas con |ΔP|>1e-6, máx 0,0104. Inocuo. (Tras corregir, el orden (fecha,hora) deja de ser monótono en el archivo; no afecta a ag12.)

**M4. Registro.** Los pendientes creados por registrar() (servidor.py:1696) no llevan sombra y quedan fuera de ambos brazos por igual (se excluyen ANTES de medir, mismas filas): sin sesgo de selección por resultado.
deshacer() (servidor.py:605) reabre el registro con su sombra original (calculada con el historial anterior): honesto; deja correcciones, pero marcador_sombra no excluye ni marca registros con correcciones. Menor.

**M5. Test de oro sintético sin scores_sin_8am.** La ruta sc_base = scores_sin_8am or scores solo se cubre en test_sombra_8am/test_ajuste_8am. Los 89 tests pasan, pero el oro de marcador_sombra no ejercita ese campo.

## Verificaciones (todas limpias)
1. **Sin look-ahead en ag12.** rasgos12.py/rasgos_ag02.py: la fila t usa seq[:t], y hora/dia de t. Prueba directa: construir con prefijo recortado a t+1 da la misma fila que con todo el historial (5 filas al azar en 9000-12400, 0 distintas);
   barajando seq, hora y dia de todo lo posterior a t=9100, las filas <= t no cambian (max|dX| = 0,0). El hiperparámetro lambda=30 viene de ag02 (fijo, preregistrado), pesos ajustados con filas [2000,9357) solamente (congelar.py).
   La base P_ens es la caché walk-forward (no auditada aquí).
2. **Sombra == motor.** herramientas/modelos/ag12/parametros_V1.json igual al del motor; rasgos12.py y rasgos_ag02.py iguales salvo la línea de importación. Último commit de esa carpeta: abe291e (el refactor no la tocó).
   experimentos.sombra_de sobre 14 filas de desarrollo (con historial real hasta t) vs Modelo("V1") del motor: max|dif| = 1,06e-6 (redondeo a 6 decimales de entrada y salida).
3. **Congelado previo al resultado.** servidor.py:1587-1591 (preparar): la sombra se calcula con cargar() anterior al sorteo (pf,ph) y solo si not conocido; no se vuelve a escribir. RD (h−1):30 y (h−2):30 salen antes de LA h:00 y se aplican al puntuar (con_rd; con h−k<0 no se usa).
4. **Refactor sin cambios.** python -m pytest tests -q → 89 passed. Además, oráculo independiente: extraje ae556d0 (master antes del refactor) a una carpeta temporal y comparé marcador_sombra y marcador_cambio_rd sobre los datos sintéticos de tests/datos_experimentos.py: cmp de las dos salidas → IGUALES (nuevo vs ae556d0).
5. **Puntuado con datos locales.** El registro local de pronósticos tiene 46 registros, 0 con sombra (2026-09-12..16, anteriores a la sombra): no se puede puntuar localmente. El marcador en vivo (GET /api/sombra) da n=135 desde 2026-09-26: ensamble top3/5/15 = 11,85/17,04/46,67 %; ag12 14,07/19,26/51,11 %; mbits 112,6 vs 113,1.
   Con n=135 no dice nada (error típico de Δ ≈ 236/√135 = 20 mbits; Top-15 ±8 pp).

## Pregunta 4: ¿rinde distinto ag12 en mié-vie? (solo desarrollo, cross-fit P_V1, fechas corregidas en memoria)
Δ mbits (ag12 − ensamble) por día, IC95 por bloques de jornada: lun +13,3 [−3,7; +29,3] · mar +24,0 [+11,0; +37,1] · **mié +30,4 [+15,9; +44,6] · jue +30,0 [+15,6; +44,2] · vie +32,2 [+19,5; +45,4]** · sáb +10,0 [−3,5; +23,7] · dom +11,6 [−3,4; +26,8].
- mié-vie (n=3.176) +30,9 [+22,9; +38,9] vs resto (n=4.181) +14,7 [+7,2; +22,0]. Contraste +15,3 mbits [+4,1; +26,7], p de permutación (por jornada, 5.000) = 0,004.
  Top-5: +1,63 pp [+0,03; +3,17] (p 0,045). Top-15 +0,92 pp [−1,0; +2,9] (p 0,35). Top-3 +0,85 pp (p 0,25).
- Replica en el forward estricto (bloques 1-4): mié-vie +27,5 vs resto +14,0. Por quintiles de tiempo, mié-vie ≥ resto en los 5 (+26/+11, +25/+25, +30/+19, +36/+5, +36/+14).
- Cautelas: mié-vie es el máximo de las 35 combinaciones posibles de 3 días (rango −17,5 a +16,1); si no estaba preespecificada, Bonferroni sobre 35 da p≈0,14 (sobre las 7 ventanas contiguas, ≈0,03). Es el día de semana, no el mecanismo: el ensamble tiene
  habilidad muy distinta por día (mbits: mié 108, dom 6), así que la diferencia puede venir de la base. Solo es una hipótesis; no cambiar pesos de ag12 por día (sería una variante nueva sobre datos ya mirados).
- Para confirmarlo en vivo el contraste (+15 mbits) necesitaría ≈ 6.250 sorteos de sombra (≈17 meses): no se decidirá antes de la mirada de los 931.

## Cambios pedidos (para ACEPTAR)
1. Preregistrar (antes de n=931) qué se hace si el resultado es "no concluyente" (seguir hasta ~3.500 con el mismo criterio o descartar), y que el efecto esperado es ≤ +10.
2. Añadir a marcador_sombra el IC 90 % por jornadas de Δ(ag12 − ensamble) en mbits y el Top-5 escalonado en pp/ficha, y una columna "ensamble + cambio_rd" como base de la condición 2. No cambia datos guardados.
3. No pasar ag12 a la jugada por la sombra a n<931 ni por el efecto por día.
