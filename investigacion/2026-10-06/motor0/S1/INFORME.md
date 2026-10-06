# S1 · Selector de sorteos (CUÁNDO jugar el Top-15): NO MEJORA
Pre-registro: `PREREGISTRO.md` (no se tocó). Scripts: `rasgos.py` (rasgos y prueba de fuga), `modelo.py` (partes 1 y 3),
`estrategias.py` (parte 2), `diag.py` (diagnóstico exploratorio), `prueba.py` (una mirada a PRUEBA26, contaminada).
Salidas: `salida_*.txt`, `estrategias.json`, `registro_prueba26_S1.jsonl`. Matriz: `<scratchpad>/selector_S1.npz`
(P̂ de LR y de GBM por fila de `arnes.T`, NaN antes de 2025-07; `jugar_*` = P̂ ≥ 0,50; `fichas_grad_*`). CPU: unos 4 min.

## Qué es
Etiqueta: el ganador cae en el Top-15 del motor (PROD o M4). 21 rasgos anteriores a h:00: hora y día de la semana; π_d y
q_h del filtro de modo relajado de M1 (V3, parámetros congelados); aciertos y O−E de hoy; O−E de los últimos 1, 3, 7 y 28
días; repeticiones y reciclaje de hoy; masa del Top-15, entropía y p1; EWMA del O−E por hora (30 d), por día de la
semana (4 sem.) y global (7 d); y si RD (h−1):30 está disponible y dentro del Top-15. Logística L2 y LightGBM pequeño,
walk-forward con reajuste mensual, pesos con vida media de 365 días y calibración de Platt con los últimos 90 días.
Prueba de fuga: al alterar `seq[c:]`, los rasgos de las filas ≤ c no cambian (`salida_fuga_rasgos.txt`).

## Parte 1: ¿predice mejor que la constante? (Δ log-loss en milésimas de nat; IC 90 % por jornadas)
| motor | modelo | AJUSTE Δ | AJUSTE AUC | ELECCION Δ | ELECCION AUC | PRUEBA26* Δ | PRUEBA26* AUC |
|---|---|---|---|---|---|---|---|
| PROD | C1 masa del Top-15 | +0,2 [−2,3; +2,7] | 0,506 | −0,7 [−3,0; +1,6] | 0,516 | −0,4 | 0,513 |
| PROD | constante con olvido de 30 d (adversarial) | −1,1 [−2,8; +0,7] | 0,521 | −3,2 [−5,9; −0,6] | 0,498 | −0,4 | 0,482 |
| PROD | **LR** | −0,5 [−3,5; +2,5] | 0,526 | **−4,9 [−8,9; −1,0]** | 0,533 [0,505; 0,563] | −0,6 [−3,9; +2,8] | 0,512 |
| PROD | GBM | −0,5 [−4,0; +3,0] | 0,529 | −4,2 [−9,4; +1,1] | 0,524 | −4,9 [−9,5; −0,4] | 0,558 |
| M4 | LR | −3,6 [−8,1; +1,0] | 0,536 | +0,2 [−4,4; +4,7] | 0,504 | −0,6 | 0,503 |
| M4 | GBM | −3,1 [−7,5; +1,4] | 0,533 | +1,5 [−3,5; +6,4] | 0,504 | +0,2 | 0,533 |
\* PRUEBA26: una sola mirada, CONTAMINADA.

- PROD-LR cumple por los pelos el criterio pre-registrado en ELECCION. Pero 2/3 de esa ganancia es un cambio de nivel
  (en ELECCION el Top-15 acierta 48,6 % contra 54-55 % antes): una constante con olvido corto ya da −3,2. La AUC es 0,53,
  y en PRUEBA26 no repite (−0,6, AUC 0,51). El GBM hace lo contrario: falla en ELECCION y pasa en PRUEBA26. Es el patrón
  del hilo 6 y de R6.
- M4 no pasa en ningún tramo. Calibración de la LR: correcta en el centro. Por encima de 0,54 se rompe en ELECCION
  (n = 20, P̂ 0,54 contra 0,35 real).

## Parte 2: estrategias (filas con RD disponible; u = 0,50 elegido en AJUSTE; fichas netas por día)
| estrategia (motor PROD salvo que se diga) | AJUSTE ret/ficha · netas/día | ELECCION ret/ficha [IC 90] · netas/día · jugado | PRUEBA26* ret/ficha · netas/día |
|---|---|---|---|
| **REF: Top-5 escalonado PROD con cambio, todos** | **+31,0 % · +29,8** | **+24,9 % [+13; +38] · +23,9 · 100 %** | **+18,6 % · +15,7** |
| T15 plano, todos | +9,2 % · +16,5 | −2,9 % [−7; +1] · −5,2 · 100 % | +1,5 % · +2,3 |
| T15 plano si P̂ ≥ 0,50 | +9,2 % · +16,4 | +3,5 % [−4; +11] · +2,6 · 41 % | +3,2 % · +0,9 |
| T15 ponderado (3-3-3-2-2-1×10), todos | +16,1 % · +44,4 | +6,2 % [0; +12] · +17,2 · 100 % | +7,1 % · +17,1 |
| T15 ponderado si P̂ ≥ 0,50 | +16,0 % · +43,8 | +11,7 % [+2; +23] · +13,2 · 41 % | +13,8 % · +6,1 |
| T15 plano graduado 0/1/2/3× | +11,4 % · +38,0 | +3,5 % · +2,6 · 41 % | +3,0 % · +0,9 |
| M4: T15 ponderado si P̂ ≥ 0,50 | +23,7 % · +62,8 | +11,5 % [+4; +18] · +20,0 · 63 % | +13,3 % · +31,0 |
| T15 plano con cambio RD, todos (info) | +11,2 % · +20,2 | 0,0 % · 0,0 · 100 % | — |

