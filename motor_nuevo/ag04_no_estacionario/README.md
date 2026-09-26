# ag04_no_estacionario: ¿un ensamble que se adapta más rápido supera al ensamble_v2?

**Veredicto: NO. Ninguna de las 3 variantes pre-registradas pasa la barra.** Las ganancias son de +0,2 a +0,6 mbits
(la barra pide +3), con IC95 que cruzan 0. La hipótesis de una deriva aprovechable en la política del
operador queda descartada: el ensamble_v2 (reajuste cada 250 sorteos, olvido tau=3000) ya se adapta lo suficiente.

## Qué se probó (prerregistro en `PREREGISTRO.md`, escrito antes de correr; sin desviaciones)
Insumo: predicciones walk-forward de intradia_v2, secuencia_v3 y haz_v1 sobre `prefijo(9357)` desde la fila 1000
(`cache_sub.py`). Control: con ellas se reconstruye el ensamble_v2, y coincide con la caché del arnés (máx |dif| 6,0e-6).
- **V1 (primaria), filtro de Kalman sobre los 3 pesos log-lineales**: paseo aleatorio N(0, q·I) y actualización de Laplace
  sorteo a sorteo. q en {1e-7, 1e-6, 1e-5, 1e-4}, elegido por cross-fitting en 5 bloques contiguos de jornadas.
- **V2, reajuste con olvido corto**: el ajuste del ensamble, reajustado cada 50 sorteos, con tau en {300, 1000, 3000}
  elegido por el mismo cross-fitting.
- **V3, submodelos rápidos**: se añaden intradia_v2(tau=400, ventana=1500) y haz_v1(vida media 800, ventana 2000, cada 250)
  y se usa el procedimiento exacto del ensamble_v2 con 5 componentes.

## Resultados (salida exacta de `experimento.py`, desarrollo n=7357, ensamble +120,1 mbits)
| variante | Δ mbits [IC95] | mitad 1 | mitad 2 | Top-5 cand / ens | Δ ret Top-5/ficha | pasa |
|---|---|---|---|---|---|---|
| **V1 Kalman (primaria)** | **+0.50 [−0.65, +1.73]** | +0.37 [−0.89, +1.57] | +0.64 [−1.39, +2.64] | 20.43% / 20.25% | +0.00 [−0.01, +0.01] | no |
| V2 olvido corto | +0.58 [−0.52, +1.71] | +0.28 [−1.20, +1.74] | +0.89 [−0.76, +2.53] | 20.61% / 20.25% | +0.01 [−0.01, +0.02] | no |
| V3 submodelos rápidos | +0.15 [−0.52, +0.85] | −0.13 [−1.07, +0.80] | +0.44 [−0.53, +1.45] | 20.31% / 20.25% | −0.00 [−0.02, +0.01] | no |

- En V1, el q elegido por bloque fue 1e-5, 1e-5, 1e-5, 1e-6 y 1e-5. Con cada q fijo, en todo el tramo: 1e-7 da +120.31,
  1e-6 da +120.59, 1e-5 da +120.82 y 1e-4 da +119.51 mbits. Adaptar más rápido (1e-4) empeora.
- En V2, el tau elegido fue 1000, 300, 1000, 1000 y 1000. Con cada tau fijo: 300 da +120.70, 1000 da +120.79 y 3000 da +120.42.
- En V3, los pesos finales fueron [0.34, 0.642, −0.027, 0.224, 0.055]. El intradia rápido recibe algo de peso, pero no añade verosimilitud.
- Por trimestre, la Δ de V1 va de −1,3 a +2,9 mbits, sin tendencia.
- Los pesos del Kalman se mueven poco. intradia está entre 0,35 y 0,68, secuencia entre 0,42 y 0,74, y haz cerca de 0.
  La fluctuación es la esperable por ruido y no hay ningún cambio de régimen visible.

Se probaron 3 variantes pre-registradas y no hubo iteración. El resultado no es exploratorio.

## Modelo congelado (por si se quiere, aunque no es candidato)
`modelo.py` es V1 con q=1e-5 y s0=0,1 (`parametros.json`). `prueba_fuga.py` da `(True, None, 0.0)` sobre `prefijo(2600)` desde 2000.
Sobre todo el desarrollo, con q elegido in-sample, da +0.76 [−0.49, +2.03] (`salida_modelo_dev.txt`). No depende del número
de sorteos por jornada.

## Reproducir
```
cd motor_nuevo/ag04_no_estacionario
set PYTHONIOENCODING=utf-8
python cache_sub.py base
python cache_sub.py rapidos
python experimento.py
python prueba_fuga.py
```
Tarda unos 3 min en total y usa 1 hilo. El resultado es determinista.
