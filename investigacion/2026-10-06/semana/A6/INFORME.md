# A6, abogado del diablo: ¿mié-vie es una estadística fantasma? (2026-10-06)
Pre-registro: `PREREGISTRO.md`, escrito antes de calcular y sin cambios después. Scripts: `fantasma.py` (salida
`salida.txt`), `datos_check.py` (`salida_datos.txt`) y `semana_motor.py` (`salida_semana_motor.txt`, exploratorio y
NO pre-registrado). Datos: `prod_0605.npz`, 2026 = 3.252 sorteos en 271 jornadas. z = contraste de la celda contra el
resto, estratificado por hora y contra lo que espera el motor. Nulo: 10.000 permutaciones de jornadas completas entre
fechas.

## 1. Búsqueda en otros lugares (Top-15, 2026)
Familia de 12 particiones, unas 110 celdas. Máximo |z| observado por partición: trío mié-vie 5,15; par jue-vie 4,01;
lun-vie contra fin de semana 3,91; hora × fin de semana 3,47; día de la semana 2,79 (jueves); hora 2,25; día del mes 1,91;
mes 1,71; las demás ≤ 0,44.
- En el nulo, el máximo |z| de toda la familia tiene mediana 2,48, p95 3,23 y p99 3,68. **p familiar = 0/10.000.** La
  aproximación de cola da unos 3·10⁻⁵.
- Un día suelto, estratificado por hora, da como máximo |z| = 2,79 (jueves), y la búsqueda nula ve algo así el 22 % de
  las veces. El z ≈ −4 del informe era crudo contra el motor: arrastraba la descalibración global de 2026 (O/E 0,94). Lo
  raro no es un día. Lo raro es que los tres días seguidos vayan juntos.
- La correlación dentro de la jornada no infla el resultado. La sobredispersión diaria es 0,90 en 2026 y 1,03 en dev.
- Nada indica una mala reconstrucción de los datos. El historial coincide con la API oficial: 4 diferencias en
  ~3.100 sorteos de 2026.
- El argumento "estable en 3 trimestres" vale poco. En el nulo, la mejor celda va en el mismo sentido en los 3
  trimestres el 80 % de las veces, y con una diferencia ≥ 0,10 de O/E el 27 %.
- **Advertencia clave.** En dev 2024-25, el mismo barrido da **domingo z −6,42**, un efecto aún más fuerte, que también
  supera la permutación. Ese efecto se apagó: 0,69-0,84 hasta abril de 2025, luego 0,94, y en 2026 ~1,0. Los efectos
  de día de la semana existen dentro de una era, pero ya hubo uno que desapareció.

## 2. Segunda reconstrucción y "vivo"
`vivo_rk.npz` NO contiene puestos congelados en vivo. Sus claves son rk, t, f, h y P: 10.716 sorteos, del 2024-03-07 al
2026-10-03. Es otra reconstrucción walk-forward (ensamble_v2 sobre hist_hoy, sin los ajustes de producción). Tiene una
fila menos que hist_0605 (2026-06-24 11:00), así que hay que alinear por fecha y hora. Su log P tiene una correlación de
0,989 con prod. En local no hay pronósticos congelados del marcador: viven en Railway y no hay acceso a la red.
- En esta segunda reconstrucción el patrón se repite. En 2026, mié-vie contra el resto da Top-15 z −4,72, Top-5 −3,06 y
  mbits −5,18.
- Desde el 15-sep: Top-15 O/E mié-vie 0,77 (43/108) contra 0,96 en el resto. Son 9 jornadas y ese tramo está DENTRO de
  la ventana del hallazgo, así que no es independiente.

## 3. ¿Depende de la métrica? No
Contraste mié-vie contra el resto en 2026, con IC 95 % por jornadas:

| Métrica | z | Diferencia | p de permutación | p familiar |
|---|---|---|---|---|
| Top-15 | −5,15 | −9,1 pp [−12,1; −6,0] | | |
| mbits | −5,46 | −96 [−132; −61] | | |
| Top-5 | −3,56 | −5,1 pp [−7,7; −2,6] | 0,001 | 0,018 |
| Retorno Top-5 escalonado | −3,17 | −29 % por ficha [−45; −13] | 0,001 | 0,054 |
| Top-3 | −2,27 | −2,7 pp [−4,8; −0,5] | 0,015 | 0,27 |

El efecto se debilita en Top-3 y Top-5 por falta de potencia, pero no cambia de signo. No es un artefacto del Top-15.

## Pista mecánica (exploratoria, post hoc)
Lo que más cambia es la repetición en el mismo día: animales que ya salieron hoy, y que el motor castiga fuerte.
- En 2026, contra el motor: mié 1,70, jue 1,52, vie 1,83; el resto de los días 0,67-0,84.
- En dev el día raro era el **domingo, con 1,62**, el mismo día en que el motor fallaba.
- El reciclaje de ayer y anteayer también baja en mié-vie (0,89 contra 1,07), pero con menos fuerza relativa.

Una hipótesis que une las dos eras: hay días en que el operador relaja el "no repetir hoy", y esos días cambiaron de
domingo (2024-25) a mié-vie (2026). El motor no lo sabe. Hay que probarlo en vivo, no en este tramo.

## 4. p honesto y potencia
- **p de "fantasma por búsqueda" dentro de 2026:** < 10⁻⁴. Aun multiplicándolo por 50 por todo lo que se miró antes,
  queda en ~10⁻³. No es ruido de búsqueda.
- **Lo que sigue abierto es si el efecto persiste.** El precedente del domingo dice que un régimen así puede apagarse
  en ~1 año.
- **Potencia 80 %, α = 0,05, si el efecto real fuera la MITAD (Δ = 4,6 pp de Top-15):** ~226 jornadas (~2.700
  sorteos, ~7,4 meses) con prueba unilateral, o ~286 jornadas (~3.400 sorteos, ~9,4 meses) con prueba bilateral. Con el
  efecto entero, bastan ~56-72 jornadas.
- **El plan en vivo ya registrado (7-oct a 6-ene, 92 jornadas)** tiene potencia 0,94 si el efecto es el entero, pero
  solo 0,48 si es la mitad. Con la mitad del efecto, su umbral "O/E ≤ 0,92" queda justo en el borde.

## Veredicto: REAL en 2026 (no es fantasma de búsqueda); persistencia DUDOSA
Por el criterio pre-registrado, es candidato REAL: p familiar < 0,01, 4 de 4 métricas con z ≤ −2 y la segunda
reconstrucción lo confirma. Pero la jugada no debe cambiar hasta el vivo. Recomendaciones:
- Alargar el plan a unos 8 meses, o añadir una prueba secuencial.
- Vigilar en sombra la "repetición del mismo día por día de la semana".
