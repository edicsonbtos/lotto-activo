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

## Anexo 3 (2026-10-02, ANTES de mirar) — PRUEBA CIEGA de "una tripleta al día" (C3) y cambio en la web
El usuario pide una tripleta al día, probada a ciegas, y que se aplique a la web si pasa.
- **Tramo ciego:** inicios del 2025-12-18 al 2026-03-31 cuya ventana de 12 sorteos termina a más tardar el
  2026-03-31. Datos de `reentreno/historial_la.txt` (fechas corregidas). La tripleta por ventana NUNCA se miró
  en ese tramo: la réplica de 2026 empezó el 04-01, y la mirada del 2026-09-14 fue a la tripleta "del día"
  (`tripleta.py`), que es otro modelo y otra regla. Se anota en `registro_final.jsonl`.
- **Modelo:** `tripleta_ventana.Modelo()` de producción, walk-forward.
- **Jugada probada (C3):** UNA tripleta, los 3 animales más probables para los 12 sorteos siguientes.
- **Medida principal:** EV por ficha con 45x sobre todos los inicios del tramo (equivale a comprar una al día a
  cualquier hora; la hora no importa, Q1). IC 95 % por bootstrap de jornadas (3.000, semilla 20261002).
- **PASA** si EV > 0 y el límite inferior del IC 95 % > 0. Además, C3 no puede ir por debajo de A (2 tripletas)
  en el punto.
- **Secundario (solo informa):** una al día comprada a las 8:00 (ventana = el día) y una al día a las 9:00.
- **Si PASA:** la web genera 1 tripleta (la 1-2-3) cada 24 h, en vez de 2. No cambia nada más (ni la cadencia,
  ni el modelo, ni el marcador; las tripletas viejas se siguen puntuando igual).
- **Si NO PASA:** la web no se toca.

## Anexo 4 (2026-10-02, ANTES de mirar) — la regla de las 8:00 en el motor y en la tripleta
Script: `regla_8am.py`. Desarrollo = filas < 9357. "Post-desarrollo" = 2025-12-18..2026-09-29, fechas
corregidas. La tripleta ya se miró ahí hoy (anexos 1 y 3) y el LA de esas fechas muchas veces, así que es
**réplica débil** y se anota en `registro_final.jsonl`. El juez final sigue siendo el marcador en vivo.

**Parte A — ¿el motor (ensamble) ya está optimizado para las 8:00?**
- A1 (desarrollo): O/E del ganador de las 8:00 contra lo que esperaba el ensamble, en 3 grupos: salió ayer,
  hace 2-3 días, hace 4+ días. Si los tres quedan entre 0,90 y 1,10, **el motor ya está optimizado** y no se
  prueba nada más en la parte A.
- A2 (solo si A1 falla): corrección solo a las 8:00, P' ∝ P · m_g, con m_g ajustado por máxima verosimilitud
  en las 8:00 del desarrollo. En post-desarrollo se mide la diferencia de mbits a las 8:00 [IC 95 % por
  jornadas] y el Top-5 escalonado. Si los mbits dan IC > 0, se propone **en sombra**; no entra a la jugada.

**Parte B — la tripleta con la regla de las 8:00 (modelo T8)**
- T8 = `tripleta_ventana` + 13 variables: "salió ayer" × posición de inicio de la ventana (12) y "es el animal
  de las 8:00 de hoy" (1). Mismo ajuste walk-forward, mismos parámetros.
- Medida principal: log-verosimilitud de "sale en los 12" por animal (mbits por animal-ventana), T8 menos base.
  Secundaria: EV por ficha de la jugada actual de la web (A: 123 + 456) y de C3.
- Desarrollo: inicios en dev-B [5688, 9345]. Post-desarrollo: inicios del 2025-12-18 con ventana que termina
  a más tardar el 2026-09-29.
- **PASA** si la diferencia de mbits es > 0 con IC 95 % > 0 en dev-B **y** en post-desarrollo, y el EV de A con
  T8 no queda por debajo del base (punto) en post-desarrollo.
- **Si PASA:** la web usa T8 para armar sus 2 tripletas (misma cadencia y mismo marcador). Si no pasa, no se toca.
