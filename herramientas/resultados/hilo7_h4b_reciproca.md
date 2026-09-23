# H4b â€” Â¿Lotto Activo gana al saber lo que saliÃ³ en RD Int? (2026-09-23 18:39)

Pre-registro: `herramientas/exploracion/PREREGISTRO_h4b_reciproca.md` (contaminaciÃ³n declarada ahÃ­).
LA 2024-03-07 .. 2026-09-22 (10587 filas evaluables); con RD ese dÃ­a: 99.0 %.
Prueba de fuga (cambiar RD desde h:30 no mueve la fila de LA h:00): **SIN FUGA**; control movido: 282.
Coeficientes al final: [-1.038, -0.089]  (exp: [0.35, 0.91])

| ventana | n | Î” mbits [IC95] | Top-3 ens â†’ +RD | Top-3 plano ens â†’ +RD | Top-5 escal. ens â†’ +RD [IC95] |
|---|---|---|---|---|---|
| PRINCIPAL (2025-12-17..2026-09-23) | 3239 | +9.7 [+4.9, +14.1] | 12.20 â†’ 11.95 % | +22.0 â†’ +19.5 % | +19.0 â†’ +16.6 [+8.3, +24.8] % |
|   sub: tramo test de RD (2025-12-17..2026-04-13) | 1332 | +6.3 [-3.3, +14.6] | 11.64 â†’ 11.56 % | +16.4 â†’ +15.6 % | +15.1 â†’ +12.0 [-0.1, +25.0] % |
|   sub: rÃ©plica (2026-04-13..2026-09-23) | 1907 | +12.2 [+6.9, +17.2] | 12.59 â†’ 12.22 % | +25.9 â†’ +22.2 % | +21.7 â†’ +19.8 [+9.4, +30.5] % |
| control (prueba ciega vieja) (2025-07-01..2025-12-17) | 1908 | +3.1 [-5.3, +10.6] | 13.57 â†’ 13.63 % | +35.7 â†’ +36.3 % | +33.3 â†’ +35.0 [+23.6, +47.4] % |
| desarrollo (ya visto) (2024-03-01..2025-07-01) | 5440 | +11.5 [+7.5, +15.4] | 12.65 â†’ 12.70 % | +26.5 â†’ +27.0 % | +21.0 â†’ +22.1 [+15.1, +29.0] % |

RepeticiÃ³n cruda LA h:00 == RD (hâˆ’1):30 (contra 1/38), ventana principal, por hora:
  total 25 de 2923 (esperado 76.9)

**VEREDICTO H4b: PASA** (Î” â‰¥ +5 mbits e IC95 > 0 en la ventana principal)
**Dinero (Top-5 escalonado con RD > sin RD): NO**

_Corrido en Railway (botón Herramientas) el 2026-09-23. Auditoría de fuga: sin hallazgos que invaliden (3 menores)._
