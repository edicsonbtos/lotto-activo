# Estrategia de juego: del Top-15 al Top-5 escalonado (2026-09-22)

Reproducible con `python herramientas/exploracion/estrategia_top5.py`. Usa el
tramo de desarrollo walk-forward (`calor_cache.npz`, n = 7.357). En esta sesión
no se hizo ninguna mirada nueva al tramo de prueba. **Salvedad honesta:** las
cifras de prueba ciega que se citan (`registro_final.jsonl`, línea 5) ya se
conocían al decidir, y el corte en el 5º no estaba preregistrado. El desarrollo
respalda el corte por sí solo (puestos 4-5 a 3,68 %, puestos 6-15 a 3,28 %),
pero el +19 % mezcla una estimación de prueba con una decisión tomada después
de verla. La confirmación limpia tiene que venir del marcador en vivo.

## 1. El modelo está calibrado; el problema era cuántos animales jugar

Cuando el ensamble dice 3,5 % el animal sale el 3,51 %; cuando dice 4,2 %, sale
el 4,08 %. En todo el rango de 1 % a 5 % el valor prometido cae dentro del IC95
de lo observado. Solo el tramo 5-6 % promete de más (5,36 % → 4,14 %, 3.381
casos). **No hace falta recalibrar**, y retocar la temperatura con estos datos
sería ajustar ruido.

## 2. Cada puesto del orden, con plata (pago 30x → equilibrio 3,33 % por animal)

| Puestos | Desarrollo | Prueba ciega | Retorno por ficha (ciega) |
|---|---|---|---|
| 1º-3º | 4,30 % c/u | 4,09 % c/u | **+22,7 %** |
| 4º-5º | 3,68 % c/u | 3,62 % c/u | +8,4 % (IC toca el 0) |
| 6º-15º | 3,28 % c/u | **3,00 % c/u** | **−10 %** |

El Top-15 acierta mucho (≈1 de cada 2), lo que *se siente* bien. Pero 10 de sus
15 animales aciertan por debajo del 3,33 %, y cada ficha puesta ahí pierde
dinero. En prueba ciega el Top-15 dio 49,46 %: **−1,1 % de retorno**. Los
aciertos del Top-15 no alcanzan para pagar las 15 fichas.

## 3. Estrategias comparadas (desarrollo, por mitades; IC95 por bloques de jornada)

| Estrategia | Fichas | Ganancia/sorteo | Retorno | 1ª mitad | 2ª mitad |
|---|---|---|---|---|---|
| **Top-5 escalonado 2-2-2-1-1** | 8 | **+1,94** | +24,3 % | +18,6 % | +30,0 % |
| Top-8 plano (misma plata) | 8 | +1,22 | +15,2 % | +9,8 % | +20,6 % |
| Top-3 plano | 3 | +0,87 | +28,9 % | +24,5 % | +33,2 % |
| Top-15 plano | 15 | +0,92 | +6,1 % | **+2,4 %** | +9,9 % |

Con las mismas 8 fichas, el escalonado gana un 60 % más que repartirlas planas.
El Top-15 usa casi el doble de fichas y gana menos; en la primera mitad ya
rozaba el cero, y en prueba ciega quedó en negativo.

Esperado fuera de muestra (tasas de prueba ciega): Top-5 escalonado
0,1227·60 + 0,0723·30 − 8 = **+1,53 fichas por sorteo (+19,1 %)**; Top-3 +22,7 %;
Top-15 −1,1 %.

## 4. Por qué 2-2-2-1-1 y no otra mezcla

Es el Kelly de apuestas simultáneas redondeado. Con las tasas de prueba ciega,
la apuesta óptima es pᵢ − R/30, con R = 0,966. Eso da 0,78-0,91 % de la banca a
cada puesto 1-3 y 0,40 % a cada puesto 4-5, una proporción de ≈2:1. **No se
probaron otras proporciones para quedarse con la mejor**: 2:1 sale de la
fórmula, no de una búsqueda.

**Los puestos 4-5 no están probados**: 228 de 3.154 (7,23 %) frente a un
equilibrio de 6,67 %, z = 1,27. Con el supuesto prudente (4-5 sin ventaja),
Kelly les daría 0 y el Top-3 plano crecería un poco más. Por eso el Top-3 es la
**base** y el 4-5 es un **refuerzo**: sube la frecuencia de cobro de 1 de cada 8
a 1 de cada 5 y, si su ventaja medida es real, suma algo. El usuario jugaba
Top-15 por la frecuencia de cobro; el refuerzo le da buena parte de esa
frecuencia sin los puestos 6-15, que pierden.

`gestion_banca.py` dimensiona la base con ¼ de Kelly sobre el límite bajo del
IC del Top-3 (11,17 %), y pone el refuerzo encima a media ficha. Queda en
≈0,32-0,40 % de la banca por sorteo. Con una banca de menos de ≈1.850 (ficha
mínima 1) recomienda solo el Top-3. Para jugar solo lo probado basta con
`FICHAS = [1, 1, 1, 0, 0]`. Retorno esperado del escalonado: +19 %, con IC95
aproximado de +10 % a +28 %.

## 5. Lo que NO mejora (ya probado y descartado)

- Saltar sorteos que se ven "fríos" o cargar más en los "calientes": falló en
  prueba ciega (hilo 6). Por eso se quitó la abstención por p3 de `gestion_banca.py`.
- Rachas del favorito, rachas de aciertos o de fallos: no informan (hilos 5 y 6).
- 308 hipótesis adicionales (Operación Turing): 0 señales.

## 6. Cómo se confirma en vivo

La web muestra ahora "Cada forma de jugar, con plata" sobre el marcador real. Al
2026-09-22 (85 sorteos con orden) el Top-5 iba a +5,9 % y el Top-15 a −8,2 %.
Con n = 85 eso todavía es ruido (el error típico del Top-5 es ±4 puntos de
acierto). Hacen falta ~1.000 sorteos para decidir.
