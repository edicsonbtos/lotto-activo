# PRERREGISTRO — reciclaje del proveedor con 3-4 sorteos (2026-10-08)

Origen (mirado en vivo hoy, NO es evidencia): RD Internacional acertó 10/12 en el Top-15 (esperado ~6); Lotto Activo 3/12
(repitió Ciempiés 12:00-13:00 y Delfín 10:00-19:00). Pregunta: con los primeros k=3 o 4 sorteos del día, ¿se puede saber si el
resto del día "recicla" más de lo que el motor espera, y si eso mejora el Top-15?

Definiciones:
- R(t) = animales cuya última salida fue hace 1 o 2 días de calendario (no hoy). Es la banda de reciclaje que el motor ya premia.
- E_k = (ganadores de los primeros k sorteos del día que están en R) − (suma de P del motor sobre R en esos k sorteos).
- Día "recicla" = E_k ≥ +1; día "no recicla" = E_k ≤ −1; el resto se ignora.
- Métrica 1 (reciclaje): en los sorteos k..11 de esos días, O/E_R = ganadores en R / suma de P sobre R.
- Métrica 2 (beneficio Top-15): en esos mismos sorteos, O/E_T15 = aciertos del Top-15 / suma de P del Top-15 del motor.
- IC95 por bootstrap de días. Tramos: LA = calor_cache (dev, por mitades); RD = cache_todo P1 tramo dev (por mitades).

PASA (útil para jugar) si, en las dos mitades de LA o de RD, O/E_T15 de los días "recicla" tiene IC95 entero >1 (o el de "no recicla" entero <1) para k=3 y k=4.
Si solo la métrica 1 se mueve y la 2 no: hay persistencia pero el motor ya la captura, no hay nada que cambiar.
Una sola corrida. No se toca el tramo de prueba.
