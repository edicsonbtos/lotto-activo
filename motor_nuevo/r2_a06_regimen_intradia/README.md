# r2_a06_regimen_intradia: NO PASA (ángulo cerrado)

Pregunta: ¿la evitación de pares (las 6 transiciones de ag12 V1) y la no-repetición dentro del día cambian de fuerza
según la posición en el día (k 1-3 / 4-7 / 8-11), el fin de semana o los días de 12 frente a 11 sorteos?
El prerregistro (`PREREGISTRO.md`) se escribió antes de correr. Hubo 3 variantes y una ablación, en una sola corrida.

Modelo: reajuste completo con log P_ens como offset, λ=30, los mismos 5 bloques de jornada de ag02/ag12. Las variables son
las 33 de V1 + REPD (log1p de las veces que el animal ya salió hoy) + el grupo G (6 transiciones + REPD) multiplicado por
el indicador de régimen. Control: con las 33 variables se reproduce P_V1 (dif. máx. 2,0e-13).
Datos: solo filas [2000, 9357) (2024-03-07..2025-12-17), n = 7357. No se tocó el sellado ni las filas >= 9357. Tardó 15 s.

## Resultados (Δ mbits FRENTE A ag12 V1; IC95 por bootstrap de jornadas)
| Variante | Δ mbits [IC95] | mitad 1 | mitad 2 | Δ vs VR | forward vs V1-forward (b1-4) | Top-5 (V1 22,13 %) | Top-15 (V1 54,78 %) | Barra |
|---|---|---|---|---|---|---|---|---|
| **VA primaria** (tramo del día, 48 var) | **−1,08 [−2,13 ; −0,08]** | −0,66 | −1,51 | −0,26 [−1,13 ; +0,57] | −0,89 [−2,33 ; +0,39] | 22,06 % | 54,80 % | NO |
| VB (fin de semana, 41) | −1,20 [−1,89 ; −0,50] | −0,54 | −1,85 | −0,37 [−0,89 ; +0,18] | −1,11 [−2,24 ; −0,01] | 22,13 % | 54,70 % | NO |
| VC (días de 12, 41) | −1,07 [−2,15 ; +0,02] | −1,61 | −0,53 | −0,24 [−1,03 ; +0,59] | −0,65 [−1,46 ; +0,18] | 22,40 % | 54,86 % | NO |
| VR ablación (33 + REPD) | −0,83 [−1,35 ; −0,33] | −0,96 | −0,69 | — | −0,60 [−1,08 ; −0,14] | 22,20 % | 54,79 % | NO |

Top-3 VA 13,95 % (V1 13,85 %). Top-5 escalonado por ficha VA +35,02 % contra +34,92 %.

## Descriptivo (O/E frente a P_V1, sin decisión)
- Candidatos con alguna transición: O/E 0,98-1,005 en todos los regímenes (|z| < 0,6). P_V1 ya está calibrado en
  cada tramo del día, entre semana y fin de semana, y en días de 11 y de 12. **No queda heterogeneidad que sacar.**
- Ya salido hoy: k1-3 0,58 (z −1,99, 13 casos), k4-7 0,82 (z −1,65), k8-11 1,02; entre semana 0,88 (z −2,06), fin de
  semana 1,15 (z +1,62). Son pocos casos y z al borde de lo que da el azar con 14 celdas mirando.

## Lectura
- Los pesos de interacción tienen a menudo el mismo signo en los 5 pliegues (p. ej. T2×TAR −0,28; en VC las transiciones
  pesan más en los días de 12 = la época más reciente, lo que cuadra con que el mecanismo nació hacia 2022 y se fortalece).
  Pero los pliegues comparten el 80 % de los datos, así que ese acuerdo no prueba nada, y fuera de muestra ninguna
  interacción suma: todas empeoran P_V1 en −1 mbit, y el forward da entre −0,65 y −1,11.
- REPD (no-repetición dentro del día) no aporta: el ensamble ya la recoge (ablación −0,83).
- VC es la época del horario disfrazada (la mitad 1 es casi toda de 11 sorteos). Aunque la señal crezca con el tiempo,
  un peso por época no mejora la predicción del bloque que queda fuera.

**Veredicto:** la fuerza del mecanismo de pares es la misma a cualquier hora del día, cualquier día de la semana y con
11 o 12 sorteos, o al menos no varía lo bastante para medirlo. Ninguna variante pasa la barra (+3 mbits). No hay candidato
para el marcador en vivo.

Reproducir (PowerShell, desde la raíz del worktree lotto-activo-motor):
`$env:PYTHONIOENCODING='utf-8'; python motor_nuevo/r2_a06_regimen_intradia/experimento.py` (unos 15 s, un hilo, < 400 MB).
Archivos: `consola.txt`, `salida_experimento.txt`, `resultados.json` (con los pesos por pliegue), `P_VA.npy`.
