# T1 / C2: decisiones fijadas ANTES de correr S2 en RD (2026-10-06)

- **Datos.** RD sale de `rdint_historial.txt` (13 031 sorteos, del 2023-09-04 al 2026-09-22) y LA, de la copia
  `hist_0605.txt` del arnés. La comparación se hace en 2025-07-01..2026-09-22, que son las filas 7886..13030.
- **Rasgos de S2-RD.** Se calculan con la secuencia de RD, con el mismo código congelado:
  - los 31 rasgos de M4 sin rd1, rd2 ni hay_rd (`M4/rasgos.construir(..., rd=None)`);
  - los 6 nuevos de `rasgos_s2.nuevos`, es decir, num_fecha_m1, par_evita, loglift, q_prior, q_post y llr.
- **ρ del modo normal.** Se usa el mismo procedimiento (`calibrar_rho`, media de repeticiones en 6 meses), pero con
  RD de 2025-01-01..2025-06-30, los 6 meses inmediatamente anteriores al tramo de comparación. La regla y el prior de
  0,2 no cambian. El ρ = 0,24 de LA no se transfiere tal cual, porque es un parámetro del juego y no un hiperparámetro
  del aprendizaje. Calibrarlo dentro del tramo miraría el futuro.
- **Rasgos de LA.** Son los mismos tres que usa el motor de RD (`herramientas/rdint/modelo.features`):
  - LA h:00 == i;
  - LA (h−1):00 == i;
  - salió hoy en LA a las h:00 o antes, sin contar h ni h−1.

  Así el conjunto de información es idéntico al del motor de RD. Hay una variante secundaria, solo informativa, que
  usa únicamente LA h:00.
- **Entrenamiento.** Se usa `motor_s2.correr("C", 90)` sin cambios: reentreno mensual de 2025-07 a 2026-09, LightGBM
  con los mismos PRM, ventana de 600 días, parada temprana con 60 días, MAXR 500, paciencia 40 e INI_FILA 300.
- **Rival.** Es el motor de RD walk-forward, igual que en `herramientas/rdint/prueba_ciega.py`:
  - B0 = secuencia_v3 desde la fila 2000, con reajuste cada 250;
  - B1 = `modelo.cruzado`, con b walk-forward (R = 250, mínimo 500, λ = 1).

  En vivo se usa b congelado (`coef_b1.json`, ajustado con datos hasta 2026-04-12), pero eso no vale para comparar
  walk-forward.
- **Criterio C2, tal cual el pre-registro.** S2-RD solo (w = 1) contra B1. Pasa si Δ mbits tiene IC 90 % por
  jornadas > 0. Como información se reportan también:
  - la mezcla log-lineal S2-RD^0,75 · B1^0,25, análoga a S2+PROD con w = 0,75;
  - Top-5 y Top-15 (ranking directo, sin regla de cambio);
  - Top-5 escalonado en plata;
  - los semestres por separado.
