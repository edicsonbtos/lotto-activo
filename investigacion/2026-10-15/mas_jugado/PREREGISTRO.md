# Pre-registro: ¿el operador esquiva OTROS números "de los más jugados"? (2026-10-15, escrito ANTES de medir)

Script: `mas_jugado.py` (misma carpeta). Salida: `salida.txt`, `resultados.json`.

## Punto de partida
Señal conocida (top15_70 ronda 2, 2026-10-01): el ganador esquiva el animal cuyo número es el día del mes
(D0, O/E 0,71 / 0,51), el de mañana (D+1, 0,66) y el de la hora en reloj de 12 h (H12, 0,91 / 0,64).
Hipótesis de fondo: el operador esquiva lo más jugado.

## Ya medido (NO se repite)
- Ronda 2: D0, D+1, D−1, D+2, H12, H24; popularidad estable por animal (Spearman, no pasa).
- Ronda 5: mes (C1, 0,84/0,88, no pasa), día de la semana, día+mes, suma de dígitos del día (pasó en LA, no replicó en RD:
  archivada), n.º de sorteo, día+hora12, año de dos dígitos (25/26), "espejo" 38−día.
- Barrido 2 (366): `eq_fecha` y distancia circular / cuadrante / color / paridad / lado respecto al último ganador.
- Francotirador G3a: quincena (días 15 y 30) como filtro de retorno del Top-5 (no pasa).
- Ataque al generador H3: distribución en fechas especiales (chi² de homogeneidad, no pasa).
- "Otras loterías h−1" como fuente: cerrado (top15_70). No se usa ningún dato de otras loterías.
- Misma hora de ayer (1,06), primer sorteo de ayer (ya aplicado), salió ayer: calibrados.

## Lista de hipótesis (10, Bonferroni 10). Objetivo = conjunto de animales "muy jugados" en ese sorteo
Regla común: de cada conjunto se QUITAN siempre los animales D0, D+1 y H12 del sorteo (efectos ya conocidos),
para medir solo información nueva. Si el conjunto queda vacío, el sorteo no cuenta para esa hipótesis.
Las fechas son las CORREGIDAS (`herramientas/correccion_historial_2026-09-29.json`, en memoria, como `robustez_fechas.py`).
"Último ganador" = el sorteo anterior de Lotto Activo en la secuencia (a las 8:00, el de las 19:00 de la víspera).

| Id | Conjunto | Por qué sería "lo más jugado" |
|---|---|---|
| M1 día invertido | número del día leído al revés: 10→1, 20→2, 30→3, 12→21, 13→31, 21→12, 23→32, 31→13 (si ≤36 y distinto del día) | "jugar la fecha al revés" es costumbre de la charada y de los triples |
| M2 terminal del día | animales cuyo último dígito = último dígito del día (0 y 00 terminan en 0) | los "terminales" son la jugada más común en triples; el terminal de la fecha se juega mucho |
| M3 terminal de la hora | animales cuyo último dígito = último dígito de la hora 12 h | igual que M2 con la hora (la hora 12 h ya es esquivada) |
| M4 hora invertida | hora 12 h al revés: 10→1, 12→21, 1→10, 2→20, 3→30 (11 y 4..9 no tienen) | "la hora al revés" |
| M5 invertido del último ganador | 1↔10, 2↔20, 3↔30, 12↔21, 13↔31, 23↔32 | "salió el 12, juega el 21": muy repetido en grupos de pronóstico |
| M6 terminal del último ganador | animales con el mismo último dígito que el último ganador (sin él) | "salió el 14, va el terminal 4" |
| M7 suma de la fecha completa | suma de los 8 dígitos dd+mm+aaaa (p. ej. 14/10/2026 → 16) | numerología de la fecha; distinta de la suma de dígitos del día (C4) y de día+mes (C3) |
| M8 víspera de fecha festiva | en los 3 días anteriores a 1/1, 19/4, 1/5, 24/6, 5/7, 24/7, 12/10, 24/12, 25/12, 31/12: el número del día festivo | se juega la fecha patria/festiva con anticipación |
| M9 números de quincena | {15, 30} en días a ±3 de un día de pago (12-18, 27-31, 1-3) | quincena y fin de mes: "el 15 y el 30" en días de cobro |
| M10 día de pago × fecha | NO es un conjunto: compara el O/E del animal D0 en días de pago {15, 16, último del mes, 1} contra el resto (razón de O/E). Aquí D0 NO se quita | "más jugadores en quincena → más esquive" |

## Métrica
- Para M1-M9: O = n.º de sorteos en que el ganador ∈ conjunto; E = Σ P(conjunto) del motor (caché walk-forward
  `herramientas/exploracion/calor_cache.npz`, normalizada). O/E = ΣO/ΣE. Como E se calcula sorteo a sorteo, la razón ya está
  estandarizada por hora (estimador de Mantel-Haenszel para tasas con referencia interna = Σ_h O_h / Σ_h E_h); se reporta además
  el O/E por hora y una prueba de heterogeneidad (descriptiva).
- M10: R = (O/E en días de pago) / (O/E en el resto), animal D0.
- IC y p unilateral por bootstrap de jornadas (4.000 réplicas, semilla 20261015).
- Placebo descriptivo por hipótesis: el mismo conjunto corrido +7 en el orden de códigos (mod 38), con las mismas exclusiones.

## Tramos (solo desarrollo [2000, 9357); el tramo ≥ 9357 NO se lee)
- dev-A = filas [2000, 5688) — elige. dev-B = filas [5688, 9357) — confirma (mismos cortes que top15_70).

## Criterio (fijo)
Una hipótesis PASA si:
1. dev-A: O/E < 1 (R < 1 en M10) con p unilateral < 0,05; y
2. dev-B: O/E < 1 (R < 1) con p unilateral < 0,005 (Bonferroni 10).
Si O/E > 1 de forma clara se reporta, pero no cuenta como pase (la hipótesis es "esquiva").

## Ganancia (solo las que pasen)
Corrección multiplicativa P' ∝ P · m sobre el conjunto (renormalizada por sorteo), m ajustado por máxima verosimilitud
SOLO en dev-A; se mide en dev-B la ganancia en mbits = 1000·media(log2 P'[y] − log2 P[y]), IC por bootstrap de jornadas.
También con todas las que pasen juntas (un m por hipótesis, ajustado conjunto en dev-A).
Referencia: la corrección D0/D+1/H12 ya conocida suma ~+6 mbits.

## Si nada pasa
Se declara: ningún otro indicador de "lo más jugado" probado aquí aporta; la veta fecha/hora sigue limitada a D0, D+1 y H12.
No se prueba ninguna variante de estas hipótesis sobre los mismos datos. No toca motor, web, historial ni marcador.
