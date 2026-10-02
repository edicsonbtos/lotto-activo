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

## Enmienda (2026-10-01, ANTES del primer sorteo puntuable; auditoría de sesgo, código y seguridad)
La auditoría estadística encontró que el criterio original estaba mal calibrado. Se corrige ahora, antes de que
exista un solo sorteo en la cuenta, y la versión original queda arriba como historia.
1. **Potencia real.** El +6,1 mbits de dev-B es descriptivo y optimista. Con los multiplicadores congelados el
   efecto esperado es **≈ +2,3 mbits** por sorteo (sd ≈ 78). Con n = 930 el error típico es ≈ 2,6 mbits y la
   potencia al 5 % unilateral es **≈ 22 %**, no 80 %. Si el efecto fuera nulo, el valor esperado es ≈ −2,4 mbits
   (renormalizar cuesta), así que un "no pasa" a n = 930 **no informa**.
2. **Qué se hace con n = 930 (≈ 2026-12-19):** solo la mirada de freno (apagar si va claramente peor, regla de
   arriba). Un resultado no concluyente NO descarta la corrección.
3. **Decisión de encender:** con **n ≥ 6.000** sorteos del bloque `exposicion` (≈ 1,5 años; potencia ≈ 75-80 % para
   +2,3 mbits). Pasa si el límite inferior del IC 90 % por jornadas de la diferencia en mbits es > 0 y el Top-5 no
   queda más de 3 pp por debajo (límite inferior del IC 90 % por jornadas > −3 pp).
4. **Comparación primaria:** `ensamble_exp` frente a `ensamble` (es lo que se juega). `ag12_rd_exp` frente a
   `ag12_rd` se reporta como secundaria y no decide.
5. **IC por jornadas:** ya lo calcula `/api/sombra` → `exposicion.diferencias` (IC 90 % agrupando por fecha,
   media de la diferencia por sorteo en mbits y en pp de Top-5) y `exposicion.fallos` cuenta los sorteos en que
   la corrección falló (si > 0, esos sorteos no entran en los cuatro modelos a la vez).
6. **Réplica de la premisa en 2026** (`herramientas/exploracion/PREREGISTRO_fecha_2026.md`, `fecha_2026.py`,
   datos oficiales de LA): día R = 0,77 [0,60; 0,95], día+1 R = 0,73 [0,55; 0,90], hora 12 h R = 0,77 [0,58; 0,97];
   las tres PASAN. Es consistente en dirección con los multiplicadores congelados, pero D0 se debilita de
   may a sep (R = 0,92) y día−1, día+2 y mes no están replicados.
