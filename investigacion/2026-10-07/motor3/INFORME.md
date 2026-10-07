# S3 = S2 + regla RD dentro + vida corta (2026-10-07). Veredicto pre-registrado: DUDOSO

Pre-registro `PREREGISTRO.md` (subido antes de correr). Código `correr_s3.py`, `evaluar_s3.py`; salidas `salida_evaluar.txt`,
`salida_reciente.txt`. 4 corridas walk-forward (S2_90 control, S2_45, S3_90, S3_45) × w ∈ {0,5; 0,75; 1}. Aviso: las primeras
tres corrieron juntas y se atascaron (12 hilos en 4 núcleos); se repitieron una por una con el mismo código y semilla.

## ¿La regla RD dentro de S2 mejora? SÍ
Δ mbits pareado S3_90 − S2_90 (AJUSTE+ELECCION): **+11,5 [+7,2; +15,7]**. Con S2 solo (w = 1) en ELECCION: +27,8 contra +11,7 mbits.
Mezclado con PROD: S3_90 w = 0,75 da +28,4 / +31,8 mbits (AJUSTE / ELECCION) contra +21,2 / +17,8 de S2 mezclado.

## ¿Vida corta (adaptarse a lo reciente) ayuda? NO
Vida 45 contra 90: −5,0 [−10,0; 0,0] sin RD y **−11,9 [−17,4; −6,3] con RD**. Con S2 solo, vida 45 pierde plata (Top-5 esc. +16,6 % contra +27,4 %).
Seguir al operador con memoria más corta añade ruido. El reentreno mensual con vida 90 ya sigue el régimen de los últimos meses.

## Elección (regla pre-registrada)
S3, vida 90, mezcla con PROD w = 0,75 (mayor Δ mbits en ELECCION, +31,8; positivo en AJUSTE).

| tramo | Δ mbits vs PROD [IC 90 %] | Top-15 con regla RD (PROD) | Δ Top-15 pp [IC] | T5 esc. % (PROD) |
|---|---|---|---|---|
| AJUSTE | +28,4 [+19,1; +37,7] | 56,2 (55,6) | +0,62 [−0,76; +2,00] | +32,6 (+31,0) |
| ELECCION | +31,8 [+18,9; +44,8] | 53,2 (50,1) | +3,09 [+0,98; +5,20] | +28,2 (+25,0) |
| PRUEBA26 jul–oct (reciente, **contaminada**, una sola mirada) | +26,4 [+14,1; +38,7] | 53,6 (50,4) | +3,18 [+0,71; +5,65] | +22,4 (+15,3) |

Veredicto: **DUDOSO** (el IC del Top-15 en AJUSTE cruza 0; la mejora en mbits sí es clara en los tres tramos).
Contra S2 mezclado (el candidato anterior), en lo reciente S3 gana en mbits (+26,4 contra +16,8) pero no en Top-15
(53,6 contra 54,3 con la regla; 53,6 contra 53,9 sin ella). Últimos 30 días: PROD Top-5 18,6 % / Top-15 46,7 %; S3 21,1 / 55,3; S2 mezclado 20,6 / 54,7.
La regla de cambio RD aplicada encima de S3 no suma nada: con RD ya dentro, ELECCION queda en 53,2 % con y sin la regla.

## Lo que falta antes de confiar
- Sellada 2019-23: no aplica a RD (esa era no tiene historial RD). Los controles Turing de S3 NO se corrieron todavía.
- RD dentro de un modelo exige recalcular el pronóstico cuando llega el resultado de RD (~(h−1):30), no congelarlo a (h−1):10-20.
  Eso es un cambio de arquitectura del servidor. No se desplegó nada.
- La parte de "régimen mié-vie" sigue siendo un descubrimiento de 2026, y lo reciente ya estaba contaminado.
- Plata: T5 esc. mejora en los tres tramos contra PROD, pero el IC por jornadas cruza 0 donde se midió (+7,1 [−5,7; +19,9] en lo reciente).

## Recomendación
Sombra en vivo de S3_90 mezclado (w = 0,75), con el pronóstico recalculado al llegar RD, ~90 jornadas; PROD sigue jugando. Antes: Turing sobre S3
(retraso de 1 mes, rasgo de ruido) con más regularización.
