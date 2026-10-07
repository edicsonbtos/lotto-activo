# S3 = S2 + regla RD dentro del modelo + vida corta (recencia). PRE-REGISTRO, escrito antes de correr

Pedido del usuario (2026-10-07): juntar lo mejor de PROD y S2, adaptarlo a como trabaja el operador en los últimos 2-3 meses,
y meter la regla RD en S2 a ver si mejora.

## Diseño (todo fijado ahora)
- Base: S2 `C` (mezcla de expertos normal/relajado, LightGBM, reentreno mensual, mismos hiperparámetros, 600 días de ventana).
- **RD dentro**: se añaden los rasgos `rd1`, `rd2`, `hay_rd` de M4 (el animal que salió a (h−1):30 y (h−2):30 en RD
  Internacional; 1 si el candidato es ese animal). El historial RD termina el 2026-09-22 (después `hay_rd` = 0).
- **Recencia**: vida media de los pesos ∈ {45, 90} días (S2 usaba 90). Reentreno mensual, ventana 600 días.
- 4 corridas con el mismo código: S2_90 (ya existe, control), S2_45, S3_90, S3_45. Walk-forward 2025-07 .. 2026-10.
- **Mezcla con PROD** p ∝ PROD^(1−w)·M^w, w ∈ {0,5; 0,75; 1}.

## Tramos (arnés de 2026-10-06)
AJUSTE jul-25..feb-26, ELECCION mar..jun-26 (elige), PRUEBA26 jul..oct-26 = "lo reciente (2-3 meses)": CONTAMINADA,
se mira UNA vez con la versión elegida y queda en `registro_prueba26.jsonl`.

## Regla de elección (en ELECCION, exigiendo Δ mbits vs PROD > 0 también en AJUSTE)
1. Entre las 4 corridas × 3 w: la de mayor Δ mbits vs PROD en ELECCION; si dos difieren < 3 mbits, la de mayor Top-15.
2. Se juega con la regla de cambio RD (quitar y subir) en TODAS las columnas que no llevan RD dentro; las que llevan RD
   dentro se evalúan sin y con la regla (la mejor honesta: sin regla, para no contar RD dos veces) y se informa ambas.
3. Referencia de plata: PROD con la regla de cambio (la jugada actual).

## ¿RD mejora S2? (pre-registrado)
Sí si S3 supera a S2 (misma vida) en Δ mbits con IC 90 % por jornadas > 0 en AJUSTE+ELECCION juntos, o en Top-15 pareado.
¿La recencia ayuda? Sí si S?_45 supera a S?_90 con el mismo criterio.

## Veredicto del candidato final (S3 mezclado con la w elegida)
- MEJORA: Top-15 pareado vs PROD (ambos con RD) con IC 90 % > 0 en AJUSTE y ELECCION, y Δ mbits > 0 en ambos.
- DUDOSO: sube en los dos tramos pero algún IC cruza 0. NO MEJORA: en otro caso.
- Después, la prueba ciega SELLADA 2019-23 (sin RD, así que solo la parte "vida 45") y los controles Turing se repiten
  si el veredicto es MEJORA o DUDOSO.
## Aviso de despliegue
RD (h−1):30 llega ~30 min antes del sorteo h:00. Un motor con RD dentro exige recalcular el pronóstico tras conocerlo,
no congelarlo a (h−1):10-20. No se despliega nada sin permiso del usuario.
