# Informe: otros indicadores de "lo más jugado" (2026-10-15)

Pre-registro: `PREREGISTRO.md` (escrito antes de medir). Script: `mas_jugado.py` → `salida.txt`, `resultados.json`.
Datos: solo desarrollo [2000, 9357) (2024-03-07..2025-12-17, 7.357 sorteos, fechas corregidas en memoria);
dev-A [2000, 5688) elige, dev-B [5688, 9357) confirma. El tramo ≥ 9357 no se leyó. No se tocó motor, web ni marcador.

## Veredicto
**Ninguna de las 10 hipótesis pasa.** No se estima ninguna ganancia. La veta "el operador esquiva lo más jugado"
sigue limitada a lo que ya se sabía: día del mes (D0), día+1 (D+1) y hora en 12 h (H12).
Con el mismo método, esa corrección conocida da **+7,4 mbits en dev-B [+3,7; +11,3]** (m = 0,71 / 0,60 / 0,91).

## Resultados (O/E del ganador en el conjunto contra la probabilidad del motor; D0, D+1 y H12 quitados de cada conjunto)
Criterio: dev-A O/E < 1 con p < 0,05 **y** dev-B O/E < 1 con p < 0,005 (Bonferroni 10).

| Hipótesis | dev-A O/E (O/E esp.) p | dev-B O/E [IC 99 %] p | Placebo +7 (dev-B) | Veredicto |
|---|---|---|---|---|
| M1 día invertido (12→21, 10→1…) | 0,76 (18/23,8) p 0,09 | 0,80 [0,41; 1,25] p 0,12 | 1,16 | no pasa |
| M2 terminal del día | 1,04 (272/262,9) | 0,90 [0,76; 1,07] p 0,054 | 0,98 | no pasa |
| M3 terminal de la hora | 1,03 (273/264,4) | 0,97 [0,82; 1,12] | 1,11 | no pasa |
| M4 hora invertida | 1,06 (43/40,5) | 1,17 [0,77; 1,61] | 0,90 | no pasa |
| M5 invertido del último ganador | 0,81 (24/29,5) p 0,13 | **0,34** [0,10; 0,64] p 0,0002 | 0,93 | no pasa (falla dev-A) |
| M6 terminal del último ganador | 0,90 (238/265,5) p 0,028 | 0,87 [0,74; 1,02] p 0,012 | 0,95 | no pasa (falla Bonferroni en dev-B) |
| M7 suma de la fecha completa | 0,92 (82/89,3) | 0,81 [0,57; 1,07] p 0,028 | 1,23 | no pasa |
| M8 víspera de fecha festiva | 0,81 (4/4,9) | 0,27 (1/3,7) p 0,015 | 1,30 | no pasa (n mínimo) |
| M9 15 y 30 cerca de quincena | 0,97 (78/80,5) | 1,08 [0,83; 1,37] | 1,12 | no pasa |
| M10 D0 en día de pago vs resto (razón) | R 1,33 (0,92 vs 0,69) | R 0,39 (0,21 vs 0,54) p 0,017 | — | no pasa (se invierte entre mitades) |

## Lectura
- **M5 (invertido del último, 12→21)** tiene el dev-B más bajo (10 salidas contra 29,6), pero dev-A da 0,81 con IC que
  cruza 1: una mitad sola no confirma. Exploratorio (fuera del criterio): m = 0,81 ajustado en dev-A daría +1,4 mbits en dev-B [+0,8; +1,9].
- **M6 (terminal del último)** es la única con la misma dirección y tamaño en ambas mitades (0,90 y 0,87), pero p = 0,012 en
  dev-B no supera Bonferroni (0,005). Exploratorio: m = 0,89 → +1,0 mbits en dev-B [−0,4; +2,3]. Aunque pasara, es del orden
  de L3/R4 del hilo 9 (≈ +1 mbit), que no mueven ni el Top-5 ni el Top-15.
- **Quincena/día de pago (M9, M10)**: sin efecto consistente; M10 cambia de signo entre mitades.
- **Fechas festivas (M8)**: solo ~5 salidas esperadas por mitad; no tiene potencia para decir nada.
- Ninguna muestra heterogeneidad por hora fuera de lo esperado (χ² de 12 horas entre 4 y 19, descriptivo).

## Qué queda
- Nada entra al motor ni a la sombra por esta ronda. Si se quisiera seguir M5/M6, la única vía honesta es **vigilancia
  prospectiva** (marcador en vivo o una réplica pre-registrada en RD dev 2024-03-01..2025-06-30), no otra mirada al desarrollo LA.
- No se prueban variantes de estas 10 hipótesis sobre los mismos datos.

## Límites
Un solo juego (LA), solo desarrollo. El motor no conoce D0/D+1/H12; por eso se quitaron de cada conjunto. La lista de días
festivos, de días de pago y las parejas de invertidos se fijaron en el pre-registro sin ajustar.
