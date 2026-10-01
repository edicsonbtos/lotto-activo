# Camino 1: reentrenar seguido y dar más peso a lo reciente. Veredicto: NO PASA

**La idea.** El operador podría ir cambiando sus costumbres. Si fuera así, un motor que se reentrena más seguido
(cada semana) o que olvida más rápido lo viejo (memoria corta, o solo los últimos 6 meses) debería acertar más
en los meses siguientes.

**Lo que se hizo.** Las reglas se escribieron antes de medir, en `PREREGISTRO.md`, y no se cambiaron.
1. Se probaron 4 variantes **solo en el tramo de desarrollo** (2008 a 2025, filas 2000 a 9357). En cada una se
   entrenaba hasta un día, se predecía lo siguiente y se avanzaba, igual que en la vida real.
2. Se eligió la mejor y se miró **una sola vez** en los últimos 6 meses (2026-04-01 a 2026-09-29, 2.111 sorteos).
   La comparación fue contra el ensamble actual.

Los datos son una copia en esta carpeta: `historial.txt` con la corrección de fechas del 29-sep, más la API oficial
hasta el 29-sep. Se cotejaron 5.147 sorteos con la API y no hubo ninguna diferencia. No se tocó nada de producción.

## Desarrollo: ninguna variante pasa la barra
La barra exigía al menos +3 mbits, que el intervalo no tocara el 0 y que ganara en las dos mitades.

| Variante | Diferencia en mbits [IC95] | Top-5 | Top-15 | Pasa |
|---|---|---|---|---|
| Ensamble actual | 120,9 mbits (referencia) | 20,28 % | 53,13 % | — |
| V1: memoria corta (olvida 3 veces más rápido) | **−3,3** [−6,5 ; −0,4] | 20,02 % | 52,47 % | no (empeora) |
| V2: solo los últimos 6 meses | **−3,8** [−6,1 ; −1,5] | 20,25 % | 52,64 % | no (empeora) |
| V3: reentreno semanal | +1,4 [+0,5 ; +2,4] | 19,91 % | 52,96 % | no (muy poco) |
| V4: mezcla de memoria larga y corta | +0,6 [−0,2 ; +1,4] | 20,33 % | 52,74 % | no |

Olvidar el pasado **empeora** las predicciones. Reentrenar cada semana da una ganancia mínima, la mitad de lo que
pide la barra, y el Top-5 no sube.

## Confirmación única en los últimos 6 meses (V3 contra el ensamble actual)
Aviso: estos meses de Lotto Activo ya se habían revisado varias veces en otros estudios. Por eso esto cuenta como
**réplica débil**, no como prueba limpia. El juez final es el marcador en vivo.

| | mbits | Top-5 | Top-15 | Retorno por ficha, Top-5 escalonado | Retorno por ficha, Top-15 ponderado |
|---|---|---|---|---|---|
| Ensamble actual | 95,7 | 19,42 % | 49,12 % | +18,3 % [+7,6 ; +29,3] | +5,2 % [−0,3 ; +10,9] |
| V3 semanal | 95,1 | 19,66 % | 50,12 % | +20,4 % | +7,3 % |
| Diferencia V3 − actual | **−0,5** [−1,5 ; +0,5] | +0,24 pp | +0,99 pp [+0,33 ; +1,66] | +2,1 pp [−0,7 ; +5,0] | +2,0 pp [+0,7 ; +3,3] |
| Ensamble congelado al 31-mar (sin reentrenar) | 94,4 (−1,3 [−6,5 ; +3,6]) | 19,19 % | 50,07 % | +15,8 % | +5,6 % |

Por mes:

| Mes | mbits (actual / V3) | Top-5 (actual / V3) | Top-15 (actual / V3) | Retorno Top-5 escalonado (actual / V3) |
|---|---|---|---|---|
| Abril | 76,9 / 76,2 | 19,9 / 19,9 % | 48,2 / 49,1 % | +23,9 / +26,1 % |
| Mayo | 92,1 / 90,4 | 23,4 / 23,1 % | 49,7 / 50,5 % | +35,1 / +36,1 % |
| Junio | 66,9 / 67,7 | 17,0 / 16,7 % | 47,0 / 47,9 % | +4,9 / +6,1 % |
| Julio | 122,4 / 121,9 | 18,6 / 19,4 % | 50,5 / 51,1 % | +12,9 / +16,9 % |
| Agosto | 112,1 / 110,9 | 19,9 / 20,4 % | 51,6 / 52,7 % | +31,1 / +32,1 % |
| Septiembre | 97,1 / 97,5 | 17,2 / 17,8 % | 47,1 / 48,9 % | −0,9 / +2,4 % |

**Veredicto: NO PASA.** La medida principal fue mbits, que es la única con potencia suficiente. Dio −0,5, así que
el reentreno semanal no predice mejor. La subida del Top-15 (+1 pp) no cuenta, por tres razones:
- es una medida secundaria;
- en desarrollo, con 3,5 veces más sorteos, fue al revés (−0,17 pp);
- sale de una ventana que ya se había mirado.

Es el mismo tipo de espejismo que el del hilo 6. **No se adopta.**

## Lo que enseña
- **El operador no cambia de costumbre de un mes a otro.** Un ensamble congelado el 31 de marzo, sin reentrenar en
  6 meses, predice casi igual que el que se reentrena: −1,3 mbits, con un intervalo que incluye el 0. Si hubiera
  una deriva aprovechable, el congelado habría perdido claramente.
- El ensamble actual ya olvida a buen ritmo, unos 250 días. Acortarlo pierde información útil y alargar la
  frecuencia de reentreno no da nada. Esto coincide con `ag04_no_estacionario`, que el 25-sep tampoco encontró
  nada al acelerar los pesos.
- En los últimos 6 meses el ensamble rindió con el Top-5 escalonado: 19,4 % de aciertos y +18 % por ficha, con un
  IC que no toca el 0. El Top-15 llegó al 49 % de aciertos y el ponderado a +5 % por ficha, con un IC que sí toca
  el 0. **No hay forma de "asegurar" el Top-15:** con 15 de 38 animales, el azar ya da 39,5 % y el motor llega a ~49-50 %.
- La caída del Top-5 en vivo (16,8 % frente a 19,7 % prometido) no se explica por falta de reentreno. En estos 6
  meses, mes a mes, el Top-5 va de 17 % a 23 % sin ninguna tendencia. Es el vaivén normal de muestras pequeñas.

RD Internacional no se midió: su tramo de confirmación también está gastado y este camino ya falló en Lotto Activo.

## Archivos
- `PREREGISTRO.md`: las reglas, escritas antes de medir.
- `datos_la.py` y `bajar_ultimos.py`: arman la copia `historial_la.txt` (con `oficial_extra.csv` del 23 al 29-sep).
- `sub.py`: genera las predicciones de cada submodelo en `cache/`. Usa menos de 180 MB y tarda menos de 1,5 minutos cada una.
- `comun.py`: combina igual que `ensamble.py` y calcula las métricas.
- `eval_dev.py`: la elección en desarrollo. Escribe `dev_resultados.json` y `salida_dev.txt`.
- `confirmar.py`: la mirada única. Escribe `confirmacion.json`, `salida_confirmacion.txt` y `registro_confirmacion.jsonl`,
  y se niega a correr una segunda vez.
- Control sin fuga: las predicciones de desarrollo coinciden con las de la corrida completa (diferencia máxima 2e-9).
