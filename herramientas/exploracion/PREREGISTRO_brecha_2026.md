# Pre-registro: la "brecha" del operador en 2026 — 2026-10-02

Escrito ANTES de calcular. Script: `herramientas/exploracion/brecha_2026.py`.

## Por qué
En 2025 el operador casi no repetía animal el mismo día (O/E 0,25-0,37) y el motor acertaba 55-57 % de Top-15.
En 2026 repite el doble y el Top-15 cayó a ~49 % (`INFORME_hora_8am_y_caida.md`). El usuario pide encontrar qué
hace distinto el operador en 2026 y si eso da una ventaja que el motor no está usando.

## Datos y tramos
- Lotto Activo hasta el 2026-09-29 (historial congelado + corrección de fechas + API oficial; 0 diferencias).
  RD Internacional (juego 2) y LARD (juego 3) de la API oficial; RD además de `rdint_hist.csv`.
- Probabilidades base: walk-forward del `ensamble_v2` de producción (`hora_cache.npz`).
- **2025 (referencia, ya mirado):** 2025-01-01..2025-12-18. Solo para poner al lado la brecha de 2025.
- **2026-A (descubrir):** 2025-12-19..2026-05-31. Aquí se eligen las variables.
- **2026-B (confirmar, una sola vez):** 2026-06-01..2026-09-29 (incluye el vivo reconstruido 14-29 sep).
- El juez final es el vivo desde el 2026-10-02.

Este tramo de 2026 ya se miró antes para otras cosas (regla RD, calor, otras loterías, hora). Ninguna de las
variables de abajo se midió en 2026 salvo "RD (h−1):30" (control conocido) y la fecha/hora (ronda 2, que se
pre-registró en desarrollo y aquí se confirma).

## Batería (cada variable marca, antes del sorteo t, un conjunto de animales)
- G, hueco en sorteos desde la última salida: 1, 2, 3, 4-6, 7-11, 12-17, 18-23, 24-35, 36-47, 48-71, 72-107,
  108-179, 180+.
- D, hueco en días: hoy, 1, 2, 3, 4, 5-6, 7-9, 10-14, 15+.
- C, conteos: veces en los últimos 24 sorteos (0, 1, 2, 3+), en los últimos 72 (0-1, 2, 3, 4, 5+).
- H, mismo día: salió hoy 1 vez y 2+ veces, por tramo de hora (8-11, 12-15, 16-19).
- Y, días anteriores: ayer a la misma hora, ayer a h±1, ayer por la mañana / mediodía / tarde, ayer a las 19:00,
  ayer 2+ veces, anteayer a la misma hora, hace 7 días a la misma hora, a la misma hora en alguno de los últimos 7 días.
- S, secuencia: anterior ±1, anterior ±2, misma última cifra que el anterior, cifras invertidas del anterior,
  el de hace dos sorteos.
- R, RD Internacional: (h−1):30, (h−2):30, (h−3):30, cualquiera de RD hoy antes de h, RD ayer (cualquiera),
  (h−1):30 ±1, misma última cifra que (h−1):30.
- L, LARD: (h−1):00, cualquiera de LARD hoy antes de h, LARD de anoche 20:00-21:00 (solo para las 8:00).
- F, fecha y hora: número = día del mes, día+1, día−1, hora en 12 h, mes, día de la semana (1-7).
- A, identidad: cada uno de los 38 animales.
- M, solo las 8:00: ayer 19:00 en LA, RD 19:30 de ayer, LARD 20:00/21:00 de ayer, cualquiera de LA ayer,
  cualquiera de LA anteayer.

## Medida
Para cada variable: O/E = ganadores dentro del conjunto / suma de la probabilidad que el ensamble le da al conjunto.
z = (O − E) / raíz(Σ q(1 − q)). Es un contraste contra el MOTOR, no contra el azar: mide lo que el motor NO tiene.

## Reglas
1. **Descubrir (2026-A).** Pasa a confirmación la variable con |z| por encima del percentil 95 del máximo |z| de toda
   la batería bajo la hipótesis nula (2.000 simulaciones con el ganador sorteado de las probabilidades del motor;
   así se corrige por número de pruebas y por la correlación entre variables) **y** con |O/E − 1| ≥ 0,10.
2. **Confirmar (2026-B), una vez.** Confirmada si O/E va en la misma dirección con p unilateral < 0,05/k (k = número
   de candidatas), con bootstrap por jornada (10.000, semilla 20261002).
3. **¿Sirve para jugar?** Corrección P' ∝ P·exp(Σ β·x) con β ajustados SOLO en 2026-A (máxima verosimilitud, L2 = 1)
   para las candidatas. En 2026-B: diferencia de mbits con IC por jornada, Top-5, Top-15 y retorno del Top-5
   escalonado y del Top-15 ponderado frente al ensamble. "Brecha 2026 útil" si Δmbits > 0 con IC95 que no toca 0.
4. **Fuerza bruta (exploratorio, mismo corte).** LightGBM con todas las variables + log P del ensamble, entrenado
   en 2026-A y medido en 2026-B. Solo cuenta si supera al ensamble en mbits con IC que no toque 0.
5. Si nada se confirma, la respuesta es "en 2026 el operador no tiene una brecha nueva aprovechable", con el perfil
   descriptivo de 2025 contra 2026 de toda la batería.
6. Nada se cambia en producción sin el vivo y sin la regla de `gestion_banca.VIGILANCIA`.

## Anexo (2026-10-02, escrito DESPUÉS de ver la batería principal y ANTES de correr esto)
La batería principal confirmó solo "RD (h−1):30". Para agotar la búsqueda se corre, con el MISMO protocolo, un
barrido de interacciones: cada variable de la batería (sin las 38 de identidad ni las M) × tramo horario
(8:00, 9-11, 12-15, 16-19). Umbral de descubrimiento: percentil 95 del máximo |z| del barrido entero bajo el nulo
(2.000 simulaciones). Confirmación en 2026-B con Bonferroni por el número de candidatas. Las interacciones de
"RD (h−1):30" no cuentan como hallazgo nuevo (ya está confirmada). Script: `brecha_2026_interacciones.py`.
