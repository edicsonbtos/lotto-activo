# r2_a02_pares_no_adyacentes — ¿evita el operador pares NO adyacentes o la misma posición relativa?

Base: ag12 V1 (`ag12_transiciones/P_V1.npy`, cross-fit). Solo desarrollo [2000, 9357), n = 7357. Prerregistro: `PREREGISTRO.md`.
Reproducir (≈ 11 s, < 300 MB):
`cd C:\Users\edics\Downloads\lotto-activo\lotto-activo-motor; $env:PYTHONIOENCODING='utf-8'; python motor_nuevo\r2_a02_pares_no_adyacentes\experimento.py`
(además: `diagnostico.py` descriptivo, `exploratoria_x4.py` exploratoria). Salidas: `consola.txt`, `resultados.json`,
`salida_diagnostico.txt`, `salida_x4.txt`, `resultados_x4.json`.

## Barrido (24 pruebas, O/E frente a ag12 V1; BH q=0,05 en mitad 1, confirmación en mitad 2)
Sobrevive **solo una**: **D@1-1** = "i salió ANTES que s1, no adyacente (desfase >= 3), en el día de ayer"
→ mitad 1 O/E 0,676 (z −3,55), mitad 2 0,793 (z −2,55), total 0,741 (z −4,28).
Otras celdas llamativas que NO pasaron el BH en la mitad 1:
- C@1-1 (s1 antes que i, desfase >= 3, ayer): total O/E 0,763 (z −3,82); mitad 1 z −2,02 (no sobrevive BH).
- D@2-7: O/E 1,115 (z +4,54), es decir, el candidato SALE MÁS de lo que dice ag12 (mitad 1 z +2,00, no sobrevive).
- A@1-1 (s2→i ayer): O/E 1,37 (z +2,62). F@1-1: 0,63 (z −2,08).
- **Misma posición relativa (E, mismas horas): nada** (O/E 0,87-1,07, |z| < 1,3; muy pocos casos). La evitación del
  par consecutivo no depende de que sea a las mismas horas.
- Pares con un sorteo en medio (A, B) en ventanas largas: nada firme (|z| < 2 salvo A@1-1, que va al revés).
- Ventanas 8-30 y 31-90 de todo: O/E ≈ 1,00. **No hay "ventanas largas" para pares no adyacentes.**

Diagnóstico (`diagnostico.py`): la pareja no ordenada del mismo día de ayer (C|D@1-1) da O/E 0,753 (z −5,75), estable
(mitad 1 0,739, mitad 2 0,765). El 96 % de esos casos ya los marca la variable 17 de ag02 (`mismo_dia_que_s1_ant`),
pero con un peso plano para cualquier antigüedad (−0,068); la evitación real está concentrada en AYER, y a 2-7 días
el efecto se invierte (D@2-7 O/E 1,13). Es un refinamiento de algo que ag12 ya mide a medias, no un mecanismo nuevo.

## Modelos (Δ mbits FRENTE A ag12 V1)
| Variante | Δ mbits [IC95] | mitad 1 | mitad 2 | forward (b1-4) | Top-15 (ag12 54,78 %) | Top-5 (22,13 %) | Barra |
|---|---|---|---|---|---|---|---|
| V1 prim.: corrección D@1-1 sobre ag12 | **+1,59 [+0,46 ; +2,70]** | +1,88 | +1,29 [−0,53 ; +2,96] | +1,28 [+0,13 ; +2,41] | 54,76 % | 22,26 % | **NO** (< +3) |
| V2: ag12 33 var + D@1-1, reajuste conjunto | +2,02 [+0,83 ; +3,15] | +2,09 | +1,94 | +1,59 [+0,41 ; +2,79] (vs forward ag12) | 54,64 % | 22,22 % | NO |
| V3 explor.: las 24 variables | +3,08 [+0,27 ; +5,86] | +2,89 [−0,59 ; +6,21] | +3,27 [−0,96 ; +7,31] | +2,05 [−1,31 ; +5,49] | 55,43 % | 22,58 % | formal sí, forward IC cruza 0; exploratoria |
| X4 explor. (4.ª, post hoc): C@1, D@1, D@2-7 | +4,48 [+2,34 ; +6,53] | +3,22 | +5,74 | +4,15 [+2,22 ; +6,09] | 55,27 % | 22,33 % | formal sí, pero elegida mirando → exploratoria |

Pesos V1 (5 bloques): D@1-1 −0,331 [−0,377 ; −0,284]. X4: C@1 −0,296, D@1 −0,334, D@2-7 +0,182.

## Veredicto honesto
**NO pasa la barra prerregistrada.** Lo único que sobrevive al barrido estricto (i antes que s1 en el mismo día de ayer,
no adyacente) es real y estable (O/E 0,74, las dos mitades), pero sobre ag12 aporta +1,6 mbits (+2,0 reajustando todo)
y no mueve el Top-15 (54,76 % frente a 54,78 %). La misma posición relativa y los pares con un sorteo en medio no dan nada
sobre ag12; las ventanas largas tampoco.
La combinación post hoc X4 (+4,5 mbits, forward +4,1, Top-15 55,27 %) es la mejor cifra, pero se eligió DESPUÉS de ver
los datos (4.ª variante) y contiene un término con signo inesperado (D@2-7 favorece), así que es exploratoria: solo podría
confirmarse con sorteos futuros. Aun si fuera real, son +0,5 pp de Top-15: lejos del 60 %.
Sin tocar: repo principal, producción, filas >= 9357, sellado. Sin commit.
