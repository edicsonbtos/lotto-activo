# Camino 4: Guácharo y rutas nuevas (enjambre 2026-09-30)

## En pocas palabras
- **Ninguna ruta pasa una prueba limpia.** Nada de lo que hay aquí asegura el Top-15, y con esto nadie se hace rico.
- **Guácharo paga 60x y el Guácharo (75) paga 120x.** Lo dice el reglamento oficial. En los últimos 6 meses, el modelo M2 habría ganado unos +3,8 centavos por ficha, pero el margen de error va de −4,4 a +11,7. Ese tramo además ya se había mirado. Si tu agencia paga 55x o menos, pierde.
- **Ruta nueva: la DUPLETA de Lotto Activo.** Según el reglamento local paga 1.000x, pero una web dice 100x. Consiste en acertar los ganadores de dos sorteos seguidos del mismo día. Le saca más provecho a la misma lista que ya da el motor:
  - En desarrollo **pasó**: +23 centavos por ficha con el Top-15.
  - En los últimos 6 meses dio **+8 centavos, pero el margen va de −2 a +20, así que NO PASA** la confirmación que fijé de antemano.
  - Y si de verdad paga 100x, pierde 89 centavos por ficha.
- **Ruta "régimen en línea"** (medir cada mes cuánto evita el operador repetir animal): **NO PASA** en desarrollo (+0,7 mbits).

## Parte A: Guácharo Activo
**Qué dicen las fuentes:**
- Reglamento oficial (loteriadehoy.com/dist/files_pdf/Guacharo_Activo.pdf), artículo 13: paga 60 por cada 1 apostado. El comodín 75 (El Guácharo) paga 120 por 1.
- Tiene 77 figuras (00, 0 y del 1 al 75) y 11 sorteos al día según el reglamento (en los datos aparecen 12). Las jugadas cierran 5 minutos antes de cada sorteo.
- Los colores solo indican el tipo de animal: no cambian el pago.
- Coinciden con lo anterior la cuenta oficial en X ("PAGANDO 60x1 y 120x1"), elbrujodelosanimalitos.com y notilogia.com.
- **No encontré qué pagan las agencias en la práctica.** Algunas pagan menos que el reglamento. Pregunta en la tuya.
- Ojo con el 75: sale mucho menos de lo normal (0,44 veces en desarrollo y 0,52 en los últimos 6 meses). Su pago doble no es un regalo.

**M2 en los últimos 6 meses** (2026-04-01 a 09-27, 2.088 sorteos):
- Son las predicciones ya congeladas y ya puntuadas en la prueba ciega del 28-09. Solo cambié el precio. **No es una prueba nueva.**

| | Últimos 6 meses | Todo el tramo ciego (22 meses) |
|---|---|---|
| Top-15 de M2 | 25,9 % [23,9; 27,8] | 26,7 % |
| Top-15 de N0 (base) / azar | 19,0 % / 19,5 % | 19,7 % / 19,5 % |
| Retorno por ficha, Top-15, pago 60x | **+3,8 c [−4,4; +11,7]** | +7,1 c [+2,8; +11,3] |
| Retorno por ficha, Top-5 escalonado, pago 60x | +4,5 c [−12; +21] | +7,8 c [−0,5; +16] |
| Retorno por ficha, Top-15, pago 55x | −4,8 c | −1,8 c |
| Retorno por ficha, Top-15, pago 50x | −13,5 c | −10,8 c |
| Pago de equilibrio | 58,0x | 56,2x |
| mbits M2 − N0 | **−14 [−37; +8]** | +29 |

- Por mes, el Top-15 va de 22,9 % a 29,6 %.
- La ventaja va bajando, y en mbits M2 ya es **peor** que la base en estos 6 meses, porque está demasiado confiado.
- **Veredicto Guácharo:**
  - Si tu agencia paga 60x parejo: sombra sin plata de 3 a 4 semanas.
  - Si paga menos de 58x: descartado.

## Parte B: rutas nuevas (ninguna está en la lista de ideas cerradas)

