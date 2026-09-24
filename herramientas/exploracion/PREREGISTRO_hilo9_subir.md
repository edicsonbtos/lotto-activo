# PRE-REGISTRO — Hilo 9: ¿qué sube los porcentajes de LA y RD sobre los modelos actuales?

Escrito el 2026-09-23, ANTES de calcular ninguno de los números de abajo. Objetivo del usuario: subir
Top-5 / Top-15 con evidencia verificable por terceros.

## Principio
Todo se mide **por residuo contra el modelo en uso**: ensamble_v2 para LA (`calor_cache.npz`, P
walk-forward de desarrollo) y B1 para RD (`rdint/cache_todo.npz`, P1 walk-forward). Una variable sólo
sube los porcentajes si el animal marcado sale MÁS o MENOS de lo que el modelo YA le asigna.
Esperado bajo el modelo = suma de P sobre los animales marcados; varianza = suma p(1−p). Se estratifica
por hora (se reporta O/E global y por hora).

## Tramos (sólo desarrollo)
- LA: filas 2000..9357 con fecha < 2025-12-15 (se excluye el tramo con fechas corridas del historial).
- RD: tramo 'dev' de cache_todo (2024-03-01..2025-06-30).
Ni la prueba ciega de LA (≥ 9357) ni la de RD (2025-07-01..2026-04-12) se miran en este hilo.

## Batería cerrada (9 hipótesis, Bonferroni: pasa si p < 0,05/9 = 0,0056, dos colas)
Reciclaje entre juegos de días anteriores (nunca probado; el reciclaje propio 1-2,5 días sí existe):
- **R1** RD h:30 ← salió en LA AYER (cualquier hora).
- **R2** RD h:30 ← salió en LA ANTEAYER.
- **L1** LA h:00 ← salió en RD AYER.
- **L2** LA h:00 ← salió en RD ANTEAYER.
Mismo día, más allá de lo que ya usan los modelos:
- **R3** RD h:30 ← salió en LA hoy 2+ veces (B1 sólo tiene "salió hoy").
- **L3** LA h:00 ← salió en RD (h−2):30 (el (h−1):30 ya es la regla de cambio; H4 "salió hoy en RD"
  falló a ciegas, esto es sólo el lag 2).
- **R4** RD h:30 ← salió en RD hoy (¿B0 captura bien la auto-evitación de RD?).
Mejora del modelo base de RD (no es una variable, es un ensamble):
- **E1** RD: mezcla log-lineal de P1 (B1) con intradia_v2 de RD (`_b0_intradia_v2.npz`), peso ajustado
  walk-forward por bloques de 250 filas. Pasa si Δ mbits ≥ +5 con IC95 > 0 en ambas mitades de dev.
- **E2** LA: calibración de temperatura del ensamble — NO se prueba (ya cerrada: calibración OK).
  Se deja como control negativo declarado; no cuenta en Bonferroni. (Queda 8 + E1 = 9.)

## Paso 2 (sólo para lo que pase el paso 1)
Término softmax con un coeficiente walk-forward (reajuste cada 250 filas, como B1) → Δ mbits en dev
por mitades (≥ +5 e IC95 > 0 en ambas) y retorno por ficha del Top-5 escalonado (IC por jornadas).

## Paso 3 (confirmación)
Lo que pase el paso 2 se congela (código + coeficientes) y se confirma en el **marcador en vivo** con
un registro paralelo, y opcionalmente UNA vez en la ventana de réplica de RD 2026-04-13..09-13 (ya
mirada una vez para Top-15: contaminación declarada). Nada se lleva a la jugada sin pasar el paso 2.

## Si nada pasa
Se documenta el techo: con lo conocido, los porcentajes actuales son el máximo demostrable, y se deja
todo reproducible (scripts + caches + este archivo) para verificación independiente.

## ANEXO 2026-09-23 (después de los pasos 1 y 2, ANTES de correr esto) — M: prueba de techo
Resultado de pasos 1-2: L3 y R4 son reales en residuo pero aportan +1,4 y +0,3 mbits: no pasan.
Se añade UNA prueba más (no estaba en la batería; cuenta como comparación nueva):
- **M-A (techo flexible):** modelo de elección condicional (softmax sobre 38) con ~100 variables en
  tramos (hueco en sorteos × franja horaria, segundo hueco, conteos en 36 y 120 sorteos, veces hoy ×
  franja, días desde la última, RD (h−1):30, RD (h−2):30, RD hoy, RD ayer), L2, walk-forward
  (reajuste cada 500 filas, sólo filas pasadas), SIN el ensamble. Pregunta: ¿un modelo flexible con
  todo junto supera al ensamble?
- **M-B (apilado):** lo mismo + log P del ensamble como variable. Pregunta: ¿queda algo sin capturar?
- Tramo: LA dev (filas 2000..9357, fecha < 2025-12-15, con RD). Las primeras 1500 filas sólo entrenan.
- Pasa si Δ mbits contra el ensamble ≥ +5 con IC95 > 0 en ambas mitades evaluadas. Si M-B no pasa,
  queda documentado que con estos datos no hay estructura capturable por encima del ensamble.
