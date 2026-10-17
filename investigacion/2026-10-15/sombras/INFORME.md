# Modelos en sombra: sesgo, secuencial, plata y regla RD15 (2026-10-15)

Solo lectura. No se tocó `servidor.py` ni producción, y no se hizo commit.
Datos bajados de Railway el 14-oct a las 23:25, después del sorteo de las 7:00 p. m.: `/api/sombra`, `/api/sombra_decision`, `/api/cambio_rd15`, `/api/rdint`, `/api/mesa?offset=1..374` (carpeta `mesa/`) y el historial RD de `/?tab=rd&atras=1..130` (`rd_scrape.txt`).

Scripts de esta carpeta:
- `reconstruir.py` → `reg.json`
- `analisis.py` → `salida_analisis.txt` (semilla 20261015)

## 0. Por qué `/api/mesa?modelo=sombra` devuelve el ensamble

Producción corre el commit `f2f1769`. Ahí la función es `mesa_datos(offset)` y la ruta es `"/api/mesa": _api(mesa_datos, offset)`, así que no recibe `modelo` y el parámetro se ignora en silencio. `mesa1.json` y `mesa1_sombra.json` son idénticos byte a byte.

El soporte para `modelo=sombra` existe solo en la copia local sin commit: `sombra_registros`, `mesa_datos(offset, modelo)`, `mesa_stats(modelo)` y en `static/app.js` la pestaña `'-s'`. **No es un fallo del código: esa parte nunca se desplegó.**

Hoy producción no expone ag12 sorteo por sorteo. Por eso lo reconstruí: ver la sección 1.

## 1. ¿Tiene sesgo el marcador de sombra?

**Veredicto: no encontré look-ahead ni sesgo de selección relevante.**

### Cuándo se congela ag12
`preparar()` crea el pendiente solo si el sorteo no está en `sorteos_conocidos`. En esa misma llamada calcula `sombra_de(filas, pf, ph, sc_sombra(...))` con `filas`, que es el historial sin el sorteo que se pronostica, y lo guarda en el mismo registro que el ensamble.

`sombra.corregir` agrega un sorteo ficticio que no se lee. La auditoría del 2026-10-07 ya comprobó que `rasgos12` no usa filas futuras.

`deshacer()` reabre el registro sin recalcularlo. Si un pendiente quedó suspendido porque tenía un dato malo, se anulan **los dos** pronósticos juntos.

### Reconstrucción independiente
Recalculé ag12 para cada sorteo usando solo el historial anterior: `hist_ext.txt` hasta el 7-oct a las 12:00, más los ganadores de la mesa. Las probabilidades del ensamble salen del congelado de `/api/mesa`; a las 8:00, desde el 6-oct, les quité la corrección de las 8:00, que es multiplicativa y se puede invertir exactamente.

| | Top-3 | Top-5 | Top-15 | mbits | Neto Top-5 |
|---|---|---|---|---|---|
| Ensamble reconstruido (n = 226) | 24 | 38 | 106 | 86,75 | +52 |
| Ensamble en producción | 24 | 38 | 106 | 86,8 | +52 |
| ag12 reconstruido | 30 | 47 | 118 | 106,0 | +502 |
| ag12 en producción | 30 | 46 | 118 | 103,7 | +472 |

- **El ensamble coincide exacto.** ag12 queda a un sorteo de Top-5 y ~2 mbits.
- **Ese desvío va en la dirección contraria a una fuga.** El ag12 congelado en vivo rinde *menos* que el recalculado. La explicación esperable: hasta el 29-sep y el 3-oct, producción tenía el historial sin corregir (feriados corridos y el faltante del 24-jun). Eso es lo que se sabía en ese momento, no futuro.

### Mismos sorteos y empates
- **Mismos sorteos:** sí, sale de la misma lista `resueltas()`, con n = 226 para los dos.
- **Única exclusión: 2-oct, 8:00.** Ese registro no tiene sombra, probablemente porque falló `sombra_de`; no hay logs para confirmarlo. La exclusión depende de un fallo y no del resultado. En ese sorteo el ensamble puso al ganador 1.º y ag12 3.º, así que quitarlo favorece a ag12 en ≈ +1,3 mbits de media. Es poco, pero conviene registrar por qué falla la sombra.
- **Empates de puesto:** solo 1 en 227 (ensamble, 30-sep a las 10:00, puesto 14). ag12 no tiene ninguno. El desempate es por índice en los dos modelos. No influye.

### Otros detalles
- La base de la decisión es el **ensamble sin la corrección de las 8:00**, no el vivo actual. A las 8:00, desde el 6-oct, el vivo ya lleva la corrección de fecha y la de exposición. Esto respeta el preregistro, que se escribió antes de encenderlas, pero si ag12 pasa habrá que decidir si se apilan esas correcciones encima.
- **ag12 con RD** aplica RD (h−1):30 y (h−2):30 al puntuar. Los dos sorteos ocurren antes de LA h:00, así que no hay fuga.