| # | Ruta | Por qué podría funcionar | Qué la mataría | Costo |
|---|---|---|---|---|
| 1 | **Dupleta LA 1.000x** (cribada) | Con dos patas, la ventaja del motor se multiplica por sí misma. Al azar devuelve 0,71 por ficha (el animal suelto, 0,79). Con un Top-15 de 46 % por pata ya se cubre el pago; el animal suelto necesita 50 % | Que se pague 100x, que tu agencia no la venda, o que el Top-15 baje a menos del 46 % | Bajo |
| 2 | **Fuerza de "no repetir" en línea** (cribada) | El operador mueve esa perilla con el tiempo | Que el motor ya la siga sola | Bajo |
| 3 | Dupleta en RD Internacional | El mismo mecanismo; el Top-15 de RD está en el 50 % | Que RD no venda dupleta o pague otra cosa | Bajo (caché de RD en desarrollo) |
| 4 | Trío Activo 600x y Terminal Trío 60x (salen en fuentes del reglamento) | Si son 3 sorteos seguidos, la ventaja se eleva al cubo | No conocemos la regla exacta ni si se venden | Bajo, una vez conocida la regla |
| 5 | Top-15 con la regla de cambio de RD (sacar el animal de RD (h−1):30 y subir el 16.º) | El efecto está confirmado (lift 0,26) | Que solo dé +0,7 puntos, menos que el ruido | Bajo; medirlo en vivo |
| 6 | Banca conjunta LA + Guácharo M2 | Dos ventajas que no dependen una de otra bajan la varianza | Que Guácharo pague menos de 58x | Bajo |
| 7 | Guácharo M2 recalibrado (con menos confianza y una máscara más suave) | Le quitaría el exceso de confianza (los −14 mbits) | Que el Top-15 no se mueva | Medio |

### Cribado en desarrollo
Datos de desarrollo: 2024-03-07 a 2025-12-17, 7.357 sorteos de LA. No miré ningún tramo ciego.

**B1. Dupleta (h, h+1):**
- Antes del sorteo h compro todos los pares distintos del Top-k que da el motor para la hora h, y uso la misma lista para la pata h+1. Así no hay fuga.
- Pares evaluados: 6.721.
- Top-15 (210 fichas): acierta el **25,9 %** de los pares, contra 14,9 % al azar. Retorno con 1.000x: **+23,4 c [+17,4; +29,4]**, positivo en las dos mitades. **PASA en desarrollo.**
- Top-10 (90 fichas): +34 c. Top-5 (20 fichas): +44 c.
- Con 100x: −88 c.
- mbits del par contra el azar: +86,5 [+42,5; +128,8].
- Como referencia, el animal suelto en las mismas filas: Top-15 +6,1 c y Top-5 escalonado +24,3 c.

**Confirmación de B1 (una sola mirada, ya fijada de antemano):**
- Tramo: 2026-04-01 a 2026-09-16, 1.788 pares, con el ensamble walk-forward ya calculado (`P_ens_reciente.npy`).
- **Aviso:** las filas ≥ 9357 de LA ya se miraron varias veces. Esto es una réplica débil, no una prueba limpia.
- Top-15: acierta el 22,8 % de los pares. Retorno con 1.000x: **+8,4 c [−2,0; +19,6]**. **NO PASA** (el margen cruza 0).
- Top-10: +22 c [+7; +40]. Top-5: +37 c [+0,4; +76]. Eran métricas secundarias, así que no puedo cambiar la regla para quedarme con ellas.
- En el mismo tramo, el animal suelto: Top-15 −1,4 c y Top-5 escalonado +22,6 c.
- mbits del par: +15,5 [−73; +93].

**B2. Régimen en línea:**
- Δ +0,66 mbits [−1,2; +2,5]. Las mitades dan −1,2 y +2,5.
- Mueve el Top-15 +0,07 puntos y el Top-5 +0,03.
- **NO PASA.** Por hora, la de las 19:00 sale −15. El motor ya sigue esa perilla.

## Qué haría ahora
1. **Preguntar en tu agencia dos cosas:**
   - ¿Venden la dupleta de Lotto Activo? ¿Paga 1.000x o 100x? ¿Es por sorteos seguidos y en qué horas?
   - ¿Cuánto pagan Guácharo y el 75?
2. Si la dupleta paga 1.000x: anotarla **en sombra, sin plata**, unas 4 semanas. Juez: el marcador en vivo. Con el Top-15 de cada sorteo se arma la dupleta del sorteo siguiente.
3. **No** subir la apuesta. La dupleta acierta 1 de cada 4 pares en el mejor caso, así que vas a ver rachas largas sin cobrar.

## Archivos
- `PREREGISTRO.md` (sha256 7ea7be89…, en `registro.jsonl`, escrito antes de medir)
- `a_guacharo_6m.py` → `resultado_a_guacharo.json`
- `b_cribado.py` → `resultado_b_dev.json`, `resultado_b_confirmacion_B1.json` (la confirmación se niega a correr dos veces)
