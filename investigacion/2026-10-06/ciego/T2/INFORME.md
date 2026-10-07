# T2: C3, batería Turing sobre el motor S2 congelado (C-90, w = 0,75). Veredicto de C3: NO PASA

No hay fuga: el placebo, la fuga temporal y las semillas salen bien. Fallan dos controles del pre-registro: el
**retraso** (la ganancia depende del último mes) y el **rasgo aleatorio** (su importancia está lejos de 0). Según el
veredicto global de `../PREREGISTRO.md`, S2 queda como **"mejora del régimen 2026, no confirmada"**, salga lo que salga
en C1.

## Método
- **Motor.** `nucleo.py` reimplementa el reentreno mensual de `../../motor0/S2/motor_s2.py` (objetivo C, vida 90).
  Usa los mismos hiperparámetros y la misma matriz de rasgos `s2_rasgos.npz`, y solo añade parámetros para los
  controles. Con los valores por omisión reproduce la matriz congelada **bit a bit** (`validar.py`, 2026-03:
  max|ΔP| = 0, con 4 hilos y con 2). Nada se reajustó.
- **Submuestra.** La misma para todas las variantes: 4 meses de AJUSTE (2025-08, 2025-10, 2025-12 y 2026-02, alternos;
  1308 sorteos) y los 4 de ELECCION (1392 sorteos). La base es la matriz congelada en esas filas. El bootstrap (f) usa
  los tramos completos.
- **Métricas.** Δ mbits contra PROD, Top-15 con la regla RD (`eval_s2.resumen`) e IC 90 % por jornadas. PRUEBA26 no se
  tocó.
- **CPU.** Unos 32 min en total. Se usaron 2 hilos porque T1 corría a la vez. Un corte por el límite de uso obligó a
  reanudar, y los meses ya guardados se reutilizaron.
- **Umbrales.** Los umbrales operativos se fijaron en el docstring de `analizar.py` antes de ver ningún resultado. El
  criterio que manda es el de C3 tal cual.

## Resultados (`salida_analisis.txt`, `resultados.json`, `salida_fuga.txt`, `salida_bootstrap.txt`, `bootstrap.json`)
Base en la submuestra: AJUSTE Δ +10,3 mbits [−8,5; +29,1] y Top-15 −0,23 pp. ELECCION Δ +11,7 [−3,6; +27,1] y Top-15
+2,44 pp [+0,2; +4,7].

**(a) Placebo.** Las etiquetas (y la etiqueta blanda de régimen) se barajan entre jornadas enteras dentro de la ventana
de entrenamiento, con el orden de las horas intacto. Se predicen los meses reales.

| tramo | Δ placebo | permutación 2 | sin información (frecuencias) | uniforme | Top-15 |
|---|---|---|---|---|---|
| AJUSTE | −145,8 [−169; −122] | −139,9 | −149,4 | −144,6 | −14,6 pp |
| ELECCION | −78,4 [−102; −55] | −83,0 | −90,3 | −79,0 | −7,9 pp |

La ganancia desaparece por completo: el placebo cae al nivel del uniforme y la parada temprana deja casi siempre de 1
a 50 árboles. **PASA según C3** (Δ ≫ 0 sería fuga, y Δ debe quedar ≈ "sin información").

Nota honesta: mi umbral auxiliar (Δ_placebo ≤ Δ_frecuencias + 10) falla en ELECCION por 1,9 mbits. La causa es que la
referencia de frecuencias con olvido es peor que el uniforme (−90 frente a −79). Contra el uniforme, la diferencia es de
0,6 mbits.

**(b) Retraso de 1 mes.** Se entrena hasta el día 1 del mes anterior.
- AJUSTE: +6,7, con gap − base = −3,6 [−14,4; +7,1].
- ELECCION: **−0,6**, con gap − base = **−12,4 [−21,7; −3,1]**.
- Submuestra entera: Δ pasa de +11,1 a +2,9. La caída es del **74 %**, por encima del umbral del 50 %. **FALLA.**
- La mezcla aguanta mejor (ELECCION de +17,8 a +9,4) y el Top-15 de ELECCION baja de +2,44 a +1,58 pp.
- Lectura: la ventaja de ELECCION sale casi entera del último mes de datos, es decir, del régimen más reciente. Encaja
  con la lectura adversarial de S2 (modo relajado de mié a vie en 2026).

**(c) Semillas** 7, 1, 2, 3 y 4 (bagging 0,8 y feature_fraction 0,7 ya activos).

| tramo | Δ mbits | DE | Δ Top-15 (pp) | DE | Δ de la mezcla |
|---|---|---|---|---|---|
| AJUSTE | 10,3 / 15,5 / 15,8 / 14,3 / 21,5 | 4,0 | −0,23 / 0,00 / −0,15 / +1,30 / +0,99 | 0,71 | 20 a 29 |
| ELECCION | 11,7 / 9,2 / 12,7 / 12,4 / 9,8 | 1,6 | +2,44 / +1,15 / +1,22 / +2,87 / +1,01 | 0,86 | 15 a 18 |

