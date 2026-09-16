# Vectores 1 y 2 -- reporte consolidado

Generado por `herramientas/exploracion/vectores_1_2.py`.

- Historial completo: **12502 sorteos**. Tramo de prueba (>= 9357): **intacto, no se toca**.
- Analizado aqui: tramo de **desarrollo** `[2000, 9357)` = **7357 sorteos**, 2024-03-07 a 2025-12-17.
- Azar puro de referencia: Top-1 2.63%, Top-3 7.89%, 1 animal = 1/38 = 2.632%.
- alfa = 0.01, con Bonferroni y FDR (Benjamini-Hochberg) donde hay tests multiples.

---

## Vector 1 -- Sesgo de frecuencias puro

### 1.1 Uniformidad global

| test | n | chi2 | gl | p |
|---|---|---|---|---|
| 38 animales, global | 7357 | 42.5 | 37 | 0.2443 |

Mas frecuentes: `1` (219), `34` (213), `6` (210). Menos frecuentes: `27` (152), `36` (163), `25` (166). Esperado por animal: 193.6.
El animal mas frecuente sale el 2.977% de las veces (IC95 2.612-3.390%); el azar da 2.632%.

**Veredicto 1.1: RUIDO** (p=0.2443).

### 1.2 Uniformidad por ano

| ano | n | chi2 | gl | p bruto | signif. Bonferroni |
|---|---|---|---|---|---|
| 2024 | 3292 | 28.5 | 37 | 0.8424 | no |
| 2025 | 4065 | 28.7 | 37 | 0.8344 | no |

Umbral Bonferroni = 0.0050 (2 tests). Significativos: Bonferroni 0/2, FDR 0/2.

**Veredicto 1.2: RUIDO**.

### 1.3 Uniformidad por dia de semana

| dia | n | chi2 | p bruto | signif. Bonferroni |
|---|---|---|---|---|
| lunes | 1067 | 21.2 | 0.9826 | no |
| martes | 1067 | 21.1 | 0.9832 | no |
| miercoles | 1064 | 19.4 | 0.9922 | no |
| jueves | 1058 | 35.5 | 0.5384 | no |
| viernes | 1065 | 23.6 | 0.9574 | no |
| sabado | 1053 | 32.0 | 0.7041 | no |
| domingo | 983 | 23.0 | 0.9654 | no |

Umbral Bonferroni = 0.0014 (7 tests). Significativos: Bonferroni 0/7, FDR 0/7.

**Veredicto 1.3: RUIDO**.

### 1.4 Uniformidad por hora (sorteo del dia)

| hora | n | chi2 | p bruto | signif. Bonferroni |
|---|---|---|---|---|
| 0 | 372 | 32.7 | 0.6702 | no |
| 1 | 635 | 37.6 | 0.4430 | no |
| 2 | 635 | 31.5 | 0.7260 | no |
| 3 | 635 | 41.3 | 0.2888 | no |
| 4 | 635 | 41.4 | 0.2844 | no |
| 5 | 635 | 35.8 | 0.5265 | no |
| 6 | 635 | 26.9 | 0.8889 | no |
| 7 | 635 | 39.1 | 0.3745 | no |
| 8 | 635 | 42.7 | 0.2387 | no |
| 9 | 635 | 45.2 | 0.1658 | no |
| 10 | 635 | 30.9 | 0.7514 | no |
| 11 | 635 | 26.9 | 0.8889 | no |

Umbral Bonferroni = 0.0008 (12 tests). Significativos: Bonferroni 0/12, FDR 0/12.

**Veredicto 1.4: RUIDO**.

> **Vector 1 en una linea:** la frecuencia de cada animal NO se distingue de la uniforme. No hay 'animales calientes'. Apostar por frecuencia historica es tirar el dinero.

---

## Vector 2 -- Dependencia temporal

### 2.1 Markov orden 1 (el ganador anterior condiciona el siguiente?)

Tabla 38x38 de transiciones, n=7356 pares.

| test | chi2 | gl | p | celdas con esperado <5 |
|---|---|---|---|---|
| Markov orden 1 | 1413.5 | 1369 | 0.1966 | 575 de 1444 |

**Veredicto 2.1: RUIDO** (p=0.1966).

