# RETOMAR — búsqueda de motor nuevo (rama `motor-nuevo`)

Última actualización: 2026-09-25 (noche). Si una sesión se corta, empieza aquí.

## Objetivo del usuario
Subir el acierto del **Top-15 a >= 60 %** (hoy: ensamble_v2 = **53,07 %** en desarrollo, 49,5 % en prueba;
azar = 15/38 = 39,5 %). También pidió revisar: RD Internacional ↔ Lotto Activo, "animales que el Top saca y luego salen",
debilidades del generador aleatorio, rachas.

## Reglas que no se rompen
- Solo desarrollo: `historial.txt` filas [2000, 9357) vía `arnes.py`. Filas >= 9357: prohibidas (miradas 5 veces).
- Tramo **SELLADO**: Lotto Activo antes de 2023-09-04 (loteriadehoy). No se descarga hasta congelar como máximo 3 candidatos. Una sola mirada.
- No tocar producción (repo principal, Railway, historial.txt, predicciones.json). Sin commit ni push sin el OK del usuario.

## Qué ya está cerrado (no repetir)
- RD→LA: falló a ciegas (H4, +3 mbits, IC cruza 0). L3 (LA evita RD (h−2):30) real pero +1,4 mbits. La regla de cambio RD→Top-5 está en vivo.
- LARD (API id 3): independiente. Generador: Operación Turing (308 hipótesis + RNG certificado, sin debilidad pública). Vector 3 PRNG/LCG: ruido.
- Rachas del favorito (hilo 5), calor de la lista (hilo 6), techo con modelos flexibles (hilo 9).
- **ag11_sacados (2026-09-25):** los animales que salen del Top-15 entre un pronóstico y el siguiente aciertan
  exactamente lo que el modelo predice: 404 contra 396,5 esperados (O/E 1,02; z +0,37). Sesgo de memoria. `ag11_sacados/sondeo.py`.

## Cuánta señal pide el 60 % (medido 2026-09-25)
Con los 13 modelos de la ronda 1 más el uniforme y el ensamble, el Top-15 sube ~0,9-1,1 pp por cada +10 mbits.
Para llegar al 60 % haría falta ~+65-80 mbits SOBRE el ensamble (hoy +120). El mejor candidato da +12 mbits,
y su Top-15 es 53,6 %. Es decir, falta unas 6 veces la mejor mejora encontrada en 9 hilos + 10 agentes.

## Ronda 1 (10 agentes), resultados en desarrollo (Δ mbits frente al ensamble)
| Carpeta | Δ mbits [IC95] | Barra |
|---|---|---|
| ag02_residuo_boost | +12,15 [7,64 ; 16,75] (Top-5 21,56 vs 20,25) | PASA |
| ag10_comodin | +8,54 [5,03 ; 12,17] (Top-5 20,99) | PASA |
| ag01_gbm_ranker | +5,87 [2,95 ; 8,78] | PASA |
| ag03, 04, 05, 06, 07, 08, 09 | de −60 a +2 | no |

## Workflow en curso
- Guion: `motor-nuevo-reanudar.js` en el scratchpad de la sesión 2b72a97d (copia: `motor_nuevo/_workflow_reanudar.js`).
  Verifica ag02/ag10/ag01 (reproducción + revisor-sesgo). Si ninguno sobrevive, estratega + rondas 2-3.
- Diario: `~/.claude/projects/C--Users-edics-Downloads-lotto-activo-lotto-activo/2b72a97d-70ae-4f77-9b5c-14f849185c59/subagents/workflows/wf_d1cea296-5c3/journal.jsonl`
- Si se corta: leer el diario, copiar los `result` al arreglo `R1` (o a uno nuevo) del guion y relanzar desde ahí.

## Verificación (workflow wf_d1cea296-5c3, terminado): LOS 3 SOBREVIVEN
- ag02: reproducido exacto (+12,15). Forward estricto +9,0 [5,2 ; 13,0] = la cifra honesta. El bloque TABLERO (+6,15)
  no se replica en las filas previas al desarrollo [300,2000); el bloque PARES sí. Riesgo de época (efecto intradía).
- ag10: +8,54, forward +6,05. Toda la ganancia viene de trans1_30 (el mismo mecanismo de ag02); la "composición del día" = nada.
- ag01: +5,87, forward +3,37; solo mbits, Top-5/Top-15 sin cambio. Candidato flojo.
- **MECANISMO NUEVO REAL:** el operador evita repetir un par consecutivo reciente. Sondeo `ag12_transiciones/sondeo.py`:
  s1→i hace 1 d O/E 0,40, 2-7 d 0,60 (z −7,3), 8-30 d 0,84 (z −5,2), >30 d 1,00; inversa i→s1 1 d 0,56, 2-7 d 0,78 (z −4,1).

## ag12_transiciones — HECHO, mejor candidato
ag02 (27 var) + 6 de transiciones (T1-3, R1-3), λ=30, prerregistrado. Resultados en desarrollo (`consola.txt`):
- V1 cross-fit **+21,71** [16,39 ; 27,10], mitades +22,65 / +20,77; forward **+16,04**; Top-5 22,13 %, **Top-15 54,78 %**, Top-5 escalonado +0,11/ficha.
- V0 (solo 6 transiciones) +13,80; V1 − ag02 = +9,56 [6,44 ; 12,61] → las transiciones aportan.
- V2 exploratoria (8 ventanas) +19,60, peor que V1 (−2,1) → descartada.
- Sondeo 2: misma hora, misma posición, tríos, cruce entre días → O/E ≈ 1 sobre ag12 (nada más que sacar ahí).
- Congelado: `parametros_V1.json`, `parametros_V0.json` (congelar.py). prueba_fuga (True, None, 0.0) en V1 y V0.
- Auditoría revisor-sesgo de ag12: LANZADA (resultado pendiente; anotar aquí).

## RD ↔ LA con el mecanismo nuevo (`ag12_transiciones/sondeo_rd.py`)
- Pares repetidos en la secuencia intercalada LA h:00 / RD h:30: nada (O/E 0,85-1,13, |z| < 2,3).
- Control: LA h:00 evita el animal de RD (h−1):30 → 70 contra 185,8 esperados, O/E 0,38, z −8,5, incluso sobre ag12.
  Ya conocido (H4b y la regla de cambio en vivo). No entra en el sellado (sin RD antes de 2023-09); sí se puede sumar en producción.

## Prueba sellada — preparada, NO corrida
- `sellado/descargar.py` (baja LA < 2023-09-04 a `sellado/sellado_la.txt`, con el python de ..\lotto-activo\.venv_scrape).
- `sellado/prueba.py` + `sellado/candidatos.json` (ag12_V1, ag12_V0; Bonferroni k=2). Se niega a correr dos veces (registro_sellado.jsonl).
- Ensayo en seco OK con SELLADO_ENSAYO=<archivo> (no registra nada).
- Orden: auditoría OK → commit en motor-nuevo (congela) → descargar → prueba.py UNA vez.

## Siguientes pasos (en orden)
1. Esperar veredictos de la verificación. Anotar aquí cuáles sobreviven.
2. Medir el **Top-15** de cada sobreviviente y de su combinación (apilado ag02+ag10+ag01, cross-fit) en desarrollo.
3. Congelar como máximo 3, commit en `motor-nuevo`, y solo entonces descargar el tramo sellado y hacer la prueba única.
4. Informar al usuario con números; producción solo con su OK.

## Bitácora
- 2026-09-25 21:44 apagón de la PC en plena verificación de ag02. Recuperado del diario; relanzado.
- 2026-09-25 sondeo ag11_sacados: descartado.
