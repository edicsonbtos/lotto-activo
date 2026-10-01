# Top-15 de los dos últimos sorteos con descarte: hoy, hermano y fríos (2026-10-01)

Carpeta: `herramientas/exploracion/top15_tarde/`. Reglas fijadas antes de medir en `PREREGISTRO.md`
(commit `cfda9c2`, sha256 `560cf4f6…`). El desarrollo se guardó en git (`eefae58`) antes de la prueba
ciega, y la ciega se corrió **una sola vez** (`registro.jsonl`). No se tocó producción.

## La idea
En los dos últimos sorteos del día (LA 18:00 y 19:00, RD 18:30 y 19:30) se sacan del Top-15:
**HOY**, lo que ya salió hoy en ese juego ("no repite"); **HERMANO**, el último resultado del otro juego
(para LA, el RD de la media hora anterior; para RD, el LA de la misma hora); y **FRÍOS**, los que llevan
más de 4 días sin salir. Suben los siguientes del orden del modelo.

## La respuesta corta
1. **La idea no sube el Top-15 de forma demostrable.** En la prueba ciega de 2026 (enero a septiembre):
   LA +2,3 puntos con IC [−1,5; +6,3] y RD −0,4 [−3,8; +3,0]. **NO PASA** en ninguno de los dos.
   En 2024-25 tampoco se vio nada: LA +0,2 y RD +0,9.
2. **El motivo: el modelo ya hace casi todo ese descarte.** A las 18:00 y 19:00, el Top-15 de RD trae
   **0** animales de los que salieron hoy y **0** del hermano. El de LA trae **0,85** de hoy y **0,3** del hermano.
   Lo que más cambia la idea son los fríos (1,4 por sorteo en LA y 1,8 en RD), y esos no conviene descartarlos (ver abajo).
3. **Sí hay una mejora real, y está en el hermano de LA en todas las horas, no solo en las dos últimas.**
   Si el animal que salió en RD a la media hora anterior está en el Top-15 de LA, hay que sacarlo y subir
   el 16º. Hoy la web solo lo baja del 5º al 6º, así que sigue dentro del Top-15. Con la regla, el Top-15
   sube **+0,8 puntos en 2024, +0,6 en 2025 y +1,3 en 2026**, los tres con IC por encima de 0.
   Ese animal está en el Top-15 en ~37 % de los sorteos y gana **la tercera parte** de lo que el modelo
   le da (2026: 10 veces contra 40 esperadas).
4. **El modelo actual se cree mejor de lo que es en 2026.** Dice que su Top-15 acierta 52,3 % en LA, y
   acierta 49,2 %. A las 18:00 y 19:00 dice 50,3 % y acierta 45,9 %. En RD dice 53,9 % y acierta 51,8 %.
   En 2024-25 estaba bien calibrado (LA 53,1 % contra 53,4 %). La brecha se va cerrando: en jul-sep 2026,
   LA da 49,7 % contra 50,8 %. Esto no cambia el orden ni el Top-15, pero los porcentajes que muestra la web
   en 2026 están 2 a 5 puntos altos.

## 1. Prueba ciega 2026 (pre-registrada, una vez; IC 98,75 % por 4 pruebas)

| | LA 18:00-19:00 | RD 18:30-19:30 |
|---|---|---|
| Sorteos (jornadas) | 529 (265) | 530 (265) |
| Top-15 actual | 45,94 % | 53,02 % |
| **H1, la idea tal cual** (hoy + hermano + fríos > 4 días) | 48,20 %: **+2,27** [−1,51; +6,26] | 52,64 %: **−0,38** [−3,77; +3,02] |
| Veredicto H1 | **NO PASA** | **NO PASA** |
| H2, la mejor de 2024-25 | hoy + hermano + fríos > 5 días: +2,08 [−1,32; +5,47] | hoy + hermano + fríos > 3 días: −0,19 [−5,09; +4,72] |
| Veredicto H2 | **NO PASA** | **NO PASA** |
| Por mitades (ene-may / may-sep), actual → H1 | 44,3 → 47,0 / 47,6 → 49,4 | 53,8 → 53,0 / 52,3 → 52,3 |

En LA el signo es positivo en las dos mitades, pero con ~530 sorteos el IC mide ±4 puntos, y una mejora real
de 1-2 puntos no se puede distinguir del azar. En 2024-25, con más del doble de sorteos, la idea dio +0,24
en LA. De las 23 variantes probadas en desarrollo, ninguna se separó del ruido.

## 2. ¿Por qué no rinde? Lo que sale de cada grupo (2026; entre paréntesis, 2024-25)

"Contra el azar" compara con 1/38 por animal. "Contra el modelo" compara con lo que el modelo ya les daba.
Si "contra el modelo" da ~1, el modelo ya lo sabe y descartarlos no añade nada.

| Grupo | Animales por sorteo | Salen, contra el azar | Salen, contra el modelo | En el Top-15 actual |
|---|---|---|---|---|
| LA, ya salió hoy | 10,1 | 0,88 (0,82) | **1,18 (1,10)** | 0,85 |
| LA, hermano (RD media hora antes) | 0,7 | **0,32 (0,73)** | **0,30 (0,67)** | 0,30 |
| LA, frío > 4 días | 8,1 | 0,83 (0,78) | 0,94 (0,94) | 1,37 |
| RD, ya salió hoy | 10,3 | **0,44 (0,43)** | 1,36 (1,00) | 0,00 |
| RD, hermano (LA misma hora) | 0,7 | **0,20 (0,37)** | 0,86 (1,23) | 0,00 |
| RD, frío > 4 días | 6,8 | **1,13 (1,13)** | 0,99 (0,93) | 1,76 |

