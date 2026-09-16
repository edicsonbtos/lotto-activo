# Fase exploratoria 2026-09-15 — hilos 1-3

Todo medido **solo en desarrollo** (filas 2000-9357). El tramo de prueba (>=9357) no se
tocó: los scripts cargan `datos.prefijo(9357)`, así que esas filas no entran ni en memoria.
`registro_final.jsonl` sigue con las 4 entradas previas. md5 de `historial.txt`,
`predicciones.json` y `pesos_ensamble.json` idénticos antes y después.

Línea base: ensamble_v2 = **+120.07 mbits/sorteo** en desarrollo (Top-3 12.89%).
Ensamble sin secuencia_v3 = +113.33 mbits.

---

## HILO 1 — el gradiente intradía no existe: era confusión con la hora

### Qué ve intradia_v2 (`modelos/intradia_v2.py`, función `construir`)

| tabla | contenido | resolución |
|---|---|---|
| 1 | `HOY==1` × hora del sorteo actual (12) × ya-hubo-repetición-hoy (2) | 25 celdas |
| 2 | `HOY>=2` × (hora>=8) | 3 celdas |
| 3 | `~hoy & G==1` | solo cruzando día |
| 4 | `~hoy & DD<=2` × grupo de hora (4) | días desde la última salida |
| 5 | `~hoy & retraso en 20 tramos` (`GBINS`) | el hueco largo |

**El hueco dentro de la jornada no aparece.** La tabla 3 (hueco exacto = 1) está
condicionada a `~hoy`, así que solo actúa cruzando la medianoche. Para un animal que ya
salió hoy, el modelo ve la hora del sorteo actual y cuántas veces salió, nunca hace cuántos
sorteos salió. `secuencia_final` tampoco: su bloque `hoy` indexa por `k` (posición en la
jornada) × veces-hoy. Así que sí, **ambos son gruesos respecto al hueco intradía.**

### El gradiente medido (multiplicador vs. uniforme, desarrollo)

| hueco g (misma jornada) | obs | esp | mult | IC95 |
|---|---|---|---|---|
| 1 | 36 | 176.9 | 0.204 | 0.143-0.282 |
| 2 | 57 | 159.4 | 0.357 | 0.271-0.463 |
| 3 | 63 | 142.0 | 0.444 | 0.341-0.568 |
| 4 | 47 | 124.6 | 0.377 | 0.277-0.502 |
| 5 | 43 | 107.7 | 0.399 | 0.289-0.538 |
| 6 | 38 | 90.7 | 0.419 | 0.296-0.575 |
| 7 | 40 | 73.9 | 0.541 | 0.387-0.737 |
| 8 | 36 | 57.4 | 0.627 | 0.439-0.868 |
| 9 | 29 | 41.1 | 0.706 | 0.473-1.015 |
| 10 | 18 | 25.0 | 0.720 | 0.427-1.138 |
| 11 | 3 | 9.3 | 0.323 | 0.067-0.944 |
| **agregado** | 410 | 1008.1 | **0.407** | 0.368-0.448 |

Reproduce exactamente lo que dijo la fase anterior. **Y es un artefacto.**

### La auditoría (regla 4)

El bin de hueco `g` dentro de la jornada solo puede existir si `k >= g` (k = posición en la
jornada). Los bins altos están formados **únicamente por sorteos del final del día**, donde
la supresión se relaja. Hueco y posición están confundidos por construcción.

Test condicional correcto: restringido a los sorteos donde el ganador ya había salido hoy,
bajo la nula "el ganador es uniforme entre los candidatos que ya salieron hoy". Eso
condiciona en t y por tanto en k, hora y día. n = 410 sorteos.

| bin g | obs | esp | mult | z | p |
|---|---|---|---|---|---|
| 1 | 36 | 52.6 | 0.685 | -2.49 | 0.013 |
| 2 | 57 | 52.6 | 1.084 | +0.66 | 0.506 |
| 3 | 63 | 50.0 | 1.260 | +1.98 | 0.047 |
| 4-5 | 90 | 90.1 | 0.999 | -0.01 | 0.994 |
| 6-8 | 114 | 108.1 | 1.055 | +0.69 | 0.492 |
| 9-12 | 50 | 56.7 | 0.882 | -1.01 | 0.314 |
| veces hoy >=2 | 1 | 7.2 | 0.138 | -2.52 | 0.012 |

**No hay gradiente.** Sobrevive un resto en g=1 (0.685x) que no pasa Bonferroni de 6 bins
(p ajustado 0.076), y el efecto "veces hoy >= 2", que ambos modelos **ya tienen**.

El gradiente **real** es en la hora del reloj, y ambos modelos ya lo ven:
mult de "salió hoy" por hora = 0.00 (h1), 0.10-0.29 (h2-h9), 0.78 (h10), 0.83 (h11).

### Variante experimental

