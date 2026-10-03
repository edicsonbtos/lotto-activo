VEREDICTO: NULO

# ag09 — ¿La regla del primer sorteo se cuenta en días ABIERTOS y depende del día de la semana?

Scripts: `comun.py`, `explorar_dev.py`, `explorar_dev2.py`, `explorar_dev3.py` (solo dev/cal) y `probar.py` (la prueba
única). Pre-registro: `PREREGISTRO.md`. En dev se miraron unas 70 cosas: 16 O/E (k=1..4 × calendario/abiertos × era),
10 filas tras cierre, 28 celdas por día de la semana, 4 heterogeneidades, 8 grupos, la partición lun-vie/sáb-dom y
4 conteos crudos en 'cal'. A prueba fueron 2 candidatos.

## Datos: cierres y huecos (pregunta 4)
- Hay 14 cierres en 3 años: 11 de 1 día (24/25-dic, 31-dic/1-ene, Jueves/Viernes Santo, 28-jul y otros), uno de 2 días
  (2-3 abr 2026), uno de 4 días (25-28 jun 2026) y uno de 11 días (6-16 dic 2025). En todos, RD Internacional tampoco
  tuvo sorteos, así que son cierres reales y no datos perdidos.
- Hay 2 días incompletos: 2023-12-24 (5 sorteos) y 2023-12-31 (7). Son cierres tempranos de víspera, porque RD tiene
  6 y 8 ese día. Los dos caen en 'cal' y los dos van seguidos de un cierre, así que no hay casos de "ayer fue un día
  incompleto" que probar.
- Falta 2026-06-24 a las 7 PM en el volumen de producción. En la copia está, pero añadida al final del archivo, y
  `LE.cargar` la ordena. La regla del primer sorteo no se ve afectada: solo usa primeros sorteos, y el 06-25 fue cierre.
- No hay huecos de horas dentro de un día (todas las horas son consecutivas) ni días con 11/12 sorteos fuera de su era.
  **No encontré artefactos.**

## (1) Primer sorteo tras un cierre (todos los tramos, n = 14)
| | O | E bajo el motor (P sin ajuste) |
|---|---|---|
| gana el 1.º del último día ABIERTO | 0 / 14 | 0,26 (motor ≈ 0,008–0,03 por fila; 'cal' a 1/38) |
| gana el 1.º de hace 3 días ABIERTOS | 0 / 14 | 0,36 (con premio ×1,7: ≈ 0,6) |
| gana el 1.º de hace 3 días de calendario | 0 / 12 | 0,39 |

Con 0 observados y E ≈ 0,26, la razón de verosimilitud entre "esquiva" y "no esquiva" es ≈ 0,8. **No se puede saber.**
El motor ya le da a ese animal p ≈ 0,013, la mitad del azar, por el retraso en sorteos de `secuencia_v3`.

Caso raro en producción: tras un cierre de 2 días (2026-04-04), "hace 3 días de calendario" = el último día abierto.
Producción le dio ×1,736 al animal que, por días abiertos, debería llevar ×0,272. Ganó otro animal. Es 1 fila en 3 años.

## (2) ¿Días abiertos o de calendario en los días normales?
Coinciden en todo menos en las filas cercanas a un cierre: en dev, 7 filas para k=1 y 21 para k=3.
| dev, O/E contra P | 9:00 cal | 9:00 abiertos | 8:00 cal | 8:00 abiertos |
|---|---|---|---|---|
| k=1 (esquiva) | 0,23 (1/4,35) | 0,23 (1/4,37) | 0,00 (0/3,90) | 0,00 (0/3,97) |
| k=3 (premio) | 1,45 (9/6,23) | 1,44 (9/6,26) | 1,89 (19/10,07) | 1,78 (18/10,10) |

En las filas donde las dos reglas discrepan, la de calendario tiene 1 acierto (E 0,44, el 2025-07-29) y la de abiertos 0
(E 0,50) en dev. En prueba: 0 (E 0,16) contra 0 (E 0,39). Ninguna de las dos explica mejor los datos.

## (3) Día de la semana (descriptivo; heterogeneidad p_MC = 0,28–1,00 en las 4 pruebas)
- k=1: hay 0 o 1 observado en cada celda (E ≈ 0,6). La esquiva es total en todos los días y no hay nada que estratificar.
- k=3 en dev: el premio parecía ir solo de lun a vie, con O/E 2,16 (26/12,0) contra 0,47 en sáb-dom (2/4,3). Tenía el
  mismo signo en las dos eras (9:00: 1,79 contra 0,57; 8:00: 2,39 contra 0,40) y una binomial p = 0,012 sin corregir,
  con el corte elegido a posteriori. Pero el conteo crudo de 'cal' ya iba al revés: sáb-dom 4/1,34 y lun-vie 4/3,32.
- Lunes tras domingo: la lotería abre los domingos, así que el lunes es un día normal (k=3 lunes: 2,09 y 2,53, sin nada aparte).

## Prueba (una sola vez, contra P_aj, bootstrap de días)
| candidato | dev mbits/1.º sorteo | prueba mbits [IC 95 %] | p(≤0) | filas cambiadas | Top-5 | Top-15 |
|---|---|---|---|---|---|---|
| C1 días abiertos (×0,272 k=1; ×1,736 k=3) | −1,2 [−3,7; +0,3] | −0,62 [−1,51; +0,18] | 0,93 | 12 / 261 | 54 → 54 | 132 → 132 |
| C2 premio k=3 solo lun-vie (×2,117), sin premio sáb-dom | +6,2 (en la muestra) | **−14,5 [−30,4; −0,2]** | 0,98 | 254 / 261 | 54 → 49 | 132 → 128 |

- C2 en prueba se invierte: lun-vie O/E 1,14 (6/5,27) y sáb-dom 2,96 (6/2,03), binomial p = 0,97. En plata, el Top-5
  pierde −11,5 pp por ficha [−25,3; +2,3] y el Top-15 −3,1 pp [−6,1; −0,8]. Era ruido elegido a posteriori.
- C1 cambia muy pocas filas y la potencia es nula. Ningún acierto de Top-5 ni de Top-15 cambia en ningún tramo.
- Vivo (15 filas, solo se reporta): C1 no cambia ninguna fila. C2 da +35,8 mbits, con k=3 2/2 en lun-vie: sin valor.
- Referencia de la regla de producción en prueba: k=1 O/E 0,19 (1/5,36) y k=3 1,64 (12/7,30). Sigue en pie.

## Conclusión y recomendación
- La hipótesis no se puede decidir con estos datos. Solo hay 14 primeros sorteos tras un cierre en 3 años, y su efecto
  máximo posible es de ~0,5 mbits por primer sorteo. Los datos no distinguen la regla por días abiertos de la de
  calendario, y la variante por días abiertos no mejora nada medible.
- La fuerza de la esquiva o del premio no depende del día de la semana. El corte lun-vie/sáb-dom que salía en dev se
  invirtió en prueba.
- **Para producción: no cambiar nada.** Si se quiere ser defensivo, un cambio sin evidencia es no dar el ×1,736 cuando
  "hace 3 días de calendario" sea el último día abierto (solo pasa tras un cierre de 2 días; 1 fila en 3 años).
  Efecto esperado: ≈ 0.
