# ag02_residuo_boost: corrección residual sobre el ensamble_v2

**Veredicto: V1 (la variante primaria, pre-registrada) PASA la barra de desarrollo, con +12,15 mbits.**
Es un candidato para la prueba sellada, **no** una mejora confirmada. Choca con lo que se sabía
(Markov 38×38 y Turing dieron ruido), así que conviene que el revisor de sesgo lo audite antes de congelarlo.

## Qué se probó
`logit_final = log P_ens + x·w`, ajustado por máxima verosimilitud condicional (softmax de los 38 por
sorteo). El ensamble entra con peso fijo 1, sin recalibrar. x son 27 variables binarias sobre el
**contenido** de los sorteos recientes, que el ensamble no ve (este solo ve huecos, recencia y hora):
- tablero numérico respecto de s1, s2 y s3 (los últimos ganadores): vecino ±1, ±2-3, misma columna,
  misma fila, mismo último dígito, misma decena;
- pares: el sucesor y el predecesor de s1 la última vez que salió s1, el sucesor del par (s2, s1),
  y haber salido en la misma jornada que la ocurrencia anterior de s1;
- ayer: el último sorteo de ayer, la misma hora o la hora ±1 de ayer, la posición en el orden de ayer,
  y lo que siguió a s1 ayer.

Ajuste: cross-fitting en 5 bloques contiguos de jornadas (cada fila se predice con w ajustado sin su
bloque). Prerregistro en `PREREGISTRO.md`, escrito antes de correr. La única desviación es que las
variables son 27 y no 28, un error de conteo; la lista no cambió.

## Resultados (salida exacta de `experimento.py`, desarrollo n=7357)
| variante | Δ mbits [IC95] | mitad 1 | mitad 2 | Top-5 cand / ens | Δ ret Top-5 escalonado/ficha | pasa |
|---|---|---|---|---|---|---|
| **V1 lineal λ=30 (primaria)** | **+12.15 [+7.64, +16.75]** | +12.56 [+6.16, +19.18] | +11.74 [+5.17, +17.98] | 21.56% / 20.25% | +0.075 [+0.029, +0.120] | **sí** |
| V1 forward-chaining (informativa; bloque 0 = ensamble) | +9.03 [+5.21, +12.98] | +7.39 | +10.67 | 20.99% | +0.042 [+0.002, +0.081] | sí |
| V1 λ=10 (sensibilidad) | +12.05 [+7.22, +16.98] | +12.06 | +12.04 | 21.67% | +0.079 | sí |
| V1 λ=100 (sensibilidad) | +11.64 [+7.82, +15.48] | +12.32 | +10.96 | 21.44% | +0.067 | sí |
| V2 LightGBM residual (secundaria) | +11.51 [+8.41, +14.72] | +11.98 | +11.04 | 21.50% | +0.081 [+0.044, +0.120] | sí |

mbits: V1 +132.2 frente a +120.1 del ensamble. Top-3 13.59% frente a 12.89%. Top-15 54.11% frente a 53.07%.
Top-5 escalonado por ficha: +31.81% frente a +24.27%.

Variantes: 2 pre-registradas (V1 y V2) y 2 de sensibilidad de λ. Ninguna se eligió mirando el
resultado: el candidato es V1 con λ=30, fijado antes de correr. Todas dan +11,5 a +12,2 mbits.

## Controles
- **Estabilidad**: el signo de w es el mismo en los 5 bloques del cross-fit para las variables grandes:
  sucesor_s1 −0.33 [−0.36, −0.30], ayer_siguio_a_s1 −0.27, s1_digito −0.20, predecesor_s1 −0.19,
  s1_vec1 −0.18, sucesor_par −0.19 y s1_col −0.14.
- **Placebo** (`diagnostico_placebo.py`): O/E frente al ensamble de seq[p+d], con p la ocurrencia
  anterior del ancla. Con ancla s1, d=+1 da 0.583 (z −5.83) y d=−1 da 0.778 (z −3.15); d=±3 queda
  cerca de 1. Con ancla s2, s3 o seq[t−6] sale plano (|z| < 2). No es un artefacto de recencia: es
  adyacencia con el último ganador. Parece que el operador evita repetir la transición s1→i que ya
  ocurrió, y evita los animales "parecidos" al último en el tablero (vecino, mismo dígito, misma columna).
- **Ablación** (`salida_ablacion.txt`, informativa): tablero solo +6.15 [+3.00, +9.42]; pares/sucesor
  solo +5.45 [+2.95, +7.81]; ayer solo +1.48 [+0.23, +2.71]. Los dos primeros bloques aportan por separado.
- **Fuga**: `prueba_fuga.py` corre `lotto_eval.prueba_fuga` sobre `prefijo(2600)`, desde 2000, y da
  (True, None, 0.0). El ensamble_v2 que recalcula `modelo.py` coincide con la caché (máx |dif| 2.8e-17).

## Archivos
- `rasgos.py`: construye las variables (la fila t usa solo seq[:t]).
- `experimento.py`: cross-fit de V1, sus sensibilidades, el forward-chaining y V2. Genera
  `resultados.json` y `salida_experimento.txt`.
- `congelar.py`: ajusta V1 λ=30 con todo el desarrollo [2000, 9357) y escribe `parametros.json`.
- `modelo.py`: `Modelo` = ensamble_v2 walk-forward (del repo) más la corrección congelada. Admite
  jornadas de 11 o 12 sorteos.

## Reproducir
```
cd C:\Users\edics\Downloads\lotto-activo\lotto-activo-motor
$env:PYTHONIOENCODING="utf-8"; python motor_nuevo/ag02_residuo_boost/experimento.py; python motor_nuevo/ag02_residuo_boost/congelar.py; python motor_nuevo/ag02_residuo_boost/prueba_fuga.py
```
El experimento tarda unos 25 s y usa menos de 300 MB.

## Advertencias
El efecto es grande para un proyecto que tiene 308 hipótesis sin señal. Los controles de arriba no
encuentran fuga, pero:
1. las variables de tablero suponen que la numeración 1-36 es la del tablero real;
2. el tramo sellado es de otra era (11 sorteos/día), y si la conducta del operador cambió, el efecto puede no estar;
3. el cross-fit usa bloques futuros para predecir pasados; el forward-chaining, más estricto, da +9.03.
