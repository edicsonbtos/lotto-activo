# Informe: "Estrategia Francotirador" verificada (2026-10-02)

Reproducible: `python investigacion/2026-10-02/francotirador/francotirador.py` (salida en `salida_dev.txt`, cifras en `francotirador_dev.json`).
Preregistro: `PREREGISTRO_francotirador.md` (escrito antes de medir). Datos: desarrollo LA, 7357 sorteos, 636 jornadas, caché walk-forward del ensamble. El tramo de prueba no se tocó.

## Veredicto corto
**Ninguna de las 7 hipótesis pasa, y las reglas literales del texto no se pueden ejecutar.** No se modificó ningún código de producción.

## 1. Las cifras del texto son imposibles con las probabilidades reales (V1)
| Regla del texto | Medido en 7357 sorteos |
|---|---|
| Abstenerse si entropía > 4,1 bits | Entropía mínima 4,92, mediana 5,14, máx teórico 5,25. **Hay 0 sorteos con < 4,1 bits: el filtro abstiene SIEMPRE.** |
| Abstenerse si Top-3 < 15 % | Top-3 mediana 13,1 %, máx 22,0 %. Juega solo 1145 sorteos (16 %) y por una razón distinta a la que cree el texto. |
| Rango Top-3/5/7 con cobertura ≥ 60 % | Top-3 máx 22,0 %, Top-5 máx 32,7 %, Top-7 máx 41,4 %. **0 sorteos.** Incluso el Top-15 llega a ≥ 60 % solo en 349 (4,7 %); máx 67,3 %. |
| "Top-5 con 65 % de acierto" | El Top-5 acierta ~21 % en promedio. El 60-70 % por sorteo no existe (ya cerrado en `top15_70/INFORME.md`). |

Conclusión: los números 4,1 / 0,60 / 65 % salen de imaginar una distribución concentrada. Esta es casi plana (entropía ≈ 98 % del máximo). Todo "filtro de confianza" tiene que trabajar con diferencias pequeñas.

## 2. Filtros por entropía/confianza (F1-F3), Top-5 escalonado, retorno por ficha
Referencia, jugar todos: **+24,3 %** (desarrollo). IC 99,29 % por jornada.
| Filtro | n | Retorno | IC | Dif. contra jugar todos | Mitades | O/E Top-5 |
|---|---|---|---|---|---|---|
| F1 entropía, 20 % menor por hora | 1472 | +36,0 % | [+16,8; +55,0] | +11,8 pp [−5,6; +30,7] | +25 / +39 | 0,965 |
| F2 entropía, 10 % menor | 742 | +20,3 % | [−4,8; +44,3] | −4,0 pp [−26,3; +19,6] | −40 / +30 | 0,840 |
| F3 masa Top-5, 20 % mayor | 1472 | +28,9 % | [+10,1; +47,8] | +4,6 pp [−11,7; +20,7] | +20 / +35 | 0,902 |

Lectura: el retorno positivo es el del ensamble en general (+24 %), no del filtro. La diferencia contra jugar todos incluye 0 en los tres, y F2 cambia de signo entre mitades. El O/E ≤ 1 dice que en los sorteos "confiados" el modelo aciertan **menos** de lo que prometía (22,4 % observado contra 23,2 % esperado; en F2, 19,9 contra 23,7). La confianza del modelo no identifica sorteos mejores. Abstenerse solo reduce el número de jugadas.

