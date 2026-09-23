# PRE-REGISTRO — Regla de cambio RD → Top-5 de Lotto Activo

Escrito el 2026-09-23, ANTES de correr `herramientas/rdint/cambio_top5.py` sobre la ventana principal.

## Idea (del usuario)
Si el animal que salió en RD Int a las (h−1):30 está en el Top-5 del ensamble para LA h:00, sacarlo
y subir al #6. Fichas 2-2-2-1-1 por puesto después del cambio. No cambia nada más (ni modelo ni pesos).

## Ya visto (desarrollo, calor_cache, filas < 9357)
Diferencia de retorno por ficha (con cambio − sin cambio): 2024-03..10 +1,01 pp [−1,01, +2,75];
2024-11..2025-06 +0,53 [−0,93, +1,85]; 2025-07..12-16 +2,36 [+0,39, +4,52].
En esos casos el animal de RD ganó 16 veces de 934 y el #6 que entraba ganó 32.

## Ventana de decisión (nunca usada para ESTA regla)
LA 2025-12-17 .. 2026-09-22. Ya se miró una vez para H4b (modelo con coeficientes, no esta regla):
contaminación declarada.

## Criterio
- Métrica: diferencia de retorno por ficha del Top-5 escalonado, IC95 por bootstrap de jornadas (2.000).
- **CONFIRMADA** si diferencia > 0 y límite inferior del IC95 > 0.
- **SE ADOPTA** (sin confirmar) si diferencia > 0 con IC que cruza 0: la regla no cuesta fichas y
  desarrollo apunta al mismo lado. Se sigue en el marcador en vivo.
- **SE DESCARTA** si diferencia ≤ 0.