- La DE es menor que la mitad de la semiamplitud del IC en todos los casos. **PASA.**
- Matiz: la semilla congelada (7) da el mejor Top-15 de ELECCION junto con la 3. La media de las otras cuatro es
  +1,6 pp, no +2,4. El bagging de las 5 semillas da +2,37 pp.

**(d) Rasgo de ruido N(0, 1)**, iid por (sorteo, animal).
- Efecto: ruido − base = +2,7 [−7,3; +12,6] en AJUSTE y −2,8 [−8,2; +2,6] en ELECCION. Cabe dentro del límite, así que
  no hay efecto.
- Importancia: el ruido se lleva el **6,4 % de la ganancia** y queda en el **puesto 6 de 38**. Supera a 32 de los 37
  rasgos reales; solo gap2, gapdias, llr_hoy, loglift_hoy y gap1 quedan por encima. **FALLA** ("importancia ≈ 0",
  umbral 1 %).
- Lectura: buena parte de la ganancia dentro de la muestra son cortes sobre ruido continuo. Es sobreajuste. No es fuga,
  pero la mayoría de los rasgos aportan menos que el azar.

**(e) Fuga temporal con reentreno real** (`fuga_t2.py`). Se altera toda la secuencia desde t, se recalculan TODOS los
rasgos (M4 sin RD, nuevos de S2, q_prior, lift y etiquetas) y se reentrena el mes de t.

| corte | sorteo | alteración |
|---|---|---|
| 10560 | 1.er sorteo del 2026-04-01 | +7 mod 38 |
| 9137 | 2025-11-20, h5 | biyección aleatoria |
| 11495 | último sorteo del 2026-06-19 | iid uniforme |

- P[t] y todas las filas del mes ≤ t coinciden exactamente con la matriz congelada (max|ΔP| = 0).
- Control: el 100 % de las filas > t sí cambian.
- **PASA.** El ρ del modo relajado queda fijo, como hiperparámetro calibrado en AJUSTE.

**(f) Bootstrap por jornadas** (10.000), tramos completos.

| tramo | variante | Δ mbits | IC 90 % | IC 95 % | P(Δ ≤ 0) | bloques semanales IC 90 % |
|---|---|---|---|---|---|---|
| ELECCION | S2 solo | +11,7 | [−3,4; +26,9] | — | 0,097 | — |
| ELECCION | mezcla w = 0,75 | +17,8 | **[+6,4; +29,3]** | [+4,3; +31,4] | 0,005 | [+6,0; +31,2] |
| AJUSTE | S2 solo | +12,6 | [+0,1; +25,1] | — | — | — |
| AJUSTE | mezcla w = 0,75 | +21,2 | [+11,8; +30,6] | — | — | — |

- Δ Top-15 en ELECCION: +2,44 pp, IC 90 % [+0,2; +4,7].
- El IC coincide con el normal. **PASA para la mezcla.** S2 solo cruza 0.

## Tabla de controles
| control | resultado | estado |
|---|---|---|
| (a) placebo de jornadas | −78 / −146 mbits ≈ uniforme; la ganancia desaparece | PASA |
| (b) retraso de 1 mes | caída del 74 % del Δ; ELECCION −12,4 [−21,7; −3,1] | **FALLA** |
| (c) 5 semillas | DE 1,6 a 4,0 mbits y 0,7 a 0,9 pp, < ½ IC | PASA |
| (d) rasgo aleatorio | sin efecto en Δ, pero 6,4 % de la ganancia (puesto 6 de 38) | **FALLA** |
| (e) fuga temporal (3 cortes, reentreno real) | P[t] idéntico | PASA |
| (f) bootstrap ELECCION | mezcla [+6,4; +29,3]; S2 solo [−3,4; +26,9] | PASA (solo la mezcla) |

## Veredicto de C3: NO PASA
- Sin fuga ni artefacto: (a) y (e) son limpios, y la ganancia no depende de la semilla.
- C3 exige además una caída pequeña con retraso e importancia ≈ 0 del ruido, y ninguna de las dos se cumple.
- La mejora de S2 en ELECCION depende del último mes de datos y convive con un sobreajuste visible.
- Por el pre-registro, S2 no puede declararse REAL. Queda como **"mejora del régimen 2026, no confirmada"**. Si se
  despliega en sombra, tiene que reentrenarse cada mes sin falta.

Archivos: `nucleo.py`, `validar.py`, `correr.py`, `analizar.py`, `fuga_t2.py` y `bootstrap.py`. Las predicciones por
mes están en `<scratchpad>/T2/*.npz`.