No se construyó `intradia_grad`: habría sido ajustar un modelo a un efecto inexistente.
En su lugar, sonda directa y más barata: se añadió al ensamble un cuarto componente que es
solo el indicador "salió en el sorteo inmediatamente anterior de HOY", con su peso ajustado
walk-forward igual que los demás.

**Aporte: +0.32 mbits, IC95 [-0.12, +0.73].** Nulo.

### Veredicto HILO 1: NO SUBE

El gradiente fino no existe; el que existe ya está capturado por la hora. El único candidato
vivo (g=1 intradía, 0.685x condicional) necesitaría ~4x los datos de desarrollo para
decidirse con |z|>=5 — unos 29.000 sorteos, ~8 años más de historial.

---

## HILO 2 — los 6.7 mbits de secuencia_v3 son la política de jornada

### Features (`modelos/secuencia_final.py` con `mismacol=False, mismacol2=False`)

- `gap`: hueco exacto 1..40 + tramos + "nunca", cadena suavizada (s=15)
- `hoy`: si salió hoy, `k` (posición en jornada, 1..11) × veces-hoy (1, 2+)
- `dias`: si no salió hoy y su última salida fue hace dd<=4 días, dd × k
- `cuota`: candidatos que salieron **ayer** y no hoy → cuántos animales de ayer ya salieron hoy, × grupo de k
- `g2`: penúltimo hueco 1..30 + tramos
- `bandas`: conteos en [38,200) y [200,700) (z bajo azar)
- `ventanas`: conteos densos cnt12, cnt38

### Dónde vive el aporte (delta pareado vs. ensamble sin secuencia_v3)

Aporte total **+6.74 mbits**, EE pareado 1.49 (z=+4.5), bootstrap por bloques de día
IC95 [+4.01, +9.35].

| estrato | n | delta mbits | IC95 |
|---|---|---|---|
| ganador con hueco 12-37 | 3349 | **+13.49** | +9.59, +17.38 |
| ganador con hueco 38-109 | 2221 | +4.42 | -0.17, +9.01 |
| ganador con hueco >=110 | 347 | +0.31 | -12.74, +13.37 |
| ganador con hueco 1 | 47 | -74.64 | -134.3, -15.0 |
| ganador **no** salió hoy | 6947 | **+7.19** | +4.34, +10.05 |
| ganador **sí** salió hoy | 410 | -0.99 | -21.49, +19.51 |
| k=1-3 | 1905 | **+17.66** | +11.14, +24.17 |
| k=0 (primer sorteo) | 635 | -10.61 | -21.01, -0.20 |

Nada en huecos largos (>=110). Todo en huecos medios y al principio del día.

### Ablación interna dentro del ensamble

| variante de secuencia_v3 | aporte al ensamble | IC95 | pierde |
|---|---|---|---|
| completo (referencia) | +6.74 | +4.23, +9.56 | — |
| sin `gap` fino (curva plana) | +6.80 | +3.58, +9.98 | **-0.07** |
| sin `ventanas` | +6.46 | +3.89, +9.04 | +0.28 |
| sin `dias` | +5.59 | +3.21, +8.01 | +1.15 |
| sin `g2` | +5.20 | +2.56, +7.89 | +1.54 |
| sin `bandas` | +4.53 | +1.92, +6.99 | +2.20 |
| sin `cuota` | +3.58 | +1.60, +5.62 | +3.16 |
| sin `hoy` | +2.40 | +0.45, +4.52 | **+4.34** |

El bloque `gap` fino — el que parecía la joya — no aporta nada.

### La prueba decisiva

| configuración | aporte | IC95 |
|---|---|---|
| completo | +6.74 | +3.89, +9.46 |
| **solo** bloques de jornada (hoy+dias+cuota) | +2.91 | +0.91, +5.10 |
| **sin ningún** bloque de jornada | **-0.14** | -0.86, +0.64 |
| sin jornada y sin bandas (gap+g2) | -0.30 | -0.86, +0.29 |
| solo gap | -0.20 | -0.72, +0.32 |

Quitando la jornada, secuencia_v3 **no aporta nada**. Las bandas de conteo y g2 solo pagan
cuando los bloques de jornada están presentes: son moduladores, no señal independiente.

Redundancia: corr(intradia_v2, secuencia_v3) = 0.886 sobre los logits centrados; el 17% de
la varianza de secuencia_v3 no la explica intradia_v2, y ahí es donde están los 6.7 mbits.

### Veredicto HILO 2: versión mejor parametrizada de f(DÍA)

No captura estructura adicional. Lo único que intradia_v2 no tiene y secuencia_v3 sí es el
bloque `cuota` (cuántos animales del conjunto de ayer ya salieron hoy), que vale ~3.2 mbits
— y sigue siendo política de jornada, no "secuencia".

**Se retira "estructura de secuencia sin caracterizar" de la lista de pendientes.** Los 0.6
puntos no atribuidos de Top-3 son la política de jornada resuelta con dos parametrizaciones
distintas que se promedian.

