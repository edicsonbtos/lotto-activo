# Hilo 7 — E1: RD Int con memoria cruzada de Lotto Activo (H1 y H2)

Generado por `herramientas/rdint/correr_modelo.py`. Pre-registro: `herramientas/exploracion/PREREGISTRO_rdint_cruzado.md` (criterios sin cambios).

- Datos truncados al primer sorteo de 'test' (fila 7886) ANTES de modelar. Predicciones walk-forward desde la fila 2000 (dentro de 'cal'); **métricas solo en 'dev'**: 5784 sorteos, 482 días (2024-03-01 .. 2025-06-30).
- Mitades del desarrollo (cortadas en cambio de día): 1ª = 2892 sorteos (2024-03-01 .. 2024-10-29), 2ª = 2892 (2024-10-30 .. 2025-06-30).
- IC95 por bootstrap de bloques de jornada (2000 remuestreos). Azar = 1/38 (RD usa los 38 códigos; la Ballena '00' sale menos).
- Sorteos dev sin Lotto Activo a las h:00: 305 (feature = 0).
- **Prueba de fuga de B1** (sobre secuencia_v3; se baraja RD desde c y Lotto Activo desde c+1, se exige que P0 y P1 de las filas ≤ c no cambien): **SIN FUGA**. Cortes: c=5935 máx|ΔP0|=0.0e+00 máx|ΔP1|=0.0e+00 (futuro sí cambia: 4.4e-02); c=7053 máx|ΔP0|=0.0e+00 máx|ΔP1|=0.0e+00 (futuro sí cambia: 4.9e-02).

## B0 (solo RD Int) contra el uniforme

| modelo | mbits dev | 1ª mitad | 2ª mitad | IC95 dev |
|---|---|---|---|---|
| secuencia_v3 **(B0)** | +108.03 | +101.31 | +114.75 | [+95.94, +119.96] |
| intradia_v2 | +104.97 | +94.63 | +115.31 | [+92.41, +116.53] |

B0 = **secuencia_v3** (más mbits en dev; selección en desarrollo, permitida).

## H1 — Δ mbits por sorteo, B1 − B0

| tramo | n | Δ mbits | IC95 | ¿Δ ≥ +5 e IC>0? |
|---|---|---|---|---|
| dev completo | 5784 | +19.92 | [+14.63, +24.80] | sí |
| 1ª mitad | 2892 | +17.88 | [+12.01, +22.95] | sí |
| 2ª mitad | 2892 | +21.97 | [+12.91, +30.02] | sí |

**H1: PASA** (criterio: Δ ≥ +5 mbits y límite inferior del IC95 > 0 en AMBAS mitades).

### Coeficientes de B1 (log-razón de tasa sobre B0; walk-forward, reajuste cada 250)

| ajuste con filas < | LA h:00 | LA (h-1):00 | LA antes hoy |
|---|---|---|---|
| 2000 (2024-02-21) | +0.000 (×1.00) | +0.000 (×1.00) | +0.000 (×1.00) |
| 2750 (2024-04-25) | -1.875 (×0.15) | -0.073 (×0.93) | -0.027 (×0.97) |
| 3500 (2024-06-26) | -1.596 (×0.20) | -0.104 (×0.90) | +0.018 (×1.02) |
| 4250 (2024-08-29) | -1.670 (×0.19) | -0.260 (×0.77) | +0.032 (×1.03) |
| 5000 (2024-10-30) | -1.864 (×0.15) | -0.423 (×0.66) | -0.039 (×0.96) |
| 5750 (2025-01-03) | -1.690 (×0.18) | -0.401 (×0.67) | +0.012 (×1.01) |
| 6500 (2025-03-06) | -1.676 (×0.19) | -0.451 (×0.64) | +0.038 (×1.04) |
| 7250 (2025-05-08) | -1.666 (×0.19) | -0.551 (×0.58) | +0.092 (×1.10) |
| 7750 (2025-06-19) | -1.586 (×0.20) | -0.592 (×0.55) | +0.098 (×1.10) |

