# ag07_mezcla_expertos: pesos del ensamble que dependen del contexto

**Veredicto: NO. La variante primaria (V1) no pasa la barra.** Gana +0,67 mbits, con un IC95 que cruza 0, y en la
segunda mitad pierde. La compuerta por contexto no aporta nada aprovechable. Los pesos óptimos de los expertos
casi no dependen de la hora del día, de las repeticiones del día ni de la dispersión de la distribución. Añadir un
experto de recencia tampoco suma.

## Qué se probó
Todo está fijado en `PREREGISTRO.md`, escrito antes de correr. No hubo desviaciones.
- **Expertos:** intradia_v2, secuencia_v3 y haz_v1 del repo, con las cachés walk-forward de ag04 (`cache_sub_*.npy`,
  filas [1000, 9357)). Se añade además un experto de **recencia**: una tasa de acierto por hueco desde la última
  salida, con Laplace y acumulada hacia delante.
- **Contexto:** 1, k/11 y (k/11)² (k = nº de sorteos ya celebrados hoy), min(repeticiones de hoy, 3)/3, y la
  dispersión log38 − H de la combinación igualitaria.
- **V1 (primaria):** log-lineal con pesos a_m + b_m·x (20 parámetros, L2 λ=5 y λ=20).
- **V2:** mezcla lineal con una compuerta softmax, es decir, una regresión multinomial pequeña.
- **V3:** V1 sin el experto de recencia, como ablación.
- **Ajuste:** cross-fitting en 5 bloques contiguos de jornadas del tramo [2000, 9357). Cada bloque se predice con
  parámetros ajustados sin él (las filas [1000, 2000) siempre entran en el ajuste). Nada se ajusta in-sample.

## Resultados (salida exacta de `experimento.py`, desarrollo n=7357)
| variante | Δ mbits [IC95] | mitad 1 | mitad 2 | Top-5 cand / ens | Δ ret Top-5/ficha | pasa |
|---|---|---|---|---|---|---|
| **V1 log-lineal + contexto (primaria)** | **+0.67 [−0.85, +2.18]** | +1.90 [−0.23, +3.99] | −0.57 [−3.17, +1.85] | 20.27% / 20.25% | +0.00 [−0.01, +0.02] | no |
| V2 MoE lineal | −3.32 [−5.54, −1.17] | +0.06 [−3.11, +3.00] | −6.70 [−9.95, −3.41] | 20.28% / 20.25% | −0.01 [−0.02, +0.01] | no |
| V3 sin recencia | −0.05 [−1.32, +1.20] | +1.13 [−0.37, +2.71] | −1.23 [−3.36, +0.78] | 20.10% / 20.25% | −0.01 [−0.02, +0.00] | no |

Valores exactos de V1 (`resultados.json`): Δ = 0.66599 [−0.85151, +2.18332]; mitad 1 = 1.90167; mitad 2 = −0.56937;
Δ retorno Top-5 = 0.00459; Top-5 = 0.20266 frente a 0.20253.

- **Coeficientes:** los términos de contexto b están en |b| ≤ 0,17, frente a pesos base de ~0,5-0,7. El único algo
  consistente es que, cuando el día ya tuvo repeticiones, secuencia_v3 baja (−0,1 a −0,17) y haz_v1 sube (+0,1).
  El efecto en verosimilitud es despreciable. La recencia recibe un peso de ≈ −0,05, así que no aporta.
- **La mezcla lineal (V2) es peor:** los expertos son afilados y complementarios, y el producto log-lineal les va mejor
  que el promedio.
- Se probaron 3 variantes pre-registradas y no hubo iteración, así que el resultado no es exploratorio.

## Modelo congelado (no es candidato)
`modelo.py` implementa V1 con los parámetros de `parametros.json`, ajustados con todas las filas [1000, 9357) por `congelar.py`.
Ejecuta los tres submodelos del repo más la recencia y sirve para días de 11 o de 12 sorteos, porque k sale de `dia`.
`prueba_fuga.py` da `(True, None, 0.0)` sobre `prefijo(2600)` desde 2000.

## Reproducir
```
cd motor_nuevo/ag07_mezcla_expertos
$env:PYTHONIOENCODING="utf-8"
python experimento.py     # ~1 min, determinista (las cachés vienen de ../ag04_no_estacionario/cache_sub.py base)
python congelar.py
python prueba_fuga.py
```
