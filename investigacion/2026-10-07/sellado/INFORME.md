# Prueba ciega sellada de S2 (2019-01-07 .. 2023-09-03): CONFIRMADO, pero es un efecto chico

Pre-registro: `PREREGISTRO.md` (escrito antes de correr nada). Datos: `sellado_2019_2023.txt`, 15.166 filas pegadas por el
usuario, verificadas (conteo exacto y idénticas fila a fila a la transcripción previa). Cierran justo donde empieza el
historial del servidor (2023-09-04). Código: `rasgos_sellado.py`, `motor_s2_sellado.py` (= `motor_s2.py` + salto de meses
sin 60 días de datos previos), `correr_sellado.py`, `evaluar_sellado.py`; salidas `salida_correr.txt`, `salida_evaluar.txt`.
Una sola corrida, nada se ajustó después de verla.

## Qué se corrió
S2 congelado (C, vida 90, reentreno mensual, ρ = 0,24 de 2025) y la base `ensamble_v2` (W = 2000), ambos walk-forward sobre
la serie sellada sola; mezcla p ∝ base^0,25·S2^0,75. Sin regla RD ni ajustes de primer sorteo/8:00 (no existen en esa era).
Tramo 2020-01-01..2023-09-03, 11.741 sorteos y 1.113 jornadas con ambas predicciones. Septiembre de 2020 se saltó (el cierre
de abril a agosto de 2020 deja la validación de 60 días vacía) y por eso faltan 114 filas.

## Resultado (IC 90 % por jornadas, pareado contra la base)
| | mbits vs azar | Δ mbits vs base | Top-15 (base 48,7) | Δ Top-15 pp | Δ T5 escalonado, puntos de retorno |
|---|---|---|---|---|---|
| base ensamble | +61,9 | – | 48,7 | – | (retorno +10,6 %) |
| S2 solo | +61,9 | +0,04 [−4,2; +4,3] | 49,4 | +0,63 [−0,17; +1,43] | −3,3 [−7,6; +1,0] |
| **mezcla 0,75** | **+67,0** | **+5,17 [+1,96; +8,38]** | **49,6** | **+0,87 [+0,20; +1,54]** | +0,1 [−3,7; +3,9] |

Por año, mezcla: Δ mbits 2020 +5,1, 2021 +6,5 (IC sobre cero), 2022 +2,6, 2023 +7,4: **los cuatro años son positivos**;
solo 2021 tiene el IC por encima de 0 por separado.

## Veredicto pre-registrado: CONFIRMADO (la mezcla)
Δ mbits con IC inferior > 0 ✓, Δ Top-15 con IC no negativo ✓, 4 de 4 años positivos ✓.

## Lo que sí y lo que no significa
- S2 **solo no gana** a la base (+0,04 mbits). Lo que sale es el beneficio de mezclar dos modelos distintos (+5 mbits,
  +0,9 pp de Top-15): coincide con lo medido en 2026 (+17 mbits, +1,9 a +3,9 pp). La dirección se sostiene en una era
  que nadie había visto; la magnitud es menor.
- La plata no se mueve: el Top-5 escalonado queda en +0,1 puntos [−3,7; +3,9] y el Top-15 plano sigue negativo en la era
  (−0,8 % contra −2,5 % de la base). Un Top-15 con 49,6 % de acierto contra 39,5 % de azar no alcanza a pagar 15 fichas a 30×.
- La base ya tenía +62 mbits contra el azar en 2020-2023, así que en esa era el operador también era predecible.
- Limitaciones: sin RD; sin 8:00; sin ajuste de primer sorteo; ρ viene de 2025 (parámetro congelado, no ajustado con
  esos datos); base y S2 entrenan sobre una serie con huecos (2020, abr-may 2023).

## Decisión que queda en manos del usuario
Poner S2 en **sombra** en vivo (no en la jugada) durante ~90 jornadas: reentreno mensual, LightGBM en `requirements.txt`,
más regularización. Nada se desplegó. Con esta prueba la evidencia es: mejora pequeña y consistente en dos eras, sin
traducción a plata demostrada.
