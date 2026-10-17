# RD Internacional: primer sorteo + número de la fecha/hora sobre su motor (2026-10-14)

**Resultado: NO PASA.** Las dos correcciones que LA tiene (o tiene en sombra) no suman nada sobre el motor de RD
en la confirmación. Recomendación: **no ponerlo en sombra** para RD. Se archiva.

Pre-registro: `PREREGISTRO.md` (escrito antes de calcular). Script: `analizar.py` (`dev`, `conf`, `vivo`; ~10 s
cada etapa, poca RAM). Salidas: `factores.json`, `resultados_dev.json`, `resultados_conf.json`, `resultados_vivo.json`.

## Motor de referencia
P1 de RD = B0 `secuencia_v3` (solo RD) × exp(b·x), con x = memoria cruzada de LA (h:00, (h−1):00, salió hoy en LA).
Es el código de `rdint_vivo.py`. Para dev y desc se usa su walk-forward en `herramientas/rdint/cache_todo.npz`. El vivo
(2026-09-14..2026-10-07, último dato local de `oficial_multi.csv`) se reconstruyó igual que el servidor: fronteras
2000 + k·250 y `coef_b1.json` congelado.

## Correcciones (6 factores, ajuste conjunto sin selección)
Logit con offset log P1 y L2 λ = 1 (`rdint/modelo.ajustar`), ajustado **solo en dev RD 2024-03-01..2025-06-30**:

| factor | dónde | multiplicador | O/E contra el motor en dev |
|---|---|---|---|
| primer sorteo de ayer | solo 8:30 | ×0,729 | 4 / 5,9 = 0,68 |
| primer sorteo de hace 3 días | solo 8:30 | ×0,819 | 10 / 12,4 = 0,81 |
| número = día − 1 | todas las horas | ×1,010 | 1,02 |
| número = día | todas | ×0,769 | 0,78 |
| número = día + 1 | todas | ×0,866 | 0,87 |
| número = hora (reloj de 12 h) | todas | ×0,876 | 0,88 |

Primer hallazgo: **el motor de RD ya captura la mayor parte del "primero de ayer"**. Contra el azar, RD lo esquiva con
O/E 0,32, pero el motor ya le da poca probabilidad. Esperaba 5,9 casos y no 12,7, así que lo que queda es 0,68 con
n = 4. En LA quedaba 0,12. A RD le queda poco que corregir ahí. El "hace 3 días" sale bajo (0,81) en RD y no alto
como en LA (1,7), lo que coincide con el forense del enjambre 8:00.

## Resultados (Δ mbits por sorteo contra el motor RD, estratificado por hora; IC90 por bloques de jornada)

| tramo | n | conjunto | (a) primer sorteo | (b) fecha/hora | Top-5 | Top-15 |
|---|---|---|---|---|---|---|
| dev (dentro de muestra) | 5.784 | +1,95 [+0,36; +3,53] | +0,15 | +1,80 | 17,81 → 18,08 | 50,40 → 50,71 |
| **confirmación** 2026-04-13..09-13 | 1.800 | **−1,29 [−4,64; +2,01]** | −0,12 | −1,17 | 17,67 → 17,39 | 51,22 → 51,56 |
| vivo 2026-09-14..10-07 (descriptivo) | 288 | −1,46 [−9,83; +5,97] | +0,01 | −1,46 | 18,40 → 18,75 | 47,92 → 50,00 |

- Criterio pre-registrado: IC90 inferior > 0 → **falla** (−4,64). Top-5 −0,28 pp (no empeora > 0,5) → cumple.
  **NO PASA.**
- Incluso en dev el efecto es pequeño, +2 mbits por sorteo. En LA, la exposición sobre ag12 daba unos +6.
- En la confirmación, la hora en 12 h se invierte (O/E 1,23, 59 contra 47,9) y el día se acerca a 1 (0,92). Solo
  día + 1 sigue bajo (0,81). En el vivo, día + 1 sale alto (1,44) y la hora baja (0,52). Es el patrón típico del ruido:
  cada factor cambia de signo según el tramo.
- (a) por primer sorteo: −1,5 mbits en la confirmación (n = 150) y +0,1 en el vivo (n = 24). No hay nada.
- Por hora en la confirmación (conjunto): −2,9, −10,5, +0,9, −1,6, −3,5, −3,2, +4,9, −0,1, −3,1, −0,4, +0,5, +3,5.
  Ninguna hora se salva de forma consistente.

## Ejemplo con el congelado vigente (`/api/rdint`, GET, 2026-10-15 8:30)
Los animales tocados (8 por la hora, 14, 15 y 16 por la fecha, 21 por el primero de ayer) están todos fuera del
Top-15. Con la corrección, **el Top-15 no cambia** (11, 00, 29, 34, 20, 36, 4, 35, 31, 3, 10, 2, 5, 13, 0).

## Notas y salvedades
- El tramo test de RD (2025-07..2026-04-12) no se usó. La confirmación ya se gastó: no se vuelve a medir aquí.
- Antes, `desc` se había mirado de forma cruda para el "primero de ayer" (1/4,2 en el enjambre 8:00) y para el
  Top-15 de la regla RD. Ninguna de esas miradas eligió estos factores.
- El vivo usa `oficial_multi.csv` (juegos 1 y 2). Hay 92 choques de fuente: 81 de LA en dic-2025/ene-2026 (feriados
  corridos, ya corregidos en historial.txt) y 11 de RD en mar-2026. Ninguno cae en el periodo del vivo.
- El ajuste de LA (`prediccion.ajuste_primer_sorteo`, `exposicion.aplicar_8am`) no se toca: esto solo dice que no se
  traslada a RD.
- Para que el vivo de RD se pueda auditar con mbits completos, el congelado debería guardar las 38 probabilidades.
  Hoy `rdint_predicciones.json` solo guarda las del Top-15.