## 3. Las 8:00 (F4)
- Top-15 en las 8:00 (372 días desde 2024-11-25): 60,5 % observado, 57,3 % esperado por el modelo. O/E 1,055, IC [0,936; 1,177] → **no pasa**.
- Racha: con p = 0,605, 12 aciertos seguidos desde un punto dado ocurre 0,24 % de las veces, pero entre 372 días la racha máxima por azar tiene mediana 10 y **P(≥12) = 29,6 %**. En desarrollo hubo una racha de 16 (por azar 4 %, y esto es 1 hora elegida entre 12 mirando la racha más larga). Una racha de 12 en las 8:00 no es anomalía.
- Top-5 escalonado en las 8:00: +42,1 % [+6,9; +82,5] descriptivo. Alto, pero es una hora elegida a posteriori entre 12 y 372 sorteos; no es preregistrable como confirmación (misma situación que "17:00" en `top15_70`).
- La explicación de "entropía de hardware fresca" no tiene base medible: si fuera cierta, el O/E del modelo en hora 0 sería > 1 de forma clara y no lo es. La hipótesis prospectiva ya está en `PREREGISTRO_manana_8am.md` (30 sorteos desde 2026-10-02, umbral ≥ 24/30 para señalar algo).

## 4. Otros "edges" del texto
| Idea | Resultado |
|---|---|
| Lunes (F5) | O/E Top-5 1,055 [0,886; 1,220], mitades 1,08 / 1,03. No pasa. |
| Animales fríos > 12 días (F6) | Salieron 171 contra 273,5 por azar y 210,8 que decía el modelo. O/E 0,811 [0,651; 0,977]. **Dirección contraria a la del texto**: los fríos salen menos, no más ("regresión a la media" no existe). El modelo todavía los sobreestima un 19 % (IC no contiene 1, pero no pasó el criterio preregistrado porque este era ">1"). Descriptivo, un solo corte (12 d) → no se actúa. |
| Varianza condicional / GARCH (F7) | Autocorrelación lag-1 de la sorpresa por hora: −0,017 [−0,055; +0,022]. No hay agrupación de varianza que modelar. |
| Doble consecutiva / terminación | No probada (la caché no trae el número de lotería). Es una hipótesis barata de preregistrar. |

## 5. Ideas del texto que no se pueden probar con estos datos
- **Sesgo del apostador / pari-mutuel**: el pago es fijo (30×); no hay datos de volumen jugado por animal. Si el pago fuera repartido, la idea sería válida, pero no es el caso aquí. Lo único medible: el operador sí esquiva el número de la fecha y la hora (señal de 2026-10-01, pendiente de sombra en vivo).
- **Jitter de hardware / HMM del PRNG**: Turing ya midió PRNG/semilla y Markov 38×38: ruido. Los resultados de F7 (sin estructura de segundo orden) van en la misma dirección.

## 6. Lo que sí es utilizable
1. **"Menos sorteos con certeza" no se puede lograr con el modelo actual**: no existe un subconjunto de sorteos identificable donde el acierto sea sustancialmente mayor. El 60-70 % solo se obtiene cambiando la forma de jugar (Top-22 ≈ 74 %; Top-15 en dos sorteos ≈ 80 % "al menos uno"), con el coste esperado ya medido (Top-15 plano pierde).
2. La ventaja real está en el **tamaño de la apuesta por puesto** (Top-5 escalonado), que ya se juega, no en elegir cuándo jugar.
3. El **marcador en vivo** (`lotto-marcador`) decide. Para las 8:00 se mide solo con sorteos desde 2026-10-02.

## Limitaciones
Un solo juego (LA), un solo tramo (desarrollo), cortes de 20 % y 10 % escogidos antes de medir y no optimizados. No se probó el tramo ciego porque ningún hallazgo pasó el desarrollo. No se hizo revisión de `revisor-sesgo` porque no cambia el modelo ni el registro.

---
# Anexo: "Motor Contrarian" (segundo texto, 2026-10-02)
Preregistro `PREREGISTRO_contrarian.md`, script `contrarian.py`, salida `salida_contrarian.txt`. Desarrollo LA, 7357 sorteos, IC 99,17 % por jornada. Pregunta: dónde se equivoca el ensamble (O/E = salidas / ΣP), porque el ensamble ya ve huecos y repeticiones.

