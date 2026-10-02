# PRE-REGISTRO — Sombra en vivo del "Top-15 con la brecha 2026"

Escrito el 2026-10-02, antes de que exista un solo sorteo puntuable: la cuenta empieza el **2026-10-03**.
Origen: `INFORME_brecha_2026.md`. El usuario pidió armarlo y ponerlo en sombra el 2026-10-02.

## Qué se mide
`/api/sombra` → bloque `brecha26`, sobre los MISMOS sorteos resueltos desde el 2026-10-03:
- **producción**: el orden congelado con el cambio RD del Top-5, el que muestra la web.
- **brecha26** (`herramientas/modelos/brecha26.py`):
  - Top-5: idéntico al de producción.
  - Puestos 6-15: las probabilidades congeladas del ensamble × exposición (multiplicadores congelados de
    `herramientas/modelos/exposicion.py`), sin los 5 de arriba y sin el animal de RD (h−1):30.
  - El animal de RD queda 16º.
  - De 9:00 a 19:00. A las 8:00 no hay RD de la misma mañana: solo actúa la exposición.
- Solo usa el congelado, el calendario y RD (h−1):30, que sale antes de LA h:00. Por eso se calcula al PUNTUAR
  sin usar nada del futuro, igual que `marcador_cambio_rd` y la sombra de exposición.
- Nada de esto cambia la jugada ni el marcador principal.

## Referencia (2026, ya mirado, optimista porque la forma híbrida se eligió viendo 2026)
- Top-15: 49,26 % → 51,43 % (+2,17 pp [+1,38; +2,98]).
- Ponderado: +2,83 pp por ficha [+1,81; +3,89].
- Por sorteo: la diferencia del Top-15 vale +1 el 4,0 % de las veces y −1 el 1,8 % (sd 0,241).
- La diferencia del ponderado por ficha tiene sd 0,314.

## Criterio (una sola mirada decisoria)
- **Medida principal:** diferencia del Top-15 (brecha26 − producción) por sorteo, con IC 90 % agrupando por jornada
  (ya lo calcula `_ic90_jornadas`).
- **Cuándo:** con **n ≥ 1.600** sorteos en el bloque (~mediados de febrero de 2027). Con un efecto real de +1,5 pp,
  la potencia es 80 % (al 5 % unilateral). Con +2,17 pp, la potencia es 97 %.
- **PASA** si el límite inferior del IC 90 % de la diferencia del Top-15 es > 0 **y** la diferencia del ponderado
  por ficha es ≥ 0.
  - Si pasa, se propone al usuario usar brecha26 en los puestos 6-15 de la jugada.
  - El Top-5 no se toca.
  - Nada cambia sin su OK ni sin la regla de `gestion_banca.VIGILANCIA`.
- **NO PASA:** cualquier otro resultado a n ≥ 1.600. Se archiva.
- **Freno (solo para apagar):** se puede mirar cada mes. Si con n ≥ 600 la diferencia del Top-15 es < −1 pp, se
  apaga y se archiva.
- Mirar antes de tiempo **no** permite encender.

## Lo que no cuenta
- Los sorteos antes del 2026-10-03, incluidos el vivo del 14-sep al 2-oct.
- Rachas: la regla es la de arriba.
