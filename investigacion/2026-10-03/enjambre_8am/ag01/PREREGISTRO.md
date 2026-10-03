# PREREGISTRO ag01 — Mapa de memoria completo del primer sorteo
Escrito (parte 1) ANTES de mirar dev en detalle y SIN mirar prueba. La parte 2 (candidatos) se añade tras dev y antes de prueba.

## Hipótesis
El ganador del primer sorteo del día d coincide con más/menos frecuencia de lo que dice el motor (P_aj) con el
ganador del sorteo en la posición j (orden dentro del día, 0 = primero) del día d−k (calendario; si el día d−k no
tuvo sorteos, la fila no aporta a ese rasgo).

## Rasgos (familia de dev)
- A: (k, j) con k = 1..14, j = 0..11 (j=11 solo existe en días de 12 sorteos) → 168 rasgos.
- B: primero de hace k días, k = 15..30 (k=1..14 ya están en A, j=0) → 16 rasgos.
- C: último sorteo de hace k días, k = 1..30 (para k≤14 coincide con una celda de A) → 16 nuevos (k=15..30).
- Total ≈ 200 contrastes distintos. Controles: (k=1, j=0) y (k=3, j=0) ya están en P_aj → deben dar O/E ≈ 1.
- Estructura (agregados, contrastes adicionales declarados): paridad de k (k par vs impar, todas las j);
  ciclo semanal del primero (k = 7, 14, 21, 28 juntos, j=0) vs resto de k del primero.

## Métrica
O = nº de primeros sorteos con y = S[d−k, j]; E = Σ P_aj[t, S[d−k, j]]. O/E con IC Poisson exacto 95 %.
p bilateral Poisson exacta en dev (dos eras juntas). Benjamini-Hochberg q = 0,10 sobre la familia de ~200.
Requisito adicional: mismo signo (O/E>1 o <1) en era 9:00 (hora 1) y era 8:00 (hora 0) de dev.
Control crudo en 'cal' (sin motor): O contra N/38.

## Confirmación (prueba, una sola vez, ≤ 3 candidatos)
Multiplicador m = (O_dev + 0,5)/(E_dev + 0,5) ajustado en dev, aplicado sobre P_aj y renormalizado.
Prueba: O/E contra P_aj, p unilateral Poisson en el sentido de dev. CONFIRMADO si p < 0,0017 y mismo signo en las
dos eras de dev; PROMETEDOR si p < 0,05; si no, NULO. mbits por primer sorteo con IC bootstrap por días.

## Parte 2 — resultados de dev y candidatos (escrita ANTES de mirar prueba)
Contrastes mirados en dev: 200 rasgos del mapa + 33 agregados de estructura (paridad 2+2, ciclo semanal 2+1,
por posición j 12, por k 14) = 233. Ninguno de los 200 rasgos pasa BH (q mínimo 0,87). Controles: primero de
ayer O/E 0,43 (O=1, E=2,3) y primero de hace 3 días O/E 1,02 (28/27,5) → el ajuste de producción está bien.
Sin patrón por paridad de k ni ciclo semanal (k=7,14,21,28: O/E 0,94).

Candidatos (multiplicador por ML en dev con L2=1 sobre log m, aplicado sobre P_aj y renormalizado):
- C1 "salió en los 2 días anteriores" (ayer en posición ≥1, o anteayer en cualquier posición; indicador):
  m = 1,378. Dev O/E 1,18 (321/271,5), 9:00 1,30, 8:00 1,11. Sentido: >1.
- C2 "salió en la posición j=3 en los últimos 14 días" (conteo; m^conteo): m = 1,201. Dev O/E 1,21
  (283/234,1), 9:00 1,19, 8:00 1,22. Sentido: >1. (Sin mecanismo conocido; el conteo crudo en 'cal' da 0,87.)
- C3 "ganador de la posición 6 de hace 8 días" (mejor celda del mapa, q=0,87): m = 0,434. Dev O/E 0,40
  (7/17,7), 9:00 0,41, 8:00 0,38. Sentido: <1. Se espera que sea ruido; sirve de control del barrido.
Prueba (261 filas, una sola vez): p unilateral Poisson del O/E contra P_aj en el sentido indicado.
CONFIRMADO p < 0,0017 (los tres cumplen mismo signo en las dos eras de dev); PROMETEDOR p < 0,05; si no, NULO.
Además: mbits por primer sorteo con IC bootstrap por días (2000 réplicas), Top-5/Top-15 y retorno por ficha.