**Pero cuidado con leer eso como 'no hay dependencia'.** El chi2 de la tabla completa reparte la evidencia en 1369 grados de libertad, y la dependencia real de este sorteo vive en **una sola** de esas direcciones: la diagonal (no repetir el animal anterior). Ese efecto se diluye. El test dirigido a la diagonal:

| test dirigido | observado | esperado | tasa | IC95 | z | p |
|---|---|---|---|---|---|---|
| s(t) == s(t-1) | 47 | 193.6 | 0.639% | 0.481-0.849% | -10.7 | 1.31e-26 |

**Veredicto 2.1-bis: SENAL REAL, y muy fuerte.** El sorteo NO repite el animal anterior casi nunca: 0.639% contra el 2.632% del azar (0.24x). La leccion metodologica es que un chi2 de 1369 gl es la herramienta equivocada para un efecto que vive en 38 celdas.

### 2.2 Markov orden 2

Una tabla 38x38x38 son 54872 celdas para 7355 observaciones: **0.13 observaciones por celda**.
El test esta **sin potencia**: no se puede concluir nada de orden 2 con este n.
Lo que si se puede mirar es el efecto marginal del sorteo t-2 sobre el t:

| test | chi2 | gl | p |
|---|---|---|---|
| s(t-2) -> s(t), marginal | 1519.5 | 1369 | 0.0026 |

**Veredicto 2.2: SENAL REAL** para el efecto marginal a lag 2; **INCONCLUSO** para Markov de orden 2 completo (harian falta ~274,360 observaciones para 5 por celda, o sea ~63 anos de sorteos).

### 2.3 Gaps entre repeticiones vs geometrica

Bajo azar puro los huecos entre apariciones de un animal son geometricos de media 38.0 sorteos.

| estadistico | valor |
|---|---|
| animales evaluados | 38 |
| z medio del hueco medio | -0.01 |
| animales con \|z\| > 3 | 1 |

Indice de dispersion (varianza observada / varianza geometrica), media sobre los 38 animales: **1.083**. Menor que 1 = los huecos son **mas regulares** que el azar (evitacion / balanceo); mayor que 1 = mas irregulares (rachas).

**Veredicto 2.3: SENAL REAL**.

### 2.4 Ljung-Box sobre la serie indicadora de cada animal

Un test por animal (38 tests), h=24 lags.

| p minimo | animal | signif. Bonferroni | signif. FDR |
|---|---|---|---|
| 0.00004 | `31` | 1/38 | 1/38 |

**Veredicto 2.4: SENAL REAL**.

---

## El sesgo conductual (lo que de verdad mueve la aguja)

### 3.1 Evitacion de repeticion dentro de la jornada

Jornadas completas de 12 sorteos: **371**.

| medida | observado | esperado por azar | z | p |
|---|---|---|---|---|
| animales distintos por jornada | **11.337** (IC95 11.269-11.404) | 10.407 | +27.0 | 1.48e-160 |

Probabilidad de que dos sorteos del **mismo dia** separados por `d` posiciones den el mismo animal (azar = 2.632%):

| distancia d | pares | repeticiones | tasa | IC95 | vs azar |
|---|---|---|---|---|---|
| 1 | 4081 | 20 | 0.490% | 0.317-0.756% | 0.19x |
| 2 | 3710 | 38 | 1.024% | 0.747-1.403% | 0.39x |
| 3 | 3339 | 32 | 0.958% | 0.680-1.350% | 0.36x |
| 4 | 2968 | 27 | 0.910% | 0.626-1.320% | 0.35x |
| 5 | 2597 | 25 | 0.963% | 0.653-1.417% | 0.37x |
| 6 | 2226 | 20 | 0.898% | 0.582-1.384% | 0.34x |
| 7 | 1855 | 22 | 1.186% | 0.785-1.789% | 0.45x |
| 8 | 1484 | 26 | 1.752% | 1.198-2.555% | 0.67x |
| 9 | 1113 | 20 | 1.797% | 1.166-2.759% | 0.68x |
| 10 | 742 | 14 | 1.887% | 1.127-3.142% | 0.72x |
| 11 | 371 | 3 | 0.809% | 0.275-2.350% | 0.31x |

