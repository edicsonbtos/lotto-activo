# PRE-REGISTRO — Ronda 3: ¿el operador esquiva los números que más juega la gente?

Escrito el 2026-10-01, DESPUÉS de la ronda 2 y de los placebos sobre todo el desarrollo de LA, y ANTES de
mirar ningún otro juego. Script: `ronda3.py`.

## Lo que se sabe al escribir esto (solo LA, desarrollo)
- Ronda 2 (pre-registrada): A1 "número = día del mes" O/E 0,71 en dev-A y 0,51 en dev-B → PASA.
  A2 "número = hora en reloj de 12 h" O/E 0,91 y 0,64 → PASA. A3 "popularidad estable" ρ = +0,33, p = 0,023
  → NO PASA (por poco).
- Placebos en TODO el desarrollo de LA (mirados; por eso en LA ya no se confirma nada):
  día+s: s = −1 0,87; **s = 0 0,61; s = +1 0,66**; s = +2 0,87; el resto entre 0,97 y 1,15.
  Hora 12 h + s: **s = 0 0,78**; el resto entre 0,89 y 1,10. Hora en 24 h por la tarde: 1,10 (nada).
  Mes (1..12): 0,86. Día de la semana: 1,08.
- Lectura: el operador parece evitar el número de la fecha (hoy y mañana) y el de la hora, que son
  números que la gente juega mucho. Encaja con un operador que elige resultados para pagar menos.

## Réplicas (juegos y tramos NUNCA mirados para esta hipótesis)
Tres pruebas por juego: **D0** número = día del mes, **D1** número = día del mes + 1 y **H12** número =
hora del sorteo en reloj de 12 h (8:30 cuenta como 8; 13:00 o 13:15 como 1). Solo números 1..36 (en Selva Plus
y Guácharo, 1..31 para el día y 1..12 para la hora, que existen en su tablero).
1. **RD Internacional** (mismo operador), tramo de desarrollo de RD 2024-03-01..2025-06-30
   (`verificacion/hilo9/datos/cache_todo.npz`, tramo == 'dev'). Esperado = probabilidad del modelo B1 de RD,
   que ya sabe lo de LA y lo de su propio día.
2. **LARD** (Lotto Activo RD, mismo operador, 14 sorteos de 8:00 a 21:00), `oficial_multi.csv` juego 3, todo
   (2025-07-01..2026-09-22). Esperado = frecuencia del número en LARD en ese tramo.
3. **La Granjita, Selva Plus, Guácharo** (otros operadores), 2026-04-13..09-13 (`datos_multiloteria/*.csv`).
   Esperado = frecuencia del número en cada lotería.

## Criterios
- Por juego, Bonferroni por sus 3 pruebas: **réplica** si O/E < 1 y el IC por bootstrap de jornadas al
  99,17 % (4.000 réplicas, semilla 20261001) no contiene 1.
- RD y LARD son el mismo operador: si al menos D0 o D1 se replica en los dos, la hipótesis "el operador
  esquiva la fecha" queda **CONFIRMADA** a nivel de operador.
- Otras loterías: descriptivo (dice si es una costumbre del sector). No cambia nada de LA.

## LA: corrección por exposición (descriptivo, contaminado)
Sobre P6 (ronda 1) se ajusta en dev-A una corrección log-lineal con indicadores día−1, día, día+1, día+2,
hora 12 h y mes (λ = 30), y se reporta en dev-B: Top-15, diferencia con P6 y con B1, mbits. Las variables
se eligieron mirando todo el desarrollo, así que **no da veredicto**; solo dice cuánto podría sumar y si vale
la pena ponerla en sombra.