## 2. Análisis secuencial

### ag12: regla preregistrada

**Regla:** mirada única con n ≥ 931 y fecha ≥ 14-dic. PASA si:
- el límite inferior del IC90 por jornadas de Δmbits es > 0, y
- el Top-5 en pp/ficha (punto) no es peor que −3.

Si a 931 no concluye y el punto es > 0, hay una sola mirada más a n = 3.500. Freno: si con n ≥ 600 el Δ es < −10, se apaga.

**Hoy:** n = 226, Δ = +16,9 mbits, EE = 14,9, z = 1,14 (p = 0,13). Para pasar, la media a 931 tiene que superar +12,1, así que los 705 sorteos que faltan deben promediar más de **+10,5 mbits**.

| Supuesto sobre el efecto verdadero | P(pasa a 931) | P(pasa a 931 o 3.500), simulación por jornadas |
|---|---|---|
| δ = 0 | 0,11 | 0,18 |
| δ = +5 | 0,26 | 0,52 |
| δ = +10 (lo que planifica el anexo) | 0,48 | 0,88 |
| δ = +16,9 (lo observado) | 0,78 | ≈1 |
| Bayes con prior plano | **0,65** | — |
| Bayes con prior escéptico N(0, 10²) | **0,33** | — |
| Bayes con prior según la evidencia previa N(6, 8²) | **0,43** | — |

- **Probabilidad realista de pasar el 14-dic: 35–65 %, según cuánto se le crea a la evidencia previa.** La sellada 2019-2023 dio −1,2; la ciega reciente, +19,4.
- La condición de Top-5 no frenó ninguna simulación: hoy va en +23 pp/ficha.
- **Fecha:** a 12 sorteos por día, n = 931 se alcanza hacia el **12-dic**. Por la regla, la mirada es el **14-dic-2026**. Si no concluye, n = 3.500 llega hacia julio de 2027.

**¿Se puede decidir antes?** No.
- La regla preregistrada no tiene mirada intermedia para adoptar; solo el freno por inutilidad, que no permite adoptar. **No se cambia.**
- Aunque se hubiera definido un gasto de alfa tipo O'Brien-Fleming (Lan-DeMets, α = 5 % unilateral), con información t = 0,24 la frontera sería z ≈ 3,98. Con Pocock sería ≈ 2,2. Hoy z = 1,14: ninguna frontera razonable se habría cruzado.
- **Nota técnica:** el plan de dos miradas (931 y, si el punto es > 0, 3.500, ambas con z > 1,645) tiene un error de tipo I real de **≈ 8,2 %** unilateral, no 5 %. No hay que corregirlo ahora, pero conviene saberlo al leer un "pasa a 3.500". Si se quisiera el 5 %, una enmienda **antes** de la mirada solo podría endurecer la frontera de 3.500 (z ≈ 1,96).

### ensamble_exp (exposición)

**Hoy:** n = 155, +7,7 mbits, IC90 [+0,6; +14,9]. La σ efectiva es 54 por sorteo; el preregistro suponía ~78.

- **La mirada a 930 es solo para apagar** (enmienda del 1-oct). Se apaga si Δ < −5 con n ≥ 600. P(apagar) ≈ 0 en cualquier escenario razonable. Fecha: ~**18-dic-2026**.
- **La decisión de encender es a n = 6.000**, hacia **feb-2028**. P(pasa mbits): 0,94 con prior plano, 0,88 con el prior del preregistro N(2,3; 2,6²) y 0,08 si δ = 0.
- **Ojo con la condición de Top-5:** hoy su IC90 es [−3,0; +1,0] y el límite exigido es > −3. Está justo en el borde.
- La exposición ya está activa en el vivo solo a las 8:00, dentro de la corrección de las 8:00.

### ventana_8am

**Hoy:** n = 11 mañanas, 0 aciertos en la ventana contra 0,72 esperados. Decide a 730, hacia oct-2028. El freno se mira desde 180, hacia abr-2027.

El "+39 mbits, IC90 [+35,5; +43,2]" de `/api/sombra` es un **artefacto**. Con 0 aciertos en la ventana, todas las mañanas suman casi lo mismo, así que el IC sale angosto y engaña. Un solo acierto en la ventana resta ~760 mbits. No significa nada todavía.

## 3. Plata, con los puestos reales

Mismos 226 sorteos desde el 26-sep. Pago 30. IC por bootstrap de jornadas (10.000). "Como se juega" aplica la regla RD al Top-5 y, desde el 7-oct, también al Top-15.

