# REPORTE ÚNICO — JORNADA 2026-09-16/17 (Lotto Activo)

Fecha del análisis: 2026-09-17 (~00:30 UTC) · Repo: `lotto-activo` · Producción: Railway `lotto-activo-production.up.railway.app`
Despliegue activo: `a3b0dd86` = commit **c23792f** (2026-09-16 14:45 UTC). Los commits posteriores (`67e3eb8`, `7886132`) **no están desplegados**.

---

## TAREA A — FORENSE DEL TOP CONGELADO

### A.0 Veredicto corto
El top "congelado" **no fue una falla de infraestructura**: las 11 predicciones del 16-09 fueron
recomputadas sorteo por sorteo con los pesos correctos y coinciden **exactamente** (conjunto y
orden) con lo que el modelo debió producir. El congelamiento *aparente* es una propiedad medida
del modelo (hazard por huecos) durante rachas de fallos. Sí se encontraron 4 defectos reales de
infra (abajo), ninguno de los cuales corrompió las predicciones de la jornada.

### A.1 Evidencia (logs + datos vivos + recomputo)

1. **Logs de Railway**: el servidor arrancó 2026-09-16T14:46:43Z y no ha vuelto a arrancar (sin
   crash-loop). Pero `servidor.py:835` silenciaba `log_message` y `registrar()` no tenía
   try/except: **el servidor corría sordo** — los logs solo contienen el banner de arranque. No
   hay trazas que correlacionar (defecto de observabilidad, no de causa).
2. **Contradicción con "caché vieja"**: la tabla histórica de la página viva muestra que el orden
   del top-3 **permuta** entre sorteos consecutivos ("24 4 23" → "24 23 4"). Una caché congelada
   serviría bytes idénticos. La clave de caché (sha1 de historial.txt + slot, `prediccion.py:129`)
   cambia con cada registro y cada slot.
3. **Recomputo forense** (`herramientas/exploracion/_forense_top16.py`, usa la ruta exacta de
   producción `prediccion.Predictor`):
   - Con los pesos reales `[0.516, 0.585, -0.059]`: **11/11 top-3 coinciden exactamente** con lo
     servido, incluidos los 4-6 sorteos de la ventana "congelada".
   - Con pesos uniformes (el fallback temido): **6/11 difieren** → el fallback **no ocurrió**.
   - El top-15 del slot vivo recomputado = el mostrado por la página (±0.05 pp).
4. **El "00" nunca fue el problema del día**: pesos vigentes (`frontera=12500 ≤ T`), píldora
   "ensamble activo", sin aviso de recálculo, contador creciente (12.515) y strip de resultados
   al día.

### A.2 Por qué el top se veía congelado (tasa base medida en desarrollo)
`herramientas/exploracion/_racha_top3.py` (dev walk-forward n=7.357):

| Evento | Probabilidad | Frecuencia esperada |
|---|---|---|
| Mismo **conjunto** top-3 ≥4 sorteos seguidos | 2,0 % de rachas | ~1 vez cada 5-6 jornadas |
| Mismo conjunto top-3 ≥6 seguidos | 0,2 % | ~1 vez cada 1,5 meses |
| Mismo **orden exacto** ≥4 seguidos | 0,3 % | ~1 vez cada mes |
| Conjunto estable ≥4 **y cero aciertos dentro** | 10,4 % de rachas perdedoras | común en rachas de fallos |

Mecanismo: el modelo es mayormente hazard (huecos binned, `BINS` en `servidor.py`); ningún
favorito salió (los que salieron fueron ranks 19-35), así que la cohorte de atrasados no cambia.
La segunda ocurrencia desde el deploy es **estadísticamente esperada**, no una alarma.

### A.3 Causa raíz de lo que SÍ está roto (defectos reales encontrados)
1. **Contenedor en UTC, sin `TZ`**: la página decía "hoy 8:00 AM" cuando en Caracas era la noche
   del 16 (labels "hoy/ayer" desplazados). La lógica de jornada es 100 % data-driven, así que no
   afecta predicciones ni marcador, pero confunde la operación.
