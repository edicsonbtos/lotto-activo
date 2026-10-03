# PRERREGISTRO — Barrido 2: familia de ~330 hipótesis NUEVAS (2026-10-02)

Pedido del usuario: otra familia de ~300 ideas que no estén en la Operación Turing (308 hipótesis, 0 señales, mejor q_BH 0,523).
Se definen aquí, ANTES de correr nada. No se agrega, quita ni ajusta ninguna después de ver resultados.

## Método (idéntico al de Turing, para que sean comparables)
- Base congelada: `investigacion/2026-09-18/a_estadistica/baseline_dev_full.npz` (walk-forward de ensamble_v2, desarrollo [2000, 9357), 7357 sorteos).
- Cada hipótesis = feature causal (log-rate empírico con cuentas estrictas < t, suavizado a ∈ {1, 8}) añadida al logit con UN peso escalar por máxima verosimilitud.
- Métrica: mbits. p-valor: bootstrap por día (2000), una cola. Corrección Benjamini-Hochberg sobre toda la familia.
- **Compuerta (única)**: aporte OOF > 0 en 4/4 cuartos Y q_BH < 0,05 Y mbits > 0. Semilla 20261002.
- Solo desarrollo. No toca el tramo ≥ 9357, ni producción, ni modelos.
- Un rasgo de contexto (igual para los 38 animales) no aporta nada por sí solo; por eso las hipótesis son
  (A) rasgos del animal solos y (B) pares rasgo-del-animal × contexto.

## Rasgos del animal (A, 17)
cuadrante, paridad, color de ruleta (rojo/negro/verde), mod3, mod4, docena, mismo cuadrante / color / paridad que el último ganador,
lado respecto al último ganador (mayor/menor/igual), distancia circular al último ganador (6 bins),
distancia circular al ganador de la misma hora de ayer (7 bins), hueco en DÍAS desde su última salida a esta misma hora,
conteo en últimos 7 y 30 días calendario, `eq_fecha` (número == día del mes / día+1 / día−1 / hora 12 h / ninguno), y `gap_bin` (de Turing, solo como pareja).

## Contexto (C, 10)
hora (12), día de la semana, trimestre, tramo del mes, color / cuadrante / paridad del último ganador,
dirección del último paso, largo de la racha de color, hueco previo del último ganador antes de ganar.

## Catálogo
- Singles: 16 rasgos de A (sin gap_bin) × 2 suavizados.
- Pares: cada rasgo A (17) × cada contexto C (10), sin los 3 duplicados triviales, × 2 suavizados.
- El número exacto lo imprime el script y queda en el informe.

## Control positivo (declarado de antemano)
`eq_fecha` es la señal hallada el 2026-10-01 (el operador esquiva el número de fecha/hora, O/E 0,5-0,7). Si el barrido NO la recupera, tiene poca potencia
y un "0 señales" vale menos. Si la recupera, es validación, no descubrimiento nuevo.

## Qué pasa con los sobrevivientes
Cada sobreviviente (si hay, aparte del control positivo) se prueba ciego en [9357, 12511) por DOS agentes independientes, sin comunicación,
con un pre-registro adicional por hipótesis. Si no sobrevive ninguna, la familia queda cerrada.
