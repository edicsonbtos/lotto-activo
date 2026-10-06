# M2 · Fugas de calendario más allá del día de la semana (2026-10-06)
Pre-registro: `PREREGISTRO.md`. Scripts: `comun.py`, `pruebas.py` → `pruebas2.py` (pruebas), `correccion.py`, `fijo.py`,
`wf.py`, `wf2.py`, `final.py`. Salidas: `salida_*.txt`, `pruebas2.json`. Matriz: `<scratchpad>/motor2_M2.npz` (P 10744×38).

## 1. Patrones de calendario: NINGUNO (residuo contra PROD)
Grupos: pago (1, 15, 16, 30, 31), quincena 15-16, fin de quincena 30-31-1, viernes de quincena, inicio de mes (1-3), fin de
mes (últimos 3), feriados VE 2025-26, fines de semana largos. Métricas: Top-15 O/E, mbits, "ya salió hoy", reciclaje
"ayer o anteayer", fecha {d−1, d, d+1}, número de la hora. Todo **más allá del día de la semana**: E se reescala por día de
la semana, y las etiquetas se barajan entre días con el mismo día de la semana.
- AJUSTE: 48 tests, **0 pasan BH-FDR q=0,10**. El p mínimo es 0,049 (fin de semana largo × reciclaje), lo que se espera
  por azar. Nada se confirma.
- Día de la semana × hora (¿el relajo de mié-vie es de tarde?): la interacción no pasa. Top-15 ×1,14 en AJUSTE y ×0,83 en
  ELECCION, con el signo invertido.
- Fecha × día de la semana (¿esquiva más la fecha en los días de mucha jugada?): no. Fecha O/E fin de semana/resto 1,04 y
  0,78, viernes 1,07 y 0,81, pago 1,00 y 0,74. Nada se acerca a la significación.
- Desviación del pre-registro, declarada: con conteos minúsculos (feriados, fines de semana largos), el SE por bootstrap
  daba z falsos (O = 0 ⇒ SE ≈ 0; p. ej. "fin de semana largo × hora", con z −5 en `salida_pruebas.txt`). Se usó la otra vía
  pre-registrada: p por permutación de jornadas en cada test, más BH.
- Control, exposición general (fecha, hora, mes; PROD no la lleva fuera de las 8:00). En AJUSTE gana +8 mbits y en
  ELECCION da −0,5 a 0,0. **En el régimen actual no suma.**

## 2. Lo que sí se confirma es solo día de la semana (ya conocido) → corrección adaptativa
Pasa FDR en AJUSTE y se confirma en ELECCION (familia "semana", 24 tests):
- sáb-dom: "ya salió hoy" ×0,41 / ×0,73 y reciclaje ×1,13 / ×1,12;
- mié-vie: "ya salió hoy" ×2,1 / ×1,9 y mbits −61 / −76;
- viernes: "ya salió hoy" ×2,0 / ×1,5.
Corrección: logit = log PROD + β·[ya salió hoy] + β'·[ayer o anteayer], con β por clase (lun-mar / mié-vie / sáb-dom).
Se reajusta cada semana con los días anteriores, con olvido de semivida H y L2. Se eligió en ELECCION entre 12 variantes,
más 7 clases, más una mezcla w:
**V1, H = 60 días, w = 0,75**. Las variantes con temperatura (V2) o con exposición (V3, V4) no mejoran en ELECCION, y
H = ∞ pierde (−5 en AJUSTE). Esto confirma que la regla se mueve y que hay que adaptarse rápido.

| M2_final | n | mbits | Δ vs PROD [IC90] | Top-5 (prod) | Top-15 (prod) | ret Top-5 (prod) |
|---|---|---|---|---|---|---|
| AJUSTE | 2748 | +166,2 | +5,37 [+2,68; +8,06] | 21,6 (21,2) | 54,5 (54,6) | +31,7 % (+29,1) |
| ELECCION | 1392 | +86,9 | +7,90 [+2,87; +12,93] | 20,2 (20,1) | 48,1 (48,6) | +27,4 % (+23,4) |
| PRUEBA26 (una vez) | 1164 | +118,6 | **+9,52 [+4,12; +14,93]** | 19,2 (18,6) | 51,5 (49,6) | +16,9 % (+14,4) |

Fuga: se alteraron el futuro (ganadores y categorías) en 3 cortes y las filas anteriores no cambian (OK). PROD ya es
walk-forward.

## Cautelas (adversarial)
- La partición lun-mar / mié-vie / sáb-dom viene del enjambre `semana`, que miró todo 2026, **incluido el tramo de
  PRUEBA26**. La prueba no está del todo limpia para la elección de las clases. La versión neutra, de 7 clases (una por
  día), da +4,7 [−1,5; +11,0] en ELECCION: va en la misma dirección, pero el IC toca 0.
- Se eligió 1 de unas 20 variantes en ELECCION. La ganancia es modesta: +5 a +10 mbits sobre unos +94. Mueve poco el Top-5 y
  el Top-15 (este baja 0,5 pp en ELECCION y sube 1,9 pp en PRUEBA26).
- Es la misma familia que el factor AD de `../../adaptativo/`, que no pasó el dev-B de 2024-25. Aquí se juzga en el régimen
  actual, con olvido de 60 días y con reciclaje. En el régimen de 2024-25 (domingo) no está demostrado. Las clases fijas
  no siguen un cambio del día relajado a días que no estén en su clase.

## VEREDICTO
- Fugas de calendario más allá del día de la semana (pago, quincena, feriados, puentes, inicio y fin de mes, fecha × día,
  día × hora): **NO MEJORA**. No hay ninguna.
- Corrección adaptativa de las reglas por día de la semana: según la regla pre-registrada sería **MEJORA**, porque
  PRUEBA26 da +9,5 con el IC 90 % por encima de 0. Por la contaminación de las clases, **en la práctica es DUDOSO**:
  conviene una sombra en vivo antes de encenderla.
