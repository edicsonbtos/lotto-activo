# ag10_comodin — prerregistro (escrito ANTES de correr el experimento principal)

Fecha: 2026-09-25. Rama `motor-nuevo`. Solo filas de desarrollo [2000, 9357) vía `arnes`.
Nada del tramo >= 9357 ni del tramo sellado (LA antes de 2023-09-04). Sin RD ni otras loterías.

## Por qué es nueva (revisión de lo cerrado)
Todo lo probado hasta hoy es **por animal y marginal** (hueco, veces hoy, salió hoy, conteos
móviles, día/hora: ensamble, Turing 308, hilo 9 techo) o **relativo a los últimos 1-3 ganadores**
(Markov 38×38 lag 1, docena lag k, vecino de tablero del último, y ag02: tablero de s1-s3,
sucesor/predecesor de s1 *la última vez*, par (s2,s1), ayer por hora/posición). Nadie probó la
**composición del día como conjunto** en relación con la historia de varios días:
(a) si el animal i y los animales YA salidos hoy salieron **juntos en un mismo día** hace poco
(co-ocurrencia de pares en la jornada, ventanas de 1, 2-7 y 8-30 días);
(b) cuántos animales de **ayer** ya se reciclaron hoy (cuota de reciclaje: interacción de conjunto,
que un modelo por animal como el ensamble no puede ver);
(c) transiciones **acumuladas** en 30 días (s1→i a lag 1 y s2→i a lag 2, contando todas, no solo la
última ocurrencia) y la precedencia ordenada dentro del día (b antes que i en días recientes).
ag02 (su hallazgo principal: evitar repetir el sucesor de s1) sugiere un operador "anti-déjà-vu" de
transiciones; esta idea generaliza ese mecanismo a la jornada completa y a memoria de varios días.

## Hipótesis
H1: Un término lineal `x·w` de 9 variables de composición/déjà-vu, sumado al logit congelado del
ensamble_v2 (peso 1), sube la log-verosimilitud en desarrollo: Δ >= +3 mbits, IC95 inferior > 0,
positivo en ambas mitades (barra de `arnes.evaluar`).
Esperado a priori: pequeño. Signo esperado: negativo en f1-f6 (el operador evita recrear pares/orden).

## Variables (candidato i, sorteo t; d = jornada de t; S = animales salidos hoy antes de t;
Y1 = conjunto de la jornada previa presente en el historial; todo con seq[:t])
- f1 `ayer_cooc`   = [i∈Y1] · |S ∩ Y1|
- f2 `sem_cooc`    = Σ_{b∈S} #{jornadas d' con d−7 <= d' <= d−2 (calendario) en que i y b salieron ambos}
- f3 `mes_cooc`    = Σ_{b∈S} #{jornadas d' con d−30 <= d' <= d−8 en que i y b salieron ambos}
- f4 `trans1_30`   = #{u < t, dia[u] >= d−30, u−1 >= 0: seq[u−1]=s1 y seq[u]=i}   (s1 = seq[t−1])
- f5 `trans2_30`   = #{u < t, dia[u] >= d−30: seq[u−2]=s2 y seq[u]=i}             (s2 = seq[t−2])
- f6 `orden_30`    = Σ_{b∈S} #{jornadas d' en [d−30, d−1] en que b salió antes que i}
- f7 `ayer_x_S`    = [i∈Y1] · |S|                   (control de f1: posición en la jornada)
- f8 `nsem_x_S`    = |S| · #{jornadas en [d−7, d−2] con i}  (control de f2: frecuencia de i)
- f9 `nmes_x_S`    = |S| · #{jornadas en [d−30, d−8] con i} (control de f3)
Se cuenta todo en jornadas de calendario (dia), así funciona con jornadas de 11 o 12 sorteos.

## Ajuste
- V1 (primaria, única que decide): logit condicional `log P_ens + X·w`, variables estandarizadas con
  media/desv. del bloque de entrenamiento, L2 λ = 30 sobre la suma de log-verosimilitudes
  (mismo λ fijo que ag02/hilo 9; no se ajusta), L-BFGS.
- Cross-fitting en 5 bloques CONTIGUOS de jornadas del desarrollo: cada fila se predice con w
  ajustado en los otros 4 bloques.
- Informativos (no eligen nada, se reportan): forward-chaining (bloque k con bloques < k; bloque 0 =
  ensamble); pesos por bloque; incremento de V1 SOBRE ag02 V1 (ensamble + 27 variables de ag02 frente a
  ensamble + 27 + mis 9, mismo cross-fit) para saber si lo que aporta es nuevo o duplica ag02.
- modelo.py: V1 ajustado con todo el desarrollo [2000, 9357) y congelado en `parametros.json`.

## Qué la falsaría
V1 no pasa la barra (Δ < +3 o IC95 inferior <= 0 o alguna mitad <= 0). No se añadirán variables ni se
cambiará λ tras ver el resultado; si se hiciera, se cuenta como variante y se reporta exploratorio.

## Desviaciones
- (antes de correr) Ninguna en V1.
- (después de ver V1) Se añadió `ablacion.py`, INFORMATIVA: 4 subconjuntos de las mismas 9 variables, mismo
  cross-fit y λ. No elige ni cambia el candidato (sigue siendo V1 completo). Mostró que la parte de
  composición del día (f1-f3, f6-f9) NO aporta por sí sola (+1,45 mbits, IC cruza 0) y que la ganancia
  viene de las transiciones acumuladas en 30 días (f4, f5).
- En el contraste informativo con ag02, las 27 variables de ag02 se estandarizan igual que las mías
  (ag02 las usa crudas), por eso ag02 re-ajustado aquí da +11,68 y no +12,15.