2. **Commit `7886132` (pesos al volumen) sin desplegar + volumen sin semilla de pesos**: el
   despliegue actual lee `pesos_ensamble.json` del repo (bien), pero el día que se despliegue
   `7886132`, el volumen `/data` **no tiene** ese archivo (la siembra solo copia historial y
   predicciones) → fallback silencioso a pesos uniformes hasta que el hilo de recálculo escriba
   (1-3 min; para siempre si falla, p. ej. memoria). Los pesos uniformes sí aplacan el top
   (6/11 tops habrían sido distintos) — es decir, **este defecto latente ES capaz de producir
   exactamente el síntoma "top plano y repetitivo"**.
3. **Hueco del sorteo sin pronóstico**: `registrar()` resolvía el `pend` solo si existía; si el
   usuario registraba un resultado antes de que ningún render creara el `pend` (ventana de
   ~10 s de cálculo o doble registro rápido), el slot quedaba **sin pronóstico y sin puntaje**.
   Así ocurrió el **5PM del 16-09: hay resultado (31) pero ninguna predicción registrada**.
4. **Servidor sordo y `registrar()` sin try/except**: un fallo de escritura en el volumen hubiera
   congelado TODO (contador, strip, scoring) con únicamente un traceback en stderr.

### A.4 Fixes aplicados (solo infra; `herramientas/modelos/` y `pesos_ensamble.json` intactos)
- `prediccion.py`: `_pesos_guardados()` lee volumen primero y **cae a la copia del repo** si falta.
- `servidor.py`:
  - siembra de `pesos_ensamble.json` al volumen en el arranque (junto a historial/predicciones);
  - `TZ=America/Caracas` + `tzset()` al inicio;
  - `registrar()`: cierra el hueco del pend (si la predicción ya estaba en caché — calculada
    **antes** del resultado — se registra; sigue siendo honesto), try/except con **aviso explícito**
    si el volumen no escribe, y el `pend` ya no se pierde si falla el append;
  - `log_message` reactivado a stderr (Railway lo captura);
  - el último error del modelo (`PRED.error`) se muestra siempre, no solo mientras "calculando".
- **Pendiente de decisión del usuario**: commit + push + redeploy (no se toca git sin
  confirmación). Con el seeding incluido, desplegar ya es seguro.

### A.5 Sorteos de la jornada INVÁLIDOS para el SPRT — **ninguno por infra**
| Slot | Estado | ¿Cuenta para el SPRT? |
|---|---|---|
| 2026-09-16 h0-h8, h10-h11 (11 sorteos) | Predicción verificada fresca y correcta | **SÍ, válidos** (incluidas las pérdidas — excluirlas sería cherry-picking) |
| 2026-09-16 h9 (5PM) | **Sin pronóstico previo** (hueco del pend) | No puntúa (nada que invalidar; ausencia ya registrada) |
| Repeticiones (12×3, 30×2) | Resultados reales del operador | Válidos como datos; marcados para la vigilancia de política (Tarea B) |

Con el fix, slots futuros en la misma situación quedarán puntúados honestamente.

---

## TAREA B — AUDITORÍA ESTADÍSTICA DE LA JORNADA

### B.1 P(0/12) bajo tres escenarios — y corrección del hecho registrado
**Corrección con datos**: el top-15 **no** cerró 0/12. Con los top-15 reales por sorteo
(`_verifica_0de12.py`): **1/11** — el 4PM acertó (salió 10, rank 14). Solo existieron 11
pronósticos (falta el 5PM). Top-3: 0/11.

| Escenario | cálculo | P(jornada así) |
|---|---|---|
| (a) top-15 uniforme (h=15/38=39,5 %) | (1−0,395)^12 | **0,24 %** |
| (b) top-15 "vivo" (h dev medido = 53,07 %) | P(≤1/11) binomial | **0,33 %** (1 de cada ~306 jornadas) |
| (c) idem con 4 sorteos de predicción fija sin info del día | (1−0,5307)^9 efectivos | **0,11 %** |

Matiz obligado: en (c) **la premisa no ocurrió** — las predicciones no estaban congeladas ni
hechas sin información del día (A.1). Y la jornada se señala a posteriori entre muchas observadas
(selección): una jornada ≤1/11 en top-15 ocurre ~1 vez cada 306 jornadas (~10 meses), y hoy fue
señalada precisamente porque fue mala. **Lectura honesta**: es un evento de cola, no una rotura.
Vista top-3 (el marcador oficial): 0/11 con p=12,27 % tiene P = 21,9 % — totalmente normal. El
marcador vivo acumulado va 1/26 top-3 (3,8 %): P(X≤1 | modelo) = 15,4 % → sin evidencia contra
el modelo todavía.

