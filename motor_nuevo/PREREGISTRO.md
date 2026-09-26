# Prerregistro: búsqueda de un motor nuevo (rama `motor-nuevo`, 2026-09-25)

Este archivo se escribe y se commitea **antes** de que ningún agente empiece a buscar y
**antes** de bajar los datos del tramo sellado. El hash del commit fija las reglas.

## Qué se busca
Un motor (un `Modelo` con la interfaz de `herramientas/lotto_eval.py`) que prediga Lotto Activo
mejor que el `ensamble_v2` en producción. El motor de producción NO se toca: todo vive en la
rama `motor-nuevo`, carpeta `motor_nuevo/`.

## Tramos de datos
| Tramo | Rango | Uso |
|---|---|---|
| Desarrollo | `historial.txt` filas [2000, 9357) | los agentes buscan aquí (vía `motor_nuevo/arnes.py`) |
| Prueba vieja | `historial.txt` filas >= 9357 | **PROHIBIDO**: ya se miró 5 veces |
| **Sellado** | Lotto Activo **antes del 2023-09-04** (loteriadehoy, desde 2020-01-01) | **una sola mirada**, al final, con los candidatos congelados |

El tramo sellado **no existe en disco** cuando los agentes trabajan: se descarga solo después de
congelar los candidatos (commit con sus pesos). Ningún modelo del proyecto lo ha visto nunca.
Sondeo previo (solo conteo de filas, sin mirar animales ni hacer ningún cálculo):
semanas 2020-01-06, 2022-01-03 y 2023-06-05 existen, con 70-77 sorteos por semana (11 por día).

## Barra de desarrollo (para llegar a candidato)
Con `arnes.evaluar(P_cand)` en desarrollo:
- Δmbits frente al ensamble >= +3,0 y IC95 (bootstrap por jornadas) con límite inferior > 0;
- Δmbits > 0 en las dos mitades del tramo;
- parámetros ajustados sin usar la fila predicha (forward-chaining o cross-fitting por bloques de jornada);
- el candidato pasa `lotto_eval.prueba_fuga` y lo audita el revisor de sesgo.

## Prueba final (una sola vez)
- Como máximo **3 candidatos** congelados (código y parámetros fijados solo con desarrollo).
- En el tramo sellado se corren el candidato y el `ensamble_v2` (los pesos de producción, sin reajustar)
  walk-forward, con los primeros 2000 sorteos sellados como calentamiento de ambos.
- **Métrica primaria:** Δmbits del candidato frente al ensamble. **PASA** si el IC95 de bootstrap
  por jornadas, corregido por Bonferroni (IC 1 − 0,05/k, con k = nº de candidatos), queda entero por encima de 0.
- **Secundaria (informativa):** Δ retorno por ficha del Top-5 escalonado 2-2-2-1-1, Top-3 y Top-15.
- Si ninguno pasa, se informa como **no hay motor mejor** y producción sigue igual.
- Aunque uno pase, para llevarlo a producción hace falta el OK del usuario y después la confirmación en el marcador en vivo.

## Advertencia de era
El tramo sellado es de otra época (11 sorteos por día y quizá otra política del operador).
Afecta por igual al candidato y al ensamble, y la comparación es relativa. Si el ensamble mismo
pierde su señal ahí, se reporta.
