# ag10_comodin: composición del día y déjà-vu de transiciones sobre el ensamble_v2

**Veredicto: V1 (primaria, pre-registrada) PASA la barra de desarrollo con +8,54 mbits [+5,03, +12,17].
Pero la parte nueva de la hipótesis (la composición del día como conjunto) NO aporta. La ganancia viene
casi entera de contar las transiciones s1→i de los últimos 30 días, y eso extiende el hallazgo de ag02
(sucesor de s1).** Sobre ag02 suma +5,36 mbits [+2,27, +8,62], pero en la mitad 2 el IC cruza 0.

## Por qué la idea era nueva
Todo lo cerrado (ensamble, Turing 308, hilo 9, ag01-ag09) usa variables por animal (hueco, conteos,
hora) o relativas a los últimos 1-3 ganadores. Nadie había probado el día como **conjunto**: si i y los
animales ya salidos hoy salieron juntos en días recientes, cuántos animales de ayer ya se reciclaron hoy,
el orden de precedencia dentro del día en los últimos 30 días, ni las transiciones **acumuladas** de 30
días (ag02 solo mira la última ocurrencia de s1).

## Qué se probó
`logit = log P_ens + ((x − mu)/sd)·w`, logit condicional (softmax de 38), L2 λ = 30, 9 variables
(ver `PREREGISTRO.md` y `rasgos.py`): ayer_cooc, sem_cooc, mes_cooc, trans1_30, trans2_30, orden_30 y los
controles ayer_x_S, nsem_x_S y nmes_x_S. Cross-fitting en 5 bloques contiguos de jornadas.

## Resultados (salida exacta de `experimento.py` y `ablacion.py`, desarrollo n=7357)
| variante | Δ mbits [IC95] | mitad 1 | mitad 2 | Top-5 cand / ens | Δ ret. Top-5 esc./ficha | pasa |
|---|---|---|---|---|---|---|
| **V1 cross-fit (primaria)** | **+8.54 [+5.03, +12.17]** | +10.22 [+5.41, +14.60] | +6.87 [+1.61, +12.16] | 20.99% / 20.25% | +0.05 [+0.01, +0.09] | **sí** |
| V1 forward-chaining (inform.) | +6.05 [+2.46, +10.00] | +5.75 | +6.35 | 20.93% | +0.04 [+0.01, +0.08] | sí |
| abl.: solo transiciones (f4, f5) | +7.99 [+4.64, +11.42] | +9.50 | +6.48 | 21.25% | +0.06 [+0.03, +0.09] | sí |
| abl.: solo composición del día (f1-f3, f6-f9) | +1.45 [−0.19, +3.19] | +1.96 | +0.93 | 20.32% | +0.00 | no |
| abl.: solo ayer (f1, f7) | +0.43 [−0.58, +1.42] | −0.10 | +0.96 | 20.13% | −0.01 | no |
| abl.: co-ocurrencia sem./mes + orden | +1.16 [−0.36, +2.68] | +2.25 | +0.07 | 20.47% | +0.01 | no |
| ag02 re-ajustado aquí (inform.) | +11.68 [+6.55, +16.90] | +11.02 | +12.35 | 21.64% | +0.08 | sí |
| ag02 + ag10 (inform.) | +17.04 [+11.02, +23.06] | +17.97 | +16.11 | 22.18% | +0.11 [+0.06, +0.17] | sí |
| **incremento ag10 sobre ag02** | +5.36 [+2.27, +8.62] | +6.95 [+2.77, +10.89] | +3.77 [−0.88, +8.57] | — | +0.04 [+0.00, +0.07] | — |

V1: mbits +128,6 frente a +120,1 del ensamble. Top-3 13,46 % frente a 12,89 %. Top-15 53,57 % frente a 53,07 %.
Top-5 escalonado por ficha: +29,16 % frente a +24,27 %.

Pesos por bloque (unidad cruda) estables en los 5 bloques: trans1_30 −0,217 a −0,251 (dominante: cada vez
que i siguió a s1 en los últimos 30 días baja su probabilidad un ~20 %), ayer_cooc −0,055 a −0,086,
sem_cooc −0,010 a −0,019. Congelado con todo el desarrollo: trans1_30 −0,2295.

Variantes: 1 pre-registrada que decide (V1). Forward-chaining, la ablación (añadida después de ver V1)
y el contraste con ag02 son informativos. Ninguno cambió el candidato.

## Lectura honesta
1. La hipótesis de la composición del día queda **falsada**: sola da +1,45 mbits con IC que cruza 0.
2. Lo que pasa la barra es "el operador evita repetir la transición s1→i", medido con memoria de 30 días.
   Es el mismo mecanismo que encontró ag02 (su `sucesor_s1`). Aquí se ve que la evitación no mira solo la
   última vez: contar todas las veces en 30 días añade +5,4 mbits sobre ag02, sin replicar con claridad en la
   mitad 2.
3. Si se congela un candidato para la prueba sellada, lo razonable es **ag02 + trans1_30** (una sola
   variable más), no V1 completo. Eso sería una variante nueva y habría que medirla y declararla como tal.
   Aquí no se hizo.
4. Choca con Markov 38×38 (ruido). Es compatible: la matriz completa diluye un efecto que es "evitar
   cualquier transición ya vista", de 1 parámetro.

## Controles
- Fuga: `prueba_fuga.py` corre `lotto_eval.prueba_fuga` sobre `prefijo(2600)` desde 2000: `(True, None, 0.0)`.
  Las variables, calculadas sobre un futuro barajado, coinciden en todas las filas anteriores al corte.
- Solo se usan filas < 9357 (`datos().prefijo(CORTE)`), sin RD ni el tramo sellado.

## Archivos
`rasgos.py` (variables), `experimento.py` (V1, forward, contraste ag02; escribe `resultados.json`,
`P_V1.npy`), `ablacion.py`, `congelar.py` (escribe `parametros.json`), `modelo.py` (ensamble_v2 del repo +
corrección congelada; jornadas de 11 o 12 sorteos), `prueba_fuga.py`; salidas `salida_*.txt`.

## Reproducir (~15 s el experimento y la ablación; la prueba de fuga ~1-2 min; < 400 MB)
```
cd C:\Users\edics\Downloads\lotto-activo\lotto-activo-motor
$env:PYTHONIOENCODING="utf-8"; python motor_nuevo/ag10_comodin/experimento.py; python motor_nuevo/ag10_comodin/ablacion.py; python motor_nuevo/ag10_comodin/congelar.py; python motor_nuevo/ag10_comodin/prueba_fuga.py
```
