# PRE-REGISTRO — Camino 2: ag12 en sombra + regla de cambio RD aplicada al Top-15

Escrito el 2026-09-30 ANTES de correr `medir.py`. No se cambia después de ver resultados.

Ya visto antes de escribir esto: solo `/api/sombra` (marcador en vivo de la sombra, 59 sorteos) y los
números publicados de la prueba ciega de ag12 (RETOMAR.md). Ningún número de la regla Top-15.

## Datos y fechas
- LA: `historial.txt` local (12.511 filas, hasta 2026-09-16). Las fechas se corrigen EN MEMORIA con
  `herramientas/correccion_historial_2026-09-29.json` (no se toca el archivo). Se excluyen los días tocados
  por esa corrección (fecha vieja o nueva) porque el ensamble se calculó con la fecha vieja.
- RD Int: `datos_multiloteria/rdint_hist.csv` (hasta 2026-09-22).
- Ensamble walk-forward: `herramientas/exploracion/calor_cache.npz` (filas 2000..9356) y
  `lotto-activo-motor/motor_nuevo/reciente/P_ens_reciente.npy` (filas 9357..12510). ag12 V1:
  `.../reciente/P_ag12_V1.npy` (mismas filas). No se recalcula ningún modelo.
- Limitación: la ventana pedida llega a 2026-09-22/29, pero las matrices locales llegan a 2026-09-16.
  Se usa 2026-04-01..2026-09-16. Lo posterior lo juzga el marcador en vivo.

## (a) ag12 en sombra — solo descripción + criterio para el futuro
- Se resume `/api/sombra` sin veredicto (59 sorteos no deciden nada).
- Tamaño necesario: desviación por sorteo de Δ(mbits) = la de la 2.ª prueba ciega (filas 9357..12510,
  ya gastadas: solo se usa para la varianza). n = ((z_α + z_β)·σ / 19,4)² con α = 0,05 unilateral, potencia 80 %;
  también con la cifra encogida (~+10 mbits) que espera la auditoría.
- **Criterio para pasar ag12 a la jugada (pre-registrado):** una sola mirada decisoria cuando el marcador de
  sombra tenga **n ≥ N80** sorteos (N80 calculado arriba, con el efecto +19,4), contados desde 2026-09-26. Fecha
  estimada = 2026-09-26 + N80/12 días. PASA si Δ(ag12 − ensamble) > 0 y el límite inferior del IC 90 % bilateral
  (= 95 % unilateral) por bloques de jornada > 0. Además Top-5 escalonado de ag12 no peor que el del ensamble en
  más de 3 pp/ficha (punto, no IC). Freno por inutilidad (puede mirarse cada mes, no permite adoptar):
  si con n ≥ 600 Δ < −10 mbits, se apaga la sombra y ag12 queda descartado.

## (b) Regla de cambio RD → Top-15 de LA
Regla: si el animal de RD Int (h−1):30 está en el Top-15 del ensamble para LA h:00 (h ≥ 9:00), sale,
los de abajo suben un puesto y el 16.º entra 15.º. Sin RD ese día/hora: sin cambio. Base = ensamble sin
cambio en el Top-15 (el Top-5 escalonado ya lleva la regla en vivo; con esta extensión el Top-5 es idéntico
al de la regla actual, así que no se mide de nuevo).
- Métrica principal: diferencia de retorno por ficha del **Top-15 ponderado** (3-3-3-2-2-1×10 = 23 fichas, paga 30),
  con − sin. Secundarias: Top-15 plano (15 fichas), acierto Top-15. IC95 por bootstrap de jornadas (2.000, semilla 20260930).
  Se reporta por hora (descriptivo) y cuántas veces ganó el de RD contra el 16.º que entró.
- **Desarrollo:** LA 2024-03-01..2025-06-30. Si Δ ponderado ≤ 0 en desarrollo → NO PASA y no se mira la confirmación.
- **Confirmación (una sola vez):** LA 2026-04-01..2026-09-16. Contaminación declarada: las filas ≥ 9357 de LA
  se miraron muchas veces (prueba de ag12, H4b, regla Top-5 en 2025-12-17..2026-09-22, Top-15 de RD en
  2026-04-13..09-13). Esta regla Top-15 nunca se midió ahí, pero es réplica débil.
  - **PASA** si Δ ponderado > 0 y límite inferior IC95 > 0.
  - **NO PASA** si Δ ≤ 0, o si el IC cruza 0 (se puede seguir en vivo como "no cuesta", pero no se llama PASA).

## (c) ag12 en los últimos 6 meses de LA (RÉPLICA, no prueba)
LA 2026-04-01..2026-09-16 es un subconjunto de la 2.ª prueba ciega ya usada. Solo descriptivo:
Δ mbits [IC95 bloques], Top-3/5/15, retorno Top-5 escalonado, Top-15 ponderado y plano, ensamble vs ag12 V1,
y exploratorio ag12 + regla Top-15. Sin veredicto propio.

## Anexo (2026-09-30, después de correr; solo rellena la fórmula de (a), no cambia ningún criterio)
- σ por sorteo de Δ mbits en la 2.ª ciega = 238 (con bloques 229). N80 (efecto +19,4, α 5 % unilateral) = **931 sorteos**.
- A ~12 sorteos con sombra por día desde 2026-09-26: **mirada decisoria única el 2026-12-14** (o el primer día con n ≥ 931
  en /api/sombra, lo que llegue después). Si el efecto real es +10 mbits harían falta ~3.500 (~10 meses).
