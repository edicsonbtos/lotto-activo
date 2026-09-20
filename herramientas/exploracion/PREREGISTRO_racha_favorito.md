# PRE-REGISTRO — ¿La racha del favorito informa?

Escrito el 2026-09-20 **antes** de correr nada sobre el histórico.
Origen: observación post-hoc en el marcador en vivo (87 pronósticos) donde
las rachas de 3+ dieron 16,7% de Top-3 contra 4,4% en rachas cortas
(Fisher p=0,083). Esa observación NO es evidencia: el corte se eligió
mirando los datos. Este documento fija la prueba honesta.

## Hipótesis

**H1.** La tasa de acierto Top-3 del ensamble es MAYOR en los sorteos donde
su favorito (#1) lleva 3 o más sorteos consecutivos siendo el mismo animal,
que en los sorteos donde lleva 1 o 2.

**H0.** No hay diferencia: la longitud de racha no informa sobre el acierto.

## Datos

* `historial.txt`, matriz walk-forward de `ensamble_v2` vía
  `modelo.predecir(datos, LE.W)` — el MISMO código que produce las
  predicciones en producción.
* **SOLO tramo de desarrollo**: índices `LE.W` (2000) a `LE.CORTE_FIJO`
  (9357). n ≈ 7357 sorteos. **El tramo de prueba (>=9357) no se lee.**
* La racha en el sorteo t usa únicamente predicciones de sorteos <= t, que a
  su vez sólo usan `seq[:t]`. No hay look-ahead.

## Definición de racha

`racha(t)` = número de sorteos consecutivos terminando en t (incluido) en que
`argmax(P)` es el mismo animal. Mínimo 1.
**No se resetea en frontera de día** (el fenómeno observado cruzó la
medianoche). Se reporta también la variante con reset, como descriptivo.

## Confusor que hay que controlar

La racha crece a lo largo de la jornada: el conjunto "no ha salido hoy" sólo
se achica de a uno por sorteo, así que las rachas largas se concentran al
final del día. Y la tasa de acierto YA depende de la hora
(`intradia_v2`: coeficientes `hoy_k1`=-1,41 … `hoy_k11`=+0,02).

**Esto es exactamente el artefacto que mató al HILO 1** (el "gradiente
intradía" resultó ser confusión con k). Por eso la prueba primaria va
estratificada por hora, no cruda.

## Pruebas (pre-especificadas, Bonferroni α = 0,05/3 = 0,0167)

| # | Prueba | Qué decide |
|---|--------|------------|
| **T1 (PRIMARIA)** | Mantel-Haenszel de `racha>=3` vs `racha<=2` sobre acierto Top-3, **estratificado por hora (12 estratos)** | ¿El efecto sobrevive al confusor horario? |
| T2 | Lo mismo, estratificado por **quintil de la masa de probabilidad del propio Top-3** | ¿Es información NUEVA, o sólo "sorteos que el modelo ya marcaba como buenos"? |
| T3 | Top-1 sobre el animal en racha | ¿Es el favorito repetido el que acierta, o el efecto vive en el #2/#3? |

Intervalos por **bootstrap de bloques de día** (2000 remuestreos), porque los
sorteos del mismo día están correlacionados.

## Criterio de falsación — COMPROMETIDO DE ANTEMANO

* Si **|z| de T1 < 2,0** → **la hipótesis se descarta.** Se archiva, no se
  buscan otros cortes, no se prueban otros umbrales de racha, y no se vuelve
  a mirar. Un umbral distinto elegido después de este resultado sería
  sobreajuste con otro nombre.
* Si **|z| de T1 >= 2,0 pero T2 no sobrevive** → el efecto es redundante con
  lo que el modelo ya sabe. No se toca nada.
* Si T1 **y** T2 sobreviven a Bonferroni → hipótesis **candidata**. Aun así:
  NO se cambia ninguna apuesta. Pasa a la cola de validación en el tramo de
  prueba, que sólo puede mirarse UNA vez más (ver `registro_final.jsonl`).

El umbral de racha es **3**, fijado aquí. La curva completa por longitud se
imprime como descriptivo, **no como menú para elegir un corte mejor.**

## Lo que este estudio NO puede concluir

Aunque salga positivo, no dice que apostar sea rentable: el equilibrio a 30x
sigue siendo 10% de Top-3, y el marcador en vivo va en 7,5% sobre 67 sorteos.
