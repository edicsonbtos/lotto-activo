# PRERREGISTRO — seguimiento en vivo de dos reglas (2026-10-01)

Escrito antes de mirar ningún sorteo en vivo posterior al 2026-09-29 (lo último que usó `INFORME.md`).
Los dos marcadores cuentan desde **2026-09-30** y se calculan sobre los pronósticos **congelados** de
Railway (`predicciones.json` y `rdint_predicciones.json`), así que no pueden maquillarse a posteriori.
Cada uno se juzga **una sola vez**, al llegar a su tamaño fijado; antes de eso solo se muestra.

## A. Lotto Activo: el RD (h−1):30 fuera del Top-15 (ADOPTADA en la web, sin confirmar)
Regla: si el animal que salió en RD a las (h−1):30 está entre los 15 primeros del congelado de LA h:00, sale
del Top-15; los de abajo suben un puesto y el 16º entra 15º (él queda 16º). El Top-5 queda igual que con la
regla del Top-5 ya vigente (`PREREGISTRO_cambio_rd_top5.md`). Sin efecto a las 8:00.
Evidencia previa (post-hoc, `INFORME.md` §3): +0,76 / +0,62 / +1,29 puntos de Top-15 en 2024 / 2025 / 2026.

- Marcador: `/api/cambio_rd15` y una fila en "Cada forma de jugar, con plata".
- Medida: en los sorteos donde hubo cambio, cuántas veces ganó el animal de RD que se sacó (`gano_rd`) contra
  cuántas el 16º que entró (`gano_16`). Además, aciertos del Top-15 y neto del Top-15 ponderado con y sin regla.
- **Juicio al llegar a 500 cambios** (unos 4 meses): **CONFIRMADA** si `gano_16 > gano_rd` con p < 0,05 en una
  binomial unilateral sobre los casos discordantes (`gano_16 + gano_rd`, p = 1/2). Si no, **NO CONFIRMADA** y se
  vuelve a mostrar el Top-15 del ensamble tal cual. Lo esperado (2026): el de RD gana ~0,9 % de los cambios y
  el 16º ~2,7 %, es decir, ~4-5 contra ~13-14.

## B. RD Internacional 18:30: Top-21 (SOLO seguimiento, sin plata)
Origen: en 2026 el Top-21 de RD a las 18:30 acertó 78,9 % (265 sorteos), en 2025 78 % y en 2024 67 %. Se eligió
la mejor de 24 horas mirando los datos, así que puede ser suerte. El empate del Top-21 plano es **70 %**
(21 fichas, paga 30).

- Marcador: `seguimiento_top21` dentro de `/api/rdint` y una línea en "Marcador RD". Control: el mismo Top-21
  en todas las demás horas de RD.
- Medida: aciertos del Top-21 congelado (puesto ≤ 21) en los sorteos de las 18:30 (hora 10) desde 2026-09-30.
- **Juicio al llegar a 150 sorteos de las 18:30** (unos 5 meses): **CONFIRMADA** si el límite inferior del
  IC 95 % de Wilson del acierto queda **por encima del 70 %**. Si no, **NO CONFIRMADA**: no se juega.
  Hasta el juicio no se recomienda poner plata por esta regla.