| Regla del texto | O/E del ensamble | IC | Veredicto |
|---|---|---|---|
| C1 atrasados >12 sorteos (penalizar) | 0,990 | [0,976; 1,004] | No pasa: el ensamble ya los descuenta |
| C2 salió en los últimos 2 (penalizar) | 0,976 | [0,772; 1,189] | No pasa |
| C3 zona muerta 5-8 sorteos (bonificar) | 1,030 | [0,919; 1,145] | No pasa |
| C4 8:00 sin penalizadores | 8:00 1,001 / resto 0,989 | [0,94; 1,05] / [0,975; 1,004] | No pasa: no hay diferencia entre 8:00 y el resto |
| C5 terminación como desempate | −7,3 mnats/sorteo | [−12,4; −2,2] | No pasa: **empeora** el modelo en ambas mitades |
| C6 estrategia completa (x0,5 / x0,7 / x1,3, 8:00 intacta) | dif. retorno −24,0 pp | [−33,6; −15,3] | No pasa: pasa de +24,3 % a +0,3 % |

Hallazgos: (1) el "37 % menos que el azar" de los fríos es lo que el ensamble ya aplica (predijo 210,8, salieron 171; el residuo es O/E 0,81 con hueco en días y 0,99 con hueco en sorteos). (2) Con ">12 sorteos" la regla afecta a 27 de 38 animales por sorteo, porque 12 sorteos es un día; el texto confunde días con sorteos. (3) La regla completa mueve el Top-5 en el 95 % de los sorteos y borra todo el retorno. (4) La causalidad "público persigue, operador bloquea" no se puede medir: no hay datos de volumen jugado, y lo medido es compatible con el solo hecho de que el operador evita repetir y recicla con huecos (ya en el ensamble).

---
# Anexo 2: "Geometría y macro-estacionalidad" (tercer texto, 2026-10-03)
Preregistro `PREREGISTRO_geometria_macro.md`, script `geometria_macro.py`, salida `salida_geometria_macro.txt`. Desarrollo LA, 7357 sorteos, 8 pruebas, IC 99,375 % por jornada. Sin multiplicadores sobre P.

| Hipótesis | Resultado | Veredicto |
|---|---|---|
| G1 clúster dinámico (brecha > 0,002) | Tamaño medio 3,2; en el 65 % de los sorteos el clúster es 1 solo animal. Retorno/ficha +8,0 % contra Top-5 plano +21,5 % (dif −20,1 pp [−28,3; −12,2], ambas mitades negativas) | No pasa, es peor |
| G2a diversificar por terminación | Cambia el 27 % de sorteos; retorno +24,3 % → +24,6 % (dif +0,31 pp [−1,48; +2,14]); mitades −0,4 / +1,0 | No pasa |
| G2b diversificar por paridad | Cambia el 4 %; dif −0,15 pp [−0,82; +0,46] | No pasa |
| G3a quincena (15 y 30) | O/E Top-5 0,978 [0,738; 1,226], 486 sorteos | No pasa |
| G3b fin de mes | O/E 0,935 [0,695; 1,178] | No pasa |
| G3c festivos fijos | O/E 0,924 [0,603; 1,260], solo 186 sorteos (poca potencia) | No pasa |
| G4a alternancia de paridad | O/E 0,993 [0,962; 1,024]; control lag 2: 1,019 | No pasa |
| G4b alternancia de magnitud | O/E 1,020 [0,986; 1,053]; control lag 2: 0,941 [0,906; 0,974] | No pasa |

Notas: (1) La distribución es casi plana, por eso un clúster por brecha suele ser un solo animal y juega menos fichas con peor retorno; el tamaño "dinámico" no encuentra grupos reales. (2) Las pruebas de calendario tienen IC de ±25 %: aunque existiera un efecto del 10-15 %, 40 jornadas no lo detectan; el resultado es "sin evidencia", no "demostrado que no existe". Los festivos móviles (Carnaval, Semana Santa) no se probaron por falta de calendario. (3) El control de lag 2 en magnitud (0,941) excluye 1, pero era un control no preregistrado como hipótesis y entre 10 contrastes se espera alguno; no se actúa.
