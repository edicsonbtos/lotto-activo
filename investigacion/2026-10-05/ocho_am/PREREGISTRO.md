# Pre-registro: sorteo de las 8:00 (2026-10-05, escrito ANTES de ver resultados)

Datos: historial del volumen hasta el 2026-09-29 7 PM (copia versionada en
`herramientas/exploracion/enjambre_2026-09-30/reentreno/historial_la.txt`). Del 30-sep al 5-oct faltan
horas anotadas a mano, así que esos días no entran. Las 8:00 existen desde el 2024-11-28.
Motor: walk-forward de `ensamble_v2` (`0_walkforward.py`) más `ajuste_primer_sorteo` = **B (producción)**.
Tramos: dev = filas < 9357 (hasta 2025-12-18), prueba = 2025-12-19..2026-09-14, vivo = 2026-09-15..09-29.
El tramo de prueba **ya se miró** en otras investigaciones; aquí solo se usa para confirmar hipótesis que
no se habían medido en él. La única confirmación limpia es el vivo posterior a hoy.

## H1. "A las 8:00 el operador trata lo que salió ayer como si hubiera salido hoy"
- Métrica: el ganador de las 8:00 ¿está en Y = animales distintos que salieron ayer?
  O/E crudo (contra |Y|/38) y O/E contra el motor B (suma de B sobre Y). IC 95 % de Poisson.
- Referencia "dentro del día": para los sorteos de 9:00 a 7:00 PM, O/E crudo de que el ganador esté entre los
  que ya salieron hoy.
- **La hipótesis se acepta** si el O/E crudo de las 8:00 en dev y en prueba queda por debajo de 0,5 y su IC no
  toca 1 (la referencia dentro del día debería estar cerca de 0). **Se rechaza** si el IC del O/E crudo contiene 1
  o queda por encima: entonces las 8:00 NO ignoran ni esquivan a ayer.
- Variante "lo ignora por completo": si el O/E contra el motor ≈ 1, el motor ya lo trata bien y no hay nada
  que ganar.
- Descriptivo: O/E por posición de ayer (8:00 ... 7:00 PM), crudo y contra el motor. Para que una posición
  pase a candidata hace falta |z| ≥ 3 contra el motor en dev (Bonferroni 12) y luego mismo signo con p < 0,05
  en prueba.

## H2. Sombras a las 8:00
- B → C (corrección fecha/hora, `exposicion.aplicar`) y C → C8 (ventana {día−1, día, día+1} × 0,59,
  `aplicar_8am`), SOLO en las 8:00: mbits por sorteo con IC 90 % por jornadas, Top-5 y Top-15, por tramo.
- Esto no decide nada: los pre-registros de sombra mandan (n ≥ 730 para la ventana y n ≥ 6.000 para C).
  Se informa.

## H3. Perfil del primer sorteo de hace k días (k = 1..10) a las 8:00
- O/E del motor B para "el ganador de las 8:00 = primer sorteo de hace k días" (k = 1 y 3 ya están en B).
- Candidata si |z| ≥ 3 en dev (Bonferroni 10) y mismo signo con p < 0,05 en prueba.

## H4. Retraso del animal (sorteos desde su última salida) a las 8:00
- O/E del motor B por tramos de retraso fijados de antemano: 1-12, 13-24, 25-36, 37-60, 61-120, > 120.
- Candidata con el mismo criterio (|z| ≥ 3 en dev con Bonferroni 6, p < 0,05 en prueba).

## Cómo se adopta algo
Nada de lo que salga aquí entra en la jugada. Una candidata que pase dev y prueba se ajusta SOLO en dev, se
audita con `revisor-sesgo` y va a sombra en vivo con su propio pre-registro.

---
*Nota posterior (auditoría): la fila 9357 parte el 2025-12-19, así que el 8:00 de ese día cuenta como dev. Es una sola fila. `2_tiempo.py` (cortes por trimestre) se escribió DESPUÉS de ver `salida_analisis.txt`: es exploratorio, no pre-registrado.*