Coeficientes al empezar dev: [0.0, 0.0, 0.0]. Al final: [-1.586, -0.592, 0.098].

### Descriptivo en dev: tasa del animal marcado, Mantel-Haenszel por hora

| feature | expuestos | salió | esperado 1/38 | obs/esp | OR MH por hora | exposición media por sorteo |
|---|---|---|---|---|---|---|
| LA h:00 | 5479 | 30 | 144.2 | 0.21 | 0.20 | 0.95 |
| LA (h-1):00 | 5000 | 76 | 131.6 | 0.58 | 0.56 | 0.86 |
| LA antes hoy | 22713 | 708 | 597.7 | 1.18 | 1.24 | 3.93 |

## H2 — ¿B1 gana plata en desarrollo?

Retorno por ficha: pago 30x. Top-3 plano = 1 ficha a cada uno de los 3 primeros (equilibrio 10 %). Top-5 escalonado = 2-2-2-1-1 fichas (8 por sorteo).

| modelo | tramo | Top-3 | IC95 | retorno/ficha Top-3 (IC95) | retorno/ficha Top-5 esc. (IC95) |
|---|---|---|---|---|---|
| B0 | dev | 10.53 % | [9.77, 11.27] | +5.3 % [-2.0, +12.9] | +4.3 % [-1.8, +10.3] |
| B0 | 1ª mitad | 9.61 % | [8.61, 10.62] | -3.9 % [-13.6, +6.5] | -2.4 % [-10.8, +6.6] |
| B0 | 2ª mitad | 11.45 % | [10.30, 12.48] | +14.5 % [+3.0, +25.9] | +10.9 % [+1.9, +19.3] |
| B1 | dev | 10.93 % | [10.17, 11.71] | +9.3 % [+1.5, +17.7] | +7.8 % [+1.4, +14.0] |
| B1 | 1ª mitad | 10.27 % | [9.16, 11.34] | +2.7 % [-7.7, +13.4] | +0.8 % [-8.3, +10.3] |
| B1 | 2ª mitad | 11.58 % | [10.44, 12.69] | +15.8 % [+4.4, +27.2] | +14.8 % [+5.7, +23.3] |
| B1 − B0 (pareado) | dev | | | +4.0 pp [+0.5, +7.4] | |
| B1 − B0 (pareado) | 1ª mitad | | | +6.6 pp [+2.1, +11.4] | |
| B1 − B0 (pareado) | 2ª mitad | | | +1.4 pp [-3.8, +6.6] | |

**H2: PASA** (criterio: Top-3 de B1 ≥ 10,5 % en dev [10.93 %] Y retorno por ficha del Top-3 plano > 0 en ambas mitades [+2.7 %, +15.8 %]).

## Veredicto E1

- H1 (B1 mejora a B0 en log-verosimilitud): **PASA**.
- H2 (B1 gana plata con el Top-3 plano): **PASA**.

## Notas

- B1 usa b = 0 en sus primeras 500 filas (hasta la fila 2499): los primeros 398 sorteos de dev tienen B1 = B0 y Δ = 0, lo que diluye (no infla) la 1ª mitad.
- Casi toda la ventaja económica ya está en B0 (evitación intradía propia de RD Int): B0 solo da Top-3 10.53 % en dev. Lo que aporta Lotto Activo se lee en la fila pareada B1 − B0.
- B0 se eligió entre 2 candidatos en dev; la diferencia entre ellos (3.1 mbits) es menor que el IC.
- El retorno del Top-3 plano de la 1ª mitad tiene IC95 que cruza 0: H2 pasa por la estimación puntual que fija el pre-registro, no con margen.
- La prueba ciega NO se miró. `cache_dev.npz` guarda P0, P1, y, hora, dia, fila solo de filas dev.