| Modelo | Top-5 2-2-2-1-1 (8 fichas) | Top-15 ponderado 3-3-3-2-2 + 1×10 (23 fichas) |
|---|---|---|
| Vivo congelado | +82 u (+4,5 %) IC90 [−352; +546] | −128 u (−2,5 %) IC90 [−726; +532] |
| **Vivo como se juega** | **+142 u (+7,9 %)** IC90 [−324; +652] | **−158 u (−3,0 %)** IC90 [−774; +532] |
| Ensamble sin 8:00 (base de la decisión) | +52 u (+2,9 %) | −158 u (−3,0 %) |
| **ag12** | **+502 u (+27,8 %)** IC90 [+68; +998] | **+652 u (+12,5 %)** IC90 [+38; +1.342] |
| ag12 + RD ×0,5/×0,75 | +502 u IC90 [+22; +1.056] | +652 u IC90 [−22; +1.416] |
| ag12 − vivo como se juega (pareado) | +360 u IC90 [0; +720] | +810 u IC90 [+240; +1.410] |

**Desde el 2-oct (n = 154):**
- `ensamble_exp` frente a `ensamble`: Top-5 0 u [−150; +150]; Top-15 ponderado +60 u [−180; +270]. En plata no se distinguen.
- `ag12_rd`: Top-5 +538 u; Top-15 ponderado +748 u.

**Cómo leer estas cifras:**
- Son ~19 jornadas y métricas secundarias.
- La ventaja de ag12 se concentra en el tramo del 3 al 14 de octubre. Del 26-sep al 2-oct, ag12 iba −56 u en Top-5.
- ag12 está reconstruido; en producción tiene ~30 u menos en Top-5.
- **El Top-15 ponderado con IC por encima de 0 no es la métrica preregistrada y no autoriza pasar ag12.**
- El vivo gana en Top-5 y pierde en Top-15 ponderado, igual que en la reauditoría del 14-oct.

## 4. Regla RD en el Top-15 (`/api/cambio_rd15`: n = 88, −30 u)

La reproduje exacta: sin la regla −194 u, con la regla −224 u, diferencia −30 u.

**Por qué va en −30:**
- De los 88 sorteos, la regla movió al ganador en 14 (la API cuenta 40 "cambios": las veces que el animal de RD estaba en el Top-15).
- En 13 de esos 14 el ganador subió un puesto **sin cambiar de escalón de fichas**, así que dieron 0 u.
- **Todo el −30 es un solo sorteo:** el 12-oct a las 7:00 p. m. El animal de RD de las 6:30 (35, Jirafa) estaba 6.º en LA, la regla lo bajó al 16.º y salió. Perdió su ficha: −30.
- El 16.º que entra no ganó ninguna vez.

**¿Está perjudicando al vivo?** No hay evidencia de daño.
- −30 u son 1,5 pp/ficha. Es exactamente un evento de 1 ficha.
- Con el efecto de la prueba (+1,6 a +2,5 pp/ficha), lo esperado en 88 sorteos era +32 a +50 u. La diferencia entre −30 y +40 son dos o tres eventos de una ficha: puro ruido.
- Aplicada desde el 26-sep al ensamble sin 8:00 (n = 208) da **+30 u** (+0,6 pp/ficha, IC90 [−60; +120]). Sobre ag12 da −30 u.
- LA repitió el animal de RD (h−1):30 en 5 de 208 sorteos (2,4 %), frente a 2,63 % del azar. Es justo la premisa débil de la regla: casi no hay ventaja que cobrar.

**Riesgo acotado:**
- Lo peor que puede pasar en un sorteo es −90 u, si el animal de RD estaba 1.º a 3.º y repite. En el Top-15 ponderado eso es 3 fichas de 23.
- Pero la parte 1.º a 5.º es la regla vieja del Top-5, que en vivo va **+60 u**.
- **La extensión del 6.º al 15.º solo arriesga 1 ficha por evento.**

Ni gana ni pierde de forma medible. Mantenerla no daña el vivo de manera apreciable, y quitarla tampoco mejoraría nada que se pueda medir.

## Recomendación

1. **No cambiar nada.** ag12 sigue en sombra hasta la mirada única del 14-dic. No hay base preregistrada, ni siquiera con O'Brien-Fleming, para adelantarla. P(pasa) ≈ 35–65 %.
2. Antes del 14-dic, una sola acción técnica: **dejar que se guarde el motivo cuando `sombra_de` falla.** El 2-oct a las 8:00 quedó fuera sin explicación. Hoy esa exclusión favorece levemente a ag12.
3. **Regla RD en el Top-15: mantenerla.** Las −30 u son un solo evento y caben de sobra en el ruido. Revisarla con n ≥ 600, igual que el resto.
4. Si se despliega la versión local (`modelo=sombra` en la mesa), probarla antes con `curl` contra el congelado, sin cambiar lo que se puntúa.
