# PRE-REGISTRO — ¿RD de las 7:30 PM afecta a Lotto Activo de las 8:00 del día siguiente?

Escrito el 2026-09-23, ANTES de mirar ningún dato de esta pregunta (ni en desarrollo ni en la ventana
principal). Idea del usuario.

## Idea
La regla de cambio en vivo usa RD (h−1):30 para LA h:00 y excluye las 8:00 a propósito. Aquí se prueba
extenderla a las 8:00 con el RD de las **19:30 del día anterior** (12 h 30 min antes, cruza la noche).
Misma regla ya validada: si ese animal está en el Top-5 del ensamble de LA 8:00, sale, los de abajo
suben y el 6º entra 5º. Fichas 2-2-2-1-1.

## Datos
LA 8:00 existe desde 2024-11-25. Desarrollo: 2024-11-25..2025-12-16 (~370 sorteos de 8:00).
Ventana de decisión: 2025-12-17..2026-09-22 (~270). Esa ventana ya se usó para H4b y para la regla
de cambio con h ≥ 1, pero **nunca para las 8:00 ni para el cruce de noche**: contaminación declarada.
Se espera que la regla actúe en ~1 de cada 7-8 sorteos: ~50 casos en desarrollo y ~35 en la ventana.
**Poca potencia:** lo más probable es un resultado no concluyente.

## Métricas (las dos se reportan en las dos ventanas)
1. Señal: veces que LA 8:00 == RD 19:30 del día anterior, frente a lo esperado por azar (n/38) y frente
   a lo esperado por el ensamble (suma de P del ensamble para ese animal). Hay señal si observado <
   esperado por el ensamble con p < 0,05 (Poisson, una cola).
2. Dinero: diferencia de retorno por ficha del Top-5 escalonado (con cambio − sin cambio), IC95 por
   bootstrap de jornadas (2.000), como en PREREGISTRO_cambio_rd_top5.md.

## Criterio (ventana de decisión)
- **CONFIRMADA:** diferencia > 0 con IC95 entero sobre 0 **y** señal con p < 0,05.
- **SE ADOPTA sin confirmar:** diferencia > 0 en la ventana **y** en desarrollo (no cuesta fichas).
- **SE DESCARTA:** diferencia ≤ 0 en la ventana. No se vuelve a mirar esa ventana para esta idea;
  la única vía siguiente sería el marcador en vivo.
