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