---

## HILO 3 — la frontera filtra, pero el modelo ya la ve

### 3.1 El reset no es limpio

| medida | obs | esp | mult | z | p |
|---|---|---|---|---|---|
| ganador del 1er sorteo de hoy ∈ conjunto de **ayer** | 125 | 182.8 | **0.684** | -5.07 | 6e-7 |
| placebo: ∈ conjunto de **anteayer** | 238 | 182.8 | **1.302** | +4.84 | 1e-6 |
| último animal de ayer repite en el 1er sorteo | 11 | 16.7 | 0.658 | — | ns |

La supresión **cruza la medianoche**, pero solo un sorteo: en k=1, 2 y 3 el multiplicador
respecto al conjunto de ayer es 1.09, 1.11 y 1.10 (todos ns). El placebo de anteayer sale
*favorecido* 1.30x — el reciclaje a 1-2.5 días que ya estaba documentado.

Comparación pedida: 0.684x cruzando el día vs. 0.204x en repetición inmediata intra-jornada.
El reset recorta la supresión a un tercio, no la elimina.

### 3.2 El último sorteo del día sí se comporta distinto

mult de "salió hoy" por hora: 0.00 (h1) → 0.10-0.29 (h2-h9) → **0.78** (h10) → **0.83** (h11).
Último de la jornada 0.859 [0.726-1.010] vs. no último 0.315 [0.278-0.355]. El operador
relaja la supresión en las últimas dos horas.

### 3.3 Jornadas de 11 vs 12 sorteos

El horario cambió el 2024-11-25 (se añadió el slot `hora 0`): 446 jornadas de 11, 632 de 12,
2 truncadas (5 y 7 sorteos). Multiplicador agregado de "salió hoy": 0.438 en jornadas de 11
vs 0.388 en las de 12 — IC solapados.

**Lo que ordena la supresión es la hora del reloj, no la posición k.** Alineadas por hora,
los dos regímenes coinciden (h10: 0.802 vs 0.776; h11: 0.899 vs 0.833). Alineadas por k, no
(k=9: 0.802 vs 0.255). Esto importa porque el bloque `hoy` de secuencia_final indexa por `k`,
no por hora — pero desde 2024-11-25 todas las jornadas son de 12 y k == hora, así que hoy
la corrección vale 0.

### 3.4 Cuantificación de la filtración

Sondas añadidas al ensamble como cuarto componente con peso ajustado walk-forward:

| sonda | aporte | IC95 |
|---|---|---|
| indicador "∈ conjunto de ayer" × k=0 | +0.14 | -0.39, +0.72 |
| indicador "∈ conjunto de anteayer" × k=0 | +0.32 | -0.68, +1.43 |
| ambos | +0.41 | -0.75, +1.46 |

El efecto es real (z=-5.07) pero **ya está dentro del modelo**: la tabla 4 de intradia_v2
(`~hoy & DD<=2` × grupo de hora) y el bloque `dias` de secuencia_final lo capturan.

### Veredicto HILO 3: frontera con filtración documentada, sin margen extra

### Variantes pre-registradas (4 pruebas, FDR Benjamini-Hochberg)

| variante | delta vs ensamble_v2 | IC95 | p | q |
|---|---|---|---|---|
| `cuota_kfull=True` | -1.13 | -1.87, -0.32 | 0.003 | 0.012 |
| `cuota_dd=[1,2]` | -0.95 | -1.68, -0.26 | 0.014 | 0.028 |
| `ddmax=6` | -0.27 | -0.85, +0.33 | 0.356 | 0.475 |
| `horabal=8` | -0.04 | -0.24, +0.16 | 0.723 | 0.723 |

Las cuatro negativas; las dos primeras significativamente peores.

---

## HILO 4 — no se hizo

Decisión del usuario (2026-09-15): saltarlo en esta fase. Requiere URLs o archivos con
historial de otras loterías de animalitos, que no existen en este repositorio.

---

## Propuestas archivadas para el post-SPRT

**Ninguna.** Los tres hilos están muertos:

| propuesta | delta medido | evidencia |
|---|---|---|
| intradia_grad (gradiente fino intradía) | +0.32 mbits, IC95 [-0.12,+0.73] | el gradiente era confusión con la hora |
| indicadores de frontera de jornada | +0.41 mbits, IC95 [-0.75,+1.46] | el efecto ya está en `dias` / tabla 4 |
| `cuota_dd=[1,2]` | -0.95 mbits | q(BH)=0.028, peor |
| `cuota_kfull=True` | -1.13 mbits | q(BH)=0.012, peor |
| `ddmax=6` | -0.27 mbits | ns |
| `horabal=8` | -0.04 mbits | ns |
| `hoy` indexado por hora en vez de k | no probado | k == hora desde 2024-11-25; delta esperado 0 |

El ensamble se queda como está. Esperar al SPRT en vivo (~día 92).
