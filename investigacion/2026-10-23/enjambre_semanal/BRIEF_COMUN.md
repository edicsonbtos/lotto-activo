# Brief común — enjambre semanal 2026-10-23

Pregunta del usuario: ¿hay ciclos semanales, "reinicios" de la casa (empieza la semana debiendo), repelencias entre
Lotto Activo (LA, h:00) y RD Internacional (RD, h:30) por hora o fecha, y qué dice la semana actual frente al histórico?

## Reglas (protocolo `lotto-nueva-idea`, obligatorio)
1. Lee `.claude/skills/lotto-nueva-idea/SKILL.md` ANTES de empezar. Lista de ideas cerradas: no las repitas.
   Ya cerradas y relevantes aquí: paridad (alternancia, misma paridad que el anterior), color, docena, consecutivo,
   número = mes, número = día de semana, aves, hora del día, día de semana, lunes, domingo, quincena y festivos
   (`investigacion/2026-10-15/mas_jugado/`), días buenos/malos y rachas (`investigacion/2026-10-14/`),
   primer sorteo de hace 7/14/21/28 días (`investigacion/2026-10-03/enjambre_8am/ag01/`), RD (h−1):30 → LA h:00 (hilo 7),
   LA → RD (falló), LARD independiente (hilo 8), "todos los RD de hoy" (top15_70).
2. Escribe `PREREGISTRO.md` en tu carpeta ANTES de mirar resultados: hipótesis (familia cerrada), métrica, corte, umbral.
3. Datos de desarrollo LA: `verificacion/hilo9/datos/historial.txt` + `verificacion/hilo9/datos/calor_cache.npz`
   (P walk-forward del ensamble 7357×38, filas [2000, 9357) = 2024-03-07..2025-12-17). Plantilla de carga y de O/E con
   bootstrap por jornada: `investigacion/2026-10-22/bateria/dev.py` y `rasgos.py`. dev-A = primera mitad de días (descubre),
   dev-B = segunda mitad (confirma). **Filas ≥ 9357 de LA NO se tocan.**
4. Métrica: O/E del ganador contra el ensamble (Σ P del rasgo); mbits si propones una corrección. Contrastes entre grupos de
   sorteos estratificados por hora. Corrección por múltiples pruebas (Bonferroni sobre tu familia).
   Pasa desarrollo: mismo sentido en dev-A y dev-B con |z| ≥ 2 en cada mitad y |z| total ≥ umbral de Bonferroni.
5. Réplica independiente (solo lo que pase desarrollo): RD en su tramo de desarrollo 2024-03-01..2025-06-30
   (`datos_multiloteria/rdint_hist.csv`, línea base = uniforme sobre animales aún no salidos ese día, como en
   `investigacion/2026-10-22/bateria/replica_juegos.py`). Datos oficiales al día (LA=1, RD=2, LARD=3, desde 2025-07-01,
   actualizados hasta 2026-10-23): `datos_multiloteria/oficial_multi.csv` (fecha,juego,hora HH:MM,codigo).
6. No toques producción (`prediccion.py`, `servidor.py`, `modelos/`, `pesos_ensamble.json`, `herramientas/registro_final.jsonl`).
   No hagas commit. Trabaja solo dentro de tu carpeta `investigacion/2026-10-23/enjambre_semanal/<agente>/`.
7. Entrega `RESULTADO.md` (≤ 40 líneas, en español llano): tabla de cada hipótesis con O/E, IC, z en dev-A/dev-B,
   veredicto PASA/NO PASA, réplica si aplica, y una línea de "qué haría falta para confirmarlo en vivo".
   Un z de 2,5 sin réplica NO es señal. Si nada pasa, dilo sin suavizar.
8. Corre los scripts con `python -I` no es necesario (son datos propios). Tiempo de cómputo: mantenlo bajo (minutos).
