# r2_a07_memoria_larga: NO PASA (ángulo cerrado)

Pregunta: con la base ag12 V1, ¿tiene el operador una memoria SEMANAL? En concreto: (a) ¿evita el par consecutivo
s1–i que salió exactamente hace 7/14/21/28 días (el mismo día de la semana)?, (b) ¿evita el animal que ganó a la misma
hora hace 7 (y 14/21/28) días?, (c) ¿evita completar un par de un día de hace 1-4 semanas con el que hoy ya comparte
pares (composición del día)? Control placebo con desfases no naturales (6/8/13/15/20/22/27/29 días).
El prerregistro (`PREREGISTRO.md`) se escribió antes de correr. Hubo 3 variantes y una sola corrida (11 s, un hilo, poca RAM).
Datos: solo filas [2000, 9357), n = 7357. No se tocaron las filas >= 9357 ni `sellado/`.

Modelo: reajuste completo (log P_ens offset + 33 variables de ag12 V1 + las nuevas), λ = 30, cross-fit en los mismos
5 bloques de jornada de ag02/ag12. Control: el mismo código sin variables nuevas reproduce P_V1 (diferencia máxima 2,0e-13).

## Resultados (Δ mbits frente a ag12 V1 = +141,78 mbits; Top-15 V1 54,78 %, Top-5 22,13 %)
| Variante | Δ mbits [IC95] | mitad 1 | mitad 2 | Top-5 | Top-15 | Barra |
|---|---|---|---|---|---|---|
| **V1 primaria** (PS par semanal + HS1 misma hora d−7 + HS2 misma hora d−14/21/28) | **+0,01 [−1,04 ; +1,08]** | −1,33 [−3,03 ; +0,29] | +1,36 [+0,10 ; +2,67] | 22,35 % | 54,97 % | NO |
| V2 placebo (mismas variables, desfases no naturales) | −0,34 [−0,69 ; +0,03] | −0,22 | −0,45 | 22,21 % | 54,82 % | NO (esperado) |
| V3 composición del día (log1p CS) | +0,20 [−0,27 ; +0,63] | +0,03 | +0,37 | 22,10 % | 54,85 % | NO |
| Δ(V1) − Δ(V2 placebo) | +0,35 [−0,75 ; +1,46] | | | | | NO |
| V1 forward frente a ag12 forward | +0,15 [−0,53 ; +0,81] (bloques 1-4: +0,19 [−0,62 ; +1,01]) | −0,61 | +0,91 | 21,99 % | 54,97 % vs 54,61 % | NO |
| V3 forward (bloques 1-4) | +0,23 [−0,06 ; +0,50] | | | | | NO |

Top-5 escalonado por ficha: V1 +35,94 % contra +34,92 % (Δ +0,01 [−0,01 ; +0,03]).
Pesos V1 por bloque: PS −0,095 a −0,165; HS1 −0,025 a −0,146; HS2 −0,023 a −0,074 (todos negativos, pequeños).
Pesos placebo: PP −0,00 a +0,085; HP1 −0,049 a +0,024; HP2 −0,051 a +0,020 (alrededor de 0). CS −0,118 a −0,174.

## Sondeo descriptivo (O/E frente a P_V1 por desfase exacto, `consola.txt`)
- Par s1–i del mismo día de la semana (L = 7/14/21/28): 297 contra 337,9 esperados, O/E 0,879 (z −2,22).
  Placebo (6/8/13/15/20/22/27/29): 725 contra 710,1, O/E 1,021 (z +0,56). Por desfase suelto: L = 7 0,945; 14 0,973;
  21 0,784; 28 0,807. Pero hay desfases no semanales igual de bajos (L = 4 0,685; 9 0,748) y otros altos (12 1,211):
  el perfil es ruidoso y no hay un patrón semanal limpio.
- Misma hora hace L días: semana 719 contra 767,1, O/E 0,937 (z −1,73); placebo 0,986 (z −0,53). L = 7: 0,911 (z −1,26).
  El más extremo es L = 33 (0,816, z −2,49), que no tiene sentido de calendario → ruido de 70 pruebas.

## Lectura
Hay un indicio débil de dirección correcta (O/E 0,88 en pares semanales, pesos negativos en los 5 bloques, placebo en 0),
pero el efecto es pequeño y raro (1,9 candidatos marcados por sorteo para PS; menos de 1 para HS1). Sobre ag12 aporta
+0,01 mbits, la mitad 1 va en contra, y no se separa del placebo (+0,35 [−0,75 ; +1,46]). La composición del día tiene
peso negativo estable pero aporta +0,2 mbits. Las ventanas 2-7 y 8-30 de ag12 ya absorben la evitación de pares
antiguos; alinear al día de la semana no añade nada medible.

**Veredicto:** no existe memoria semanal útil sobre ag12 V1 (ni pares del mismo día de la semana, ni misma hora de la
semana pasada, ni composición del día). No hay candidato para el marcador en vivo. Ángulo cerrado.

Reproducir (PowerShell, desde la raíz del worktree lotto-activo-motor):
`$env:PYTHONIOENCODING='utf-8'; python motor_nuevo/r2_a07_memoria_larga/experimento.py` (unos 11 s).
Archivos: `PREREGISTRO.md`, `experimento.py`, `consola.txt`, `salida_experimento.txt`, `resultados.json`, `P_V1sem.npy`.
