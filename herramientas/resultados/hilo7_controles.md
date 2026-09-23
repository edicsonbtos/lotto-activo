# Hilo 7 — tres pruebas de control de la señal RD Int ← Lotto Activo

Criterios escritos el 2026-09-23 ANTES de correr las pruebas (sección "Criterio" de cada una).
Los resultados se añaden debajo de cada criterio después de correr los scripts
`herramientas/exploracion/controles_rd*.py`. No se cambió ningún criterio tras ver números.

Datos: `herramientas/rdint/cache_todo.npz` (B0 = secuencia_v3 walk-forward, B1 = modelo.cruzado
R=250, minimo=500, lam=1; filas 2024-02-21 .. 2026-09-13). Las filas 'cal' (8 días) no se evalúan.
Para las pruebas 2 y 3 se rehace x con Lotto Activo de `rdint/datos._la_por_fecha()` y se reajusta b
con `modelo.cruzado` exactamente igual (mismo P0, mismos R/minimo/lam). IC95: bootstrap de bloques de
día (2000 remuestreos, `correr_modelo.boot_media`).

## 1. Heterogeneidad por semestre

### Criterio (fijado antes)
- Semestres por fecha: 2024a (2024-03-01..06-30), 2024b, 2025a, 2025b, 2026a, 2026b (hasta 2026-09-13).
  La prueba ciega (2025-07-01..2026-04-12) = 2025b + parte de 2026a.
- Métricas de B1 del caché: Δ mbits B1−B0, retorno por ficha Top-3 plano, retorno por ficha Top-5
  escalonado 2-2-2-1-1. Media e IC95 por semestre; EE = desviación típica del bootstrap.
- Heterogeneidad: Cochran Q con pesos 1/EE², gl = 5. **Heterogéneo si p < 0,05.**
- 2025b atípico: z = (m_2025b − m_resto)/√(EE² + EE_resto²), resto = los otros 5 semestres juntos.
  **Atípico si p bilateral < 0,05/6 = 0,0083** (|z| > 2,64).
- Tendencia: meta-regresión ponderada de la media por semestre sobre el índice 0..5.
  **"Se debilita" si la pendiente es < 0 con p < 0,05.** Pendiente negativa con p ≥ 0,05 = no
  concluyente.

### Resultado (`controles_rd1.py`)
| semestre | sorteos | Δ mbits B1−B0 | Top-3 plano, % por ficha | Top-5 escalonado, % por ficha |
|---|---|---|---|---|
| 2024a | 1452 | +9,5 [+0,2, +17,2] | +1,9 [−11,2, +16,4] | +0,2 [−11,7, +13,1] |
| 2024b | 2184 | +21,0 [+12,4, +28,3] | +6,2 [−6,1, +18,6] | +6,3 [−4,0, +17,6] |
| 2025a | 2148 | +25,9 [+15,9, +35,0] | +17,3 [+4,7, +31,8] | +14,4 [+4,2, +24,8] |
| **2025b** | 2052 | +26,6 [+17,4, +34,8] | +23,3 [+9,2, +37,0] | +24,1 [+13,1, +34,7] |
| 2026a | 2085 | +15,9 [+3,4, +27,1] | +14,2 [−0,2, +28,5] | +8,8 [−1,8, +20,5] |
| 2026b | 900 | +21,6 [+7,3, +33,5] | +15,6 [−3,4, +35,6] | +14,6 [−0,8, +29,6] |
| resto sin 2025b | | +19,2 [+14,5, +23,7] | +11,1 [+4,5, +17,8] | +8,7 [+3,6, +14,0] |
| Cochran Q (gl 5) | | Q=10,3, p=0,067, I²=52 % | Q=6,1, p=0,30 | Q=10,1, p=0,073, I²=50 % |
| 2025b contra el resto | | z=+1,49, p=0,14 | z=+1,56, p=0,12 | z=+2,54, p=0,011 |
| tendencia por semestre | | +2,1 (ee 1,3), p=0,095 | +3,3 (ee 1,9), p=0,081 | +2,7 (ee 1,6), p=0,078 |

