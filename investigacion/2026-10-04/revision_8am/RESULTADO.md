# Revisión del 2026-10-04 (hasta las 3 PM): ¿qué cambió y qué pasó a las 8:00?

Historial: copia del volumen hasta el 2026-10-03 7 PM, más los sorteos de hoy tomados de los logs de Railway
(8a 31, 9a 35, 10a 30, 11a 21, 12p 28, 1p 14, 2p 33, 3p 13). Para cada sorteo el motor se reproduce solo con el
pasado (`ensamble_v2`). En el 8:00 de hoy coincide con lo congelado: diferencia máxima 1e-4.
- **A**: motor sin el ajuste del primer sorteo.
- **B**: producción (A más el ajuste del primer sorteo).
- **C**: B más la corrección fecha/hora, que sigue en sombra.

## ¿Qué se cambió?
- El único cambio al motor es el ajuste del primer sorteo (366365b). Entró en Railway el 3-oct a las 3:46 PM,
  con el despliegue de a7e194f. Por eso el **8:00 de hoy es el primero que lo usa**. El 8:00 de ayer no lo usaba.
- Hoy castigó a 11 Gato (×0,272, primero de ayer) y subió a 7 Perico (×1,736, primero de hace 3 días). No salió
  ninguno de los dos. El ganador, 31 Lapa, quedó en el puesto 35 sin ajuste y en el 34 con ajuste. **El ajuste no
  causó el fallo.**
- El 8:00 de ayer (11 Gato) quedó en el puesto 16 con y sin ajuste: se salió del Top-15 por un puesto.
- Los demás cambios (Anti Top-15, sombras) no tocan la jugada.

## Puestos del ganador a las 8:00 en vivo (B)
29, 23, 4, 7, 12, 31, 1, 12, 9, 13, 6, 1, 7, 11, 3, 14, 16, 1, 16, 34. **Top-15: 14/20 (70 %).** Es la mejor hora.
Con una tasa del 56 %, dos fallos seguidos en una mañana dada pasan con probabilidad 0,19, y en 20 mañanas lo
normal es ver al menos un par así.

## El día
- Ayer: Top-15 7/12 (ganadores en los puestos 2, 3, 4, 6, 8, 10 y 10). Hoy: 3/8.
- Top-15 ponderado 3-2-1: ayer +84 fichas (+30 %), hoy −34 (−18 %). Desde el 15-sep: −418 (−8 %). A las 8:00
  desde el 15-sep: +230 (+50 %).
- Top-15 en vivo: 106/236 = 44,9 %. El motor esperaba 51,7 % (P = 0,02). Es el exceso de confianza ya conocido.

## La única mejora candidata con respaldo fuera de muestra: C (fecha/hora, en sombra)
C − B en mbits por sorteo (IC 90 % por jornadas):

| tramo | n | C − B | Top-15 B | Top-15 C |
|---|---|---|---|---|
| dev (incluye dev-A, donde se ajustó) | 7.357 | +6,0 [+4,5; +7,5] | 53,2 % | 53,9 % |
| prueba (dic-25 a 14-sep) | 3.134 | **+4,2 [+1,8; +6,5]** | 49,6 % | 50,8 % |
| vivo (desde 15-sep) | 236 | +13,1 [+7,7; +18,1] | 44,9 % | 48,7 % |

En vivo, C habría acertado 115 de 236 en vez de 106. El pre-registro (`PREREGISTRO_sombra_exposicion.md`,
enmienda) solo permite encenderla con n ≥ 6.000 en la sombra. Encenderla antes **rompe ese pre-registro** y le
toca decidirlo al usuario. No se cambia nada en producción.

Reproducir: copiar el historial a `hist.txt`, correr `1_walkforward.py` (~50 s) y luego `2_puestos.py` y `3_plata.py`.
`2_puestos.py` lee además `man.json`, el pronóstico congelado del 8:00 de hoy, solo para validar.
