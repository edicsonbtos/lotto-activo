# Hilo 9 — anexo M: prueba de techo en LA (sólo desarrollo, walk-forward)

Filas evaluadas: 5789 (las 1500 primeras sólo entrenan). λ=1.0, reajuste cada 500 filas.

| modelo | Δ mbits vs ensamble | IC95 | 1ª mitad | 2ª mitad | Top-3 | Top-5 | Top-15 | pasa |
|---|---|---|---|---|---|---|---|---|
| ensamble_v2 (en uso) | 0 | — | — | — | 12.80 % | 20.35 % | 53.39 % | — |
| M-A flexible, sin ensamble | -38.33 | [-47.89, -28.49] | -24.34 [-37.75, -10.95] | -51.67 [-65.66, -38.05] | 11.57 % | 18.33 % | 50.08 % | no |
| M-B flexible + ensamble (apilado) | -4.42 | [-11.28, +2.83] | -4.30 [-14.95, +6.57] | -4.54 [-14.51, +5.45] | 12.71 % | 19.99 % | 52.50 % | no |

Peso final del ensamble en M-B: 0.953. Banderas RD [(h−1), (h−2), hoy, ayer]: [-0.996, -0.382, -0.068, -0.003]
