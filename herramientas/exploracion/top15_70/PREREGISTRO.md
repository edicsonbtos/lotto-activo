# PRE-REGISTRO — 10 planes para subir el Top-15 de Lotto Activo hacia el 70 %

Escrito el 2026-10-01 ANTES de medir ningún plan. Las reglas no se cambian después de ver resultados.
Script: `top15_70.py` (misma carpeta). Resultados: `resultados.json`, informe: `INFORME.md`.

## Lo que ya se sabía al escribir esto (no es resultado de ningún plan)
Medido en todo el desarrollo [2000, 9357) con `calor_cache.npz`, antes de este pre-registro:
- El ensamble acierta el Top-15 el **53,07 %** (azar 39,47 %), con 120,1 mbits por sorteo.
- La masa que el ensamble le da a su propio Top-15 es 53,4 % de media, y **como máximo 67,3 %**: no hay
  ni un sorteo en el que el propio motor crea que el Top-15 tiene un 70 %.
- Para que un Top-15 acierte el 70 % hacen falta, como mínimo, **275 mbits por sorteo**. Esa cifra es
  la información mínima: la distribución más pareja posible con 70 % en 15 animales y 30 % en los 23 restantes.
  El ensamble tiene 120. Un Top-15 del 60 % exige ≥ 123 mbits.
- Top-15 por hora en todo el desarrollo (mirado): 8:00 60,5 % (n=372), 17:00 56,1 %, 18:00 55,9 %, el resto
  49,9-53,5 %. **Esto contamina el plan 7**: por eso, en el plan 7, las horas se eligen solo con dev-A y el
  resultado en dev-B se declara réplica débil.
- Error encontrado: `en_vivo_manana_8am.py` (parte DEV) y `PREREGISTRO_manana_8am.md` usan `hora == 8`
  como si fuera las 8:00 AM. En el historial, la hora va de 0 a 11 y 0 = 8:00, así que `hora == 8` son
  las **16:00**. El 53,1 % "de las 8:00" es en realidad el de las 16:00; el de las 8:00 de verdad es 60,5 %.

## Datos y tramos
- LA: `verificacion/hilo9/datos/historial.txt` (12.511 filas, huella SHA-256 congelada) y
  `verificacion/hilo9/datos/calor_cache.npz` (P walk-forward del ensamble, filas 2000..9356).
- RD Internacional: `datos_multiloteria/rdint_hist.csv`. Los días ≥ 2025-12-15 se tratan como sin RD, porque
  esas fechas de LA están corridas (hilo 8/9).
- **dev-A** = filas [2000, 5688) (2024-03-07 .. 2025-02-03): ajuste y elección de todo.
- **dev-B** = filas [5688, 9357) (2025-02-04 .. 2025-12-17): una sola medida por plan.
- El tramo de prueba (≥ 9357) **no se usa**. Ya se miró 5 veces.
- Plan 10: solo existe la ventana 2026-04-13..09-13 (`datos_multiloteria/*.csv`), que pisa el tramo de
  prueba de LA. Esas otras loterías nunca se usaron como fuente para LA, pero cuenta como réplica débil.

## Comparadores
- **B0** = ensamble tal cual (lo que está en producción).
- **B1** = ensamble + regla RD en el Top-15: si el animal de RD (h−1):30 está en el Top-15, sale y entra el 16.º.
  Pasó el 2026-09-30; es lo mejor que se conoce.
- Para los planes de orden (1-6) el comparador principal es **B1**. Si el plan no usa RD, se le aplica la
  regla RD encima. mbits se comparan contra B0.

## Medidas (todas en dev-B)
- Acierto Top-15 (el ganador está entre los 15 primeros) y la diferencia con el comparador, sorteo a sorteo.
- IC 95 % y p unilateral por bootstrap de jornadas (4.000 réplicas, semilla 20261001).
- mbits (solo planes que dan probabilidades).
- Retorno por ficha con pago 30: Top-15 plano (15 fichas) y Top-15 ponderado (3-3-3-2-2-1×10 = 23 fichas).

## Criterios (iguales para todos)
- **MEJORA**: Δ Top-15 > 0 con p unilateral < 0,005 (Bonferroni por 10 planes). En los planes que dan
  probabilidades, además Δ mbits > 0.
- **OBJETIVO 70 %**: Top-15 ≥ 70 % en dev-B y límite inferior del IC 95 % ≥ 65 %.
- Si no cumple: **NO PASA**. No se reintenta con otro umbral, ni con otra semilla, ni con otro corte.
- Si algo da MEJORA, el juez final es el marcador en vivo (skill `lotto-marcador`). No se mira el tramo de prueba.

