# Hilo 9 — anexo M: prueba de techo en LA (sólo desarrollo, walk-forward)

Filas evaluadas: 5789 (las 1500 primeras sólo entrenan). λ=30.0, reajuste cada 500 filas.

| modelo | Δ mbits vs ensamble | IC95 | 1ª mitad | 2ª mitad | Top-3 | Top-5 | Top-15 | pasa |
|---|---|---|---|---|---|---|---|---|
| ensamble_v2 (en uso) | 0 | — | — | — | 12.80 % | 20.35 % | 53.39 % | — |
| M-A flexible, sin ensamble | -35.15 | [-43.58, -26.64] | -18.87 [-30.32, -7.35] | -50.67 [-62.98, -38.46] | 11.26 % | 18.14 % | 50.41 % | no |
| M-B flexible + ensamble (apilado) | +4.51 | [+0.20, +9.27] | +6.04 [-0.31, +12.57] | +3.06 [-3.49, +9.66] | 12.85 % | 20.18 % | 53.17 % | no |

Peso final del ensamble en M-B: 0.985. Banderas RD [(h−1), (h−2), hoy, ayer]: [-0.723, -0.304, -0.061, -0.002]
