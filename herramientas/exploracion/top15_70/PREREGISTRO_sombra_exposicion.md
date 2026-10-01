# PRE-REGISTRO — Sombra en vivo de la corrección por exposición (fecha y hora)

Escrito el 2026-10-01, antes de que exista un solo sorteo puntuable (la cuenta empieza el 2026-10-02).

## Qué se mide
`/api/sombra` → bloque `exposicion`, sobre los MISMOS sorteos resueltos desde 2026-10-02:
- `ensamble` (el que se juega) y `ag12_rd` (sombra ya existente).
- `ensamble_exp` y `ag12_rd_exp`: los anteriores × los multiplicadores congelados de
  `herramientas/modelos/exposicion.py`: día−1 ×0,881, día ×0,816, día+1 ×0,750, día+2 ×0,984,
  hora (reloj de 12 h) ×0,955, mes ×0,903. Se ajustaron solo en dev-A y no se tocan más.
  Dependen solo del calendario, así que aplicarlos al puntuar no usa nada del futuro.

## Criterio (una sola mirada decisoria)
- Cuándo: con **n ≥ 930** sorteos en el bloque `exposicion` (~2026-12-19). N80 sale de dev-B: efecto
  +6,1 mbits, desviación 74,8 por sorteo, α = 5 % unilateral, potencia 80 %.
- **PASA** si `ag12_rd_exp` supera a `ag12_rd` en mbits y el límite inferior del IC 90 % por jornadas es > 0.
  La misma regla se aplica por separado a `ensamble_exp` frente a `ensamble`. Además, su Top-5 no puede quedar
  más de 3 pp por debajo.
- Freno: se puede mirar cada mes solo para APAGAR. Si con n ≥ 600 la diferencia es < −5 mbits, se descarta.
- Si pasa, se propone al usuario usar los multiplicadores en la jugada. Nada cambia la jugada sin su OK.
- El Top-15 se reporta, pero no decide: ver +0,8 pp exige ~3.150 sorteos.
