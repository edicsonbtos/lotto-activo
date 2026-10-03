VEREDICTO: CONFIRMADO (= el hallazgo es REAL, no es un artefacto de datos)

ag10 tenía el papel de forense: no envió candidatos a prueba. CONFIRMADO quiere decir que ninguna de las 4 vías de
artefacto pre-registradas (PREREGISTRO.md) se sostiene. La regla "primero ≠ primero de ayer" aparece en la API
oficial del operador por sí sola, y aparece también en RD Internacional, un juego que nunca se usó para descubrirla.

## A. Código: ningún paso borra, corrige ni desplaza repeticiones
- `scraping/etl.py`, `construir_csv.py`: solo trabajan con los CSV multi-lotería (LH/TZ) y no tocan el historial de LA.
  No hay deduplicación por valor, solo un índice `n_sorteo_dia`.
- `auto_resultado.py`, `fuente_oficial.py`, `herramientas/lard/descargar.py`: piden cada fecha por separado y no
  comparan con ayer. No hay ninguna regla del tipo "dato viejo o repetido". El único riesgo real es la portada de
  tuazar del día, que pondría el animal de ayer en la casilla de hoy. Eso CREARÍA repeticiones, no las quitaría.
  Además el auto-anotado existe solo desde 2026-09-20.
- `servidor.registrar` añade la línea sin validar el valor. `deshacer` quita la última línea y no filtra.
  `grep` de viejo/stale/repetido/duplic: nada relevante.
- `correccion_historial_2026-09-29.json`: 406 cambios, solo de FECHA. Ninguno cambia la hora ni el código. Reconstruí
  el historial de antes de la corrección y el conteo k=1 da 2/439 (era 9:00) y 1/636 (era 8:00). Después de la
  corrección da 2/440 y 1/638. Ningún par cambia de "repite" a "no repite". La corrección solo añade o quita pares
  sin repetición alrededor de los feriados (`forense_correccion.out`).
- `faltantes_historial_2026-10-03.json`: añade 1 línea (2026-06-24 a las 7 PM). No afecta a ningún primer sorteo.

## B. Historial contra las fuentes externas: 0 discrepancias
| contraste | slots comunes | distintos | repeticiones primero-ayer (hist / fuente) |
|---|---|---|---|
| hist_la contra la API oficial (juego 1), 2025-07-01..09-22 | 5148 (0 sobran, 0 faltan) | 0 | 1/422 / 1/422 |
| hist_la contra lottoactivo.csv (LH+TZ), 2026-04-13..09-13 | 1800 | 0 | 1/148 / 1/148 |
| API oficial contra LH+TZ | 1800 | 0 | — |
No hay ningún día en que la fuente oficial muestre una repetición que el historial no tenga, ni al revés. Los 422
pares de días son idénticos en las dos fuentes. La única repetición es la del 2026-06-22.

## C. El patrón en las fuentes externas solas (conteo crudo contra el azar 1/38, sin motor)
| serie | primero = primero de ayer | azar | O/E | P(≤k) | misma hora de ayer, demás horas (control) | primero de hace 3 días |
|---|---|---|---|---|---|---|
| LA, API oficial, 2025-07..09-22 | 1/422 | 11,1 | 0,09 | 1,8·10⁻⁴ | O/E 1,01 | 23/415, O/E 2,11, p = 0,001 |
| ↳ tramo dev (hasta 2025-12-19) | 0/157 | 4,1 | 0,00 | 0,016 | 0,97 | O/E 2,48 |
| ↳ tramo prueba | 1/257 | 6,8 | 0,15 | 0,009 | 1,05 | O/E 1,81 |
| LA, LH+TZ (espejos independientes) | 1/148 | 4,0 | 0,25 | 0,09 | 0,98 | O/E 1,28 |
| **RD Int, API oficial (juego 2)** | **1/422** | 11,1 | **0,09** | **1,8·10⁻⁴** | 0,98 | O/E 1,10 |
| RD Int, rdint_hist, 2023-09..2024-11-27 | 7/440 | 11,6 | 0,60 | 0,11 | — | — |
| RD Int, rdint_hist, 2024-11-28..2025-06 | 1/209 | 5,5 | 0,18 | 0,027 | — | — |
| LARD, API oficial (juego 3, 14 sorteos/día) | 13/448 | 11,8 | 1,10 | 0,70 | 0,91 | O/E 0,77 |
- La regla de ayer se ve en los datos del operador sin pasar por nuestro ETL. Es exclusiva del primer sorteo:
  en las demás horas, "misma hora de ayer" da O/E ≈ 1.
