# Preregistro ag3 — repelencias cruzadas LA h:00 / RD h:30 (rueda, fecha, hora, opuesto)

Escrito ANTES de correr nada. Protocolo `lotto-nueva-idea` + BRIEF_COMUN. No se repite: RD h:30 evita el animal de LA h:00;
LA h:00 evita RD (h-1):30; LA evita RD (h-2):30; LA->RD a nivel de modelo; "todos los RD de hoy".

## Alineación
Índice de hora j = hora-8 (LA h:00 = j; RD h:30 = j). Par "RD antes": LA (fecha, j) con RD (fecha, j-1), j>=1 (la hora 8:00 no entra).
Par "LA antes": RD (fecha, j) con LA (fecha, j), j>=0. Rueda: RUEDA de `bateria/rasgos.py`; vecinos = distancia circular 1;
opuesto = distancia 19. Se excluye del desarrollo de LA la fecha 2025-12-17 (la historia hilo9 no coincide con el oficial ese día).

## Datos y cortes
- Objetivo LA (C1, C3, C4, C5): filas [2000, 9357) de hilo9/historial.txt; base = P walk-forward del ensamble (calor_cache.npz),
  renormalizado. dev-A / dev-B = primera / segunda mitad de los DÍAS. Filas >= 9357 de LA no se tocan.
- Objetivo RD (C2 y espejos): RD 2024-03-01..2025-06-30 (rdint_hist.csv, nombres mapeados con rdint_vivo.NOMBRE), partido en
  dos mitades de días. Base uniforme sobre animales de RD aún no salidos ese día, sin el ganador de LA h:00 de ese par.
- Métrica: O/E = observados con el rasgo / Σ P(rasgo); z = (O-E)/sqrt(Σ e(1-e)); IC95 por bootstrap de jornadas.

## Familia (5 hipótesis, Bonferroni 0,05/5 => |z| >= 2,576 bilateral en el total)
- C1 LA h:00 frente a los vecinos de rueda (±1) del ganador de RD (h-1):30. Esperado: O/E < 1. Sensibilidad (no decide):
  misma cosa con el animal de RD (h-1):30 puesto a 0 en la base (regla de cambio ya en producción).
- C2 RD h:30 frente a los vecinos de rueda (±1) del ganador de LA h:00. Esperado: O/E < 1. Espejo temporal de C1 (el primer
  juego precede 30 min al segundo).
- C3 (una sola hipótesis) "acoplamiento de fecha": en LA h:00, cuando RD ya sacó HOY (sorteos 8:30..(h-1):30) el número igual al
  día del mes, LA lo esquiva MÁS que de costumbre. Estadístico: sobre los sorteos LA con ese subgrupo (G1), O1 observados del
  número-día contra E1' = r0 * ΣP, con r0 = O/E del número-día en el resto de sorteos (G0) con día-número en 1..31 y j>=1;
  z = (O1-E1')/sqrt(r0*Σp(1-p)). Esperado: O1 < E1'. Si G1 tiene < 30 de esperado (ΣP), se declara "sin potencia" y no pasa.
  Descriptivo aparte (no entra en la familia): O/E del día del mes en RD con base uniforme (ya medido 0,78) en este desarrollo.
- C4 LA h:00 frente al número (h-1) en reloj de 12 h (el de la hora de RD (h-1):30; 12 si h-1 = 12 o 0), j>=1. Debe diferir del
  número de la propia hora. Esperado O/E < 1. Placebo descriptivo: número h+1.
- C5 LA h:00 frente al animal opuesto en la rueda (d=19) del ganador de RD (h-1):30. Esperado O/E < 1.

## Criterio
PASA desarrollo: mismo sentido en dev-A y dev-B, |z| >= 2 en cada mitad y |z| total >= 2,576. Sentido contrario al esperado
también cuenta como señal (se reporta) pero el esperado es <1.
Réplica (solo lo que pase): 
- C1 <-> C2 se replican entre sí (espejo temporal, juegos contrarios): ambos deben pasar en dev.
- C2 además, si pasa: tramo oficial RD 2025-07-01..2025-12-17 (oficial_multi.csv, juego 2 con LA juego 1), base uniforme igual.
  Ese tramo no se ha usado para vecinos de rueda cruzados (hilo 7 lo usó para el animal exacto, otra idea); se documenta.
- C4 (RD espejo C4r): RD h:30 frente al número de la hora del RD anterior (h-1 en 12 h), base uniforme sin LA h:00.
- C5 (espejo C5r): RD h:30 frente al opuesto en la rueda (d19) del ganador de LA h:00.
- C3: espejo en RD: RD h:30, G1 = LA ya sacó hoy el número-día; mismo estadístico.
  Las réplicas de espejos C4r/C5r/C3r se corren en RD dev 2024-03-01..2025-06-30 y, si pasan, en el oficial 2025-07-01..2025-12-17.
Réplica pasa: mismo sentido, z <= -1,645 (unilateral 5 %) en el tramo independiente.
Un z de 2,5 sin réplica NO es señal.
