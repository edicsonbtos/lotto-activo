# PREREGISTRO: ag13 en sombra (2026-10-15)

Escrito ANTES de escribir el código de ag13 y antes de que exista un solo sorteo puntuado con él. Todo lo de abajo
queda fijo: ningún valor se reajusta mirando el marcador de ag13.

## Qué es ag13
Un pronóstico en sombra, junto al ensamble y ag12. NO entra en el marcador principal ni en lo que se juega.
La cadena, en este orden y sin parámetros nuevos ajustados:

1. **ag12** congelado (ya existe, `sombra.corregir`).
2. **Regla RD** `con_rd`: ×0,50 al animal de RD (h−1):30 y ×0,75 al de (h−2):30 (igual que `ag12_rd`).
3. **Exposición** `exposicion.aplicar` en TODAS las horas: día−1, día, día+1, día+2, hora en 12 h y mes
   (multiplicadores congelados de `herramientas/modelos/exposicion.py`). Es la `ag12_rd_exp` que ya mide la sombra.
4. **Pronosticadores**: ×**0,862** a cada animal del conjunto U del día, y se renormaliza.
   U = unión de lo que publican `lotoven.com/datos/` y `loteriadehoy.com/datos/animalitos/` para Lotto Activo ese día
   (mismo U de `investigacion/2026-10-15/pronosticadores/`). 0,862 es el valor ajustado en confirmación 1 de ese estudio.
   No se reajusta.

La ventana de las 8:00 (`aplicar_8am`) NO se apila: sigue en su sombra aparte. ag13 usa la exposición base a las 8:00.

## Diagnóstico secundario (no decide nada): `ag13_nd`
Parte de lo que publican los pronosticadores es la fecha, que la exposición ya descuenta. Para ver si se cuenta dos veces,
se calcula también `ag13_nd`: igual que ag13, pero con ×**0,924** (el O/E de U sin lo explicado por la fecha, mismo estudio)
y solo a los animales de U que la exposición NO tocó ese sorteo (se excluyen día−1..día+2, hora en 12 h y mes).
Se reporta; no entra en ninguna regla de decisión.

## Qué se guarda al congelar (para poder auditar)
En el registro del pronóstico: `pron = {"u": [índices], "fuentes": {fuente: {n, bytes, sha256}}}`, leído de las páginas que
Railway ya guarda entre las 6:00 y las 7:55, ANTES del primer sorteo (una página bajada después de las 8:00 no vale). La
fecha impresa en la página tiene que ser la del día. El 8:00 se congela la noche anterior, cuando las páginas aún no existen:
a ese registro se le añade `pron` en cuanto la ventana de descarga cierra; es solo un insumo, no cambia su congelado. Si una fuente falta o la fecha de la página no es la del
día, se guarda `pron = {"falta": motivo}` y ese día NO cuenta para ag13. La exclusión depende solo de que falte el dato,
nunca del resultado, y el motivo queda escrito (lección del 2-oct 8:00, que quedó sin sombra sin explicación).
Hace falta que estén las DOS fuentes; con una sola no se puntúa.

## Muestra
Cuenta cada sorteo resuelto que tenga a la vez: pronóstico congelado del ensamble, ag12 y `pron["u"]`. Mismos sorteos para
todos los modelos comparados (pareado). El conteo empieza en el primer sorteo con `pron`; no hay retroactivo.

## Métricas (todas pareadas, IC 90 % por jornadas, el mismo `ic90_jornadas` del código)
- **P1 (decide):** Δ mbits = ag13 − ensamble (sobre el congelado sin la corrección de las 8:00, igual que ag12).
- **P2 (condición):** Top-5 escalonado en pp/ficha, ag13 − ensamble, ambos con la regla RD del Top-15 (`cambiar15`), no peor que −3.
- **Componentes (informativos):** ag13 − ag12_rd_exp (qué aporta pronosticadores); ag12_rd_exp − ag12_rd (qué aporta la exposición);
  ag12_rd − ensamble. Más el O/E de U contra la probabilidad de ag12_rd_exp normalizada, por jornadas.

## Regla (mirada única)
- **Mirada de decisión: n = 931 sorteos puntuados con pron** (≈ 78 días, ≈ finales de ene-2027 si arranca a fines de oct).
  **PASA** si el límite inferior del IC90 de P1 es > 0 y se cumple P2. No hay segunda mirada: si no pasa en 931, ag13 no
  se promueve como motor (el error de tipo I queda en 5 % unilateral, sin las dos miradas de ag12).
- **Freno (solo apagar):** con n ≥ 600, si P1 punto < −10 mbits, se apaga ag13.
- **Veredicto del componente pronosticadores, aparte, a E ≈ 350 aciertos esperados de U (≈ 140 días, ≈ 1.700 sorteos):**
  se conserva solo si O/E de U < 1 con IC95 superior < 1 y ag13 − ag12_rd_exp > 0 en punto. Si el motor global pasa en 931 pero
  este componente falla a 1.700, se vuelve a `ag12_rd_exp` (sin pronosticadores). Pasar P1 no avala por sí solo el 0,862.
- El resultado de ag13 NO cambia la decisión de ag12 del 14-dic (que sigue su regla propia). Aunque ag13 pase, entra a
  producción solo con tu OK expreso, con un anexo al preregistro.

## Lo que ya se sabe y por qué hay que ser escéptico (escrito antes de medir)
- Pronosticadores: desarrollo O/E 1,00 (nulo); confirmación 1 0,86; en vivo 0,70 (27 días). El 0,862 se ajustó en
  confirmación 1, así que lo único fuera de muestra es el vivo, con IC ancho. Más de la mitad se explica por la fecha.
