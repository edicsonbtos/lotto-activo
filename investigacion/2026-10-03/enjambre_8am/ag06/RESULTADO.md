VEREDICTO: NULO
(C1/C2 "hueco ≤ 1 día" p = 0,10 / 0,09 en prueba. C3 temperatura queda en p = 0,049 por un pelo, pero no es propia del
primer sorteo: es la sobreconfianza general del motor desde oct-2025. Da +1,9 mbits y no cambia ningún Top-N.)

# ag06 — ¿Está mal calibrado el motor en el primer sorteo? (temperatura y curva de reciclaje)
Línea base: `P_aj` (ensamble_v2 + ajuste ×0,272/×1,736 de producción). Solo primeros sorteos. Pre-registro: `PREREGISTRO.md`.

## Qué se miró en dev (635 = 263 era 9:00 + 372 era 8:00)
36 bins O/E (puesto 5, hueco en días 8, horas exactas 11, conteo 3 d 4, conteo 7 d 6, franja de ayer 4) + temperatura
por era + validación cruzada entre eras para 3 familias × 6–9 λ. Al umbral Bonferroni de 0,05/36 = 0,0014 no
sobrevive ningún bin. Los únicos p < 0,01 son bins sueltos de la era 9:00 que la era 8:00 no replica.

| rasgo (O/E contra P_aj) | era 9:00 | era 8:00 | dev |
|---|---|---|---|
| puesto 1-5 / 6-10 / 11-15 / 16-25 / 26-38 | 0,85/1,12/0,88/1,01/1,10 | 0,98/1,09/1,17/0,84/1,02 | 0,93/1,10/1,06/0,91/1,06 |
| hueco 0 d (salió ayer) | 1,26 | 1,07 | 1,17 |
| hueco 1 d | 1,33 | 1,12 | 1,18 (p = 0,02) |
| hueco 2 d / 3 d | 0,73 / 0,50 | 0,91 / 1,06 | 0,84 / 0,81 |
| hueco 4 / 5 / 6 / 7+ d | 1,09/0,89/0,97/0,89 | 1,04/0,78/0,53/0,89 | 1,06/0,84/0,74/0,89 |
| apariciones en 3 d: 0 / 1 / 2 / 3+ | 0,84/1,05/1,30/1,33 | 0,90/1,11/1,00/0,80 | 0,88/1,08/1,11/1,01 |
| apariciones en 7 d: 0…5+ | 0,89…1,30 | 0,89…1,13 | 0,89–1,14 (nada) |
| salió ayer en mañana / tarde / noche | 1,14/1,36/1,23 | 1,11/0,98/1,14 | 1,12/1,19/1,18 (iguales) |
| horas exactas desde la última | 36-48 h: 2,48; 60-72 h: 0,51 | 0,64; 1,03 | no replica entre eras |

- **Temperatura** (q ∝ P_aj^β): β* = 0,81 ± 0,20 (era 9:00), **1,01 ± 0,11 (era 8:00)**, 0,97 ± 0,10 (dev). Entropía
  media 5,05 bits a las 8:00, log-loss 5,05. En validación cruzada entre eras cualquier β ≠ 1 PIERDE mbits para todo λ.
  **La temperatura del primer sorteo está bien calibrada.** No hay "otra temperatura tras la noche".
- **Reciclaje**: la única estructura coherente es "hueco ≤ 1 día" (salió ayer o anteayer, a cualquier hora). Da O/E 1,18
  (322 obs. contra 273,2), con el mismo signo en las dos eras (1,30 y 1,11). La franja de ayer en que salió no importa.
- Control: en las otras 11 horas de dev, el motor está calibrado por hueco (O/E 0,94–1,03). El exceso es solo del
  primer sorteo. Tampoco es artefacto del ajuste de producción: con P sin ajuste da 1,28/1,10, y sin el 1.º de ayer 1,30/1,12.
- Concuerda con la fe de erratas del PREREGISTRO_manana_8am: a las 8:00, hueco 1-3 días = 65,3 % obs. contra 61,6 % esperado
  (yo cuento 0-2 días "desde ayer" = su 1-3 días). Ellos dan 65,6 % contra 61,3 %.

