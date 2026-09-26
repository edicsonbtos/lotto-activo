# Pruebas ciegas 3 y 4 de ag12: otros juegos (2026-09-26, escrito ANTES de correr)

## Por qué existe (declarado)
El usuario pidió dos pruebas ciegas más del motor nuevo. En Lotto Activo ya no queda historia sin mirar:
el sellado 2019-2023 y las filas >= 9357 están gastados, y el vivo solo lleva unos días.
Quedan dos series del mismo tipo de juego (38 animales) donde el mecanismo de ag12 NUNCA se miró:

- **Prueba 3: RD Internacional** (h:30), `datos_multiloteria/rdint_hist.csv`, 13.031 sorteos desde 2023-09-04.
  En esta serie se probó el hilo 7 (RD usando LA), pero nunca los pares consecutivos de RD consigo misma.
  `ag12_transiciones/sondeo_rd.py` solo puntuó sorteos de LA.
- **Prueba 4: Lotto Activo República Dominicana** (LARD, juego 3 de la API oficial, 14 sorteos al día de 8 a 21),
  `datos_multiloteria/oficial_multi.csv`, desde 2025-07-01. El hilo 8 solo miró si LARD evita a LA o a RD.

Pregunta: ¿el operador de ESE juego también evita repetir un par consecutivo reciente (s1→i)?
Si sí, el mecanismo de ag12 es una costumbre general y no una casualidad del desarrollo de LA.

## Qué se congela (sin reajustar nada con estos datos)
- Solo las 6 transiciones de ag12 **V0**, con los pesos de `ag12_transiciones/parametros_V0.json`
  (commit c4a2b17, ajustados solo en LA filas [2000, 9357)): T1 −0,457, T2 −0,614, T3 −0,284, R1 −0,339, R2 −0,332, R3 −0,043.
  Los rasgos salen de `rasgos12.transiciones()`, el mismo código. V1 no se usa porque sus 27 rasgos de ag02 están atados al ensamble de LA.
- Modelo probado: Q ∝ P_base · exp(x·w).
- **Base RD**: `secuencia_v3` corriendo walk-forward sobre RD desde la fila 2000 (es el B0 de RD en producción).
- **Base LARD**: `secuencia_v3` supone 12 sorteos al día y LARD tiene 14, así que se usa una regla fija sin ajuste:
  P ∝ 0,38 si el animal ya salió hoy en LARD, y 1 si no. El 0,38 es la razón medida en LA (política f, 2026-09-15).
- Filas puntuadas: RD [2000, n); LARD desde el primer sorteo de la jornada 31 (así las ventanas de 30 jornadas tienen historia).

## Criterio (uno por prueba)
- Primaria: Δmbits = media de 1000·log2(Q(y)/P_base(y)). IC por bootstrap de días (4.000 réplicas, semilla 20260926).
- **Bonferroni k = 2** → IC bilateral 97,5 %. **PASA si el IC queda entero por encima de 0.**
- Secundarias, solo descriptivas: O/E del par s1→i de hace 2-7 jornadas frente a la base; Top-5 y Top-15 de la base
  y del modelo con transiciones.
- Qué significa cada resultado:
  - Pasan las dos: la costumbre es del operador y ag12 gana credibilidad para LA.
  - Pasa una: señal mixta.
  - No pasa ninguna: la evitación de pares no se generaliza, lo que no invalida la 2.ª prueba en LA pero no la refuerza.
- Potencia (dicha antes): en LA el aporte forward de V0 fue ~+12 mbits. Con ~11.000 sorteos en RD el error típico es de ~2 mbits,
  así que un efecto de la mitad de tamaño ya se vería. LARD (~5.800 sorteos) tiene la mitad de potencia.
- Se corre UNA vez (`prueba_ciegas34.py` se niega a repetir). Se informa el resultado sea cual sea.