**Todos los pares del mismo dia**: 247 repeticiones en 24486 pares = **1.009%** (IC95 0.891-1.142%) contra 2.632% del azar -> **0.383x**.
z = -15.9, p = 1.12e-56.

La evitacion **depende de la distancia**: es mas fuerte en sorteos consecutivos y se diluye al alejarse.

### 3.2 Balanceo de conteos a largo plazo -- NO se sostiene

Si el operador equilibrara conteos, en ventanas largas los animales saldrian **mas parejo** de lo que dicta el azar: el indice de dispersion (varianza observada / multinomial) quedaria **por debajo de 1**, y de forma consistente al crecer la ventana.

| ventana (sorteos) | ventanas | indice de dispersion | IC95 de la media | lectura |
|---|---|---|---|---|
| 190 | 38 | **1.161** | 1.107 - 1.215 | mas desparejo |
| 380 | 19 | **1.142** | 1.031 - 1.253 | mas desparejo |
| 950 | 7 | **0.776** | 0.585 - 0.966 | mas parejo |
| 1900 | 3 | **0.792** | 0.364 - 1.221 | no se distingue del azar |

(Indice = 1.000 es exactamente multinomial, o sea azar puro.)

**Veredicto 3.2: NO CONFIRMADO / INCONCLUSO.** Los indices no son consistentes (1.16, 1.14, 0.78, 0.79) y las ventanas largas son solo 7 y 3 observaciones, con intervalos que cruzan el 1. Los huecos entre repeticiones tampoco apoyan el balanceo: su indice de dispersion es **1.083**, es decir por ENCIMA de 1, lo contrario de lo que produciria un mecanismo que equilibra conteos.

> **Correccion a lo que creiamos.** El proyecto venia asumiendo dos fuentes de senal: evitacion intradia **y** balanceo de conteos a largo plazo. Los datos de desarrollo solo sostienen la primera. El balanceo a largo plazo queda como **no demostrado**: no lo damos por muerto (falta potencia), pero deja de citarse como hecho establecido.

---

## 3.3 El mecanismo completo, y el techo que permite

La evitacion intradia no es un efecto suelto: es el tramo corto de **una sola curva de recencia**. Tasa de salida de un animal segun cuantos sorteos lleva sin salir (azar = 2.632%):

| hueco (sorteos sin salir) | n | tasa | vs azar |
|---|---|---|---|
| 1-1 | 7357 | 0.649% | **0.25x** |
| 2-2 | 7310 | 1.306% | **0.50x** |
| 3-3 | 7215 | 1.572% | **0.60x** |
| 4-5 | 14106 | 1.619% | **0.62x** |
| 6-7 | 13618 | 2.028% | **0.77x** |
| 8-9 | 13031 | 2.808% | **1.07x** |
| 10-11 | 12292 | 2.563% | **0.97x** |
| 12-14 | 17236 | 3.178% | **1.21x** |
| 15-19 | 25051 | 3.579% | **1.36x** |
| 20-29 | 38413 | 3.256% | **1.24x** |
| 30-44 | 39874 | 2.749% | **1.04x** |
| 45-69 | 39262 | 2.583% | **0.98x** |
| 70-109 | 26689 | 2.862% | **1.09x** |
| 110-179 | 12369 | 2.063% | **0.78x** |
| 180-299 | 4920 | 1.634% | **0.62x** |
| >=300 | 823 | 1.510% | **0.57x** |

Tres regimenes, no uno:

1. **Huecos 1-7 (mismo dia): fuerte supresion, hasta 0.25x.** Es la evitacion intradia.
2. **Huecos 12-29 (uno a dos dias y medio): elevacion, 1.21x-1.36x.** El operador **recicla** los animales con esa cadencia. Esto NO es intradia y el proyecto no lo tenia documentado.
3. **Huecos >=110: supresion otra vez, hasta 0.57x.** Un animal que lleva mucho fuera **tiende a seguir fuera**. Esto es lo **contrario** de un mecanismo que equilibra conteos, y es otra razon para retirar la hipotesis de balanceo.

### Techo alcanzable por mecanismo

Cada fila es un **oraculo**: se le entrega la tabla empirica ajustada sobre los MISMOS datos que evalua. Son techos **optimistas** (tienen sobreajuste a favor), asi que sirven de cota superior de lo que ese mecanismo puede dar.

