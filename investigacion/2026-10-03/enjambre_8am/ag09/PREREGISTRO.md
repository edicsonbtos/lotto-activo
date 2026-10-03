# PREREGISTRO ag09 — escrito ANTES de mirar prueba (2026-10-03)

Hipótesis: la regla del primer sorteo (esquiva el 1.º de ayer ×0,272; premia el 1.º de hace 3 días ×1,736) se cuenta
en días ABIERTOS, no de calendario, y/o su fuerza depende del día de la semana.

Lo mirado en dev (y 'cal' crudo), scripts `explorar_dev*.py`: 16 O/E (k=1..4 × cal/abierto × era), 10 filas tras cierre,
28 celdas O/E por día de la semana (k=1,3 × era × 7 días) + 4 heterogeneidades + 8 grupos (lun/sáb/dom/mar-vie × era)
+ partición lun-vie/sáb-dom (6 celdas) + 4 conteos crudos en cal. Total ≈ 70 cosas miradas.

Resumen dev: (1) tras cierre, 0 de 7 (E≈0,1) repiten el 1.º del último día abierto → sin información. En las 21 filas dev
donde k=3 de calendario y de abiertos discrepan: calendario O=1 (E=0,44), abiertos O=0 (E=0,50). (2) Ninguna regla
explica mejor. (3) Heterogeneidad por día de la semana no significativa (p_MC 0,28–1,00), pero el premio k=3 parece
concentrarse en lun-vie (O/E 2,16) frente a sáb-dom (0,47), mismo signo en las dos eras (9:00: 1,79 vs 0,57;
8:00: 2,39 vs 0,40), binomial condicional p=0,012 SIN corregir (elegido a posteriori). OJO: el conteo crudo de 'cal'
va en sentido CONTRARIO (sáb-dom 4/1,34, lun-vie 4/3,32). (4) En dev no hay días incompletos.

## Candidatos (2), fijados en dev, se aplican tal cual en prueba
- **C1 (días abiertos)**: igual que producción (×0,272 k=1, ×1,736 k=3, exige misma hora) pero k se cuenta en días
  abiertos (días con algún sorteo en el historial). Solo cambia filas tras un cierre.
- **C2 (premio solo laborables)**: k=1 de calendario ×0,272 igual que producción; k=3 de calendario ×2,117 en
  lun-vie (m = (26+0,5)/(12,02+0,5), ajustado en dev contra P) y SIN premio en sáb-dom.

## Métrica y umbral (una sola vez en prueba, 261 primeros sorteos)
- Principal: ganancia en mbits por primer sorteo contra `P_aj` = 1000·mean(log2(q[y]/P_aj[y])), IC 95 % por bootstrap
  de días (2000 réplicas, semilla 0); p unilateral = fracción de réplicas con media ≤ 0.
- C2 además: binomial condicional "aciertos k=3 en sáb-dom ≤ obs dado el total", E contra P sin ajuste.
- CONFIRMADO: p < 0,0017 y mismo signo en las dos eras de dev. PROMETEDOR: p < 0,05. Si no, NULO.
- Expectativa honesta: C1 cambia ~10-15 filas de prueba → potencia casi nula; se espera NULO.
- Vivo (15 filas) solo se reporta.
