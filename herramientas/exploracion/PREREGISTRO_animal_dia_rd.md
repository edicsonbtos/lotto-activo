# PRERREGISTRO — "animal del día" en RD Internacional (2026-09-27)

Método congelado, igual que el de Lotto Activo (PREREGISTRO_animal_dia.md): Top-k del modelo B1 de RD en el primer sorteo
del día (8:30, ya con el resultado de LA 8:00), k = 1, 2, 3. ¿Sale al menos uno en el día? Azar exacto con los D animales
distintos del día.

Desarrollo (tramo 'dev' 2024-03-01..2025-06-30, ya visto):
- 1.ª mitad: k=1 z +1,91; k=2 z +1,84; k=3 z +0,05.
- 2.ª mitad: k=1 z +2,12; k=2 z +2,97; k=3 z +2,49.

**PASA para k si z ≥ 2,39** (Bonferroni por 3 k). Secundaria: retorno por ficha jugando hasta que sale, paga 30.
Tramo ciego: 'test' + 'desc' de cache_todo.npz (2025-07-01..2026-09-13). Ese tramo se usó para el modelo de RD y el
Top-15, **nunca para esta idea**. Una sola corrida (`python animal_dia_rd.py ciega`).