## Candidatos (fijados en dev) → PRUEBA (261, una sola vez) → vivo (15)
C1: ×1,287 a los animales con hueco ≤ 1 d (λ = 20 por VC entre eras). C2: 4 bins {0-1, 2-3, 4-6, 7+} = ×1,170/0,915/0,967/0,966
(λ = 50 por VC). C3: β = 0,967.

| mbits por primer sorteo [IC 95 % bootstrap días] | dev 9:00 | dev 8:00 | **prueba** | p(≤0) prueba | vivo |
|---|---|---|---|---|---|
| C1 hueco ≤ 1 d | +30,7 | +7,2 | **+13,5 [−7,2; +34,0]** | 0,10 | +1,9 |
| C2 4 bins | +31,0 | +6,0 | **+12,4 [−5,9; +30,8]** | 0,09 | +0,8 |
| C3 temperatura | +0,7 | −0,3 | **+1,9 [−0,4; +4,2]** | 0,049 | −6,3 |

O/E del bin "hueco ≤ 1 d" contra P_aj: dev 9:00 1,30 [1,08; 1,54], dev 8:00 1,11 [0,96; 1,28], **prueba 1,12 [0,95; 1,30]
(166 contra 148,6, P = 0,085)** y vivo 1,05 (10 contra 9,5). Los tres bloques independientes apuntan igual. En conjunto,
dev + prueba da 488 contra 421,8 (O/E 1,16). Pero la prueba sola no llega ni a p < 0,05.

Sobre C3: en prueba, β = 0,967 también gana en las OTRAS horas (+0,68 ± 0,31 mbits/sorteo, 2874 sorteos). Es la
sobreconfianza general ya documentada desde oct-2025, no un rasgo del primer sorteo. La diferencia entre el primer
sorteo y el resto es +1,2 ± 1,2. Una temperatura no cambia el orden, así que no mueve aciertos ni plata.

## Efecto en plata (primer sorteo, prueba n = 261; Δ retorno por ficha a pago 30, IC bootstrap días)
| | Top-5 aciertos | Top-15 aciertos | Δret/ficha Top-5 | Δret/ficha Top-15 |
|---|---|---|---|---|
| C1 | 54 → 57 | 132 → 136 | +0,069 [−0,023; +0,184] | +0,031 [−0,038; +0,100] |
| C2 | 54 → 57 | 132 → 134 | +0,069 [−0,023; +0,184] | +0,015 [−0,046; +0,077] |
| C3 | 54 → 54 | 132 → 132 | 0 | 0 |
En dev 8:00, C1 dio Top-5 90 → 92 y Top-15 232 → 229. C2 dio Top-15 232 → 224, empeora. En vivo, Top-5 4 → 3.
Repartido en los 12 sorteos del día, C1 vale ~+1,1 mbits/sorteo.

## Escepticismo
- Casi todo el efecto de dev viene de la era 9:00 (+31 mbits). La era 8:00, que es la que se juega, da solo +6/+7 en dev
  y +13 en prueba, con IC que incluye el 0. La potencia era baja (SE ≈ 10 mbits) y el pre-registro ya lo anticipaba.
- Se miraron 36 bins y se eligió el bin "≤ 1 d" a posteriori. El λ salió de la VC entre eras: no se tocó la prueba.
- Sin fuga de futuro: los huecos usan solo seq[:t], y P_aj es walk-forward.

## Recomendación
Nada a producción. Para el ensamble: la hipótesis de "otra temperatura en el primer sorteo" queda descartada. Que el motor
subestime los animales de hueco ≤ 1 día en el primer sorteo es lo único con señal coherente en 3 bloques. Queda como
**candidato para sombra en vivo** (C1, ×1,287; estimación: ~+0,3 aciertos Top-5 por mes a las 8:00). Se re-evalúa con
≥ 250 primeros sorteos nuevos desde 2026-10-04: pasa si O/E del bin ≥ 1,10 contra scores congelados con p < 0,05.

Archivos: `rasgos.py` (rasgos) → `explorar_dev.py` (.out) → `control_otras_horas.py` → `ajustar_dev.py` (.out,
parametros_dev.json) → `evaluar.py` (.out). Todo en esta carpeta, ~5 s.