- RD Internacional, que es del mismo operador, sale del mismo modo (1/422). Es una réplica que no se usó para
  formular la hipótesis. LARD no la muestra, y funciona como control negativo.
- La regla de hace 3 días (k = 3) solo aparece en LA: oficial O/E 2,11 y LH O/E 1,28 con un IC amplio. RD
  (1,10) y LARD (0,77) no la tienen. Es real en la API, pero es menos sólida que k = 1.
- Pista sobre el mecanismo: en RD la regla aparece con fuerza desde nov-2024, cuando LA pasó a las 8:00.
  Antes daba O/E 0,60.
- Salvedad: la era de las 9:00 de LA (2/440) solo existe en nuestro historial. No hay fuente independiente
  anterior a 2025-07, pero tampoco hay ningún mecanismo de artefacto (punto A) y la corrección de fechas no la toca.

## D. Multiplicadores re-derivados en dev y fuga
- Modelo: q ∝ P·exp(b1·[primero de ayer] + b3·[primero de hace 3 días]), solo filas de primer sorteo de dev (n = 635).
  - Sin L2: m1 = 0,118, m3 = 1,775.
  - Con penalización ½·λ·b² y λ = 1: **m1 = 0,272, m3 = 1,736**, idénticos a producción.
  - Con λ·b² y λ = 1: 0,360 y 1,700.
  - Ajustado solo en prueba: 0,462 y 1,564. Ajustado en dev + prueba: 0,310 y 1,701. Producción no usó prueba.
- Conteos en dev: k = 1, O = 1 y E = 8,25 (O/E 0,12). k = 3, O = 28 y E = 16,3 (O/E 1,72). Por era:
  - k = 1: 0,23 a las 9:00 y 0,00 a las 8:00.
  - k = 3: 1,45 a las 9:00 y 1,89 a las 8:00. El signo es el mismo en las dos eras.
- Fuga: rehice P_aj desde P en las 911 filas de primer sorteo, con una diferencia máxima de 0 contra base8.
  - 0 referencias a sorteos que no sean de una fecha anterior: en todas, tp < t y fecha(tp) < fecha(t).
  - Las filas que no son primer sorteo tienen P_aj = P.
  - Cambiar el ganador de la propia fila no altera su multiplicador en ninguna fila.
  - `prediccion.ajuste_primer_sorteo` hace lo mismo: solo filas < n y solo si la fecha es nueva.
  - Lo que no audité es la fuga interna de P (ensamble_v2). Viene de lotto_eval walk-forward y no la recalculé,
    tal como pide el brief.
- Ganancia de P_aj frente a P, en mbits por primer sorteo (IC bootstrap por días):
  - dev: +19,1 [+6,6; +32,6]
  - prueba: +22,2 [−3,2; +48,9]
  - vivo (n = 15): +102 [−7; +263]

## Cosas miradas (sin selección en dev)
4 vías de artefacto, 3 contrastes de fuentes, 11 series para el patrón crudo, 3 periodos de RD y 5 variantes de
ajuste. Ninguna se usó para elegir un candidato, así que no hay contraste en prueba que corregir.

## Recomendación
- Producción: mantener ×0,272 y ×1,736. Son reproducibles y no tienen fuga. El 0,272 es prudente: la API oficial
  sola da una O/E cruda de 0,09.
- Sobre k = 3: vigilarlo con el pre-registro del informe (falsado si O/E < 0,8 hasta 2027-01-03). Es el eslabón débil.
- Idea nueva para el motor de RD Int (aún no probada): aplicar la misma regla k = 1 al sorteo de las 8:30. Habría que
  medirla contra el motor de RD con su propio dev/prueba. Su "dev" natural sería la serie desde 2024-11-28.

Scripts: `forense_bc.py`, `forense_correccion.py`, `forense_d.py`, `control_rd.py`. Las salidas están en los `*.out`.
