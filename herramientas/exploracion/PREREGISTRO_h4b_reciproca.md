# PRE-REGISTRO — H4b: ¿Lotto Activo gana al saber lo que salió en RD Int? (segunda prueba)

Escrito el 2026-09-23, ANTES de correr `herramientas/rdint/reciproca_la.py`.

## Por qué hay una segunda prueba
H4 (PREREGISTRO_rdint_cruzado.md) pasó en desarrollo (+12,6 mbits) y FALLÓ en su prueba ciega
(+3,1 [−5,7, +10,8]). Esa prueba ciega fue corta: 1.908 sorteos de LA (2025-07-01 .. 2025-12-16),
porque la caché del ensamble (`calor_cache.npz`) termina en la fila 9356 de LA. Los sorteos de LA
desde 2025-12-17 nunca se han puntuado con variables de RD.

**Contaminación declarada (no es una prueba ciega pura):**
1. H4 ya falló una vez: esta es la segunda mirada a la misma hipótesis. Si pasa, cuenta como
   "pasa en la segunda de dos pruebas", no como una confirmación limpia.
2. El 2026-09-23, antes de escribir esto, se vio una tabla cruda por semestre (sin modelo):
   LA h:00 repite al animal de RD (h−1):30 0,51x en 2025-S2, 0,28x en 2026-S1 y 0,27x en 2026-S2.
   Eso hace probable que la variable 1 aporte en la ventana nueva. Lo que NO se ha visto es si el
   aporte sobrevive encima del ensamble ni cuánto dinero mueve.
3. Los sorteos de LA ≥ fila 9357 son el tramo de prueba del ensamble (ya mirado 5 veces para
   elegir el ensamble). Aquí el ensamble no se elige ni se ajusta: se usa tal cual, walk-forward.

## Diseño (congelado)
- Base: `ensamble_v2` walk-forward sobre todo el historial de LA hasta 2026-09-22, `desde = LE.W`.
- Sonda: exactamente la de H4: x = [RD (h−1):30 == i, salió hoy en RD antes de h:00 sin contar
  (h−1):30]; `modelo.cruzado(R=250, minimo=500, lam=1)`. LA de 8:00 no tiene RD previo (x = 0).
- RD de h:30 o posterior NUNCA entra en la fila de LA h:00 (prueba de fuga incluida).
- Ventana PRINCIPAL: LA 2025-12-17 .. 2026-09-22 (todo lo nunca puntuado con RD).
  Sub-ventanas informativas: 2025-12-17 .. 2026-04-12 y 2026-04-13 .. 2026-09-22.
  Control: 2025-07-01 .. 2025-12-16 (repite la prueba ciega vieja con el ensamble recalculado).
- IC95 por bootstrap de bloques de jornada (2.000 remuestreos).

## Criterio (fijado antes de correr)
- **PASA** si en la ventana principal Δ mbits ≥ +5 Y el límite inferior del IC95 > 0.
- **Uso en dinero**: solo se considera jugar LA con RD si, además, el retorno por ficha del Top-5
  escalonado con RD supera al del ensamble solo en la ventana principal. Si Δ mbits pasa pero el
  dinero no se mueve, se reporta como "señal real sin valor práctico".
- Nada de lo que salga cambia la jugada de LA sin confirmarlo después en el marcador en vivo.
