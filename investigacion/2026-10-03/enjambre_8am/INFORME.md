# Enjambre de 10 agentes: solo el primer sorteo del día (8:00), 2026-10-03

Pedido del usuario: buscar una ventaja más en el sorteo de las 8:00, con 10 agentes. Protocolo común (`BRIEF_COMUN.md`):
- Base compartida `base8.npz`: ensamble_v2 walk-forward, P_aj = motor con el ajuste del primer sorteo de producción.
  Se reconstruye con `construir.py` sobre una copia del historial.
- Cada agente pre-registra, elige solo en dev (eras 9:00 y 8:00) y manda a prueba (261 primeros sorteos) como mucho 3 candidatos.
- Hay 30 contrastes en total. CONFIRMADO exige p < 0,0017 en prueba y mismo signo en las dos eras.

## Resultado por agente
| # | Hipótesis | Veredicto | Número clave |
|---|---|---|---|
| 01 | Mapa de memoria (233 rasgos: k = 1..14 días × posición; primero de hace 1..30) | NULO | q mínimo FDR 0,87. "Salió ayer (pos ≥ 1) o anteayer" ×1,378: prueba O/E 1,12, p = 0,085 |
| 02 | Calendario en el primer sorteo | PROMETEDOR | Ventana {D−1, D, D+1}: prueba 9/20,9 = 0,43 contra P_aj. Parte propia de las 8:00, p = 0,049 |
| 03 | Distribución marginal (color, docenas, 0/00, cumpleaños…) | NULO | χ² por animal p = 0,81 / 0,67; solo reaparece la fecha general |
| 04 | Relaciones numéricas de noche a mañana (±1, espejo, rueda, tablero) | NULO | p mínimo en dev 0,13; las eras se contradicen en 12 de 20 |
| 05 | Los primeros sorteos como serie propia (bolsa, coleccionista, balanceo) | NULO | 69 contrastes; ninguno con p < 0,01 y mismo signo en las dos eras |
| 06 | Calibración del motor a las 8:00 (temperatura, hueco, puesto) | NULO | β = 1,01 ± 0,11. Hueco ≤ 1 día ×1,287: prueba +13,5 mbits, p = 0,10 |
| 07 | Regla cruzada con el primer sorteo de ayer de RD, LARD y otras | NULO | LA contra RD: O/E 1,00. Lateral: **RD esquiva su propio primero de ayer** (9/28,2) |
| 08 | Modelo especializado (logit con 98 rasgos sobre P_aj) | NULO | −19,4 mbits fuera de pliegue en dev |
| 09 | Regla en días abiertos y por día de la semana | NULO | "Premio solo de lunes a viernes" se invirtió en prueba (−14,5 mbits) |
| 10 | Forense del hallazgo de hoy (¿artefacto?) | REAL | Historial = API oficial en 5.148 sorteos; API sola 1/422 (O/E 0,09); RD 1/422; LARD 1,10 |

## Lo que queda en pie
1. **La regla de producción (primero de ayer ×0,272) es real.** Se reproduce con la API oficial sola, en RD Internacional
   (que no se usó para descubrirla) y no en LARD (control). El premio de hace 3 días (×1,736) es más débil y no se
   replica en RD.
2. **Ventana de fecha a las 8:00 (ag02): PROMETEDOR, no confirmado.** Auditoría del revisor-sesgo:
   - No hay fuga. El p corregido honesto de la parte propia es ≈ 0,1.
   - Entre 2023 y 2024-T2 la ventana iba al revés (1,42-1,68 contra el azar). Desde 2024-T3 sale 0,40, estable en
     9 trimestres.
   - Veredicto de la auditoría: **sombra, no la jugada**. Por eso, según la condición del usuario ("si pasa la
     auditoría"), **no se aplica a la jugada**.
   - Va en sombra desde 2026-10-04: `exposicion.aplicar_8am`, bloque `ventana_8am` de `/api/sombra`,
     pre-registro en `PREREGISTRO_sombra_8am.md`.
3. **"Salió ayer o anteayer" en el primer sorteo (ag01 y ag06, el mismo efecto):** prueba O/E 1,12 [0,95; 1,30],
   p ≈ 0,09. Queda para vigilar en vivo; no entra en sombra.
4. **RD Internacional esquiva su propio primer sorteo de ayer** (crudo O/E 0,32, en dev y en prueba de RD).
   Es un hilo aparte para el motor de RD (8:30). No se tocó.

## Prueba en 2026 y en los pronósticos "congelados" (`verif/eval2026.py`, `verif/salida_eval2026.txt`)
- Railway y lottoactivo.com están bloqueados por la red de esta sesión, así que no se pudieron bajar los registros
  congelados. Se usó su reconstrucción walk-forward, que reproduce los congelados con diferencia ≤ 0,0001.
- **Advertencia:** 2026 está dentro del tramo de prueba, que los agentes ya miraron hoy. **No es una prueba ciega nueva.**
  La única ciega real es el vivo desde 2026-10-04.

Primeros sorteos de 2026 (01-01..09-29, n = 265). Fichas: Top-5 escalonado = 8 por sorteo; Top-15 ponderado = 23 por sorteo.

| modelo | mbits contra producción [IC95] | Top-5 | Top-15 | neto Top-5 esc. | neto Top-15 pond. |
|---|---|---|---|---|---|
| motor sin ajuste del primero | −28,3 [−54; −3] | 57 | 134 | +400 | +445 |
| **producción (P_aj)** | 0 | 57 | 139 | +460 | +655 |
| + ventana ×0,486 | +24,2 [+0,7; +44,6] | 64 | 141 | +820 | +1.075 |
| + exposición + ventana ×0,59 | +24,6 [+1,0; +46,2] | 63 | 140 | +820 | +1.045 |
| + ayer/anteayer ×1,378 | +13,0 [−14; +40] | 59 | 143 | +550 | +865 |
| + ventana + ayer/anteayer | +36,4 [−0,3; +71] | 65 | 143 | +820 | +1.135 |

- Los 15 primeros sorteos en vivo (09-15..09-29) no cambian ningún acierto.
- El ajuste ya aplicado hoy le gana al motor sin ajuste en 2026 (+28 mbits, Top-15 de 134 a 139).
- Las dos candidatas suman algo en 2026, pero eso es el mismo tramo en que se eligieron y el salto del Top-5 no
  apareció en dev. Lo decide el vivo.

## Ideas cerradas hoy (no repetir sin razón nueva)
- Memoria completa del primer sorteo más allá de k = 1 y 3.
- Distribución marginal del primer sorteo.
- Relaciones numéricas de noche a mañana.
- Bolsa o balanceo de los primeros sorteos.
- Temperatura a las 8:00.
- Regla cruzada de primer sorteo entre juegos.
- Modelo especializado del primer sorteo.
- Regla por días abiertos o por día de la semana.
