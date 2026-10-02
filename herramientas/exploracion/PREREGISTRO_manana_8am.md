# Pre-registro: racha de las 8:00 y concentración en el puesto 16-25 (2026-10-01)

Estas hipótesis nacen de mirar el marcador en vivo (2026-09-15..10-01), así que ESOS datos
no pueden confirmarlas. Solo cuentan los sorteos desde 2026-10-02.

## Referencias fijas (tramo de desarrollo, calor_cache.npz, n=7357; escritas antes de ver datos nuevos)
- Top-15 a las 8:00 (hora==8, n=635): 53,1 %.
- Autocorrelación día a día del acierto Top-15 dentro de cada hora: media −0,01 (error ≈ 0,04). No hay horas calientes.
- Ganador con hueco 1-3 días a las 8:00: 58,4 % (el modelo esperaba 64,4 %).
- Puesto 16-25: 26,3 % observado, 25,8 % esperado por el modelo, 26,3 % azar.

## H1: "las 8:00 siguen acertando el Top-15"
- Muestra: los próximos 30 sorteos de las 8:00 AM puntuables (desde 2026-10-02), sin parar antes.
- Pasa si acierta Top-15 en ≥22/30 (P bajo 53,1 % = 1,9 %). Con ≤19/30 se da por falsada; entre 20 y 21 queda sin concluir.
- Si pasa, hay que replicarla en otros 30 antes de tocar nada: es 1 hora elegida entre 12.

## H2: "el ganador cae en 16-25 más de lo que dice el modelo"
- Muestra: los próximos 150 sorteos con las 38 probabilidades guardadas (desde 2026-10-02).
- Métrica: observados en 16-25 contra la suma de las probabilidades del modelo en 16-25.
- Pasa si z ≥ +2,0 (contra el modelo, no contra el azar). Si z < +1,0 queda falsada.
- Si pasa, solo sugiere recalibrar ese tramo; no se cambia el modelo sin la regla de 3 meses.

## H3 (descriptiva): "a las 8:00 el ganador sale con hueco de 1-3 días"
- Las 11 madrugadas desde el 09-21 salieron todas con hueco 1-3 d (5 con 1, 5 con 2, 1 con 3).
- En desarrollo eso ocurre en 58,4 %; ventanas de 11 madrugadas seguidas todas en 1-3 d: 2 de 625.
- Prospectiva: en los 30 sorteos de H1, contar la fracción con hueco 1-3 d; pasa si ≥ 80 %.

Todo cambio de modelo o de jugada sigue gobernado por `gestion_banca.VIGILANCIA`.

## Fe de erratas (2026-10-01, añadida después; los criterios de arriba NO se cambian)
Las "referencias fijas" de arriba salieron de `en_vivo_manana_8am.py` con `hora == 8`. En el historial la
hora va de 0 a 11 y 0 = 8:00, así que `hora == 8` son las **16:00**. Valores correctos de las 8:00 en el
mismo desarrollo (`calor_cache.npz`, `hora == 0`, n = 372; las 8:00 existen desde nov-2024):
- Top-15 a las 8:00: **60,5 %** (el 53,1 % de arriba es el de las 16:00).
- Ganador con hueco de 1-3 días a las 8:00: **65,6 %** (el modelo esperaba 61,3 %).
Consecuencia para H1: con la tasa real de las 8:00 (60,5 %), acertar ≥ 22/30 pasa por azar el 10,4 % de las
veces, no el 1,9 %. Que H1 "pase" ya no indicaría que las 8:00 rinden más de lo de siempre. Para eso harían
falta ≥ 24/30 (P = 2,0 %) o ≥ 25/30 (P = 0,7 %). Se deja el criterio original tal como se escribió y se
anota esta lectura. El script ya está corregido (`hora[g] == 0`). Fuente: `herramientas/exploracion/top15_70/`.

## Nota (2026-10-02, añadida después; los criterios de arriba NO se cambian)
La ventaja de las 8:00 se probó a ciegas en el tramo de prueba 2026 (260 madrugadas, `PREREGISTRO_hora_8am_ciega.md`):
Top-15 49,2 % [43,1; 55,4] contra 49,4 % del resto → **FALSADA**. La tasa de referencia de las 8:00 en 2026 es la
de cualquier hora (~49 %). Con esa tasa, ≥ 22/30 en H1 saldría por azar solo el 0,7 % de las veces: si H1 pasa, sí
sería un indicio serio de que las 8:00 cambiaron (y aún pediría la réplica de otros 30).
La racha en vivo reconstruida (11/16; 9 seguidas del 21 al 29-sep) está en `INFORME_hora_8am_y_caida.md`.