Comparaciones pareadas en ELECCION (IC 90 % por jornadas):
- **Contra la REF:** ninguna estrategia con selector le gana. T15 plano con selector: −21,3 fichas por día [−33; −9].
  Ponderado: −10,7 [−22; +0,5]. Con M4, el ponderado gana en fichas por día en AJUSTE y en PRUEBA26 (+33 y +15) solo
  porque apuesta 2,4 veces más fichas. Su retorno por ficha es la mitad del de la REF en todos los tramos.
- **Contra jugar todos los sorteos:** el T15 plano de PROD con selector gana +6,4 pp por ficha [+0,6; +12,2] (azar con la
  misma fracción jugada: −2,8 %). En PRUEBA26 se queda en +1,7 pp [−8; +13], y en AJUSTE en 0, porque el selector juega el 99 %.
- **¿De dónde sale la selección de ELECCION? (`diag.py`, exploratorio).** Del día de la semana: el selector juega el 9-21 %
  de los mié-vie y el 58-70 % del resto. La regla "saltar mié-vie" da +4,8 % (selector +3,5 %), y ese régimen se descubrió
  con 2026. La regla RD dentro del Top-15 (cambiar el animal de RD (h−1):30 por el 16.º) suma unos 2-3 pp sin saltarse
  ningún sorteo. Es una mejora del motor, no del selector.

## Parte 3: rachas de la mañana (aciertos Top-15 de 8 a 12 h → tarde de 13 a 19 h)
| tramo (PROD) | mañana 0-1 de 5 | 2 | 3 | 4-5 | corr(O−E mañana, O−E tarde) |
|---|---|---|---|---|---|
| ANTIGUO | −4,6 pp | +2,4 | +0,4 | −2,9 | +0,005 |
| AJUSTE | +2,2 | +0,6 | −5,6 | −6,0 | −0,055 |
| ELECCION | −4,3 | −3,4 | −8,3 | −4,2 | −0,003 |
(O−E de la tarde, en puntos de acierto del Top-15.) Logística walk-forward sobre la tarde, base hora + día + masa:
añadir el O−E de la mañana da AJUSTE −0,0 [−0,6; +0,6] y ELECCION −0,7 [−2,4; +1,0]. Sobre base + q/π: −0,9 y −1,4,
los dos con IC que cruza 0. Con M4: −0,5 en AJUSTE y **+1,1 [+0,1; +2,0] (peor)** en ELECCION. **La mañana no
predice la tarde.** Si acaso, en AJUSTE una buena mañana va seguida de una tarde peor. Es coherente con "casi no repite
en el día": los animales que ya salieron no vuelven y el Top-15 se vacía.

## Lectura adversarial
1. La única "señal" que resiste es la del nivel: en 2026 algunos días (mié-vie, días relajados) el Top-15 baja del 50 %.
   El selector la aprende de π_d y del EWMA por día de la semana. Ya es conocida y no se reproduce en PRUEBA26 en log-loss.
2. Con umbral alto, la confianza se invierte fuera de muestra: en ELECCION, con P̂ ≥ 0,54 el T15 plano da −30 % y el de M4
   con P̂ ≥ 0,56 da −27 %. Es otra vez R6/hilo 6.
3. El Top-15 cobra 2× (plano) o hasta 3,9× (ponderado) por acierto. Para igualar el +25 % de la REF, el plano necesitaría
   un 62,5 % de acierto en los sorteos jugados. El mejor tramo seleccionado no pasa del 52 % fuera de AJUSTE.
4. Desviaciones declaradas: los 9 parámetros de M1 se ajustaron en AJUSTE; M4 es igual a PROD antes de 2025-07; el
   selector usaría RD (h−1):30, que llega después del congelado. Se miró PRUEBA26 porque PROD-LR pasó la parte 1 en ELECCION,
   y la mirada queda marcada como contaminada.

## VEREDICTO: NO MEJORA
El selector no supera a la REF en ningún tramo, ni en retorno por ficha ni en fichas por día pareadas. Contra "jugar
todos" solo gana en ELECCION, y por el efecto mié-vie ya conocido. Las rachas de la mañana no informan. La regla sigue
siendo jugar todos los sorteos con el Top-5 escalonado. Lo único aprovechable es aplicar la regla de cambio RD también
al Top-15 (+2,0 pp en AJUSTE y +2,9 pp en ELECCION, medido en el plano). Es una idea del motor y habría que pre-registrarla aparte.
