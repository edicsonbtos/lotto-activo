# Pre-registro: correcciones de LA llevadas al motor de RD Internacional (2026-10-14, antes de calcular)

## Qué se prueba
Dos correcciones que LA ya tiene (o tiene en sombra) y que el motor de RD (`rdint_vivo.py`) NO tiene:

- **(a) Primer sorteo** (`prediccion.ajuste_primer_sorteo` en LA). En el primer sorteo del día de RD (8:30):
  - F1 `primer_ayer`: el ganador del primer sorteo de RD de la fecha − 1 día (si existe y fue a la misma hora).
  - F2 `primer_hace3`: lo mismo con la fecha − 3 días.
- **(b) Exposición** (`herramientas/modelos/exposicion.py` en LA). En TODAS las horas de RD:
  - F3 `dia-1`, F4 `dia`, F5 `dia+1`: el animal cuyo número es el día del mes −1, 0, +1 (solo si cae en 1..36).
  - F6 `hora12`: el animal cuyo número es la hora del sorteo en reloj de 12 h (8:30 → 8, 13:30 → 1, …).

Se ajustan los 6 factores a la vez y sin selección: queda lo que salga del ajuste, aunque algún factor
salga ≈ 1 o con el signo "equivocado". No se añaden ni quitan rasgos después de ver dev.

## Motor de referencia
P1 de RD = B0 `secuencia_v3` (solo RD) + B1 (memoria cruzada de LA), walk-forward, de
`herramientas/rdint/cache_todo.npz` (filas dev, test, desc). Es el mismo código que produce el congelado en vivo.
Para el vivo (2026-09-14 en adelante, que el caché no tiene) se reconstruye igual que `rdint_vivo.py`: B0
`secuencia_v3` con fronteras 2000 + k·250 y B1 con `coef_b1.json` congelado; datos de `oficial_multi.csv`
(juego 1 = LA, juego 2 = RD).

## Ajuste (solo DESARROLLO RD 2024-03-01..2025-06-30)
Logit condicional con offset: P_adj[t,i] ∝ P1[t,i] · exp(b · x_i(t)), b por MLE con L2 λ = 1
(`herramientas/rdint/modelo.ajustar`, igual que el ajuste de LA). Multiplicadores = exp(b). Se congelan en
`factores.json` antes de abrir la confirmación. El tramo test 2025-07-01..2026-04-12 NO se usa.

## Confirmación (UNA vez, factores congelados)
Tramo `desc` 2026-04-13..2026-09-13 (≈ 1.800 sorteos; antes solo se miró para el Top-15 de otra regla y, de
forma cruda, el conteo "primero de ayer" del enjambre 8:00).

- **Métrica primaria:** Δ mbits por sorteo = 1000 · [log2 P_adj(y) − log2 P1(y)], **estratificada por hora**
  (media de las 12 medias por hora, cada hora con el mismo peso).
- **IC90** por bootstrap de jornadas (se remuestrean días completos; 4.000 réplicas; semilla 20261015).
- **Criterio PASA:** límite inferior del IC90 > 0 **y** Top-5 (P_adj) − Top-5 (P1) ≥ −0,5 pp en confirmación.
  Si no se cumplen las dos, NO PASA.

## Secundario (no decide)
- Cada corrección por separado con sus factores del ajuste conjunto: (a) sola, (b) sola.
- (a) medida solo en primeros sorteos (mbits por primer sorteo).
- Tabla por hora; Top-3 y Top-15.
- Vivo (2026-09-14 hasta el último dato local, ~2026-10-07): mismo cálculo, solo descriptivo por potencia baja
  (~290 sorteos, ~24 primeros sorteos). Se anota si el signo coincide con la confirmación. Se usa además el
  pronóstico congelado vigente de `/api/rdint` (GET) como ejemplo de qué cambiaría.

## Qué NO se hace
No se toca `rdint_vivo.py`, `servidor.py`, `prediccion.py` ni nada en producción. Sin commit ni deploy.
Si pasa, la recomendación máxima es ponerlo **en sombra** en vivo (con su propio pre-registro), no en la jugada.
