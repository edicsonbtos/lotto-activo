# r2_a05_anti_patron_numerico: NO PASA (ángulo cerrado)

Pregunta: ¿el operador evita patrones en los NÚMEROS (1..36) que ag02/ag12 no miden? Por ejemplo, repetir el salto
numérico (i − s1), alargar rachas crecientes o decrecientes, repetir la misma terminación que s1 y s2, repetir
terminaciones en el mismo día, la paridad o el color de ruleta de s1 y s2, o formar el espejo v_i + v_s1 = 37.
Base: ag12 V1 (`ag12_transiciones/P_V1.npy`, cross-fit). Solo desarrollo [2000, 9357), n = 7357. No se tocaron las filas
>= 9357 ni `sellado/sellado_la.txt`. El prerregistro (`PREREGISTRO.md`) se escribió antes de correr, con una sola corrida
y 2 variantes (VA y VB).

Reproducir (unos 5 s, < 300 MB, un hilo), en PowerShell desde la raíz del worktree lotto-activo-motor:
`$env:PYTHONIOENCODING='utf-8'; python motor_nuevo/r2_a05_anti_patron_numerico/experimento.py`
Salidas: `consola.txt` y `resultados.json` (barrido completo, pesos y métricas).

Prueba de fuga: al barajar seq[6000:], las filas < 6000 no cambian (diferencia máxima 0,0). Como control, las filas
posteriores sí cambian (6,28).

## Etapa 1: barrido de 11 variables frente a ag12 V1 (BH q = 0,05 en la mitad 1, confirmación en la mitad 2)
| Variable | mitad 1 O/E (z) | p m1 | BH | mitad 2 O/E (z) | total O/E (z) | obs/esp total |
|---|---|---|---|---|---|---|
| prog_arit (mismo salto con signo que s2→s1) | 1,192 (+1,02) | 0,308 | no | 0,858 (−0,91) | 1,024 (+0,20) | 69 / 67,4 |
| mono3 (racha creciente o decreciente de 3) | 0,980 (−0,78) | 0,433 | no | 0,969 (−1,23) | 0,974 (−1,42) | 1546 / 1586,7 |
| mono4 (racha de 4) | 1,024 (+0,39) | 0,696 | no | 0,982 (−0,29) | 1,004 (+0,08) | 310 / 308,9 |
| dif_hoy (mismo salto con signo, hoy) | 0,982 (−0,27) | 0,789 | no | 0,980 (−0,31) | 0,981 (−0,41) | — |
| difabs_hoy (mismo salto absoluto, hoy) | 0,950 (−1,05) | 0,295 | no | 0,972 (−0,61) | 0,962 (−1,15) | — |
| dif_30d_z (salto repetido en 1-30 jornadas, excedente z) | (−1,92) | 0,054 | no | (+0,46) | (−0,93) | — |
| term_s1s2 (misma terminación que s1 y s2) | 0,336 (−3,42) | 0,0006 | **SÍ** | 0,768 (−0,86) | 0,554 (−2,68) | **10 / 18,1** |
| term_hoy (terminaciones repetidas hoy) | 1,037 (+1,42) | 0,156 | no | 0,960 (−1,65) | 0,996 (−0,22) | — |
| paridad3 (misma paridad que s1 y s2) | 0,989 (−0,34) | 0,732 | no | 0,993 (−0,22) | 0,991 (−0,40) | 1166 / 1176,3 |
| color3 (mismo color de ruleta que s1 y s2) | 1,048 (+1,50) | 0,132 | no | 1,059 (+1,79) | 1,054 (+2,34) | 1293 / 1227,1 |
| espejo (v_i + v_s1 = 37) | 0,846 (−1,65) | 0,098 | no | 1,017 (+0,15) | 0,931 (−0,93) | 161 / 172,9 |

Solo term_s1s2 sobrevive el BH en la mitad 1, y **no se confirma en la mitad 2** (z −0,86, p unilateral 0,19). Además
es irrelevante en la práctica: afecta a 0,14 candidatos por sorteo y en todo el desarrollo hay 10 casos observados
contra 18,1 esperados. Aunque fuera real, movería menos de 1 mbit. **VA queda vacía (= P_V1, Δ = 0).**

color3 va en la dirección contraria (sale algo MÁS de lo esperado: total z +2,34), pero no pasa el BH en la mitad 1
(p 0,13). Con 12 pruebas y z de 2,3 es lo esperable por azar (ver regla 6 del protocolo).

## Etapa 2: modelos (Δ mbits FRENTE A ag12 V1, λ = 30, los mismos 5 bloques de jornada)
| Variante | Δ mbits [IC95] | mitad 1 | mitad 2 | forward (bloques 1-4) | Top-5 (V1 22,13 %) | Top-15 (V1 54,78 %) | Barra |
|---|---|---|---|---|---|---|---|
| **VA primaria** (seleccionadas) | 0 (vacía: ninguna confirmada) | — | — | — | 22,13 % | 54,78 % | **NO** |
| VB (las 11), cross-fit | **−0,83 [−2,38 ; +0,70]** | +0,51 [−1,43 ; +2,50] | −2,17 [−4,57 ; +0,23] | −1,24 [−3,38 ; +0,96] | 22,26 % | 55,09 % | NO |
| VB forward (bloque 0 = V1) | −1,00 [−2,75 ; +0,73] | −0,03 | −1,98 | — | 22,03 % | 55,09 % | NO |

Top-5 escalonado por ficha (VB cross-fit): +35,84 % contra +34,92 %, con Δ +0,01 [−0,01 ; +0,03]. El +0,3 pp de Top-15 de VB
no viene acompañado de mbits (Δ negativo, mitad 2 −2,2), así que es ruido.
Pesos de VB (media [mín, máx] en los 5 pliegues): term_s1s2 −0,145 [−0,164 ; −0,114], color3 +0,100, espejo −0,081,
difabs_hoy −0,079, mono3 −0,062, prog_arit +0,055, mono4 +0,052, y el resto con |w| < 0,03.

## Veredicto
**No hay anti-patrón numérico aprovechable más allá de lo que ya mide ag02.** El operador no evita repetir el salto
numérico, ni las rachas crecientes o decrecientes, ni las terminaciones del día, ni la paridad, el color o el espejo.
La única señal en la mitad 1 (triple terminación) tiene 10 casos y no se replica. Sumar las 11 variables empeora
(−0,83 mbits, −2,17 en la mitad 2). El ángulo queda cerrado y no hay candidato para el marcador en vivo.