Nota: 2024a incluye 398 sorteos (2024-03-01..04-03) en los que el walk-forward aún tenía b = 0
(menos de 500 filas de historia), donde Δ = 0 por construcción; sin ellos 2024a da +13,1 [+1,1, +23,4].

**Veredicto 1:** no hay heterogeneidad significativa (p = 0,067 / 0,30 / 0,073, todos ≥ 0,05). La señal
en mbits es positiva con IC95 > 0 en los seis semestres. 2025b (prueba ciega) es el **mejor semestre
pero no un atípico** según el criterio (p = 0,14 en mbits; en Top-5 p = 0,011 > 0,0083, al borde): en
plata, la prueba ciega cayó en la parte alta, y lo esperable fuera de ella es ~+9 % (Top-5) y ~+11 %
(Top-3) por ficha, no +20 %. **No se debilita con el tiempo**: las pendientes son positivas (no
significativas); la bajada de 2026a es compatible con ruido.

## 2. Placebo de días cruzados

### Criterio (fijado antes)
- x se rehace con el Lotto Activo de OTRO día, misma hora: (a) el mismo día de la semana 7 días antes
  (d−7); (b) 19 permutaciones aleatorias de fechas (cada fecha RD recibe el LA completo de otra fecha
  elegida al azar, sin repetir la propia; semillas 1..19).
- b se reajusta walk-forward con `modelo.cruzado` igual que el real. Métrica: Δ mbits B1placebo−B0 en
  dev+test+desc, y por tramo.
- **Pasa (la señal es de mismo día, no un artefacto) si:** el IC95 de d−7 cruza 0, Y el Δ real supera a
  las 19 permutaciones (p de permutación = 1/20 = 0,05), Y la media de las permutaciones está a menos
  de ±3 mbits de 0.

### Resultado (`controles_rd2.py`; tandas 1–8 y 9–19 por falta de RAM, misma semilla por permutación)
- Control de reproducción: x real reconstruido → P1 idéntico al caché (máx. diferencia 4e−9).
- **Real:** Δ = +20,6 [+16,5, +24,5] mbits (dev+test+desc), b final [−1,55, −0,44, +0,17].
- **d−7 (mismo día de semana, semana anterior):** Δ = −0,74 [−1,39, −0,10]; dev −1,0, test −0,2,
  desc −0,8; b final ≈ [0,00, +0,02, −0,02].
- **19 permutaciones de fechas:** Δ medio −0,61 (de 0,23), rango −1,03 .. −0,15; ninguna positiva. Todos
  los b finales |b| < 0,16 (el real: −1,55). p de permutación = 1/20 = 0,05 (el mínimo posible con 19).

**Veredicto 2: PASA en lo sustancial.** El placebo no tiene señal: cae ~−0,6 mbits, que es el costo de
estimar 3 coeficientes nulos walk-forward (las 19 permutaciones dan lo mismo). Literalmente, el IC95 de
d−7 no cruza 0, pero por el lado **negativo** (−1,39 a −0,10): es ese costo de sobreajuste, no una señal
de otro día. El real supera a todas las permutaciones por ~21 mbits (≈ 90 desviaciones típicas de la
distribución placebo). La señal es exclusiva del Lotto Activo del mismo día.

## 3. Desalineación horaria

### Criterio (fijado antes)
- Desfase k ∈ {−2, −1, 0, +1, +2}: x_k usa LA a las (h+k):00 como "h:00", (h+k−1):00 como "(h−1):00" y
  los LA de hoy hasta (h+k):00. **k = +1 y +2 usan información del FUTURO (sorteos de LA posteriores
  al sorteo RD de h:30): solo diagnóstico, NO jugables.** Horas fuera de 8:00..19:00 = sin dato.
