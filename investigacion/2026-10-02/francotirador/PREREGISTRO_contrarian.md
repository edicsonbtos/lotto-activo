# PRERREGISTRO — "Motor Contrarian" (2026-10-02)

Origen: segundo texto pegado por el usuario. Afirma que el público persigue a los atrasados y el operador los bloquea, que "racha caliente" se penaliza, que 5-8 sorteos sin salir es una "zona muerta" con bonus, que las 8:00 no tienen penalizadores, y que la terminación del animal anterior sirve de desempate.
Solo desarrollo LA [2000, 9357), caché `calor_cache.npz` (P del ensamble walk-forward). No se mira el tramo de prueba. Unidad de "sorteos sin salir" = sorteos (como dice el texto), contados antes del sorteo.

Pregunta clave: el ensamble YA ve el hueco y las repeticiones. Una regla solo agrega algo si el ensamble se equivoca en ese segmento: O/E = salidas / ΣP dentro del segmento.

## Hipótesis (6; IC 99,17 % Bonferroni 0,05/6, bootstrap por jornada, 5000 réplicas, semilla 20261002b)
- **C1 "atrasados"**: hueco > 12 sorteos. PASA (penalizar tiene sentido) si IC de O/E entero < 1 y ambas mitades < 1.
- **C2 "racha caliente"**: el animal salió en alguno de los 2 sorteos anteriores. PASA si IC entero < 1 y ambas mitades < 1.
- **C3 "zona muerta"**: hueco entre 5 y 8 sorteos inclusive. PASA si IC entero > 1 y ambas mitades > 1.
- **C4 "8:00 sin penalizadores"**: O/E de C1 en hora 0 vs en las otras horas. PASA si en hora 0 el IC contiene 1 y en el resto queda entero < 1 (la regla solo vale si hay diferencia).
- **C5 terminación**: tabla de transición 10×10 de la terminación del ganador anterior (label numérico, "00" = 0) → siguiente, estimada solo con el pasado (walk-forward, suavizado Laplace). Métrica: log-verosimilitud adicional por sorteo de multiplicar P por el factor de terminación (renormalizado) contra P sola; PASA si el IC de la mejora media por sorteo queda entero > 0 y ambas mitades > 0.
- **C6 estrategia completa**: P' = P × (0,5 si C1; 0,7 si C2; 1,3 si C3; 1 si no), renormalizado, salvo hora 0 (P sin cambios). Multiplicadores fijados aquí, sin ajustar. Retorno por ficha del Top-5 escalonado (2-2-2-1-1, pago 30) de P' menos el de P, pareado por sorteo. PASA si IC entero > 0 y ambas mitades > 0.

## Descriptivo (sin veredicto)
Fracción de animales por sorteo en C1; O/E por hora de cada segmento; la misma C1 con hueco medido en días (ya hecho en F6: O/E 0,811).

## Veredicto
Nada va a producción por desarrollo. Si algo pasa C6, se propone sombra en vivo; confirmación solo desde el marcador.
