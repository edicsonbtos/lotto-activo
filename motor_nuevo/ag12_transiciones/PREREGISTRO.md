# ag12_transiciones — prerregistro (2026-09-25, antes del experimento principal)

## Origen (honesto)
No es una idea a ciegas: sale de lo que encontraron ag02 y ag10 (el operador evita repetir la transición
s1→i) y de `sondeo.py` (crudo, desarrollo, frente al ensamble):
- s1→i ya ocurrida (dentro del día) hace 1 día: O/E 0,40; hace 2-7: 0,60 (z −7,3); hace 8-30: 0,84 (z −5,2); hace 31-90: 1,00.
- i→s1 (inversa) hace 1 día: 0,56; hace 2-7: 0,78 (z −4,1); hace 8-30: 0,99.
- Saltos s2→i: débiles o nulos (no entran).
Es reutilización secuencial del desarrollo, así que el juez es el tramo SELLADO, no la barra de desarrollo.

## Hipótesis
El operador evita formar un par consecutivo (en cualquier orden) que ya salió en los últimos ~30 días,
con fuerza decreciente según la antigüedad.

## Modelo (fijado antes de correr)
logit = log P_ens + x·w, softmax por sorteo, L2 λ = 30 (el mismo valor fijo de ag02/ag10/hilo 9).
x = las 27 variables de ag02 (rasgos.py de ag02, sin cambios) + 6 variables nuevas, conteos log1p de:
 T1 s1→i hace 1 día · T2 s1→i hace 2-7 · T3 s1→i hace 8-30 · R1 i→s1 hace 1 · R2 i→s1 hace 2-7 · R3 i→s1 hace 8-30.
Solo transiciones dentro del día (s1 del mismo día que t; en el primer sorteo del día las 6 valen 0).
Días contados por jornada del calendario (índice de jornada), así que vale con 11 o 12 sorteos por día.

## Evaluación
Cross-fit en 5 bloques contiguos de jornada (primaria) y forward-chaining (informativa, la cifra honesta).
Se reportan Δmbits, Top-5, Top-15 y el retorno del Top-5 escalonado.
Variantes: V1 (primaria, 33 variables). Una sola sensibilidad: V0 = solo las 6 nuevas (para la ablación).

## Qué la falsa
Si V1 no supera a ag02 V1 en desarrollo (Δ(V1 − ag02) con IC95 > 0), las variables nuevas no aportan
y el candidato para el sellado sigue siendo ag02.

## Desviación 1 (después de ver V1 = +21,7): variante V2 exploratoria
Mismo modelo, pero las transiciones en 8 ventanas de días (1, 2, 3, 4-7, 8-14, 15-30, 31-45, 46-60) en los dos sentidos
(16 variables en vez de 6). Se reporta como EXPLORATORIA (2ª variante tras mirar). Solo pasa a candidato si supera a V1
con IC > 0 en desarrollo; si no, el candidato es V1.
