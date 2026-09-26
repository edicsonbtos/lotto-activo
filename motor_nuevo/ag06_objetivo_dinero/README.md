# ag06_objetivo_dinero: reordenador entrenado para el dinero del Top-5 escalonado

**Veredicto: la idea (optimizar directamente el dinero) FALLA. No mejora el dinero ni los mbits.**
La variante primaria V_dinero pierde −60,48 mbits y −0,03 de retorno por ficha frente al ensamble.
El control con log-loss, que usa las mismas variables, SÍ pasa la barra: +9,51 mbits y +0,06 por ficha.
Con estas variables, entrenar con log-verosimilitud da más dinero que entrenar para el dinero.

## Qué se probó
El puntaje de cada animal es s = log P_ens + x·w (el ensamble entra con peso fijo 1). x son 9 variables
binarias de contexto (`rasgos.py`):
- tablero respecto de s1: vecino ±1, mismo dígito y misma columna;
- sucesor y predecesor de s1 la vez anterior;
- último animal de ayer y el de ayer a la misma hora;
- hueco de 12-23 sorteos y de 24-35.

Las variables de tablero y de sucesor se inspiran en ag02. El ángulo de este agente es la pérdida,
no las variables.

- **V_dinero (primaria).** El rango suave del ganador es r = 1 + Σ sigmoid((s_j − s_w)/τ), con τ = 0,25.
  La ganancia suave es g(r) = sigmoid((3,5−r)/0,5) + sigmoid((5,5−r)/0,5), que aproxima las fichas 2-2-2-1-1.
  Se maximiza la media de g con L2 = 1e-3, por L-BFGS desde w = 0 y con gradiente analítico
  (verificado con check_grad). La probabilidad publicada es softmax(c·s), con c ajustado por log-loss;
  c no cambia el orden.
- **V_logloss (control).** Mismas variables, entropía cruzada y L2 = 1e-3.
- **V_dinero_tau0.1.** Sensibilidad pre-registrada de τ.
- **V4 (exploratoria, añadida después de ver el fallo).** Pérdida de dinero con τ = 0,05, arrancando
  desde la solución log-loss.

Ajuste de todas: cross-fitting en 5 bloques contiguos de jornadas (636 días; filas por bloque
1400/1397/1515/1524/1521). Todo es determinista.

## Resultados (salida exacta, desarrollo n=7357; `salida_experimento.txt`, `salida_exploratorio_v4.txt`)
| variante | Δ mbits [IC95] | mitad 1 | mitad 2 | Top-5 cand/ens | Top-5 escalonado/ficha cand vs ens | Δ ret T5 [IC95] | pasa |
|---|---|---|---|---|---|---|---|
| **V_dinero (primaria)** | **−60.48 [−69.44, −51.47]** | −49.06 | −71.90 | 19.48% / 20.25% | +20.80% vs +24.27% | −0.03 [−0.09, +0.03] | no |
| V_logloss (control) | +9.51 [+5.60, +13.28] | +10.39 | +8.64 | 21.34% / 20.25% | +30.13% vs +24.27% | +0.06 [+0.02, +0.10] | sí |
| V_dinero τ=0,1 | −39.31 [−47.19, −31.55] | −31.30 | −47.31 | 19.42% / 20.25% | +20.65% vs +24.27% | −0.04 [−0.09, +0.02] | no |
| V4 exploratoria | −19.31 [−26.23, −12.73] | −11.95 | −26.67 | 19.87% / 20.25% | +22.89% vs +24.27% | −0.01 [−0.07, +0.04] | no |

(Los valores exactos sin redondear de Δret están en `resultados.json`.)

**Diagnóstico** (`salida_diagnostico.txt`): V_dinero da MENOS retorno que el ensamble incluso dentro de
muestra, en los 5 bloques. En el bloque 0, por ejemplo, saca +0,245 frente a +0,246 dentro de muestra y
+0,117 frente a +0,229 fuera. No es solo sobreajuste: el sustituto suave no sigue al retorno real. La
suma de sigmoides sobre 37 animales sesga el rango, y el optimizador empuja a lo bruto la variable
hueco_12_23 (w ≈ +2,06). Además, la señal de dinero es escasa: solo acierta ~20 % de las filas, frente
a la log-loss, que usa todas. Afinar desde la solución log-loss (V4) también empeora el dinero fuera
de muestra. La log-loss, en cambio, sube el retorno dentro y fuera de muestra en todos los bloques.

**¿Mejora el dinero pero no los mbits?** No: V_dinero empeora las dos cosas.

## Variantes y honestidad
Hubo 3 variantes pre-registradas y 1 exploratoria posterior (4 en total). Por eso, cualquier conclusión
positiva sería exploratoria, y no la hay. El control V_logloss pasa la barra, pero no es la idea de
este agente: replica, con 9 variables, el hallazgo de ag02 (corrección lineal por log-loss). No se
propone como candidato propio.

## Archivos y fuga
- `rasgos.py`: las variables; la fila t usa solo seq[:t].
- `nucleo.py`: las pérdidas y los ajustes.
- `experimento.py`: el cross-fit de las 3 variantes. Guarda `resultados.json` y `P_*.npy` y congela
  `parametros.json` (V_dinero, ajustada con las filas [2000, 9357)).
- `modelo.py`: `Modelo` = ensamble_v2 walk-forward del repo más el reordenador congelado. Admite
  jornadas de 11 o 12 sorteos.
- `prueba_fuga.py`: `lotto_eval.prueba_fuga` sobre prefijo(2600), desde 2000, da **(True, None, 0.0)**.
  El ensamble recalculado coincide con la caché (máx |dif| 2.8e-17).

## Reproducir
```
cd C:\Users\edics\Downloads\lotto-activo\lotto-activo-motor\motor_nuevo\ag06_objetivo_dinero
$env:PYTHONIOENCODING='utf-8'; python experimento.py; python prueba_fuga.py; python diagnostico_sobreajuste.py; python exploratorio_v4.py
```