## Los 10 planes
1. **Exclusión dura del día (LA).** Se sacan del Top-15 todos los animales que ya salieron hoy en LA y se
   rellena con los siguientes del ensamble. Encima va la regla RD. No se ajusta nada.
2. **Exclusión cruzada RD completa.** En dev-A se mide O/E de "LA h:00 = RD de hoy a (h−j):30" para j = 1..11.
   Se excluyen del Top-15 los RD de los desfases con O/E < 0,80 en dev-A (el (h−1) siempre entra) y se rellena.
3. **Corriente combinada con rechazo.** LA y RD se ordenan como un solo chorro (8:00, 8:30, 9:00…). El modelo
   es P ∝ P_ens · Π m_k para el animal que salió k pasos atrás en ese chorro (k = 1..24), más m_hoy si ya salió
   hoy en cualquiera de los dos. Los m_k se ajustan por máxima verosimilitud en dev-A (L2, λ = 10).
4. **Apilado con árboles (LightGBM binario).** Variables: logit y puesto del ensamble, huecos de LA (último y
   penúltimo, en sorteos y en días), veces hoy, conteos 12/36/120/456, retardos 1..12, RD de hoy por desfase,
   veces en RD hoy y ayer, hora, sorteos ya hechos hoy, y las 33 de ag12. El ensamble entra como punto de
   partida (init_score) y el árbol aprende la corrección. Ajuste en dev-A con parada temprana en el último
   20 % de dev-A. Hiperparámetros fijos: 31 hojas, tasa 0,03, mín. 200 por hoja, fracción 0,8.
5. **Árboles que ordenan para el Top-15 (LightGBM LambdaRank).** Mismas variables y mismo punto de partida, con
   el objetivo de ordenar dentro de cada sorteo y truncamiento en 15 (lambdarank_truncation_level = 15,
   eval_at = 15). Las probabilidades salen de un softmax del puntaje, con la temperatura ajustada en dev-A.
6. **ag12 re-ajustado limpio + RD.** Las 33 variables de ag12 más RD (h−1) y (h−2) como término log-lineal
   sobre el ensamble. Pesos ajustados SOLO en dev-A (λ = 30, igual que ag12). Así se mide ag12 en dev-B fuera de
   muestra, porque los pesos congelados de ag12 se ajustaron con todo el desarrollo.
7. **Jugar solo las horas buenas.** En dev-A se eligen las horas con Top-15 (B1) ≥ 56 % y n ≥ 150. En dev-B se
   mide el acierto solo en esas horas. Las 8:00 tienen n < 150 en dev-A, así que se reportan aparte, como réplica
   débil (ya se miraron). MEJORA si las horas elegidas superan al resto de horas de dev-B con p < 0,005.
8. **Reencuadre de dos sorteos.** Se juega el Top-15 (B1) de h y el de h+1 del mismo día y se cuenta como
   acierto si sale en al menos uno. Se reporta la tasa, el costo y el retorno. No es una mejora por sorteo, y
   así se dirá en el informe. Se reporta también la dupleta del Top-15 (los dos ganadores dentro de su Top-15).
9. **Top-N necesario para el 70 %.** N* = el N más chico con Top-N (B1) ≥ 70 % en dev-A. En dev-B se reportan
   el acierto de Top-N* y su retorno por ficha, plano y ponderado (3-3-3-2-2 y 1 al resto).
10. **Fuentes nuevas: otras loterías.** En 2026-04-13..09-13 se mide O/E de "LA h:00 = X", donde X es:
    La Granjita (h−1):00 y h:00 (sorteo simultáneo, solo descriptivo), Selva Plus (h−1):15, Guácharo (h−1):00,
    y LA de RD Int (h−1):30 como control positivo. Se compara por número 1..36 (y por nombre donde coincide el
    tablero). PASA si alguna fuente da O/E fuera de [0,80; 1,20] con un IC 99,5 % que no contiene 1
    (Bonferroni por 4 fuentes). Si pasa, se mide su regla de exclusión en vivo; nada aquí la mete en producción.

## Lo que este estudio no hace
- No toca `servidor.py`, ni `historial.txt`, ni `predicciones.json`, ni Railway.
- No mira el tramo de prueba (≥ 9357).
- No cambia el modelo en producción. Si un plan da MEJORA, se propone una medición en sombra y se pide el OK
  al usuario.
