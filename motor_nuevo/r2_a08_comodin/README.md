# r2_a08_comodin: NO PASA. La lista de pares que el operador evita NO es compartida con RD Internacional (ángulo cerrado)

## Hipótesis (prerregistrada en `PREREGISTRO.md` antes de correr)
ag12 muestra que Lotto Activo (LA, h:00) evita repetir un par consecutivo propio reciente. El hilo 7 muestra que el
filtro anti-repetición del operador mira también su otro juego: LA h:00 evita el animal de RD (h−1):30, con O/E 0,38.
Hipótesis: si el operador lleva UNA sola lista negra de pares, LA también evitaría s1→i cuando ese par salió consecutivo
**dentro de RD** (RD h':30 → RD (h'+1):30) en las últimas 1-30 jornadas.
Es nueva porque ag02, ag10, ag12 y r2_a01 solo usan pares de LA. `sondeo_rd.py` solo miró la secuencia intercalada
LA→RD→LA. r2_a03 usa el animal de RD y pares cruzados RD→LA / LA→RD. Nadie había probado los pares RD→RD.

## Modelo
Reajuste completo con offset log P_ens, las 33 variables de ag12 V1 y las nuevas, λ=30, cross-fit en los mismos 5 bloques
de jornada (`bloques_jornada` de ag02). Control: con las 33 variables se reproduce P_V1 con una diferencia máxima de 2,02e-13.
Solo se usan pares RD de jornadas anteriores (edad >= 1) y RD hasta 2025-12-17: 9.782 sorteos RD, 8.915 pares internos.
Datos: desarrollo [2000, 9357), n = 7357. No se tocaron las filas >= 9357 ni `sellado/sellado_la.txt`.
Hubo 3 variantes y una sola corrida de 13 s.

Reproducir, en PowerShell desde la raíz del worktree lotto-activo-motor:
`$env:PYTHONIOENCODING='utf-8'; python motor_nuevo/r2_a08_comodin/experimento.py`
Salidas: `consola.txt` y `resultados.json`, con los pesos por bloque y el diagnóstico completo.

## Resultados (Δ mbits FRENTE A ag12 V1 = +141,78 mbits; Top-15 de V1 54,78 %; IC95 por bootstrap de jornadas)
| Variante | Δ mbits [IC95] | mitad 1 | mitad 2 | forward vs V1-forward (b1-4) | Top-5 (V1 22,13) | Top-15 | Barra |
|---|---|---|---|---|---|---|---|
| **V1 primaria** (33 + RF1-3 + RR1-3) | **+0,86 [−0,55 ; +2,29]** | +0,79 | +0,94 | +0,99 [−0,38 ; +2,42] | 22,16 % | 55,25 % | NO |
| V2 lista única (27 ag02 + 6 agrupadas LA+RD) | −6,97 [−9,66 ; −4,28] | −6,56 | −7,39 | −6,33 [−9,24 ; −3,47] | 21,94 % | 54,08 % | NO |
| V3 parsimoniosa (33 + RF 1-30 + RR 1-7) | +0,97 [−0,13 ; +2,11] | +0,40 | +1,54 | +1,05 [+0,27 ; +1,87] | 22,07 % | 54,97 % | NO |

Otras cifras de V1: forward frente a P_V1 (bloque 0 = P_V1) −1,50 [−3,39 ; +0,58]. Top-3: 14,38 % contra 13,85 %.
Top-5 escalonado por ficha: +37,01 % contra +34,92 % (Δ +0,02 [−0,00 ; +0,04]).

Pesos de V1 (media [mín ; máx] de los 5 bloques):
- RF1: −0,070 [−0,133 ; −0,042]
- RF2: −0,055 [−0,101 ; −0,016]
- **RF3: +0,112 [+0,100 ; +0,122]**
- RR1: +0,037
- **RR2: +0,185 [+0,139 ; +0,221]**
- RR3: +0,020

Los pesos de LA (T1-T3, R1-R3) no cambian: de −0,05 a −0,53.

## Diagnóstico descriptivo (O/E crudo frente a ag12 V1)
| Máscara | 1 d | 2-7 d | 8-30 d | placebo 31-90 d |
|---|---|---|---|---|
| RD s1→i | 46/52,3 = 0,879 (z −0,87) | 294/310,5 = 0,947 (z −0,93) | 1216/1131,4 = 1,075 (z +2,52) | 1,047 (z +2,36) |
| RD i→s1 | 55/51,6 = 1,065 (z +0,47) | 361/311,4 = 1,159 (z +2,81) | 1,012 (z +0,40) | 1,030 (z +1,50) |

Como referencia, los pares propios de LA dan 0,40 a 1 día y 0,60 a 2-7 días frente al ensamble (z −7,3).

## Veredicto
**NO PASA. Se falsa la hipótesis de una lista negra compartida.**
- Los pares vistos en RD no se evitan en LA. A 1 y 2-7 días, s1→i da O/E 0,88 y 0,95, sin significación y lejos del 0,40-0,60
  de los pares propios de LA.
- Los pesos a 8-30 días y el de i→s1 a 2-7 días salen **positivos**, que es lo contrario de la hipótesis. El placebo de
  31-90 días también sale por encima de 1 (z +2,4). Eso apunta a una confusión leve de "animales que circulan en RD"
  más que a un mecanismo. Además hubo 8 máscaras, así que un z de 2,8 no basta según el protocolo.
- V2 impone un peso común a los pares de LA y de RD, y pierde −6,97 mbits. Sería la forma natural si la lista fuera
  única, así que el operador trata los dos juegos por separado.
- V1 y V3 ganan ~+0,9 mbits, con un IC que cruza 0 o roza 0. Es ruido y está lejos de la barra de +3.

Lectura del mecanismo: el filtro de pares de LA mira **solo la historia de LA**. El único vínculo con RD sigue siendo el
de "no repetir el animal de hace 30 minutos" (hilo 7, r2_a03). Este ángulo queda cerrado y no hay nada que llevar al marcador en vivo.
