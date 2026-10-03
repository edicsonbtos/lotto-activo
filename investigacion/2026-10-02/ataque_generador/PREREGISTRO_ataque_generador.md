# PRERREGISTRO — "Ataque al generador" (texto de otro LLM, 2026-10-02)

Datos: LA, 38 animales (0, 00, 1..36). Solo desarrollo, filas [2000, 9357). Prueba (>=9357) NO se toca. Semilla 20261002.
Familia: 5 hipótesis ejecutables -> alfa por hipótesis 0,01 (Bonferroni 0,05/5). Dudoso: 0,01-0,05.

## Qué NO se ejecuta y por qué (escrito antes de medir)
- A1 reconstrucción MT19937: exige salidas crudas de 32 bits consecutivas; aquí solo hay 1 de 38 categorías (~5,2 bits) y se desconoce el mapeo. Imposible por construcción. Se sustituye por la complejidad lineal (H2), que detecta registros lineales en GF(2).
- A4 timing de la API: la latencia de una consulta HTTP no codifica el resultado (el sorteo ya está fijado). No hay datos de tiempos ni mecanismo.
- A3 correlación Pearson entre loterías: Pearson sobre etiquetas categóricas no tiene sentido; la prueba correcta ya está hecha: hilo 7 (RD<->LA, real, en producción), hilo 8 (LARD independiente), ronda 3 (hermanas: nada).
- F1 LSTM / F2 autoencoder / F4 clustering de firmas: el hilo 9 mostró que un modelo flexible de 91 variables NO supera al ensamble. No se corren sin una señal previa.
- Dieharder: no está instalado; la batería tipo NIST de H2 cubre lo mismo en pequeño.

## H1 sesgo de módulo / uniformidad
H0: P(animal)=1/38. Métrica: chi-cuadrado, 37 g.l. Falsa si p>=0,01. (El sesgo de 2^32 mod 38 es ~1e-8 relativo: indetectable aunque exista.)
## H2 batería tipo NIST sobre el flujo de bits (5 bits por sorteo, con rechazo de los símbolos >=32)
Monobit, runs, espectral (DFT), serial m=2, complejidad lineal (Berlekamp-Massey, bloques de 500). p<0,01 = falla. Una falla puede ser la estructura ya conocida (no repetir animal en el día), no un PRNG roto.
## H3 fechas especiales
24/12, 25/12, 31/12, 1/1, 19/4, 24/6, 5/7, 24/7, 12/10. H0: misma distribución que el resto. Chi-cuadrado de homogeneidad 2x38, p por permutación de días (5000). Falsa si p>=0,01.
## H4 matriz de transición lag-1 (38x38)
Pasa solo si >=5 celdas con p<0,05/1444. Se repite para pares del mismo día y de días distintos. (Markov 38x38 ya cerrado como ruido.)
## H5 entropía aproximada (ApEn m=2)
Contra 1000 permutaciones del mismo flujo. Falsa si p>=0,01.

Veredicto: "pasa" solo si p<0,01 Y se replica en las dos mitades del desarrollo con p<0,05. Aunque pase, no cambia el ensamble sin un ROI propio en su preregistro.

## Corrección registrada (2026-10-02, tras la 1ª corrida)
La 1ª versión de H2 usaba 6 bits por código 0..37: los valores 38..63 no existen, así que monobit/runs/serial fallaban por construcción (error del test, no del generador). Se corrige con rechazo (solo símbolos 0..31 -> 5 bits uniformes bajo H0). Ningún umbral cambia.
