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

## Enmienda (2026-10-02, ANTES del primer sorteo puntuable; auditoría de `revisor-sesgo`)
1. **Mirada única fijada en el código.** El estadístico decisorio se calcula sobre los **primeros 1.600 sorteos
   válidos** (por fecha y hora) y no cambia al seguir acumulando (`decision` en `/api/sombra`). `todo` es solo
   informativo. Esto evita elegir el momento favorable después de 1.600.
2. **Qué señal aporta qué.** brecha26 mezcla dos señales: exposición (que ya tiene su propia sombra, con decisión a
   n ≥ 6.000) y RD fuera del Top-15. Aunque brecha26 pase a 1.600, **la exposición no se enciende por esta vía
   antes de su propio criterio**. Se publica la contrastación secundaria "solo sacar RD del Top-15 (sin
   exposición) − producción" (`secundaria_solo_rd_fuera_top15_pp`). Si brecha26 pasa pero la secundaria no, solo
   se propone la parte de RD. Referencia 2026 (descriptiva): RD solo +1,2 pp; con exposición +2,17 pp.
3. **El segundo criterio ("ponderado ≥ 0") es redundante**: con el Top-5 idéntico y 23 fichas en los dos brazos,
   el ponderado por ficha es (30/23) × la diferencia del Top-15. Se deja como informativo; decide solo el Top-15.
4. **Potencia realista** (sd 0,241; n = 1.600; umbral ≈ +0,99 pp): efecto +1,04 pp (2025) → 53 %; +1,5 pp → 80 %;
   +1,78 pp (jun-sep 2026) → 90 %; +2,17 pp (cifra elegida viendo 2026) → 97 %. El rango esperado realista es
   +1,0 a +1,8 pp, no +2,2.
5. **La regla de utilidad del pre-registro de la búsqueda NO se cumplió**: Δmbits de "Ensamble + confirmadas"
   fue +8,6 [−1,3; +16,7] (toca 0). El híbrido por Top-15 es exploratorio y su cifra está elegida viendo 2026.
6. Un registro malo (scores nulos o en cero, orden incompleto o con duplicados) se salta y se cuenta en
   `registros_saltados`; no apaga el bloque.
