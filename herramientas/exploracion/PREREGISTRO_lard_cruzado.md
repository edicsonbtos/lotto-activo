# PRE-REGISTRO — Hilo 8: Lotto Activo República Dominicana (LARD) como tercer juego cruzado

Escrito el 2026-09-23, mientras se descarga la historia y ANTES de mirarla. Solo se vieron 3 días de
prueba del descargador (2025-07-01..03) y los resultados del 2026-09-23. Idea: el operador evita
repetir el animal del sorteo inmediatamente anterior también entre juegos (hilo 7: RD h:30 evita LA
h:00; LA h:00 evita RD (h−1):30; la noche corta el efecto). ¿Pasa lo mismo con LARD?

## Datos
API oficial, juegos 1 (LA, h:00 8-19), 2 (RD, h:30 8:30-19:30), 3 (LARD, h:00 8-21, 14 sorteos).
Historia desde 2025-07-01. **Desarrollo: 2025-07-01..2026-01-31. Prueba ciega: 2026-02-01..2026-09-22.**
La prueba ciega no se mira hasta que el desarrollo esté cerrado y este archivo, con su commit, fije
qué se prueba. LARD nunca se ha mirado; LA y RD de esas fechas sí (otras preguntas): declarado.

## Hipótesis (solo mismo día; pares consecutivos en el tiempo)
Métrica de señal: repeticiones observadas / esperadas (n/38), con p Poisson de una cola (menos).
Se prueban 4 pares, corrección de Bonferroni ×4:
- **P1: LA h:00 ← LARD (h−1):00** (1 h antes; sirve para jugar LA).
- **P2: RD h:30 ← LARD h:00** (30 min antes; sirve para jugar RD).
- **P3: LARD h:00 ← RD (h−1):30** (30 min antes; sirve para jugar LARD).
- **P4: LARD h:00 ← LA (h−1):00** (1 h antes; sirve para jugar LARD).
Descriptivo, sin decisión: LA h:00 vs LARD h:00 (simultáneos: no se pueden usar para apostar).

Dinero (solo para los pares que pasen la señal): regla de cambio como la validada (si el animal del
sorteo anterior del otro juego está en el Top-5, sale, suben los de abajo y el 6º entra 5º),
Top-5 escalonado 2-2-2-1-1, diferencia de retorno por ficha con IC95 por bootstrap de jornadas.

## Criterio
- **Desarrollo:** un par sigue a la prueba ciega solo si ratio < 1 con p < 0,01/4.
- **Prueba ciega, por par:** CONFIRMADO si ratio < 1 con p < 0,05 **y** diferencia de dinero > 0
  con IC95 entero sobre 0. SE ADOPTA sin confirmar si la señal pasa y la diferencia es > 0 con IC que
  cruza 0. SE DESCARTA en otro caso.
- Si ningún par pasa en desarrollo: LARD no aporta, fin del hilo 8 (sin mirar la prueba ciega).
