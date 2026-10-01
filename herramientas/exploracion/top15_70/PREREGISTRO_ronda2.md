# PRE-REGISTRO — Ronda 2 (Top-15 hacia el 70 %)

Escrito el 2026-10-01, DESPUÉS de ver la ronda 1 (`salida.txt`) y ANTES de medir lo que sigue.
Script: `ronda2.py`. Mismos tramos que la ronda 1: dev-A [2000, 5688) para elegir y dev-B [5688, 9357)
para confirmar. No se usa el tramo de prueba.

## Lo que se sabe al escribir esto
- Ningún plan de la ronda 1 llega al 70 % por sorteo. El mejor, P6 (ag12 reajustado solo en dev-A + RD),
  da 56,9 % contra 55,6 % de B1, con +25,5 mbits. No pasa Bonferroni en el Top-15 (p = 0,03).
- Ni el ensamble ni P6 le dan jamás ≥ 70 % de masa a su Top-15 (máximos 67,3 % y 68,2 %). La información
  está en **descartar** a los animales recientes (los puestos 30-38 aciertan ~1 %), no en **concentrar**:
  el #1 acierta ~5 %.

## Familia A — "el operador evita lo que más se juega" (hipótesis nueva, nunca probada)
Si el operador eligiera resultados para pagar menos, evitaría los animales más jugados. Tres proxies que se
pueden calcular antes del sorteo:
- **A1**: el animal cuyo número es el **día del mes** (1..31).
- **A2**: el animal cuyo número es la **hora del sorteo** en reloj de 12 h (8, 9, 10, 11, 12, 1, …, 7).
- **A3**: **popularidad estable**. Si hay animales que el operador evita siempre, su frecuencia en dev-A
  anticipa la de dev-B. Medida: correlación de Spearman entre las 38 frecuencias de dev-A y las de dev-B,
  con p por permutación (20.000, semilla 20261001).
- A1 y A2: O/E (observado / esperado con la probabilidad del ensamble, no con 1/38, para no confundir con
  lo que el motor ya sabe), IC por bootstrap de jornadas.
- **Pasa** (cada una, Bonferroni 3): en dev-A O/E < 1, y en dev-B O/E < 1 con IC 99,17 % que no contiene
  1. A3 pasa si ρ > 0 con p < 0,0167.
- Si alguna pasa, se mide en dev-B cuánto mueve el Top-15 sacarla del Top-15 (relleno con el 16.º).

## Familia B — juntar lo mejor de la ronda 1 (descriptivo, contaminado)
- **B-comb** = media geométrica de P4 y P6, más la regla RD en el Top-15. Se reporta en dev-B, pero dev-B
  ya se vio en la ronda 1 para P4 y P6: **no da veredicto**. Solo sirve para decidir qué poner en sombra.

## Familia C — "acertar" el 70 % sin perder (medida ya pre-registrada en el plan 9, aquí solo se desglosa)
- Top-22 escalonado 3-3-3-2-2-1×17 = 30 fichas: si el ganador está en los puestos 6-22, se cobra 30 y se
  recupera lo apostado. Se reporta en dev-B cuántas veces no se pierde, cuántas se gana y el retorno.
  Es la misma medida del plan 9, desglosada; no es una mirada nueva.

## Lo que no hace
No toca producción, ni el historial, ni el tramo de prueba. Nada pasa a la jugada sin el marcador en vivo y
sin el OK del usuario.
