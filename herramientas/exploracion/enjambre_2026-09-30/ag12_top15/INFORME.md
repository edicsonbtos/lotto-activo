# Camino 2: ag12 en sombra y la regla de RD llevada al Top-15

Fecha: 2026-09-30. Reglas: `PREREGISTRO.md` (escrito antes de medir). Script: `medir.py`. Números: `resultados.json`.
No se tocó nada de producción: ni el historial, ni el servidor, ni Railway. Solo se leyó `/api/sombra` con un GET.

## Lo más importante, en pocas palabras
1. **La regla de RD extendida al Top-15 PASA.** La regla dice: si el animal que salió en RD a las (h−1):30 está en
   el Top-15 de LA h:00, se saca y entra el 16.º. En los últimos 6 meses el Top-15 ponderado sube de +7,8 % a
   **+10,1 % por ficha** (+2,3 pp [+1,4; +3,3]). El Top-15 plano pasa de −0,7 % a **+2,0 %**.
   Cuidado: esa ventana ya se había mirado muchas veces por otros motivos. Cuenta como réplica débil, no como prueba
   limpia. El juez final es el marcador en vivo.
2. **ag12 en los últimos 6 meses** (repetición de una prueba ya usada): +16,4 mbits sobre el ensamble [+6,4; +26,1].
   Top-5 escalonado de +23,6 % a +32,7 % por ficha, pero el intervalo cruza 0 (−1,8 a +19,3 pp).
3. **La sombra en vivo va a favor, pero todavía no dice nada:** 59 sorteos, ag12 +14 mbits sobre el ensamble.
   Hacen falta unos **931 sorteos** (hasta ~**2026-12-14**) para decidir con el efecto que dio la prueba ciega.
4. **El Top-15 no se puede "asegurar".** Con todo junto, el Top-15 acierta ~52 % de las veces (antes 49,7 %).
   El azar da 39,5 %. La mitad de los sorteos seguirán fallando.

## (a) ag12 en sombra (en producción desde 2026-09-26)
| | sorteos | Top-3 | Top-5 | Top-15 | mbits | Top-5 escalonado (fichas netas) |
|---|---|---|---|---|---|---|
| ensamble | 59 | 5,1 % | 11,9 % | 42,4 % | 70,3 | −172 |
| ag12 | 59 | 10,2 % | 11,9 % | 45,8 % | 84,6 | −82 |
| ag12 + RD | 59 | 10,2 % | 11,9 % | 45,8 % | 60,1 | −82 |

Con 59 sorteos el error del Top-15 es de ±13 pp: es solo una tendencia. Que los dos pierdan en el Top-5 se debe a la
mala racha de esta semana. No es una señal.

**Cuántos sorteos hacen falta.** En la prueba ciega la diferencia variaba unos 238 mbits de un sorteo a otro.
Para ver +19,4 mbits con 80 % de potencia hacen falta **931 sorteos**, es decir ~78 días: **alrededor del 2026-12-14**.
Si el efecto real es menor (+10 mbits, lo que espera la auditoría), harían falta ~3.500 sorteos (~10 meses).

**Criterio pre-registrado para pasar ag12 a la jugada:** se mira una sola vez, cuando `/api/sombra` llegue a 931 sorteos.
- PASA si ag12 le gana al ensamble en mbits y el límite inferior del IC 90 % por jornadas es mayor que 0.
- Además, su Top-5 escalonado no puede quedar más de 3 pp por debajo del ensamble.
- Freno por inutilidad: se puede revisar cada mes, pero solo sirve para apagar, nunca para adoptar.
  Si con 600 sorteos o más ag12 va 10 mbits por debajo, se apaga y queda descartado.

## (b) Regla de cambio RD aplicada al Top-15
El Top-5 queda igual que con la regla que ya está en vivo. Lo que cambia es del 6.º al 15.º puesto.

| ventana | sorteos | cambios | ganó el de RD | ganó el 16.º | Top-15 sin → con | ponderado sin → con | Δ ponderado pp/ficha [IC95] | Δ plano [IC95] |
|---|---|---|---|---|---|---|---|---|
| desarrollo 2024-03..2025-06 | 5.241 | 2.003 | 25 | 55 | 51,9 → 52,4 % | +9,8 → +10,8 % | +0,97 [+0,32; +1,64] | +1,14 [+0,50; +1,79] |
| **últimos 6 meses** 2026-04-01..09-16 | 1.927 | 684 | 3 | 29 | 49,7 → 51,0 % | +7,8 → +10,1 % | **+2,30 [+1,36; +3,25]** | +2,70 [+1,66; +3,85] |

Hubo mejora en 10 de las 11 horas con RD previa. Las 8:00 no tienen RD anterior y no cambian.
El motivo ya se conocía: Lotto Activo casi nunca repite el animal que acaba de salir en RD. En los últimos 6 meses
el animal sacado ganó 3 veces y el que entró en su lugar ganó 29. **Veredicto pre-registrado: PASA.**
Es réplica débil: las filas ≥ 9357 de LA ya se miraron varias veces. Además, el mecanismo salió de esas mismas
fechas (H4b). Hay datos locales hasta 2026-09-16; del 17 al 22 de septiembre no se midió.

## (c) ag12 en los últimos 6 meses de LA (RÉPLICA de la prueba ciega ya usada)
| 2026-04-01..09-16, 1.927 sorteos | ensamble | ag12 | ag12 + regla Top-15 |
|---|---|---|---|
| mbits | 97,2 | 113,6 (Δ +16,4 [+6,4; +26,1]) | |
| Top-3 / Top-5 / Top-15 | 12,8 / 20,2 / 49,7 % | 13,3 / 22,1 / 50,5 % | Top-15 51,9 % |
| Top-5 escalonado (con la regla RD viva) | +25,1 % | +36,4 % | |
| Top-15 ponderado por ficha | +7,8 % | +12,1 % (Δ +4,3 [−0,1; +8,7]) | **+15,2 %** |
| Top-15 plano por ficha | −0,7 % | +1,1 % | +3,9 % |

La columna "ag12 + regla Top-15" es exploratoria: no estaba en una prueba ciega.

## Qué hacer
1. La regla Top-15 es sencilla y no cambia el Top-5. Se puede añadir a lo que se MUESTRA y medirla en vivo, igual que la
   regla del Top-5. Eso requiere tocar servidor.py y desplegar, así que necesita el OK del usuario.
2. Dejar correr la sombra de ag12 sin tocarla hasta 931 sorteos (~2026-12-14) y mirar una sola vez.
3. Nada de esto "asegura" el Top-15: sube ~1-2 pp de acierto y unos pocos puntos de retorno, con ruido grande.