- Posible contaminación: no se puede probar que los archivos por fecha sean lo publicado esa mañana. Esta sombra lo resuelve
  hacia adelante: guarda la página de la mañana antes del sorteo.
- ag12: +16,9 mbits, z = 1,14; la sellada 2019-2023 dio −1,2. Su prior es escéptico.
- Expectativa realista planificada: ag13 − ensamble ≈ +10 (ag12) +6 (exposición) +4 a +11 (pronosticadores), con solapes;
  potencia de pasar a 931 estimada en 0,5-0,9 según el efecto real. Si el efecto verdadero es 0, pasa con 5 %.
- Probar varias cadenas distintas y quedarse con la mejor es lo que se prohíbe: ag13 es UNA cadena, definida arriba.

## Falsación (resumen)
Si a n = 931 el IC90 de P1 incluye 0, o P2 falla, ag13 NO pasa. Si a n ≥ 600 P1 < −10, se apaga. Ninguna de estas reglas
se puede mover después de mirar.

---

# ANEXO 1 (2026-10-15): prueba sobre 2026, escrito ANTES de bajar el archivo de pronosticadores de 2026 y de correr nada

Pedida por el usuario: "correrlo en la prueba ciega de este año". Es **retrospectiva y se corre UNA sola vez**. No sustituye ni cuenta
para la mirada de decisión en vivo (n = 931) del cuerpo del preregistro.

## Tramo
`filas 9357..12510` de `historial.txt` = 2026-01-01..2026-09-16, con las fechas corregidas en memoria y SIN los días tocados por
`correccion_historial_2026-09-29.json` (mismo recorte que `herramientas/exploracion/ag12_2026_2026-10-07/analizar.py`, n ≈ 2.959).
Matrices congeladas, sin recalcular: `P_ens_fresco.npy` (ensamble) y `P_ag12_V1_fresco.npy` (ag12 V1, λ = 30, filas < 9357).
RD de `rdint_hist.csv` + `fresco_rd.csv`. Para U: archivo por fecha de lotoven y loteriadehoy, 2026-01-01..2026-09-14
(las fechas 09-15/09-16 ya estaban bajadas).

## Qué es virgen y qué no (declarado)
- **ag12:** NO virgen. Ya fue la 2.ª prueba ciega (+19,4) y la réplica de estabilidad (+20,1 [+11,8; +28,3]).
- **Regla RD (×0,50/×0,75):** NO virgen en este tramo (misma réplica).
- **Exposición (fecha/hora):** multiplicadores ajustados solo en dev-A (filas 2000..5687) y medidos en dev-B (2025). Sobre 2026 solo
  se midió la sombra en vivo (desde el 2-oct), así que esta réplica es en esencia virgen para ella. Si en algún informe previo se
  miró en 2026-ene..sep, no queda registrado aquí.
- **Pronosticadores (×0,862):** VIRGEN. Se ajustó con 2025-02..2025-12; el archivo de 2026-01..09-14 no se había bajado nunca.
  El vivo 2026-09-15..10-14 (O/E 0,70) ya se vio y NO se mezcla en esta prueba: queda fuera.

## Cadena (idéntica a ag13, sin reajustar nada)
`P_ag12_V1` → ×0,50 al animal RD (h−1):30 y ×0,75 al de (h−2):30 → `exposicion.aplicar` (todas las horas) → ×0,862 a los animales de U.
Más `ag13_nd` (×0,924 sin lo que la exposición ya tocó) como diagnóstico. Baseline: `P_ens_fresco` (sin la corrección de las 8:00, igual que la sombra).
U = lotoven ∪ loteriadehoy, Lotto Activo, solo si las DOS fuentes están y la fecha de la página es la del día. Los días sin U se excluyen
del análisis de pronosticadores (se reporta cuántos).

## Medidas (IC por bloques de jornada, 4.000 réplicas, semilla 20261015)
- **M1:** Δ mbits ag13 − ensamble (primaria global), IC90 e IC95.
- **M2:** Δ mbits ag13 − ag12_rd_exp (qué aporta pronosticadores) e IC90.
- **M3:** O/E de U contra ag12_rd_exp normalizado, estratificado por hora, IC95.
- **M4:** Top-3/5/15 y Top-5 escalonado en pp/ficha con la regla de cambio RD (retorno por ficha; paga 30) ag13 − ensamble.
- Desgloses descriptivos: por trimestre (T1 ene-mar, T2 abr-jun, T3 jul-sep16).

## Veredicto fijado antes
- **Componente pronosticadores PASA** si M2 tiene IC90 inferior > 0 **y** M3 da O/E < 1 con IC95 superior < 1.
  **NO PASA** si M2 tiene IC90 superior < 0, o M3 da O/E ≥ 1. Cualquier otro caso: NO CONCLUYENTE.
- **ag13 PASA en 2026** si M1 tiene IC90 inferior > 0, M4 ≥ −3 pp/ficha, y los tres trimestres de M1 son positivos.
  **NO PASA** si M1 IC90 superior < 0 o si M1 no se sostiene (IC90 inferior ≤ 0 en la muestra completa de ~3.000).
- Si ag13 pasa pero M2 no pasa, se dice que el avance viene de ag12 + exposición y NO de pronosticadores.
- Nada se reajusta con este resultado (ni 0,862, ni 0,924, ni el orden de la cadena).
- Placebo de pronosticadores: se repite M3 con los datos de otro día (d ± 7), como en el estudio previo; si da O/E < 1 también, el efecto
  es del calendario/modelo y no de lo que publican ese día.
