# PREREGISTRO ag06 — "el motor está mal calibrado en el primer sorteo" (escrito ANTES de mirar prueba)

Fecha: 2026-10-03. Datos: base8.npz; línea base P_aj (con ajuste ×0,272 / ×1,736 de producción).
Solo filas de primer sorteo. Dev = 263 (era 9:00) + 372 (era 8:00). Prueba = 261 (8:00), se mira UNA vez.

## Lo explorado en dev (36 bins O/E + 3 temperaturas + validación cruzada entre eras)
- Puesto del ranking P_aj (5 bins): nada (O/E 0,91–1,10, todos p > 0,25).
- Temperatura q ∝ P_aj^β: β* = 0,81 ± 0,20 (era 9:00), 1,01 ± 0,11 (era 8:00), 0,97 ± 0,10 (dev). Ganancia ≤ +2 mbits
  in-sample y NEGATIVA en validación cruzada entre eras para todo λ. **La temperatura está bien calibrada.**
- Hueco en días (0 = salió ayer): hueco 0–1 O/E 1,18 en dev (322 vs 273,2; era 9:00 1,30, era 8:00 1,11, mismo signo);
  hueco 2–3 0,83 (era 9:00 0,64, era 8:00 0,97). Horas exactas, conteos 3/7 días y franja de ayer: nada adicional
  que sobreviva a 36 contrastes (mínimo p = 0,004 en bins sueltos de la era 9:00 que la era 8:00 no replica).
- Control: en las demás horas de dev el motor está calibrado por hueco (O/E 0,94–1,03). El exceso es del primer sorteo.

## Candidatos (parámetros fijados en dev, en parametros_dev.json / aquí)
- **C1** (principal): q ∝ P_aj · exp(c·1[hueco ≤ 1 día]), c = ln 1,287 (λ = 20 por validación cruzada entre eras).
- **C2**: 4 bins de hueco {0–1, 2–3, 4–6, 7+}: multiplicadores 1,170 / 0,915 / 0,967 / 0,966 (λ = 50 por VC).
- **C3**: solo temperatura, β = 0,967 (MLE en dev). Es la hipótesis tal como se enunció; se espera NULO.

## Métrica y umbrales (prueba, 261 primeros sorteos)
- Principal: mbits por primer sorteo = 1000·mean(log2(q[y]/P_aj[y])), IC 95 % y p unilateral (H1: > 0) por bootstrap
  de días (10 000 réplicas, semilla 6). CONFIRMADO si p < 0,0017 y mismo signo en las dos eras de dev (C1 y C2 lo tienen;
  C3 no aplica: en dev era 9:00 β < 1 y era 8:00 β ≈ 1). PROMETEDOR si p < 0,05. Si no, NULO.
- Secundario (descriptivo): O/E del bin hueco 0–1 en prueba contra P_aj, IC Poisson exacto; Top-5/Top-15 y retorno por ficha.
- Potencia estimada: SE ≈ 11 mbits con n = 261; el efecto esperado en la era 8:00 de dev es +6/+7 mbits → p < 0,0017 es casi
  imposible; lo realista es PROMETEDOR o NULO.
