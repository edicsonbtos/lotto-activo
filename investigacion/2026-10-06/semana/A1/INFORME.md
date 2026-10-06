# A1 — Validación día por día del efecto "mié-vie" (2026-10-06)
Pre-registro: `PREREGISTRO.md` (escrito antes de calcular). Scripts: `a1.py` → `salida.txt` (pre-registrado);
`a1_mecanismo.py` → `salida_mecanismo.txt` (complemento descriptivo, NO pre-registrado).
Datos: `prod_0605.npz` (walk-forward de producción) e `hist_0605.txt` del scratchpad.

## 1. Día por día (Top-15 O/E contra el motor, IC 95 % por jornadas)
| | lun | mar | mié | jue | vie | sáb | dom |
|---|---|---|---|---|---|---|---|
| dev 2024-25 | 1,02 | 1,03 | 0,97 | 1,04 | 1,04 | 1,04 | **0,82** [0,76; 0,88] |
| 2026 | 0,99 | 0,98 | **0,85** [0,78; 0,93] | **0,82** [0,77; 0,88] | **0,84** [0,75; 0,92] | 1,05 | 1,03 |

2026, mié-vie contra sáb-mar: Top-15 O/E 0,84 [0,80; 0,88] contra 1,01; mbits +36 [+7; +63] contra +135; Top-5 16,1 %
contra 21,3 %; Top-5 escalonado −0,5 % por ficha [−13; +12] contra +29,8 % [+19; +41]. En dev, mié-vie daba +26 %.

## 2. Corrección por la búsqueda (20.000 permutaciones de la etiqueta de día entre jornadas de 2026)
- Peor subconjunto de 3 días: el observado (mié-jue-vie, 0,837) no lo alcanza ninguna permutación (p < 5·10⁻⁵;
  1 % del nulo: 0,876). Bloque consecutivo: igual. χ² de 7 días: 42,2 (p = 1·10⁻⁴). Máx |z| entre 63 subconjuntos
  de 1-3 días: 6,31 (p < 5·10⁻⁵; 99 % del nulo: 4,90).
- Control dev: también hay estructura por día (χ² p < 5·10⁻⁵), pero es el domingo.

## 3. Estabilidad
- 10/10 meses de 2026 con mié-vie < resto (diferencia −0,02 a −0,30). En dev: 7/22 (sin efecto).
- Vivo (≥ 15-sep, 9 jornadas mié-vie): 0,77 contra 0,96, dif −0,19 [−0,37; −0,03]. No es independiente:
  esos días ya entraban en la ventana donde se encontró el efecto.

## 4. Artefactos
- 2026 no tiene jornadas incompletas. Sin los 7 feriados (3 caen en mié-vie): 0,838 contra 1,009, dif −0,171
  [−0,227; −0,111]. Quitar los domingos no cambia nada.
- Por hora: 10/12 horas con mié-vie por debajo. Diferencia estratificada por hora −0,171 [−0,230; −0,113].
  Mañana −0,13, tarde −0,21.
- La masa del Top-15 del motor es casi igual todos los días (0,52-0,53): el motor no "sabe" que mié-vie es distinto.

## 5. Mecanismo (sin motor, solo el historial; descriptivo)
- La firma del operador se apaga en mié-vie de 2026. "Repite un animal ya salido hoy": O/E contra iid 0,64 en mié-vie
  y 0,30 en el resto. "Sale de ayer/anteayer": O/E 1,01 (como el azar) contra 1,15. Esos días se parecen al azar puro,
  y por eso el motor, que vive de esa firma, pierde su ventaja.
- **Lo mismo le pasaba al domingo en dev**: repite hoy 0,61-0,90 entre 2023-S2 y 2025-S1, y reciclaje 1,01. El
  domingo pasó a "estricto" en 2025-S2 (0,08), y en **enero de 2026** saltó mié-vie (dic-25 0,38 → ene-26 0,71). El
  cambio es abrupto y coincide con el cambio de año.
- Hipótesis: el operador alterna, según el día, entre un sorteo "gestionado" y uno cercano al azar, y el reparto de
  días cambió al menos dos veces (mediados de 2025 y enero de 2026).

## Veredicto
**Pre-registrado: DUDOSO.** Pasa los tres criterios: búsqueda p < 5·10⁻⁵, 10/10 meses, y robusto a feriados y a la
hora. Pero cae en la cláusula pre-registrada de no estacionariedad: el día "flojo" ya cambió de domingo a mié-vie.
**En sustancia, el efecto de 2026 NO es ruido ni artefacto**: es un régimen real del operador, que se ve en el
historial crudo sin el motor. Lo dudoso es su duración, porque podría volver a cambiar sin aviso (¿enero de 2027?).
Para usarlo, el motor debería detectar el régimen de cada día de la semana con una ventana reciente, por ejemplo
pesando "repite hoy" y "reciclaje" por día de la semana con unas 8 semanas, en vez de fijar "mié-vie" a mano. Esto
debe probarse en vivo (pre-registro del INFORME de reciclaje).
