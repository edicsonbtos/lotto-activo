# PRE-REGISTRO — Tripleta inteligente (cuándo comprarla, cuántas combinaciones, lista negra)

Escrito el 2026-10-02 ANTES de medir. Script: `medir.py` (misma carpeta).

## Regla de la tripleta (como la usa la web)
3 animales; se cobra 45x si los 3 salen en los 12 sorteos que empiezan en el siguiente. La web genera
2 tripletas (puestos 1-2-3 y 4-5-6 del modelo `herramientas/tripleta_ventana.py`) cada 24 h.

## Datos y tramos
- `verificacion/hilo9/datos/historial.txt` cortado en la fila 9357: **solo desarrollo**. Los inicios van de
  2000 a 9345, para que ninguna ventana use sorteos del tramo de prueba.
- Modelo: `tripleta_ventana.Modelo()` con sus parámetros de producción, walk-forward (se reajusta cada 250
  inicios con ventanas ya terminadas).
- **dev-A** = inicios < 5688 (elige); **dev-B** = inicios en [5688, 9345] (mide una vez).
- IC por bootstrap de jornadas (las ventanas se solapan), 3.000 réplicas, semilla 20261002.

## Preguntas
- **Q1. ¿A qué hora conviene comprarla?** EV por ficha de la estrategia A según la hora del primer sorteo de
  la ventana. Candidata a priori: **8:00** (ventana = el día entero; el "no repetir" del día da más animales
  distintos y sube la base). También la mejor hora de dev-A. En dev-B, cada una frente a "cualquier hora".
- **Q2. ¿Cuántas combinaciones?** Todas las tripletas de los k primeros, C(k,3), con k = 3, 4, 5 y 6; además A
  (123 + 456) y B (123 + 124). Se reporta EV por ficha y la probabilidad de cobrar algo en la ventana. Se elige
  en dev-A la de mayor EV y se mide en dev-B.
- **Q3. Lista negra.** A, pero saltándose los animales con número = día o día+1 de la fecha del primer sorteo
  (se toma el siguiente de la lista). Diferencia de EV en dev-B.

## Criterio
- **MEJORA** sobre A a cualquier hora: diferencia de EV por ficha > 0 en dev-B y su IC 95 % no incluye 0.
- La tripleta tiene muchas menos jugadas que la apuesta simple. Si el IC cruza 0, se dice "no se distingue" y
  no se cambia nada de la web.
- La confirmación final es el marcador de tripletas en vivo.

## Anexo 1 (2026-10-02, DESPUÉS de ver dev-B y ANTES de mirar 2026) — réplica débil única en 2026
Resultado en dev-B: C3 (solo la 1-2-3) le gana a A por +41 pp [+2,5; +81] → MEJORA; lista negra +17,8 pp
[+1,8; +33,8] → MEJORA; la hora no importa. 2025 fue un año "fácil" (el ensamble rindió más). Para saber qué
esperar HOY se mira **una sola vez** abr-sep 2026:
- Datos: `herramientas/exploracion/enjambre_2026-09-30/reentreno/historial_la.txt` (fechas corregidas, hasta
  2026-09-29). Modelo walk-forward igual que arriba. Inicios con el primer sorteo entre 2026-04-01 y el último
  inicio cuya ventana termina el 2026-09-29.
- Estas filas de LA ya se miraron por otros motivos, pero nunca para tripletas por ventana: es **réplica
  débil** y se anota en `herramientas/registro_final.jsonl`.
- Se reporta el EV por ficha [IC 95 %] de A, C3, A + lista negra y C3 + lista negra, y las diferencias con A.
- **Se adopta C3 + lista negra** en lo que se recomienda al usuario si en 2026 su EV es > 0 y su diferencia
  con A no es negativa (punto). Si el EV de todas da IC por debajo de 0, se dice que la tripleta no rinde en 2026.

## Anexo 2 — la racha de las 8:00 (descriptivo)
- R1: lista de los ganadores de las 8:00 desde 2026-09-14: hueco en días, si salió ayer, puesto en el ensamble
  (recalculado walk-forward con `reentreno/sub.py todo` + `comun.combinar`) y si entró en el Top-15.
- R2: en desarrollo (8:00 = hora 0, desde 2024-11-28), ¿cuántas rachas de N madrugadas seguidas con hueco
  1-3 días hay, y qué se espera por azar con la tasa de las 8:00?
- R3: en desarrollo, ¿una racha predice la siguiente? Se compara P(hueco 1-3 | las 3 anteriores lo fueron)
  con la tasa general. Sin umbral: es descriptivo y no cambia la jugada.
