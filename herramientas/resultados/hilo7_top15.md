# RD Internacional (h:30): ¿conviene jugar Top-15?

Generado por `herramientas/rdint/top15.py` el 2026-09-23. Modelo: B1 = secuencia_v3 sobre RD Int + lo que salió en Lotto Activo a las h:00 (media hora antes). Paga 30 por 1.

## En corto

Retorno por cada ficha apostada (más es mejor; 0 % = ni ganas ni pierdes):

| Forma de jugar | Fichas por sorteo | Desarrollo | Prueba (ya vista) | Réplica nueva (abr–sep 2026) |
|---|---|---|---|---|
| **Top-3 plano** | 3 | +9,3 % | +20,5 % | +13,9 % |
| Top-5 escalonado 2-2-2-1-1 | 8 | +7,8 % | +20,0 % | +9,0 % |
| Top-15 plano | 15 | +0,8 % | +7,4 % | +2,4 % |
| Top-15 ponderado 3-2-1 | 23 | +3,2 % | +11,8 % | +4,7 % |

- **Top-15 en RD Int:** acierta 51,22 % de las veces en la réplica, y el plano deja +2,4 % por ficha en la réplica nueva; el ponderado 3-2-1, +4,7 %. En Lotto Activo el Top-15 plano daba −1 % en la prueba ciega y el ponderado ~+6 %.
- **Plan recomendado para RD Int (elegido mirando solo el desarrollo): Top-3 plano.** En la réplica nueva dio +13,9 % por ficha (IC95 -1,1 % a +27,8 %).
- Entre las dos formas de Top-15, en desarrollo rinde más el **ponderado 3-2-1** (+3,2 % contra +0,8 % por ficha); en la réplica: ponderado +4,7 %, plano +2,4 %.
- Cuidado: en la réplica (1800 sorteos) ningún plan tiene el IC95 entero por encima de 0. Todos los planes quedan en positivo, pero la réplica sola es corta para confirmarlo; junto con la prueba ciega el cuadro es coherente.
- Lo que suma Lotto Activo: sin él (B0, solo RD Int), el Top-15 plano pierde en dev (-2,1 %) y en la réplica (-2,7 %). La información de Lotto Activo de las h:00 es lo que empuja el Top-15 a positivo.
- Las cifras de 'Prueba' no son una prueba nueva (ese tramo ya se miró una vez). La 'Réplica nueva' (2026-04-13 .. 2026-09-13) nunca se usó para ajustar ni elegir el modelo: es la mejor comprobación disponible.

## Detalle

### Tramos

| tramo | sorteos | días | desde | hasta | uso |
|---|---|---|---|---|---|
| dev | 5784 | 482 | 2024-03-01 | 2025-06-30 | desarrollo: aquí se elige el plan |
| test | 3237 | 270 | 2025-07-01 | 2026-04-12 | prueba ciega del hilo 7 (ya mirado una vez): informativo |
| desc | 1800 | 150 | 2026-04-13 | 2026-09-13 | nunca usado para ajustar ni elegir: réplica |

Predicciones walk-forward desde la fila 2000 con los datos truncados al primer sorteo 'vivo'. Coeficientes de B1 al final: [-1.545, -0.444, 0.167] (h:00, (h-1):00, antes hoy). IC95 por bootstrap de días (2000 remuestreos).

### Retorno por ficha con IC95, B1

| plan | fichas | dev | test | desc |
|---|---|---|---|---|
| Top-3 plano | 3 | +9,3 % [+1,7 %, +16,9 %] | +20,5 % [+9,6 %, +32,1 %] | +13,9 % [-1,1 %, +27,8 %] |
| Top-5 escalonado 2-2-2-1-1 | 8 | +7,8 % [+1,6 %, +14,0 %] | +20,0 % [+11,0 %, +28,6 %] | +9,0 % [-2,3 %, +20,6 %] |
| Top-15 plano | 15 | +0,8 % [-1,9 %, +3,4 %] | +7,4 % [+4,0 %, +10,8 %] | +2,4 % [-2,0 %, +7,0 %] |
| Top-15 ponderado 3-2-1 | 23 | +3,2 % [-0,0 %, +6,8 %] | +11,8 % [+7,1 %, +16,3 %] | +4,7 % [-1,1 %, +10,8 %] |

Ganancia media por sorteo, en fichas (B1): Top-3 plano: dev +0,28, test +0,61, desc +0,42; Top-5 escalonado 2-2-2-1-1: dev +0,62, test +1,60, desc +0,72; Top-15 plano: dev +0,12, test +1,12, desc +0,37; Top-15 ponderado 3-2-1: dev +0,74, test +2,72, desc +1,08.

