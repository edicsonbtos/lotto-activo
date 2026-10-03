# PREREGISTRO ag04 — Relaciones numéricas/geométricas en la transición nocturna
(escrito antes de mirar el tramo 'prueba'; dev y 'cal' se exploran libremente)

## Hipótesis
El ganador del primer sorteo de hoy (D) guarda una relación estructurada con el origen O, más allá de lo que
ya da P_aj. Dos orígenes: (a) último sorteo de ayer (7 PM, hora 11; ayer = día calendario anterior; si ayer
no tiene 7 PM la fila se descarta), (b) primer sorteo de ayer.

## Codificación
val: "0"→0, "1".."36"→n, "00"→37 (círculo de 38). Dígitos solo para 0..36 (00 sin dígitos).
Rueda americana (de herramientas/exploracion/secuencia_tests.py):
0,28,9,26,30,11,7,20,32,17,5,22,34,15,3,24,36,13,1,00,27,10,25,29,12,8,19,31,18,6,21,33,16,4,23,35,14,2.
Tablero físico: el repo no tiene un tablero de apuestas distinto de la rueda ("dispuestos en una ruleta",
reglamento). Uso la mesa estándar de ruleta americana 3×12: n en fila (n−1)//3, columna (n−1)%3; vecinos
ortogonales (±1 en la misma fila, ±3); 0 junto a 1,2 y 00; 00 junto a 2,3 y 0.
En TODAS las familias se excluye la identidad (D = O), que ya cubre producción / el motor.

## Familias (conjunto S(O) de destinos) — 10 familias × 2 orígenes = 20 contrastes O/E
F1 val±1 (mod 38) · F2 val±2 (mod 38) · F3 espejo 37−val · F4 dígitos invertidos (zfill 2, ≤36, ≠n; 1↔10, 12↔21…)
F5 misma terminación · F6 misma decena (0-9,10-19,20-29,30-36) · F7 misma suma de dígitos
F8 rueda ±1 · F9 rueda ±2 · F10 tablero ortogonal
+ 4 contrastes de distribución: (D−O) mod 38 en val y en posición de rueda, chi² (37 gl) contra la esperada
por P_aj (E_k = Σ_t Σ_{j: dif=k} P_aj[t,j]), por origen. Total = 24 contrastes en dev.

## Métrica
O/E contra P_aj, IC Poisson exacto, p bilateral (Poisson con media E). Por era (dev 9:00 = hora 1, dev 8:00 = hora 0)
y conjunta. 'cal' (9:00, sin motor): conteo crudo contra |S|/38 solo como apoyo.

## Regla de selección (en dev)
Pasan a prueba como máximo 3 familias con p_dev conjunto < 0,05 Y O/E del mismo lado de 1 en las dos eras,
ordenadas por p. Si un chi² de diferencias pasa (p < 0,05 y la desviación de las clases más extremas tiene el
mismo signo en las dos eras), el candidato es el vector de multiplicadores por clase (O_k+5)/(E_k+5).
Corrección de una familia: multiplicar P_aj de S(O) por m = (O+0,5)/(E+0,5) ajustado en dev, renormalizar.
Si nada pasa en dev → NULO sin tocar prueba (salvo reporte descriptivo de 0 candidatos).

## Prueba (una sola vez)
Contraste unilateral en la dirección de dev. CONFIRMADO: p < 0,0017 y mismo signo en ambas eras de dev.
PROMETEDOR: p < 0,05. Si no, NULO. Métrica secundaria: mbits por primer sorteo (bootstrap de días, 5000),
Top-5/Top-15 y retorno por ficha (pago 30). Vivo (15 filas) solo se reporta.
