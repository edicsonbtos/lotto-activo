# Hilo 9 — paso 1: residuos contra los modelos en uso (sólo desarrollo)

Pre-registro: `herramientas/exploracion/PREREGISTRO_hilo9_subir.md`. O = veces que salió un animal marcado; E = lo que ya le daba el modelo (suma de P). O/E > 1: el modelo se queda corto; < 1: se pasa. Pasa si p < 0,05/9 = 0,0056 (dos colas). Última columna: O/E por hora (0 = 8:xx).

| hipótesis | sorteos marcados | O | E | O/E | z | p | pasa | O/E por hora |
|---|---|---|---|---|---|---|---|---|
| R1 RD ← LA ayer | 5724 | 1641 | 1616.6 | 1.015 | +0.72 | 0.47 | no | 0:0.94 1:1.02 2:1.06 3:1.09 4:1.02 5:1.07 6:1.03 7:0.97 8:0.95 9:1.04 10:0.96 11:1.05 |
| R2 RD ← LA anteayer | 5724 | 1616 | 1607.7 | 1.005 | +0.25 | 0.81 | no | 0:1.00 1:1.09 2:1.03 3:1.11 4:0.98 5:0.92 6:1.01 7:1.02 8:0.88 9:1.01 10:0.95 11:1.06 |
| R3 RD ← LA hoy 2+ veces | 870 | 18 | 19.3 | 0.934 | -0.29 | 0.77 | no | 2:0.00 3:0.00 4:0.00 5:1.60 6:0.97 7:0.68 8:0.00 9:1.07 10:0.24 11:1.63 |
| R4 RD ← RD hoy (auto-evitación) | 5302 | 227 | 274.1 | 0.828 | -2.97 | 0.003 | **SÍ** | 1:0.00 2:0.88 3:0.29 4:0.77 5:0.51 6:0.46 7:0.93 8:0.97 9:0.57 10:0.87 11:1.11 |
| L1 LA ← RD ayer | 7219 | 2214 | 2206.7 | 1.003 | +0.19 | 0.85 | no | 0:1.13 1:0.98 2:1.02 3:0.94 4:0.95 5:1.13 6:0.98 7:1.00 8:1.01 9:0.95 10:1.04 11:0.97 |
| L2 LA ← RD anteayer | 7230 | 2199 | 2205.6 | 0.997 | -0.17 | 0.87 | no | 0:1.03 1:1.04 2:0.95 3:1.04 4:1.02 5:1.01 6:0.96 7:0.89 8:1.00 9:1.02 10:0.95 11:1.05 |
| L3 LA ← RD (h−2):30 | 6293 | 121 | 171.6 | 0.705 | -3.92 | 8.7e-05 | **SÍ** | 2:0.52 3:0.52 4:0.64 5:0.58 6:0.85 7:0.52 8:0.76 9:1.00 10:0.78 11:0.90 |

Filas: RD dev 5784 (2024-03-01..2025-06-30); LA dev con RD 7289 (2024-03-07..2025-12-05).

## E1 — RD: B1 mezclado con intradia_v2 (walk-forward)

| tramo | n | Δ mbits | IC95 | pasa (≥ +5 e IC > 0) |
|---|---|---|---|---|
| dev completo | 5784 | -0.18 | [-1.76, +1.34] | no |
| 1ª mitad | 2892 | -2.33 | [-4.69, +0.05] | no |
| 2ª mitad | 2892 | +1.97 | [-0.21, +4.07] | no |

Pesos (a sobre B1, b sobre intradia_v2) al inicio de cada bloque: 0:(1.00,0.00), 1000:(1.00,0.15), 2000:(0.85,0.25), 3000:(0.95,0.15), 4000:(0.85,0.20), 5000:(0.85,0.20). **E1: NO PASA**