| mecanismo | Top-1 | Top-3 | vs equilibrio (10%) |
|---|---|---|---|
| azar puro | 2.63% | 7.89% | -2.11 pts |
| solo evitacion intradia | 3.05% | 9.25% | -0.75 pts |
| solo recencia (curva de hueco) | 3.41% | 10.78% | +0.78 pts |
| recencia x hora | 4.12% | 11.47% | +1.47 pts |
| recencia x hora x veces-hoy | 4.13% | 11.66% | +1.66 pts |
| **ensamble_v2, desarrollo (walk-forward)** | 4.53% | 12.89% | +2.89 pts |
| **ensamble_v2, PRUEBA CIEGA** | 4.00% | **12.27%** | **+2.27 pts** |
| **ensamble_v2, carrera 1 ano** | 4.09% | 12.63% | +2.63 pts |

**Como se lee esta tabla.** La evitacion intradia sola da **9.25%**: por debajo del equilibrio, o sea **no alcanza para ganar dinero**. La curva de recencia completa sube a **10.78%** y coincide casi exacta con lo que mide `hazard_actual` (10.74%): ese modelo **es** la curva de recencia. Anadir la hora llega a **11.66%**.

El ensamble saca **12.27%** a ciegas, que es **mas** que el mejor de estos oraculos pese a que ellos juegan con ventaja (ajustados en los mismos datos). O sea: **de los 2.27 puntos de margen sobre el equilibrio, alrededor de 1.7 se explican por mecanismos que sabemos nombrar (recencia + hora) y el resto por estructura de secuencia que todavia no hemos caracterizado.** Eso ultimo es lo que hay que vigilar: es la parte del margen que no sabemos justificar.

---

## Que sabemos, que no sabemos, que descartamos

1. **La frecuencia por animal NO se desvia de la uniforme.** No existen 'animales calientes': apostar por frecuencia historica no da ventaja.
2. **El ganador anterior SI condiciona al siguiente, pero solo en la diagonal**: el sorteo repite el animal anterior el 0.639% de las veces contra 2.632% del azar (0.24x, z=-10.7). El chi2 de la tabla 38x38 completa NO lo ve (p=0.1966) porque diluye el efecto en 1369 grados de libertad: es el test equivocado, no la ausencia de senal.
3. **Markov de orden 2 es INCONCLUSO**, no negativo: con 7357 sorteos hay 0.13 observaciones por celda. No se puede afirmar ni descartar.
4. **El sesgo real y explotable es conductual**: dentro de una misma jornada el operador evita repetir animal. Dos sorteos del mismo dia repiten el 1.009% de las veces contra el 2.632% del azar (0.38x, z=-15.9).
5. **La jornada trae 11.34 animales distintos** contra 10.41 esperados por azar (z=+27.0). Esa es la grieta que explota el ensamble.
6. **El balanceo de conteos a largo plazo NO esta demostrado.** Es una CORRECCION a lo que el proyecto venia asumiendo: los indices de dispersion por ventana son inconsistentes y sus intervalos cruzan el 1, y el indice de los huecos es 1.083 (>1), lo contrario de lo que produciria un equilibrador. Toda la senal medible esta en la jornada.
7. **Lo que descartamos**: frecuencias fijas por animal (V1), y, en el reporte del Vector 3, la hipotesis de PRNG/LCG debil.
8. **Lo que no sabemos**: si el operador cambia de mecanismo. Por eso la carrera mensual y el SPRT en vivo son obligatorios, no opcionales.

---

## Regla pre-comprometida de vigilancia del ensamble

> **Decidida el 2026-09-15, ANTES de ver los datos futuros.**
>
> Si el modelo `hazard` supera a `ensamble_v2` en Top-3 durante **3 meses consecutivos** en la carrera walk-forward mensual (`herramientas/resultados/carrera_1ano.txt`), se abre revision de la ponderacion del ensamble. **Antes de eso, no se toca nada.**
>
> Dato que motiva la regla: en **2026-09** hazard hizo **12.1%** de Top-3 contra **11.6%** del ensamble. Es **un solo mes y no es significativo** -- por eso la regla exige 3 seguidos y no reacciona a este.
>
> Contador actual: **1 mes** (2026-09). Faltan 2 para abrir revision.

