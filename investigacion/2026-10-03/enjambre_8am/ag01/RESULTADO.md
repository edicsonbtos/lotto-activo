VEREDICTO: NULO

# ag01 — Mapa de memoria completo del primer sorteo
Rasgo: ganador del primer sorteo de hoy == ganador de la posición j (orden dentro del día) del día d−k
(calendario; días cerrados no aportan). Línea base: `P_aj`. Dev = 635 primeros sorteos (263 a las 9:00 + 372 a las 8:00).

## Qué se miró en dev (233 contrastes)
- 200 rasgos: (k=1..14, j=0..11) = 168, primero de hace k=15..30 (16), último de hace k=15..30 (16; para k≤14 el
  último ya es una celda del mapa). p bilateral Poisson exacta y Benjamini-Hochberg.
- 33 agregados de estructura: paridad de k (2+2), ciclo semanal (2+1), por posición j (12), por k (14).
- **Ninguno de los 200 pasa FDR**: q mínimo 0,87. El mejor es k=8, j=6: O/E 0,40, p=0,007. Los 25 primeros
  tienen p de 0,007 a 0,19, que es justo lo que da el azar con 200 contrastes.

Controles, ya corregidos en P_aj (deben dar ≈1):

| rasgo | O | E | O/E [IC 95 %] | 9:00 | 8:00 |
|---|---|---|---|---|---|
| primero de ayer (k=1, j=0) | 1 | 2,3 | 0,43 [0,01; 2,41] | 1/1,2 | 0/1,1 |
| primero de hace 3 días (k=3, j=0) | 28 | 27,5 | 1,02 [0,68; 1,47] | 9/10,4 | 19/17,1 |

El ajuste de producción calibra bien los dos rasgos.

Estructura (dev, O/E; los controles quedan fuera):
- Paridad: k par 1,05 y k impar 1,04 (todas las j). Solo el primero: k par 1,02 y k impar 1,02. **No hay patrón.**
- Ciclo semanal: primero de hace 7, 14, 21 o 28 días O/E 0,94 (62/66,1; 9:00 0,89, 8:00 0,97). Con k=7 y 14 en
  todas las j da 0,97. **No hay ciclo.**
- Fondo general: sumando todas las celdas k≤14, O/E ≈ 1,045. El motor se queda algo corto con "salió hace pocos
  días". k=1: 1,18 (p=0,07). k=2: 1,18 (p=0,013). Las dos eras dan >1.
- Por posición: j=3 da O/E 1,21 (p=0,002), con 9:00 en 1,19 y 8:00 en 1,22. Las demás j van de 0,95 a 1,09.
  Sin mecanismo, y el conteo crudo en 'cal' da 0,87.
- Primero de hace k=15..30: sin estructura. k=16 da 1,60 (p=0,03) y k=30 da 0,42 (p=0,014), ambos aislados.

## Candidatos a prueba (pre-registrados en PREREGISTRO.md, multiplicador por ML en dev con L2=1)

| candidato | m (dev) | dev O/E (9:00 / 8:00) | prueba O/E [IC] | p unil. | mbits prueba [IC 95 %] | decisión |
|---|---|---|---|---|---|---|
| C1 salió ayer (j≥1) o anteayer | ×1,378 | 1,18 (1,30 / 1,11) | 1,12 [0,95; 1,30] (165/147,7) | 0,085 | +13,4 [−13,0; +39,7] | NULO |
| C2 salió en la posición j=3 en 14 días (m^conteo) | ×1,201 | 1,21 (1,19 / 1,22) | 0,94 [0,76; 1,15] (92/98,2) | 0,75 | −15,7 [−34,6; +4,1] | NULO |
| C3 posición 6 de hace 8 días | ×0,434 | 0,40 (0,41 / 0,38) | 1,16 [0,50; 2,28] (8/6,9) | 0,74 | −15,1 [−42,4; +8,1] | NULO |

Efecto en plata en prueba (n=261; retorno por ficha a 30, Δ contra P_aj, IC bootstrap por días):
- C1: Top-5 54 → 57 (Δ +0,069 [−0,023; +0,184]) y Top-15 132 → 136 (Δ +0,031 [−0,039; +0,107]).
- C2: Top-5 54 → 56 y Top-15 132 → 132.
- C3: Top-5 54 → 56 y Top-15 132 → 130.
- Ninguna diferencia es distinguible de 0.

Vivo (n=15, solo se reporta):
- C1: O/E 1,06, +0,5 mbits, Top-5 4 → 3.
- C2: O/E 1,05, −2,6 mbits.
- C3: 0/0,4.

## Lectura
- El mapa completo no muestra memoria nueva. Fuera de los dos rasgos que ya están en producción, ninguna celda
  (k, j) sobrevive a FDR. No hay paridad ni ciclo semanal.
- C2 (j=3) y C3 (la mejor celda) se dan vuelta en prueba. Eran ruido de selección, como se esperaba.
- C1 es lo único con el mismo signo en dev y en prueba (1,18 → 1,12). Coincide con el O/E 1,12 [0,94; 1,32] de
  "salió ayer" en el INFORME del 2026-10-03.
  - Hay un ligero castigo de más a los animales de los 2 últimos días a la primera hora.
  - Con p=0,085 no llega ni a PROMETEDOR.
  - Agrupando dev y prueba (exploratorio, no confirmatorio) da ~1,16.

## Recomendación
No tocar producción. Los factores ×0,272 y ×1,736 quedan validados como control: con ellos, O/E 0,43 y 1,02 en dev.
Si se quiere seguir C1, vale como vigilancia en vivo pre-registrada, no como ajuste: es O/E de "salió en los 2
días anteriores" a las 8:00 contra `scores_base` con el ajuste actual, y se esperaría ~1,15 si es real.

Archivos (en esta carpeta):
- Scripts: `comun.py`, `explorar_dev.py` (solo dev/cal), `candidatos.py`, `ajustar_dev.py` y `confirmar_prueba.py`.
- Salidas: `dev_salida.txt`, `ajuste_dev_salida.txt`, `prueba_salida.txt` y `candidatos_dev.json`.
- Reproducir: `cd ag01 && python explorar_dev.py && python ajustar_dev.py && python confirmar_prueba.py` (~1 min).
