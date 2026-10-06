# Pre-registro: días de mucho reciclaje (2026-10-06, antes de ver resultados)
Pregunta del usuario tras el 5-oct (9 de 12 ganadores de Lotto Activo habían salido ayer o anteayer).
R(día) = ganadores del día que habían salido en los 2 días de calendario anteriores (0..12). Motor = producción
(walk-forward ensamble_v2 + ajuste del primer sorteo + corrección de las 8:00). dev = filas < 9357; prueba = desde ahí.
1. Descriptivo: cuántos días tienen R ≥ 9 y cómo rinde el motor esos días (Top-15, mbits).
2. ¿Se puede SABER a tiempo? R de la mañana (8:00-1 PM, 6 sorteos) → Top-15 y O/E contra el motor en la tarde
   (2 PM-7 PM). Señal si en dev el O/E del Top-15 de la tarde en mañanas de R ≥ 5 se aparta con |z| ≥ 3 y en prueba
   va en el mismo sentido con p < 0,05.
3. ¿Persiste al día siguiente? Correlación de R entre días seguidos y Top-15 del día siguiente tras R ≥ 9.
Nada de esto cambia la jugada; si algo pasa va a sombra.

## Añadido 2026-10-06 (antes de ver): días malos en 2026
Día malo = Top-15 ≤ 4 de 12. Solo 2026 (dentro de prueba + vivo): frecuencia, R esos días, rachas de días malos,
Top-15 del día siguiente, y día de la semana (descriptivo; "domingo" ya falló a ciegas en 2026-09-27).
