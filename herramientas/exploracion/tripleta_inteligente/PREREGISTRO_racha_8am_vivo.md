# PRE-REGISTRO — Vigilancia en vivo: ¿la racha de las 8:00 trae inercia?

Escrito el 2026-10-02 (noche), ANTES de la primera madrugada que cuenta (2026-10-03). Lo pidió el usuario.
Lo mide la web: `/api/racha_8am` (`servidor.py`, `marcador_racha_8am`). No cambia la jugada ni el registro.

## De dónde sale (ya visto, por eso no puede confirmarse con esos datos)
`rachas_y_grupos.py`, época nov-2025..sep-2026, 314 madrugadas: el Top-15 de las 8:00 acertó 56,9 % tras una
madrugada con acierto y 41,9 % tras un fallo (+15 pp; +11,5 pp dentro del mismo mes). Pero en 2025 no existía
(+1,8 pp), en nov-2025..abr-2026 casi no (+3,6 pp), y el Top-5 escalonado de las 8:00 rindió al revés (+15 % tras
acierto, +29 % tras fallo). Es una **pista**, no un hallazgo.

## Qué se mide
- Datos: los pronósticos CONGELADOS de la web (modelo del marcador), sorteo de las 8:00, desde **2026-10-03**.
- Par = dos madrugadas en días seguidos de calendario, las dos con resultado y orden completo. "Acierto" = el
  ganador quedó en el puesto 1-15 del orden congelado.
- Se reporta: Top-15 de la madrugada después de un acierto y después de un fallo, la diferencia, z de dos
  proporciones, y el Top-5 escalonado (2-2-2-1-1, pago 30) por ficha en cada caso.

## Criterio (una sola mirada decisoria)
- Cuándo: al llegar a **300 pares** (~2027-07-30). Con +15 pp la potencia es ~80 %; con +11,5 pp, ~64 %.
- **PASA** si la diferencia es > 0 y z ≥ 1,645 (5 % unilateral) **y** el Top-5 escalonado tras un acierto no
  rinde menos que tras un fallo (punto).
- Si pasa, se le propone al usuario jugar el Top-15 de las 8:00 SOLO tras un acierto, en sombra primero. Nada
  cambia la jugada sin su OK.
- Antes de los 300 pares la web muestra el conteo, pero dice "midiendo"; ningún número parcial decide.