### B.2 Repeticiones vs tasa base
Jornada 16-09: 12 salió 3 veces (12PM, 1PM, 7PM) y 30 dos veces (8AM, 2PM) = **3 eventos de
repetición** (uno de ellos gap-1, el más suprimido por la política medida).

| Modelo de repetición | P(≥3 repeticiones en una jornada) |
|---|---|
| Azar (1,59 repeticiones/jornada esperadas) | ~20 % |
| Política medida (supresión 0,41×; ~0,71/jornada) | **~2-3 %** |

El 16-09 el operador repitió notablemente más de lo que su propia política histórica sugiere
(detalles: `herramientas/resultados/politica_f2.md`), y lo hizo en los números que el modelo más
suprimía (30 a p=0,53 %, 12 a p=1,36 %). Con n=1 jornada esto **no decide nada**: una jornada así
se espera ~1 vez al mes bajo la política medida.

### B.3 monitor_politica.py ejecutado AHORA (dos pasadas)
- Estándar (hasta 2026-09-15, última ventana completa): **SIN ALARMAS**; desviación máxima
  |z| = 1,4 (umbral: |z|>3 dos ventanas seguidas).
- Con las 4 filas extra del volumen: mismo resultado (el CLI no acepta otra ruta de historial;
  la diferencia de 4 filas en ventanas de 500 no mueve ningún z).

### B.4 Veredicto explícito
**(i) Contaminación de infra: NO.** Las predicciones de la jornada son válidas y correctas; lo
que parecía congelamiento es comportamiento del modelo con tasa base del 2 % por racha.
**(ii) Evidencia real contra el modelo: NO todavía** — 1/26 vivo (p=0,15), la jornada es cola
(p≈0,3 %, con selección ~esperable), y 0/3 tripletas es ruido (necesita cientos de ventanas).
**(iii) Cambio de política del operador: NO DECIDIBLE con un día.** Lo que lo decidiría:
(a) alarma del monitor (2 ventanas |z|>3 consecutivas) — correrlo a diario; (b) replicar el
test A (repetición intradía, z=−19,8 en control) sobre scrape fresco de ≥2 semanas: si el z ya
no es fuertemente negativo, la anti-repetición se debilitó; (c) tasa de repeticiones por jornada
≥3 σ sobre 2-4 semanas. Hasta entonces, máxima vigilancia y cero cambios al modelo.

---

## TAREA C — ECONOMÍA DEL TOP-15 (desarrollo walk-forward n=7.357, pago 30x, apuesta igual)

| Top-N | Aciertos | Tasa | IC 95 % | Equilibrio N/30 | EV@30x | EV IC bajo |
|---|---|---|---|---|---|---|
| 1 | 333 | 4,53 % | 4,07-5,03 | 3,3 % | **+35,8 %** | +22,2 % |
| 3 | 948 | 12,89 % | 12,14-13,67 | 10,0 % | **+28,9 %** | +21,4 % |
| 5 | 1.490 | 20,25 % | 19,35-21,19 | 16,7 % | **+21,5 %** | +16,1 % |
| **15** | 3.904 | **53,07 %** | **51,92-54,20** | 50,0 % | **+6,1 %** | **+3,8 %** |

1. **¿Excluye el top-15 el 50 % con IC95? SÍ** — límite inferior 51,92 % > 50 % (z ≈ +5,3).
   El top-15 **no** es quemar banca en desarrollo…
2. **…pero es el peor uso de capital de todos**: el EV por unidad apostada decae monótonicamente
   con N (+35,8 → +28,9 → +21,5 → +6,1). El margen del top-15 se evaporaría con cualquier
   degradación pequeña del modelo (en prueba ciega el top-3 bajó de 12,89 % a 12,27 %; una
   caída proporcional del top-15 lo deja en ~50,6 % ≈ equilibrio).
