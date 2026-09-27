# r2_a01_forma_transicion: NO PASA (ángulo cerrado)

Pregunta: ¿la forma de ag12 V1 (6 ventanas en jornadas: s1->i y i->s1 hace 1, 2-7 y 8-30) pierde señal? Se probó la edad
en SORTEOS con decaimiento exponencial continuo (vida media elegida dentro de cada pliegue de entrenamiento, rejilla
6-192 sorteos), el número de repeticiones del par y la hora en que ocurrió. El prerregistro (`PREREGISTRO.md`) se
escribió antes de correr. Hubo 3 variantes y una sola corrida.

Modelo: se reajusta completo, con log P_ens como offset + las 33 variables de V1 + las nuevas, λ=30 y los mismos 5 bloques
de jornada de ag02/ag12. Así no se usa P_V1 como offset y no hay fuga por el cross-fit. Control: el mismo código
reproduce P_V1 con una diferencia máxima de 2,0e-13.
Datos: solo filas [2000, 9357). No se tocó el sellado ni las filas >= 9357.

## Resultados (Δ mbits frente a ag12 V1 = +141,78 mbits; n = 7357; IC95 por bootstrap de jornadas)
| Variante | Δ mbits [IC95] | mitad 1 | mitad 2 | Top-5 | Top-15 (V1 54,78 %) | Barra |
|---|---|---|---|---|---|---|
| **A primaria** (33 V1 + EF + ER, edad en sorteos) | **+0,41 [−0,56 ; +1,43]** | +0,39 | +0,43 | 22,24 % (V1 22,13) | 55,08 % | NO |
| A forward frente a P_V1 | −1,39 [−3,21 ; +0,47] | −2,29 | −0,50 | 22,09 % | 54,91 % | NO |
| A forward frente a V1 forward (misma base de entrenamiento) | +0,91 [−0,02 ; +1,79] | +1,03 | +0,78 | 22,09 % vs 22,02 % | 54,91 % vs 54,61 % | NO |
| B = A + repeticiones (N2) + misma hora (HM) | +0,34 [−0,67 ; +1,35] | +0,42 | +0,26 | 22,17 % | 55,23 % | NO |
| C = 27 ag02 + EF + ER (sin las ventanas) | −0,61 [−2,11 ; +0,94] | −0,32 | −0,90 | 22,02 % | 55,05 % | NO |

Top-5 escalonado por ficha, A: +35,18 % contra +34,92 % (Δ +0,00 [−0,01 ; +0,02]).

## Lectura
- Vidas medias elegidas: h_f = 96 sorteos (unas 8-9 jornadas) en 4 de 5 pliegues y 192 en 1; h_r = 96 o 192. Los pesos
  son estables (EF entre −0,34 y −0,46; ER entre −0,19 y −0,28). El mecanismo sigue ahí, pero las ventanas de V1 ya lo
  capturan casi entero.
- La forma continua **sustituye** a las ventanas sin ganar nada (C −0,6), y **sumarla** a las ventanas aporta +0,4, que es ruido.
  Medir la edad en sorteos en vez de jornadas no cambia nada visible.
- Repeticiones del par (N2): peso negativo pequeño (de −0,06 a −0,16). Un par repetido varias veces se evita apenas algo
  más, lo que confirma la dirección, pero el efecto es despreciable. Misma hora (HM): peso ≈ 0 (de −0,06 a +0,02). La hora
  a la que salió el par no importa.
- La diferencia de Top-15 (+0,3 pp en A, +0,45 pp en B) no viene acompañada de mbits y queda dentro del ruido.

**Veredicto:** la forma del mecanismo de pares está resuelta. Las 6 ventanas de ag12 V1 bastan. Ni el decaimiento continuo,
ni la edad en sorteos, ni las repeticiones, ni la hora suben nada. No hay candidato para el marcador en vivo.

Reproducir (PowerShell, desde la raíz del worktree lotto-activo-motor):
`$env:PYTHONIOENCODING='utf-8'; python motor_nuevo/r2_a01_forma_transicion/experimento.py` (unos 4 min, un hilo).
Archivos: `consola.txt`, `salida_experimento.txt`, `resultados.json` (con las h y los pesos por pliegue), `P_A.npy`.
