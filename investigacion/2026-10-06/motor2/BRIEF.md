# Enjambre "motor 2" (2026-10-06): instrucciones comunes. Léelas enteras.
Lotto Activo: 38 animales (códigos "0","00","1".."36"; índice 0..37 con POS=["0","00","1",...,"36"]), 12 sorteos al día
(hora 0..11 = 8:00..19:00), pago 30x. El motor de producción (`ensamble_v2` + ajuste del primer sorteo + corrección
de fecha a las 8:00) saca unos +94 mbits por sorteo sobre el azar en la prueba ciega. El objetivo es superarlo.

## Lo que ya se sabe (no lo redescubras; léelo)
- `/home/user/lotto-activo/.claude/skills/lotto-nueva-idea/SKILL.md`: protocolo y la lista de ideas ya descartadas.
- `../semana/INFORME.md` (y A1-A6): en 2026, de mié a vie el operador deja de evitar repetir el animal en el día y el
  motor cae (O/E 0,82-0,85). En 2024-25 pasaba lo mismo el domingo. El día cambia sin avisar.
- `../adaptativo/INFORME.md`: un factor adaptativo por día de la semana y una temperatura global NO pasan.
- Estructura del operador: casi no repite en el día, recicla con 1 a 2,5 días de hueco, el primer sorteo esquiva el
  primero de ayer, y esquiva el número de la fecha y el de la hora.
- Código del motor: `/home/user/lotto-activo/herramientas/lotto_eval.py` y `herramientas/modelos/*.py`.

## Arnés OBLIGATORIO: `arnes.py` en esta carpeta (lee su docstring)
- `A.D`: historial hasta 2026-10-05. `A.T`: filas evaluables (10.744). `A.PROD`: probabilidades de producción por fila.
  `A.Y`, `A.F`, `A.H`, `A.DOW`.
- Tramos RECIENTES, porque lo que importa es cómo se comporta el operador AHORA. Un patrón de 2024 que en 2026 ya no
  aplica no sirve:
  - AJUSTE (2025-07-01..2026-02-28): para ajustar.
  - ELECCION (2026-03-01..06-30): para elegir entre variantes; se puede mirar todas las veces que haga falta.
  - PRUEBA26 (2026-07-01..10-05): **una sola vez**, con la versión final ya congelada; queda registrada.
  - ANTIGUO (antes de 2025-07): solo informativo.
  Tu motor puede APRENDER de toda la historia anterior a cada sorteo (walk-forward), pero se juzga en los tramos
  recientes. Prefiere modelos que se adapten rápido a cambios del operador (ventanas recientes, pesos que se olvidan).
- Tu P debe ser walk-forward: cada fila usa SOLO sorteos anteriores. Demuéstralo con `A.chequear_fuga` o con una
  prueba equivalente.
- Compara siempre contra producción (`A.evaluar` ya da Δmbits contra prod, con IC 90 % por jornadas). Prueba también
  la mezcla log-lineal con producción, p ∝ PROD^(1−w)·TUYA^w, con w elegido en ELECCION.

## Reglas
1. Antes de mirar resultados, escribe tu `PREREGISTRO.md` en `<tu_carpeta>` (= esta carpeta/<tu_id>/).
2. Escribe SOLO en tu carpeta y en el scratchpad
   `/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad`. Guarda ahí tu matriz
   final como `motor2_<tu_id>.npz` (P con forma (10744, 38)). No toques nada más: ni producción ni otros archivos.
   No hagas git, no uses la red.
3. Cómputo: unos 40 minutos como máximo de CPU en total (4 núcleos, 15 GB). Usa numpy, scipy y, si están instalados,
   sklearn/lightgbm (compruébalo).
4. Sé adversarial con tu propia idea. Si no gana en ELECCION, dilo y NO gastes PRUEBA26.
5. Al terminar: `INFORME.md` en tu carpeta y un resumen de 25 líneas como máximo, con la tabla de `evaluar` (AJUSTE,
   ELECCION y, si la usaste, PRUEBA26) y un VEREDICTO: MEJORA / NO MEJORA / DUDOSO.