3. Además el top-15 **tal como se muestra incluye el bin fantasma "00" en 43,2 % de los
   sorteos** (Tarea D): en esos sorteos se paga un cupo a un número que no existe.
4. **Recomendación formal**: mantener **top-3 plano con Kelly ¼** (ya implementado): p de entrada
   = límite inferior IC (12,14 %) → fracción 0,59 % de banca por sorteo. Si se quisiera más
   cobertura, top-5 (+21,5 %) domina a top-15 en EV y en robustez; Kelly ¼ top-15 daría 0,96 %
   con el margen más frágil del sistema — no recomendado. La regla del consejo ("no amplíes a
   5-10") queda corregida con números: ampliar a 5 no se pierde, pero **cada animal añadido
   diluye el EV**; 15 es sostenible solo mientras el modelo no se mueva un ápice.

---

## TAREA D — PASO 0 DEL TABLERO (verificado y documentado)

1. **Tablero real: 0-36, 37 números.** Muestra independiente de 1.800 sorteos scrapeados
   (`datos_multiloteria/lottoactivo.csv`, 3 fuentes): **cero "00"**. `tableros.json`:
   n_tablero=37, rango 0-36. El operador anuncia "38 figuras" pero en la práctica son 37.
2. **El token "00" existe solo en `historial.txt`**: 339 líneas (vs 337 de "0"), última el
   2026-09-03. Frecuencia combinada del bin 0 (676) ≈ **2,06× la mediana (328)** — el "2×"
   citado es artefacto de parsear `int("00")=0`: son dos tokens distintos de frecuencia normal
   cada uno (~1/38). En los HTML crudos el "00" solo aparece en horas de reloj.
3. **Lo que el modelo asume (K=38, `POS=["0","00",1..36]`) tiene el problema INVERTIDO al que
   suponía el encargo**: no hay colapso de 00 en 0; hay un **bin fantasma "00"/BALLENA** que
   ocupa un cupo del modelo y nunca puede ganar, y ~339 sorteos del Delfín (0) entrenaron en el
   bin equivocado. Impacto medido: el "00" está en el top-15 en **43,2 %** de los sorteos de
   desarrollo; todas las tasas de acierto y EV de la Tarea C están **subestimadas** por este
   cupo regalado, y el azar real es 1/37 (2,70 %), no 1/38 (2,63 %).
4. **Acción (post-SPRT, como se acordó)**: fusión 00→0 en la carga (K=37), reentrenar y
   reevaluar con `lotto_eval.py` en desarrollo. No se tocó nada del modelo en esta jornada.

---

## INTEGRIDAD Y PROTECCIÓN

- **MD5 de protegidos (antes = después, verificado al cierre)**: los 22 archivos de
  `herramientas/modelos/*.py` y `pesos_ensamble.json` (MD5 `078394FAF4D909B3BE62CFBAD5746E55`)
  **sin cambios**. Lista completa en la bitácora de la sesión (misma tabla antes/después).
- **Split de prueba**: **0 miradas nuevas** en esta jornada (no se corrió `--final` ni nada que
  puntúe el tramo de prueba). `herramientas/registro_final.jsonl` sigue en **4 líneas**.
  Todos los cálculos B/C corrieron sobre desarrollo [2000, 9357) y datos vivos.
- **Marcar sin borrar**: nada se eliminó. Se añadieron solo: 4 scripts de auditoría
  (`herramientas/exploracion/_forense_top16.py`, `_verifica_0de12.py`, `_racha_top3.py`,
  `_economia_top15.py`) y evidencia (`logs_railway_*.txt`, `logs_deploy_all.json`,
  `pagina_actual.html` en `herramientas/exploracion/`).
- **Cambios de código**: únicamente `servidor.py` y `prediccion.py` (infra). Sin commit
  (queda pendiente la confirmación del usuario para commit+push+redeploy).

## PRÓXIMOS PASOS RECOMENDADOS
1. Confirmar y desplegar los fixes (con el seeding de pesos, desplegar `7886132` deja de ser
   riesgoso).
2. Correr `monitor_politica.py` a diario; replicar test A con scrape fresco en ~2 semanas.
3. Preparar (post-SPRT) la fusión 00→0 / K=37.
4. Seguir registrando todos los sorteos; el marcador decide con ~1.000 predicciones.