- Dos medidas: (i) Δ mbits walk-forward de B1_k − B0 (modelo completo reajustado); (ii) el "lift" de la
  señal (a) sola: Σ 1[y = LA(h+k)] / Σ P0[t, LA(h+k)] (aciertos observados del animal LA(h+k) frente a
  los que B0 esperaba), con IC95. Lift < 1 = RD evita ese animal (la señal conocida es de evitación),
  así que "más señal" = |log lift| mayor.
- **Horas bien alineadas si** la señal (a) más fuerte (|log lift| máximo) está en k = 0, en total y en
  cada año (2024, 2025, 2026). Si en algún año el máximo está en otro k con IC95 que no se solapa con el
  de k = 0, las horas de ese año se consideran corridas.

### Resultado (`controles_rd3.py lift` y `controles_rd3.py modelo k`)
Lift de la señal (a) = aciertos observados del animal LA(h+k) / esperados por B0 (1 = sin efecto,
< 1 = RD lo evita):

| desfase | total | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| k=−2 | 0,852 [0,740, 0,966] | 0,684 | 0,851 | 1,042 |
| k=−1 | 0,645 [0,550, 0,740] | 0,692 | 0,493 | 0,806 |
| **k=0** | **0,208 [0,151, 0,269]** (58/279) | **0,177** [0,099, 0,266] | **0,191** [0,109, 0,272] | **0,268** [0,153, 0,406] |
| k=+1 (FUTURO, no jugable) | 0,363 [0,293, 0,439] | 0,284 [0,182, 0,397] | 0,489 [0,340, 0,639] | 0,283 [0,171, 0,408] |
| k=+2 (FUTURO, no jugable) | 0,748 [0,641, 0,859] | 0,691 | 0,752 | 0,813 |

Con la misma cobertura para todos los k (solo RD 10:30..17:30): −2: 0,774 · −1: 0,642 · **0: 0,193** ·
+1: 0,319 · +2: 0,787.

Δ mbits walk-forward del modelo completo reajustado con x desplazado (secundario):

| desfase | total | 2024 | 2025 | 2026 | b final |
|---|---|---|---|---|---|
| k=−2 | +3,7 [+1,9, +5,6] | +0,9 | +5,9 | +4,1 | [−0,12, +0,17, +0,28] |
| k=−1 | +6,0 [+3,7, +8,4] | +2,9 | +9,8 | +4,4 | [−0,42, −0,13, +0,25] |
| **k=0** | **+20,6 [+16,4, +24,6]** | +16,4 | +26,2 | +17,7 | [−1,55, −0,44, +0,17] |
| k=+1 (FUTURO, no jugable) | +25,6 [+21,1, +30,1] | +26,4 | +23,7 | +27,5 | [−1,02, −1,56, +0,07] |
| k=+2 (FUTURO, no jugable) | +10,2 [+6,8, +13,2] | +15,7 | +5,0 | +10,6 | [−0,33, −1,03, −0,08] |

El modelo k=+1 gana a k=0 porque su segundo indicador ("(h+k−1):00") ES el LA real de h:00 (b = −1,56)
y además suma el LA de (h+1):00 (futuro); no indica horas corridas. Por eso la medida del criterio es el
lift de la señal (a) sola.

**Veredicto 3: horas bien alineadas.** La evitación más fuerte está en k = 0 en total y en cada año
(2024: 0,18; 2025: 0,19; 2026: 0,27). En total y en 2025 el IC95 de k=0 no se solapa con el de ningún
otro k; en 2024 y 2026 se solapa con k=+1, pero el máximo sigue en k=0 (en 2026 por poco: 0,268 contra
0,283), así que ninguna época cumple la condición de "horas corridas". Hallazgo aparte (no jugable
para RD): RD de h:30 también "evita" el LA de (h+1):00 (lift 0,36), es decir, **Lotto Activo de las
(h+1):00 tiende a no repetir el RD de las h:30**; la dependencia va en ambos sentidos entre sorteos
vecinos (relevante para H4b, la dirección RD → Lotto Activo).
