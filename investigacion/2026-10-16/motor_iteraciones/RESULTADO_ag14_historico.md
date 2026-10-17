# Resultado de Ag14 en matrices históricas disponibles

## Qué se ejecutó

Se aplicó, sin volver a ajustar parámetros, la secuencia congelada `Ag12 V1 → RD → exposición` a las matrices walk-forward guardadas y se comparó con ensamble_v2 y Ag12+RD. La ejecución reproducible está en `evaluar_ag14_historico.py`; sus fuentes y huellas SHA-256 están en `resultado_ag14_historico.json`.

## Resultados

| Tramo ya observado | Sorteos | Modelo | mbits medios | Aciertos Top 3 / 5 / 15 | Retorno Top 5 por ficha |
|---|---:|---|---:|---:|---:|
| Réplica 2026, ene–16 sep | 2.959 | ensamble_v2 | 91,93 | 371 / 586 / 1.470 | 22,80 % |
| | | Ag12+RD | 124,11 | 397 / 651 / 1.556 | 32,82 % |
| | | **Ag14** | **127,64** | **404 / 661 / 1.586** | **34,97 %** |
| Fresco, 16 sep–7 oct | 249 | ensamble_v2 | 117,51 | 26 / 43 / 116 | 5,42 % |
| | | Ag12+RD | 145,75 | 40 / 51 / 136 | 37,05 % |
| | | **Ag14** | **157,58** | **43 / 54 / 141** | **46,08 %** |

En la réplica larga, Ag14 superó al ensamble en **35,71 mbits** (IC90 por jornada: 28,00–43,43) y a Ag12+RD en **3,53** (1,10–5,97). En el tramo fresco, las diferencias fueron **40,07 mbits** frente al ensamble (10,97–69,17) y **11,84** frente a Ag12+RD (7,01–16,66). La mejora Top 5 frente al ensamble fue de 3 puntos porcentuales en la réplica y 4 puntos en el tramo fresco; retorno Top 5: +12,17 y +40,66 puntos porcentuales por ficha, respectivamente.

## Cómo interpretar esto

La señal histórica es prometedora y Ag14 también mejora modestamente sobre Ag12+RD en ambos cortes. Sin embargo, **no es una nueva prueba ciega**: la réplica ya había sido analizada y el tramo fresco ya se había reportado para ag12/RD; además se solapa parcialmente con el período donde se observó exposición. Estos números sirven como reproducción descriptiva, no como confirmación independiente ni razón para cambiar producción.

La única validación nueva es la predicción prospectiva sellada del 17 de octubre; todavía no tiene resultado puntuable en el conjunto local. El preregistro mantiene una sola evaluación decisoria después de 931 sorteos futuros válidos, sin reajustar parámetros al mirar estos históricos. Ag14 queda en sombra; no se promovió ni desplegó.

## Reproducir

Desde la raíz del repositorio: `python investigacion/2026-10-16/motor_iteraciones/evaluar_ag14_historico.py`.
