# PRERREGISTRO — "segmento de 1 y 2 días sin salir" contra el Top-5 (2026-10-02)

Idea del usuario: los animales con **1 o 2 días sin salir** (pestaña "Días sin salir" de la mesa) salen más que el azar
(descriptivo en todo el historial: LA O/E 1,105; RD 0,980). Pregunta: **¿el segmento agrega algo sobre el Top-5 del ensamble?**

## Definiciones (fijas, ningún parámetro se ajusta)
- Segmento S del sorteo (fecha f, hora h): animales cuyo ÚLTIMO resultado ANTERIOR AL SORTEO ocurrió en f−1 o f−2
  (días de calendario, mismo juego). Es `mesa_huecos` de servidor.py: usa solo sorteos estrictamente anteriores. Los de hoy (hueco 0) NO están en S.
- P = probabilidades del ensamble para ese sorteo (cachés de abajo). Ranking = orden descendente de P, empates por índice.
- Fichas Top-5 escalonado: 2-2-2-1-1 por puestos 1..5; cada ficha paga 30; costo = 8 fichas por sorteo.

## Hipótesis (por juego: LA y RD → 4 pruebas en total → IC 98,75 %, bootstrap por jornada, 5000 réplicas, semilla 20261002)
- **H1, filtro duro**: del ranking se quitan los animales fuera de S y se juega el Top-5 escalonado de lo que queda (S-Top-5).
  Métrica: diferencia de retorno por ficha (S-Top-5 − Top-5 normal), pareada por sorteo. PASA si el IC 98,75 % queda entero por encima de 0.
- **H2, información residual**: O/E del ensamble DENTRO de S = (salidas observadas con y∈S) / (suma de P sobre S), estratificado por hora (Mantel-Haenszel:
  suma de observados / suma de esperados dentro de cada hora, combinadas por razón de sumas con pesos por hora = esperado de la hora).
  PASA ("S agrega información que el ensamble no tiene") si el IC 98,75 % de O/E queda entero por encima de 1 **y** O/E>1 en las dos mitades del tramo.
  Si el IC contiene 1: el ensamble ya captura el segmento.
- Descriptivo, sin veredicto: O/E del ensamble fuera de S; O/E para Top-5∩S y Top-5\S; acierto del Top-5 normal contra el S-Top-5; |S| medio.

## Tramos
- Desarrollo (exploratorio, se mira primero, sin veredicto): LA filas [2000, 9357) con `herramientas/exploracion/calor_cache.npz` (P);
  RD `herramientas/rdint/cache_dev.npz` (P1, fila, y).
- **Ciego (UNA vez por agente, y solo después de dejar escrito su script)**: LA filas [9357, 12511) con
  `../lotto-activo-motor/motor_nuevo/reciente/P_ens_reciente.npy` (relativo a la raíz del proyecto); RD `herramientas/rdint/cache_todo.npz` (P1),
  tramos 'test' + 'desc'. Plantilla de carga: `herramientas/exploracion/filtros_tarde.py` (filas_la / filas_rd / boot). Se excluyen los días tocados
  por `herramientas/correccion_historial_2026-09-29.json` (antes y después) como en esa plantilla.
- Mitades: del tramo ciego, por jornadas (primera mitad / segunda mitad de las fechas únicas).

## Veredicto global
La idea "S mejora al Top-5" solo se acepta si **H1 pasa en el mismo juego en los DOS agentes independientes** (y H2 coherente). Si los dos agentes difieren
en el veredicto o en cifras relevantes, se investiga la diferencia de implementación antes de concluir. La confirmación definitiva sería el marcador en vivo.