- **"No repite" es cierto en RD, no en LA.** RD saca lo de hoy a menos de la mitad del azar, pero el modelo ya
  lo sabe: ninguno entra en su Top-15. LA sí repite: lo de hoy sale al 82-88 % del azar, y **más** de lo que
  el modelo cree. Descartarlo en LA no ayuda.
- **Los fríos de más de 4 días no se pueden descartar.** Son ~7-8 animales por sorteo. En LA salen algo menos que
  el azar, pero justo lo que el modelo espera. En RD salen **más** que el azar.
- **El hermano de LA es lo único que el modelo no sabe:** sale a un tercio de lo que el modelo le da.

## 3. La mejora que sí se sostiene: el RD de la media hora anterior fuera del Top-15 de LA

Análisis posterior a la ciega (`extra_posthoc.py`, descriptivo). Medido en todas las horas, porque en las
dos últimas solas hay muy pocos casos (0,3 por sorteo):

| Año | Sorteos LA | Top-15 actual | Con la regla | Diferencia [IC 95 %] | Retorno del ponderado |
|---|---|---|---|---|---|
| 2024 | 3.292 | 51,49 % | 52,25 % | **+0,76** [+0,33; +1,21] | +1,2 pp [+0,4; +2,1] |
| 2025 | 4.200 | 54,31 % | 54,93 % | **+0,62** [+0,21; +1,02] | +1,3 pp [+0,4; +2,1] |
| 2026 | 3.179 | 49,17 % | 50,46 % | **+1,29** [+0,79; +1,79] | +2,3 pp [+1,4; +3,2] |

Esto **no es un descubrimiento nuevo**. Es la misma regla que la web ya usa en el Top-5 (hilo 7, H4b),
y el estudio `top15_70` ya la incluía en su comparador "B1". Lo nuevo es la medida en el Top-15, que se
repite en tres años por separado. Cambiarlo en la web tocaría `servidor.py` (la lista del 6º al 15º y el botón
Compartir) y su marcador en vivo, como el de la regla del Top-5. **No se hizo: necesita tu OK.**

## 4. Hasta dónde llega el Top-15 (2026, horas 10-11)

| | LA | RD |
|---|---|---|
| Top-N para acertar el 50 % / 60 % / 70 % | 17 / 21 / 26 | 15 / 17 / 21 |
| Con la idea | 16 / 21 / 26 | 14 / 18 / 21 |
| Jugar plano todo lo que queda tras el descarte (~19-20 animales) | acierta 58 %, **−8,5 %** por ficha | acierta 67 %, +0,3 % por ficha |
| Top-15 ponderado (23 fichas), actual | −0,4 % por ficha | +2,1 % por ficha |
| Top-5 escalonado, actual | +14,1 % por ficha | −5,2 % por ficha |

En 2026, las 18:00 de LA empatan con las 13:00 como la peor hora del día para el Top-15 (42 %); las 19:00 dan 50 %.

## 5. Validación del modelo actual: lo que dice contra lo que acierta (Top-15, todas las horas)

| Trimestre | LA acierta / dice | RD acierta / dice |
|---|---|---|
| 2025 T3 | 57,2 / 54,9 | 55,6 / 54,0 |
| 2025 T4 | 54,1 / 56,6 | 54,9 / 54,8 |
| 2026 T1 | **49,3 / 54,7** | **51,7 / 55,0** |
| 2026 T2 | 48,4 / 51,6 | 50,9 / 53,6 |
| 2026 T3 | 49,7 / 50,8 | 52,7 / 53,2 |

Cuando el operador "evita repetir" con menos fuerza (2026), el modelo tarda en enterarse y se queda alto.
Recalibrar no cambiaría qué animales entran al Top-15, solo los porcentajes. El reentreno más seguido ya se
probó y no mejoró (`enjambre_2026-09-30/reentreno`).

## Datos y controles
- LA: `historial_la.txt` del enjambre (fechas corregidas). Coincide con la API oficial en 5.231 sorteos, con
  0 diferencias. Falta el sorteo 2026-06-24 de las 19:00.
- RD: `rdint_hist.csv` tiene **11 sorteos corridos un día** (2026-03-04 al 07, de 17:30 a 19:30): el CSV pone
  en el día d lo que la API oficial da para el día d+1. Aquí manda la API. El `rdint_historial.txt` de
  producción se sembró de ese CSV y probablemente arrastra el error.
- Predicciones walk-forward (`predecir.py`). Control de fuga de LA (corte 9357): diferencia 0,0. RD coincide
  con `cache_todo.npz` salvo en los días tocados por las correcciones (diferencia media 0,001).
- Todos los descartes usan solo el pasado: hoy (sorteos anteriores del día), hermano (RD (h−1):30 para LA,
  LA h:00 para RD, que sale 30 min antes) y días sin salir hasta el sorteo anterior.

## Archivos
`PREREGISTRO.md`, `predecir.py` (cachés en `cache/`, no van al repo), `top15_tarde.py dev|ciega`,
`resultados_dev.json` / `salida_dev.txt`, `resultados_ciega.json` / `salida_ciega.txt`, `registro.jsonl`,
`extra_posthoc.py` / `salida_posthoc.txt`.
