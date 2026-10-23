# ag4 - Semana actual (16-23 oct 2026) y rendimiento en vivo. Solo descriptivo.
Datos: oficial_multi.csv (LA 93 sorteos, RD 92 en la ventana); mesa?modelo=la (452 pasados con puesto, 15-sep a 23-oct) y principal (329, 26-sep a 23-oct) en raw/. Guion: parte1.py, parte23.py. Ojo: el codigo 0 del CSV mezcla "0" y "00".

## 1. Semana actual vs 22 meses de historia (ventanas de igual numero de sorteos desde 2025-07-01)
| Metrica (obs / esperado azar) | LA percentil | RD percentil |
|---|---|---|
| Animal mas repetido (conteo) | 6 / pct 39 | 8 (el 0/00) / pct 96 FUERA |
| Animales que no salieron | 2 (5 y 15) / pct 15 | 1 (31) / pct 16 |
| Repite animal el mismo dia | 8 / 13,3 / pct 90 | 5 / 13,7 / pct 89 |
| Pares (1-36) | 48 / 43,5 / pct 84 | 46 / 42 / pct 88 |
| Altos (19-36) | 45 / 43,5 / pct 62 | 43 / 42 / pct 52 |
| Numero = dia del mes | 2 / 2,4 / pct 75 | 1 / 2,4 / pct 39 |
| Numero = hora (24 h / 12 h) | 2 / 2,4 y 2 / 2,4 (pct 68 / 74) | 2 / 2,4 y 4 / 2,4 (pct 52 / 88) |
| Vecino de rueda del anterior | 3 / 4,2 / pct 45 | 5 / 4,0 / pct 84 |
| Cruce LA h:00 = RD (h-1):30 | 0 / 2,4 / pct 24 | - |
| Cruce RD h:30 = LA h:00 | - | 0 / 2,5 / pct 32 |
- Mas salidos: LA el 0/00 (6), el 10, 22 y 28 (5 c/u); RD el 0/00 (8), 9, 32, 35 y 16 (4 c/u). Esperado por animal ~2,4 (el 0/00 vale doble, ~4,9).
- Fuera de 5-95: una de 20 metricas (RD "animal mas repetido", 8 contra tope historico de 8). Es casi puro artefacto: el 0 y el 00 estan fusionados en el CSV; sin ellos el maximo es 4. Con 20 metricas se esperaban ~2 fuera; hay 1. Nada anormal.
- Repetir el mismo dia sale muy por debajo del azar siempre (la historia tiene -5 a -13 de diferencia); esta semana repitio un poco mas que lo tipico (pct 89-90), dentro de rango. Los cruces entre juegos tambien son siempre mas raros que el azar; 0 de ~2,4 es normal.

## 2. Motor EN VIVO por dia y hora (Top-5 / Top-15; modelo "la" = ensamble_v2 con 452 sorteos)
Acierto global LA: Top-5 17,5 % (modelo esperaba ~19 %, azar 13,2 %); Top-15 48,0 % (modelo ~51 %, azar 39,5 %).
Por dia (aciertos Top-5 / n; IC95 Wilson): lun 20,3 % [11;33], mar 23,2 % [14;35], mie 13,0 % [6;23], jue 15,5 % [8;26], vie 19,4 % [11;31], sab 20,7 % [11;33], dom 10,2 % [4;21]. Modelo esperaba 19-20 % cada dia.
Top-15 por dia: lun 49 %, mar 55 %, mie 36 %, jue 37 %, vie 54 %, sab 53 %, dom 54 % (modelo 50-52 %). Heterogeneidad chi2: Top-5 p=0,45; Top-15 p=0,076.
Por hora (Top-5): entre 8,1 % (13h) y 26,3 % (15h); Top-15 entre 39,5 % (18h) y 65,8 % (8h). chi2: Top-5 p=0,51; Top-15 p=0,55.
Modelo "principal" (ag12+RD, 329 sorteos): Top-5 20,4 % (esperado ~21 %), Top-15 52,3 % (esperado ~53 %). Por dia chi2 Top-5 p=0,69, Top-15 p=0,087; por hora p=0,82 y 0,47. Dias: lun 27 %/67 % Top-15 el mejor, mar-jue 41-48 % el peor, sin significancia.
Semana 16-23 oct (91 sorteos): LA Top-5 17 (esperado 17,4), Top-15 49 (46,0), Top-3 8 (10,8); principal Top-5 19 (18,7), Top-15 48 (48,2), Top-3 14 (11,8). Todo igual a lo esperado.
Veredicto: ninguna hora ni dia es distinto; las diferencias caben en el ruido (con ~60 sorteos por dia el IC es de +-12 puntos y con ~37 por hora de +-17). Los dos p de 0,08 (Top-15 por dia) son los mas cercanos y aun asi no pasan 0,05 con 4 pruebas hechas. Tabla completa en tabla_la.txt y tabla_principal.txt.
RD (api/rdint solo trae el marcador agregado, no el detalle por dia/hora): n=359, Top-3 10,9 % (azar 7,9), Top-5 18,7 % (13,2), Top-15 51,5 % (39,5). No se puede desglosar por dia/hora con lo que expone la API.

## 3. Retorno por ficha en vivo (paga 30x por ficha; neto/apostado)
| Dia | LA Top-5 esc. | LA Top-3 plano | principal Top-5 esc. | principal Top-3 plano |
|---|---|---|---|---|
| lun | +14 % | +2 % | +80 % | +108 % |
| mar | +25 % | +1 % | -22 % | -58 % |
| mie | -13 % | +1 % | +6 % | +30 % |
| jue | 0 % | +13 % | +25 % | +46 % |
| vie | +23 % | +34 % | +62 % | +105 % |
| sab | +16 % | +3 % | +52 % | +49 % |
| dom | -36 % | -32 % | +9 % | +25 % |
| TOTAL | +4,5 % [-18;+27] | +4,0 % [-24;+32] | +29,9 % [+1;+59] | +42,9 % [+5;+81] |
- Por dia todos los IC son de +-60 a +-110 puntos y abarcan cero (solo el Top-3 del principal el martes queda por debajo de cero). Rentabilidades por dia = ruido de 5-10 premios por celda.
- RD (marcador de api/rdint, 359 sorteos): Top-5 esc. +10,7 %, Top-3 plano +8,6 %, Top-15 ponderado +5,7 %, Top-15 plano +3,1 %.
- Cautela: LA-mesa son solo 5 semanas; el total de "principal" (+30 %) roza el IC por encima de cero con una sola ventana de 4 semanas y sin corregir por mirar varios planes. No es evidencia de ventaja.

Que haria falta para confirmar algo de esto: nada se propone aqui. Por dia/hora haria falta del orden de 300+ sorteos por celda (meses) y regla fijada de antemano; la señal de dia/hora ya esta cerrada.