Tasa de acierto del plan (el ganador cae dentro de los animales jugados), B1: Top-3 plano: dev 10,93 %, test 12,05 %, desc 11,39 %; Top-5 escalonado 2-2-2-1-1: dev 17,81 %, test 19,96 %, desc 17,67 %; Top-15 plano: dev 50,40 %, test 53,72 %, desc 51,22 %; Top-15 ponderado 3-2-1: dev 50,40 %, test 53,72 %, desc 51,22 %.

### Lo mismo con B0 (solo RD Int, sin Lotto Activo)

| plan | dev | test | desc |
|---|---|---|---|
| Top-3 plano | +5,3 % [-2,3 %, +12,6 %] | +12,8 % [+1,9 %, +24,0 %] | +8,9 % [-6,1 %, +23,9 %] |
| Top-5 escalonado 2-2-2-1-1 | +4,3 % [-2,2 %, +10,7 %] | +13,1 % [+4,4 %, +21,2 %] | +2,3 % [-8,3 %, +14,2 %] |
| Top-15 plano | -2,1 % [-4,8 %, +0,4 %] | +4,0 % [+0,6 %, +7,5 %] | -2,7 % [-6,8 %, +1,6 %] |
| Top-15 ponderado 3-2-1 | +0,1 % [-3,1 %, +3,3 %] | +7,2 % [+2,6 %, +11,5 %] | -0,9 % [-6,6 %, +5,6 %] |

### Acierto por puesto (B1) frente al equilibrio 1/30 = 3,33 %

Cada animal jugado a 1 ficha gana dinero solo si su puesto acierta más del 3,33 %.

| puestos | dev | test | desc |
|---|---|---|---|
| 1º-3º (c/u) | 3,64 % [3,39 %, 3,91 %] | 4,02 % [3,65 %, 4,42 %] | 3,80 % [3,33 %, 4,28 %] |
| 4º-5º (c/u) | 3,44 % [3,10 %, 3,78 %] | 3,95 % [3,54 %, 4,41 %] | 3,14 % [2,61 %, 3,67 %] |
| 6º-10º (c/u) | 3,41 % [3,23 %, 3,60 %] | 3,60 % [3,33 %, 3,86 %] | 3,46 % [3,13 %, 3,77 %] |
| 11º-15º (c/u) | 3,11 % [2,93 %, 3,28 %] | 3,16 % [2,90 %, 3,41 %] | 3,26 % [2,92 %, 3,60 %] |

| puesto | dev | test | desc |
|---|---|---|---|
| 1º | 3,56 % | 4,32 % | 3,50 % |
| 2º | 3,46 % | 3,80 % | 3,94 % |
| 3º | 3,91 % | 3,92 % | 3,94 % |
| 4º | 3,44 % | 4,05 % | 2,89 % |
| 5º | 3,44 % | 3,86 % | 3,39 % |
| 6º | 3,72 % | 3,55 % | 2,44 % |
| 7º | 3,51 % | 3,37 % | 4,06 % |
| 8º | 3,35 % | 3,92 % | 3,44 % |
| 9º | 3,35 % | 3,89 % | 3,72 % |
| 10º | 3,11 % | 3,24 % | 3,61 % |
| 11º | 2,97 % | 4,08 % | 3,06 % |
| 12º | 3,39 % | 3,27 % | 3,28 % |
| 13º | 2,89 % | 2,78 % | 3,39 % |
| 14º | 3,11 % | 2,29 % | 2,72 % |
| 15º | 3,18 % | 3,37 % | 3,83 % |

### Comparación con Lotto Activo

| plan | Lotto Activo (prueba ciega) | RD Int réplica (desc) | RD Int prueba (test) |
|---|---|---|---|
| Top-3 plano | +22,7 % | +13,9 % | +20,5 % |
| Top-5 escalonado 2-2-2-1-1 | +19,1 % | +9,0 % | +20,0 % |
| Top-15 plano | −1,1 % | +2,4 % | +7,4 % |
| Top-15 ponderado 3-2-1 | ~+6 % | +4,7 % | +11,8 % |

## Notas de honestidad

- El tramo **test** ya se miró una vez (prueba ciega del hilo 7, `hilo7_prueba_ciega.md`). Sus cifras aquí son informativas, no una nueva prueba.
- El tramo **desc** (2026-04-13 .. 2026-09-13) nunca se usó para ajustar ni elegir el modelo ni el plan: es la mejor réplica disponible. B0/B1 se congelaron antes (pre-registro y enmienda del hilo 7).
- El plan recomendado (**Top-3 plano**) se eligió por el mayor retorno por ficha en **dev**, igual que en Lotto Activo (`estrategia_top5.md`). Se compararon 4 planes fijados de antemano; no se buscaron proporciones.
- Retorno por ficha no es lo mismo que plata total: un plan con más fichas puede ganar más por sorteo aunque rinda menos por ficha, pero también arriesga más y sus rachas malas son más largas.
