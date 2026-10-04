# Top-19/20, rachas, "dos días" y repartos de fichas (2026-10-04)

Base: walk-forward de `ensamble_v2` sobre el historial del volumen, hasta el 2026-10-03 a las 4 PM. Tramos: dev
[2000, 9357), prueba [9357, 2026-09-15) y vivo (desde 2026-09-15). Retorno por ficha con pago de 30. Scripts:
`r1.py` a `r5.py` y sus salidas. Leen `vivo_rk.npz` y `hist_hoy.txt`, generados en
`../../2026-10-03/vivo_y_estrategias/`.

## R1. Top-N plano
| N | acierto prueba | retorno prueba [IC 95 %] | acierto vivo | retorno vivo |
|---|---|---|---|---|
| 15 | 49,5 % | −1,1 % [−4,2; +2,2] | 44,4 % | −11,1 % |
| 19 | 60,7 % | −4,1 % [−6,9; −1,4] | 57,8 % | −8,8 % |
| 20 | 63,5 % | −4,8 % [−7,3; −2,2] | 58,2 % | −12,7 % |
| 22 | 69,1 % | −5,8 % | 67,6 % | −7,9 % |

Más animales dan más aciertos, pero menos plata: a partir de N ≈ 15 se pierde.

## R2. Rachas
Top-5, Top-15 y Top-20 aciertan igual tras 0, 1-2, 3-5, 6-10 o más de 10 fallos seguidos. Los desvíos
cambian de signo entre dev y prueba, y que el día anterior haya sido flojo o bueno tampoco informa. **No sirven.**

## R3. "Dos días": elegir el Top-k al abrir el día y jugarlo hasta que salga
| ventana, k | sale (prueba) | retorno dev / prueba / vivo |
|---|---|---|
| 12 sorteos, k = 1 | 38 % | +9 / +18 / +21 % |
| 24 sorteos, k = 1 | 61 % | +6 / +15 / +15 % |
| 24 sorteos, k = 2 | 58 % | +5 / +7 / −5 % |

Renovar el Top-1 en cada sorteo da +33 / +20 / +20 %, y el Top-2, +34 / +28 / 0 %. Renovar siempre es mejor.

## R4. Repartos de fichas: el Top-2 gana en los 6 semestres
| reparto | dev | prueba | vivo | semestres 2024a → 2026b |
|---|---|---|---|---|
| **Top-2 (1-1)** | **+33,8 %** | **+27,8 %** | 0,0 % | +34 +22 +37 +40 +29 +21 |
| 2-1 | +33,6 % | +25,1 % | +6,7 % | +33 +24 +40 +36 +26 +20 |
| Top-1 | +33,3 % | +19,7 % | +20,0 % | +31 +28 +47 +27 +18 +19 |
| 2-2-2-1-1 (actual) | +23,8 % | +18,3 % | −11,7 % | +22 +15 +22 +35 +17 +14 |

Top-2 menos el reparto actual: +10,0 pp por ficha en dev [+3,5; +16,3] y +9,5 pp en prueba [−0,6; +19,2].

## R5. Riesgo (banca de 100 apuestas, 90 días, días de prueba remuestreados)
| reparto | quiebra | llega a perder la mitad | banca final mediana | termina en pérdida |
|---|---|---|---|---|
| actual | 0,2 % | 3,8 % | 295 | 0,7 % |
| Top-2 | 2,1 % | 15,8 % | 400 | 2,6 % |
| Top-1 | 23,4 % | 49,8 % | 280 | 25,4 % |

La simulación supone que la ventaja de prueba se mantiene. En vivo (19 días) va por debajo.

## Pre-registro: Top-2 en vivo (escrito antes de ver datos posteriores a 2026-10-04)
- Desde el 2026-10-05, durante 90 días: retorno por ficha del Top-2 (1-1) contra el 2-2-2-1-1, sobre los
  pronósticos congelados del marcador.
- Diferencia esperada: ≈ +10 pp. **Se adopta** si el IC 90 % por jornadas de (Top-2 − actual) queda por encima de 0.
  **Se descarta** si la media es ≤ 0. En cualquier otro caso queda sin concluir.
- Hasta entonces la jugada oficial no cambia (`gestion_banca.VIGILANCIA`). Si alguien elige jugar el Top-2,
  conviene una banca de al menos 100 sorteos de apuesta.
