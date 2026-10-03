# PREREGISTRO ag05 — "La cadena de los primeros sorteos es una serie propia"

Escrito el 2026-10-03, ANTES de mirar el tramo de prueba (no se ha calculado nada en prueba ni en vivo).

## Hipótesis
El operador gestiona el primer sorteo del día como una lista aparte (bolsa sin reposición, o balanceo de
frecuencias solo entre primeros sorteos). Si es así, en la subserie de primeros sorteos (ordenada por día con
sorteo; j = índice en la subserie) debería verse, más allá de lo que ya captura `P_aj`:
1. Evitación acumulada: el ganador cae menos de lo esperado en el conjunto C_k = "salió como primer sorteo en
   alguno de los últimos k primeros sorteos", k = 1..15 (y por posición exacta: lag k).
2. Coleccionista: el nº de primeros sorteos hasta ver los 38 animales es menor que bajo azar / bajo P_aj.
3. Balanceo: animales con pocas apariciones como primer sorteo en los últimos 38/76 salen más.
4. Hueco entre apariciones del mismo animal como primer sorteo distinto de la geométrica (p = 1/38).

## Métricas
- O/E = observados / Σ P_aj[ganador ∈ grupo], IC Poisson exacto; dev por era (9:00 = dev con hora 1;
  8:00 = dev con hora 0). 'cal' solo conteos crudos contra 1/38.
- Ganancia: mbits por primer sorteo = 1000·mean(log2(q[y]/P_aj[y])), IC bootstrap de días (2000 réplicas).
- Lag 1 y lag 3 ya están en P_aj (×0,272 y ×1,736): su O/E en dev debe ser ≈ 1 por construcción.

## Selección
Exploración libre en dev (se cuenta cuántas cosas se miran). A prueba van como mucho 3 candidatos, cada uno una
corrección multiplicativa sobre P_aj (renormalizada) con multiplicadores ajustados SOLO en dev
(suavizado +0,5 en O y E por grupo), elegidos por p en dev Y mismo signo en las dos eras de dev.
Contraste en prueba: mbits > 0, p unilateral por bootstrap de días (P(mbits ≤ 0)), más O/E del grupo.
CONFIRMADO: p < 0,0017 y mismo signo en las dos eras de dev. PROMETEDOR: p < 0,05. Si no, NULO.
Si ningún candidato alcanza en dev p < 0,01 (tras contar comparaciones) con mismo signo en ambas eras,
no se envía nada a prueba y el veredicto es NULO.

## Candidatos elegidos en dev
(se rellena abajo ANTES de ejecutar prueba; ver sección "ADENDA")

## ADENDA (tras explorar dev, antes de mirar prueba) — 2026-10-03
Se miraron 69 contrastes en dev (explorar_dev.out, extra_dev.out). Ninguno llega a p < 0,01 en dev; el mejor
con mismo signo en ambas eras es "posiciones {2,4,5}" (O/E 1,25, p = 0,089; +3,8 mbits en dev dentro de muestra,
P(≤0) = 0,16) y el coleccionista (T = 135 contra 157 bajo P_aj, p = 0,09; por era 0,22 y 0,59).
Por la regla pre-registrada **NO se envía ningún candidato a prueba**. Prueba y vivo quedan sin mirar.
