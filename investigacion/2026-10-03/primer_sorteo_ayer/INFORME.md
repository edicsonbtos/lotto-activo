# El primer sorteo no repite el primer sorteo de ayer (2026-10-03)

Origen: pregunta del usuario tras el sorteo de las 8:00 del 2026-10-03. Salió **11 Gato** y quedó en el
**puesto 16** del Top-15. En los puestos 13 y 15 estaban **24 Iguana** (salió ayer a las 8:00) y **33 Pescado**
(salió ayer a las 6 PM, hace dos sorteos).

Reproducción del pronóstico congelado: `prediccion.Predictor().calcular()` sobre el historial del volumen
cortado antes de las 8:00, con pesos de frontera 12500. Para validar el método se reprodujo el registro
congelado del 2026-09-23 a las 19:00 (diferencia máxima 0,0001).

```
1 Cebra 4,67  2 Águila 4,67  3 Pavo 4,54  4 Delfín 4,46  5 Zorro 4,34  6 Carnero 4,30  7 Oso 3,97  8 Paloma 3,83
9 Venado* 2,93  10 Ratón* 2,83  11 Chivo* 2,78  12 Ardilla* 2,58  13 Iguana* 2,57  14 Perico* 2,43
15 Pescado* 2,40  16 Gato 2,37  17 Rana* 2,33          (* = salió ayer)
```

## ¿El motor ignora el día anterior a las 8:00? No.
`intradia_v2` tiene las variables "salió ayer × hora" y "salió anteayer × hora", y `secuencia_v3` tiene el
retraso exacto. Contra el motor, "el ganador de las 8:00 salió ayer" da O/E 1,12 [0,94; 1,32]. Ese castigo
ya está bien calibrado y, si acaso, es un poco excesivo. Por eso los puestos 9 a 15 de hoy eran todos animales
de ayer: después de los 8 favoritos, eran los "menos malos".

## Pescado (hace 2 sorteos): el motor acierta
8:00 = ayer 6 PM: observado 11 y el motor esperaba 12,0 (O/E 0,92 [0,46; 1,64]). Ayer 7 PM: O/E 1,22.
Ayer 5 PM: O/E 0,70, con un IC que incluye el 1. No hay nada que corregir.

## Iguana (ayer 8:00): señal real que el motor captura a medias
Ganador del primer sorteo = ganador del primer sorteo de ayer:

| tramo | N | observado | motor esperaba | O/E [IC 95 %] | P(≤ obs) |
|---|---|---|---|---|---|
| dev [2000, 9357) | 627 | 1 | 8,3 | 0,12 [0,00; 0,68] | 0,002 |
| prueba | 257 | 1 | 5,4 | 0,19 [0,00; 1,04] | 0,03 |
| vivo (desde 09-15) | 19 | 0 | 0,4 | — | — |
| todo | 903 | 2 | 14,1 | 0,14 [0,02; 0,51] | 9·10⁻⁵ |

- Conteo crudo: con el primer sorteo a las 9:00 (hasta nov-2024) salieron 2 de 440 (11,6 por azar). Con el
  primero a las 8:00 salió 1 de 642 (16,9 por azar). Las excepciones fueron 2023-11-02, 2024-11-21 y 2026-06-22.
- Es exclusivo del primer sorteo. En las demás horas, "misma hora de ayer" da O/E 1,06 [0,93; 1,20].
- Por qué el motor se queda corto: el retraso exacto de `secuencia_v3` es un peso compartido entre las 12 horas.
  A las 8:00, el animal de ayer 8:00 tiene retraso 12, pero en las otras 11 horas ese retraso no significa nada.
  El castigo se diluye. Con 11 sorteos al día (antes de nov-2024) la regla caía en retraso 11, y ese aprendizaje
  se borra al reentrenar. Consecuencia: el animal de ayer a la primera hora entró al Top-15 el 0 % de las veces
  en dev, el 11 % en prueba y el 21 % en vivo (4 de 19 días).

Salvedad: la hipótesis nace de mirar el vivo y se midió de una vez en todos los tramos (el de prueba ya estaba
usado). Las dos eras (9:00 y 8:00) son independientes entre sí y ambas la muestran. Se hicieron 6 contrastes,
y P = 9·10⁻⁵ sobrevive a Bonferroni.

## Corrección propuesta (NO aplicada en producción)
En el primer sorteo del día, multiplicar por m la probabilidad del ganador del primer sorteo de ayer y
renormalizar. m = 0,171 se ajustó SOLO en dev (O = 1, E = 8,25, suavizado +0,5).

| tramo | mbits por primer sorteo | Top-5 | Top-15 |
|---|---|---|---|
| dev | +11,8 | 134 → 134 | 348 → 348 |
| prueba | +15,3 | 58 → 58 | 128 → 128 |
| vivo | +28,1 | 4 → 4 | 14 → 15 (hoy) |

Con la corrección, hoy Iguana sale del Top-15 y **Gato entra en el #15**. El efecto en plata es pequeño. Ese
animal solo entra al Top-15 en 1 de cada 5-10 días, y el #16 que lo reemplaza acierta ~2,4 %. A las 8:00 eso
suma del orden de +0,3 pp de Top-15. Repartido en los 12 sorteos del día, son ~1,3 mbits por sorteo.

## Pre-registro de la verificación en vivo (escrito antes de ver datos posteriores a 2026-10-03 08:00)
- Muestra: los primeros sorteos del día desde 2026-10-04 hasta 2027-01-03 (≈ 90 días).
- Métrica: veces que el ganador del primer sorteo = ganador del primer sorteo de ayer, contra la suma de las
  probabilidades congeladas del motor para ese animal.
- Se espera ~2 por el motor y ~0,3 si la regla sigue. **Falsada** si salen ≥ 3. Con 0-1 queda consistente.
  La potencia es baja (con 0 observados, P ≈ 0,13 bajo el motor): el peso de la evidencia es el histórico.
- Cualquier cambio de modelo sigue gobernado por `gestion_banca.VIGILANCIA` y debe pasar por `revisor-sesgo`.

Reproducir: `python investigacion/2026-10-03/primer_sorteo_ayer/analizar.py COPIA_DEL_HISTORIAL` (~35 s).
