# ag04_no_estacionario: prerregistro (2026-09-25, escrito antes del experimento principal)

## Hipótesis
La política del operador cambia con el tiempo (deriva lenta o cambios de régimen), de modo que un
ensamble que **se adapta más rápido** que el ensamble_v2 predice mejor.

El ensamble_v2 ya es adaptativo, pero lento: pesos log-lineales reajustados cada R=250 sorteos con
olvido exponencial tau=3000 sorteos (~250 jornadas); intradia_v2 reajusta cada 100 con tau=1500 y
ventana 4500; haz_v1 cada 500 con vida media 4000. Si la política deriva en escalas de semanas,
estos olvidos son demasiado largos.

## Mecanismo y variantes (3, fijadas ahora)
Insumo común: predicciones walk-forward de los submodelos (intradia_v2, secuencia_v3, haz_v1) sobre
`datos.prefijo(9357)` desde la fila 1000 (igual que `ensamble.py`), en `cache_sub_*.npy`.
Control: reconstruir el ensamble_v2 con esas L y comprobar que coincide con la caché del arnés.

- **V1 (primaria): filtro de Kalman sobre los pesos del ensamble.** Estado w_t (3 pesos log-lineales)
  como paseo aleatorio w_t = w_{t-1} + ruido N(0, q·I). Observación y_t ~ softmax(L_t·w_t).
  Actualización de Laplace (Kalman extendido para GLM) sorteo a sorteo:
  Σ⁻ = Σ + qI; H = Cov_p(L_t) (3×3); Σ = (Σ⁻⁻¹ + H)⁻¹; w ← w + Σ·(L_t[y] − E_p[L_t]).
  La predicción de la fila t usa w tras procesar solo los sorteos < t. Arranque en la fila 1000 con
  w0 = (1/3,1/3,1/3), Σ0 = 0,1·I (calentamiento 1000..1999, fuera de la evaluación).
  **q** se elige en la rejilla {1e-7, 1e-6, 1e-5, 1e-4} por **cross-fitting en 5 bloques contiguos de
  jornadas** del desarrollo: para las filas del bloque b se usa el q con mejor log-verosimilitud
  media en los otros 4 bloques (el filtro corre siempre hacia adelante; solo q se elige fuera del bloque).
- **V2: reajuste con olvido corto.** Mismo ajuste que `ensamble.ajustar_pesos` (L2 λ=5 hacia 1/3),
  pero reajustando cada R=50 sorteos y con tau en {300, 1000, 3000}, elegido por cross-fitting en los
  mismos 5 bloques.
- **V3: submodelos rápidos.** Se añaden al ensamble dos versiones con olvido corto:
  intradia_v2(tau=400, ventana=1500) y haz_v1(vida_media=800, ventana=2000, cada=250). El ensamble
  de 5 componentes usa exactamente el procedimiento de ensamble_v2 (R=250, tau=3000, λ=5, sin
  parámetros ajustados nuevos, así que no necesita cross-fitting).

## Métrica y barra
`arnes.evaluar(P)`: Δmbits frente a la caché del ensamble. Pasa si Δ ≥ +3, IC95 inferior > 0 y
Δ > 0 en las dos mitades. Se informan las 3 variantes; el candidato es V1 salvo que no pase y otra sí
(en tal caso se dice que se eligió entre 3).

## Qué la falsa
Si V1, V2 y V3 dan Δ < +3 mbits o IC que cruza 0, la hipótesis de deriva aprovechable queda
descartada: el ensamble ya se adapta lo suficiente. Un q o tau elegido en el extremo "sin cambio"
(q=1e-7, tau=3000) también es evidencia en contra.

## Diagnóstico informativo (no decide)
Trayectoria de los pesos del filtro de Kalman en el tiempo, y Δmbits por trimestre.
