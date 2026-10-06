# M4 — PRE-REGISTRO (escrito antes de mirar ningún resultado del motor)

Fecha: 2026-10-06. Agente M4 del enjambre "motor 2". Arnés: `../arnes.py`.

## Idea
Motor de aprendizaje automático (LightGBM 4.7) en formato animal-sorteo (38 filas por sorteo, etiqueta 1 si ganó),
APILADO sobre producción: `init_score = log PROD` y log PROD también como rasgo. El árbol aprende solo la corrección.
Objetivo: **softmax por sorteo** (logit condicional, objetivo propio: grad = p − y, hess = p(1 − p) dentro de cada
grupo de 38). Así la salida ya son 38 probabilidades que suman 1 (softmax de log PROD + corrección).

## Por qué falló el intento previo (top15_70, planes 4 y 5) y qué cambio
1. El plan 4 (binario) en realidad sumó +24 mbits en dev-B, pero se juzgó por Top-15 con Bonferroni (sin potencia).
   Aquí se juzga en mbits (Δ contra prod, IC 90 % por jornadas), como pide el arnés.
2. El plan 5 (LambdaRank truncado en 15) optimizaba un orden, no probabilidades, y empeoró (−4 mbits). Aquí NO se
   usa lambdarank: softmax por sorteo, que es la verosimilitud que se mide.
3. Se entrenó UNA vez con dev-A y se congeló. Aquí se reentrena cada mes (walk-forward) para seguir al operador.
4. 73 rasgos muy redundantes, 31 hojas, tasa 0,03 → riesgo de sobreajuste. Aquí: ≤ 7 hojas, mín. 400 filas por hoja,
   L2 = 10, tasa 0,05, ≤ 300 árboles, parada temprana con los últimos 60 días del PASADO y reajuste con todo el pasado
   al número de árboles elegido.
5. Binario + renormalizar no es la verosimilitud del sorteo. Aquí sí.

## Rasgos (todos con sorteos anteriores al que se predice)
Retraso en sorteos y en días (último y penúltimo); veces hoy y hora de su última salida hoy; veces ayer / anteayer /
hace 3 días y hora de la última salida de ayer; frecuencias en 12, 36, 120 y 360 sorteos; hora, día de la semana,
día del mes; número = día del mes, = día+1, = hora en reloj de 12 h; fue el primero de ayer / el primero de hace
3 días; RÉGIMEN: repeticiones y reciclaje de hoy hasta ahora, y de este día de la semana en las últimas 8 semanas,
y repetición media de los últimos 7 días; log PROD y su puesto; RD Internacional (h−1):30 y (h−2):30 del mismo
día (NaN si no hay dato; el CSV acaba el 2026-09-22).

## Entrenamiento walk-forward
Para cada mes calendario M de A.T: se entrena solo con filas de A.T con fecha < primer día de M (las de antes de
2000 no tienen PROD). Meses con < 90 días de entrenamiento: se usa PROD tal cual (solo afecta a ANTIGUO).

## Variantes (fijas antes de mirar)
- V1: todo el pasado, sin pesos.
- V2: ventana de los últimos 365 días.
- V3: todo el pasado, pesos que decaen con vida media de 180 días.
- V4: todo el pasado, vida media de 90 días.
- V5: la mejor de V1-V4 en AJUSTE, sin rasgos de RD (para ver si RD aporta o solo mete ruido).
Hiperparámetros: solo se pueden retocar mirando AJUSTE (como mucho una vez: hojas 7→15 o tasa 0,05→0,1).

## Mezcla
p ∝ PROD^(1−w)·M4^w, w ∈ {0,25; 0,5; 0,75; 1; 1,25}, elegido en ELECCION (lo pide el BRIEF; queda dicho que eso
hace optimista a ELECCION).

## Elección y criterio
- Se elige la variante (y w) con mayor Δmbits contra prod en ELECCION, exigiendo Δ > 0 también en AJUSTE.
- Pasa a PRUEBA26 solo si en ELECCION Δ > 0 con el extremo inferior del IC 90 % > 0. Si no: NO MEJORA y no se gasta.
- PRUEBA26 (una sola mirada, versión congelada): MEJORA si Δ > 0 e IC 90 % inferior > 0; DUDOSO si Δ > 0 pero el
  IC toca 0; NO MEJORA si Δ ≤ 0.
- Fuga: prueba de que los rasgos de la fila i no cambian al alterar seq[i:], y `A.chequear_fuga` con el reentrenamiento
  real (entrenar con el pasado del mes, predecir la fila i).
- Se muestra la importancia de los rasgos (ganancia) del último modelo.
