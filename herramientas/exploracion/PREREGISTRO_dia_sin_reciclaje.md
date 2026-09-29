# PRERREGISTRO — "día sin reciclaje" (2026-09-28)

Origen (mirado en vivo el 2026-09-28, NO es evidencia): hoy el Top-5 de LA estuvo lleno de animales con 1-2 días de hueco
(el reciclaje que el motor ya captura) y los ganadores vinieron de animales ausentes 3-10 días. En RD pasó igual
(ganadores con 4-5 días de hueco). LA 0/8 en Top-5, RD 0/7 en Top-15.

Definiciones (iguales para las dos teorías):
- G(t) = animales cuya última salida fue hace ≥ 3 días de calendario (o nunca) y que no han salido hoy.
- Mañana = horas 0..5 (8:00-13:00 LA; 8:30-13:30 RD). Tarde = horas 6..11.
- Exceso de la mañana E = (ganadores de la mañana en G) − (suma de P del motor sobre G en esos sorteos).
- Día C ("sin reciclaje") = E ≥ +1,5.
- Métrica en la tarde: O/E_G = ganadores en G / suma de P sobre G, en la tarde de los días C. IC95 por bootstrap de días.
- También O/E_G de la tarde de los días no-C, como control.

**T1 (Lotto Activo):** caché walk-forward `calor_cache.npz`, tramo de desarrollo, por mitades.
**T2 (RD Internacional):** `rdint/cache_todo.npz`, P1 (modelo en vivo), tramo dev 2024-03-01..2025-06-30, por mitades.

**PASA** si en las dos mitades el IC95 del O/E_G de la tarde de días C queda entero por encima de 1.
Si no → NO PASA: la mañana "sin reciclaje" no dice nada de la tarde y lo de hoy fue azar.
Una sola corrida. No se toca el tramo de prueba de LA ni el de RD.
