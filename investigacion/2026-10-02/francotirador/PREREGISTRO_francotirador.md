# PRERREGISTRO — "Estrategia Francotirador" (2026-10-02)

Origen: texto pegado por el usuario (informe de otro LLM). Se verifica ANTES de tocar código.
Solo tramo de desarrollo LA filas [2000, 9357) con `herramientas/exploracion/calor_cache.npz` (P, y). El tramo de prueba NO se mira.

## Verificación aritmética de las cifras del texto (sin hipótesis, es solo medir P)
- V1: ¿existe algún sorteo con entropía < 4,1 bits? ¿con masa Top-3 ≥ 0,60, Top-5 ≥ 0,60, Top-7 ≥ 0,60, Top-3 ≥ 0,15?
- Si ninguno: las reglas literales del texto no pueden ejecutarse (abstienen siempre o nunca) y se reemplazan por cuantiles.

## Hipótesis (7; IC 99,29 % por Bonferroni 0,05/7, bootstrap por jornada, 5000 réplicas, semilla 20261002)
Retorno por ficha del Top-5 escalonado 2-2-2-1-1 (pago 30, costo 8 fichas), equilibrio = 0.
- **F1 abstención por entropía**: jugar solo el 20 % de sorteos de MENOR entropía (cuantil dentro de cada hora). PASA si el IC del retorno por ficha queda entero >0
  Y la diferencia contra jugar todos queda entera >0 Y retorno >0 en ambas mitades (por jornadas).
- **F2** igual con el 10 % de menor entropía.
- **F3** igual con el 20 % de mayor masa Top-5 del ensamble (confianza).
  Diagnóstico adicional: O/E del Top-5 en el subconjunto (observados / suma de P). Si O/E≈1, el filtro solo selecciona sorteos donde el modelo ya predice más; no hay información extra.
- **F4 las 8:00 (hora==0)**: O/E del Top-15 (obs / Σ P Top-15) en hora 0. PASA si el IC de O/E queda entero >1.
  Descriptivo: probabilidad de una racha de 12 aciertos Top-15 seguidos en las 8:00 con la tasa observada y racha máxima real en desarrollo.
- **F5 lunes**: O/E del Top-5 los lunes, estratificado por hora (razón de sumas). PASA si el IC queda entero a un lado de 1 y las dos mitades van en la misma dirección.
- **F6 fríos extremos (>12 días de calendario sin salir)**: O/E del ensamble sobre esos animales (obs / Σ P). PASA si el IC queda entero >1.
- **F7 varianza condicional (GARCH)**: autocorrelación lag-1, dentro de hora, de la sorpresa s = −log2 P[y] centrada por hora. PASA (hay algo que modelar) si el IC de la correlación excluye 0.

## No verificables con estos datos (se documentan, no se prueban)
Sesgo del apostador / pari-mutuel (el pago es fijo 30x, no hay datos de volumen por animal); jitter de hardware del PRNG; HMM sobre estado del PRNG
(Turing ya cubrió PRNG/semilla y Markov 38x38: ruido). "Doble consecutiva / terminación": el índice de animal no trae el número de lotería en la caché; no se prueba.

## Veredicto
Una idea solo se propone para sombra en vivo si PASA en desarrollo; la aceptación solo viene del marcador en vivo (lotto-marcador).
Nada de esto cambia el modelo ni la jugada en producción.
