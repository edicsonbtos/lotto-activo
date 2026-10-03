VEREDICTO: PROMETEDOR
# ag02 — Calendario en el primer sorteo (2026-10-03)

**En una línea:** en el primer sorteo, el operador esquiva la ventana del día del mes {día−1, día, día+1} con más
fuerza que en las demás horas. Contra P_aj da O/E 0,43 en prueba. Descontada la esquiva general, el exceso propio
del primer sorteo da O/E 0,57 con p = 0,049: llega a PROMETEDOR, lejos del 0,0017 que exige CONFIRMADO.
El número de la hora (8 o 9), el mes, el año, el día de la semana y el día del año no muestran nada.

## Qué se miró en dev (~45 contrastes; `explorar_dev.py`, `explorar_dev2.py`, salidas `salida_dev*.txt`)
Hubo 15 rasgos: D0, D±1, D+2, mes, D+M, año (24/25/26), H12 y H12±1, día de la semana (lunes = 1 y domingo = 1),
día del año mod 37, día invertido y D·M. Cada uno se midió por era, en el primero contra P_aj, en el resto contra P,
con su interacción y en 'cal'. Se añadieron 4 controles cruzados de la hora, 3 ventanas, 17 corrimientos placebo y
4 periodos.

| rasgo (1º sorteo, vs P_aj) | 9:00 dev | 8:00 dev | 1º dev | demás horas dev (vs P) | cal 1º (vs 1/38) |
|---|---|---|---|---|---|
| D0 (día) | 0,82 | 0,39 | 0,57 | 0,61 | 1,45 |
| D+1 | 0,28 | 0,39 | 0,35 | 0,69 | 1,87 |
| D−1 | 0,69 | 0,40 | 0,52 | 0,92 | 1,66 |
| **ventana D−1..D+1** | **0,60** | **0,40** | **0,48 (25/52,0)** | **0,74** | **1,66 (24/14,4)** |
| hora del 1º (8 / 9) | 0,69 | 0,87 | 0,79 | 0,78 (H12) | 1,45 |
| mes / año / día sem. / día año | 0,74-1,34 | 0,77-1,22 | 0,76-1,27 | 0,85-1,07 | — |

- Control cruzado de la hora: en la era 8:00, "8" da 0,87 y "9" da 0,80. En la era 9:00, "9" da 0,69 y "8" da 0,56.
  El primer sorteo no esquiva su propia hora más que la otra: no hay señal específica de la hora.
- Placebo de corrimientos D+s en el primer sorteo (dev): s = −1, 0, +1 dan 0,52, 0,57 y 0,35. Para
  |s| ≥ 2, el rango va de 0,79 a 1,52. La ventana es lo único que destaca.
- Interacción primero contra resto en dev, ventana: p = 0,018 (unilateral). Con ~45 contrastes no basta por sí sola.
- **Contra la hipótesis:** en 'cal' (183 primeros sorteos a las 9:00, de 2023-09 a 2024-03) la ventana sale de más
  (1,66 contra azar). Con el tiempo la esquiva se intensifica: 1,66 → 0,63 (2024 a las 9:00) → 0,48 (2024-11 a 2025-06)
  → 0,32 (2025-H2). Si es real, es un cambio de conducta del operador, no algo estable.

## Candidatos a prueba (pre-registrados en `PREREGISTRO.md` antes de abrir prueba; 2 de 3 posibles)
Los multiplicadores se ajustaron solo en dev, con suavizado de +0,5. Los generales, en las demás horas: día−1 ×0,921,
día ×0,611, día+1 ×0,691.
- **C1 (específico, primario):** B_gen = P_aj × los multiplicadores generales. Sobre B_gen se aplica un extra de
  **×0,640** a la ventana en el primer sorteo.
- **C2 (práctico, no específico):** P_aj × **0,486** a la ventana en el primer sorteo.

| tramo | n | C1: O/E vs B_gen [IC95] | p unil. | C2: O/E vs P_aj [IC95] | p unil. |
|---|---|---|---|---|---|
| dev 9:00 | 263 | 13/16,4 = 0,79 [0,42; 1,36] | 0,25 | 13/21,6 = 0,60 | 0,033 |
| dev 8:00 | 372 | 12/23,0 = 0,52 [0,27; 0,91] | 0,009 | 12/30,4 = 0,40 | 0,0001 |
| **PRUEBA** | 261 | **9/15,8 = 0,57 [0,26; 1,08]** | **0,049** | **9/20,9 = 0,43 [0,20; 0,82]** | **0,0030** |
| vivo | 15 | 0/0,9 | — | 0/1,2 | — |

Las dos eras de dev tienen el mismo signo y prueba va en la misma dirección. Ninguno baja de 0,0017, así que los dos
quedan en **PROMETEDOR**. En prueba, las demás horas dan 0,80 en la ventana (186/232,4) y el primer sorteo 0,43
(interacción, p = 0,036). En prueba, el desglose de C2 queda así: D−1 2/6,9, D0 4/7,2, D+1 3/6,8.

## Información (mbits por primer sorteo, IC bootstrap por días)
| | dev | prueba | vivo |
|---|---|---|---|
| C1 contra B_gen (parte específica) | +7,2 [−3,2; +16,4] | +9,5 [−5,3; +22,4] | +30,8 |
| C2 contra P_aj | +21,1 [+4,7; +35,7] | **+24,7 [+0,8; +45,5]** | +59,6 |
| C1 completo (general + extra) contra P_aj | +20,3 [+2,4; +36,6] | +22,0 [−6,8; +46,9] | +62,1 |

## Plata a las 8:00 (prueba, 261 días; pago 30; IC bootstrap por días)
- C2 contra la jugada actual: Top-5 **54 → 61** aciertos, +0,16 por ficha [+0,05; +0,30]. Top-15 132 → 134,
  +0,015 por ficha [−0,02; +0,06]. En dev el Top-5 solo pasó de 134 a 137, así que el +7 de prueba es en parte suerte.
- C1 completo: Top-5 54 → 62. Top-15 132 → 135, +0,023 [−0,02; +0,07].
- En el día: unos +2 mbits por sorteo (24,7 / 12). Es pequeño, del mismo orden que el ajuste del primer sorteo de hoy.

## Escepticismo
- No hay fuga de futuro: el rasgo depende solo de la fecha. Las fechas son las del historial corregido (las 406
  correcciones de 2026-09-29 ya están en `hist_la.txt`).
- La parte específica (C1) es débil: p = 0,049 en prueba y p = 0,018 en dev entre ~45 contrastes. Los datos de
  'cal' van en contra.
- C2 mezcla la señal general de fecha, ya conocida y ya medida en prueba por `fecha_2026.py`. Por eso su
  p = 0,003 no cuenta como hallazgo nuevo. Solo dice que a las 8:00 esa señal es útil y fuerte.

## Recomendación
No se toca producción. Para la sombra de "exposición" (`/api/sombra`), en el primer sorteo se propone usar la
ventana {D−1, D0, D+1} con ×0,49 sobre P_aj (o el general × 0,64 extra) en vez del multiplicador general. Habría que
pre-registrar el vivo: con O/E 0,5, y ~1,2 esperados por cada 15 días, hacen falta ~6-9 meses para decidir.
Scripts: `explorar_dev.py`, `explorar_dev2.py` (solo dev) y `prueba.py` (ajusta en dev y mide una vez).
Salidas: `salida_dev.txt`, `salida_dev2.txt` y `salida_prueba.txt`.
