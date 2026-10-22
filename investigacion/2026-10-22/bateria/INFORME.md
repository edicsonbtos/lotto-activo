# Batería 2026-10-22 — informe

Preregistro: `PREREGISTRO.md` (commit 4f3b8f4) y adenda (8e1c834), ambos antes de mirar las ciegas. Todo se reproduce
con los scripts de esta carpeta (semilla 20261022) y los `salida_*.txt`. El tramo de prueba ≥ 9357 no se tocó.

## 1. Hipótesis nuevas (7, Bonferroni)
| Rasgo (respecto al ganador anterior del mismo día) | O/E desarrollo | z | Veredicto |
|---|---|---|---|
| **H1 vecino de rueda americana (±1)** | **0,807 [0,72; 0,90]** (A 0,83 / B 0,79) | **−3,78** | **pasa desarrollo** |
| H2 mismo color | 1,033 | +2,43 | no |
| H3 misma docena | 0,952 | −2,51 | no (dev-A débil) |
| H4 número consecutivo | 0,856 | −2,69 | no (dev-B débil) |
| H5 número = mes | 0,858 | −2,00 | no |
| H6 número = día de semana | 1,080 | +1,13 | no |
| H7 ave tras ave | 0,886 | −1,77 | no |

Perfil exploratorio (no decide): solo cuenta el sorteo inmediatamente anterior y del mismo día. d1 0,81, d2..d18 ≈ 1,
el opuesto en la rueda (d19 = número consecutivo) 0,81, lag 2-3 ≈ 1, 8:00 contra el último de ayer 0,98.

## 2. Ciegas de H1
| Ciega | Resultado | Criterio | Veredicto |
|---|---|---|---|
| Vivo, ensamble congelado (n = 359, 14-sep..22-oct) | 12 obs / 19,7 esp, O/E 0,61; Δ +5,0 mbits, IC90 [+0,6; +9,3], p = 0,032 | p < 0,05 | **PASA** |
| Vivo, ag12+RD (n = 283) | O/E 0,68; Δ +3,9 mbits, p = 0,11 | mismo sentido | **PASA** |
| LARD, tramo ciego 2026-02-01..09-22 (n = 3.042) | O/E 0,93 [0,78; 1,07], p = 0,16 | p < 0,05 | **NO pasa** |
| RD, desarrollo de RD (descriptivo) | O/E 0,98 [0,87; 1,09] | — | sin efecto |

Lectura: es estructura propia del operador de Lotto Activo (h:00), igual que el "no repetir en el día". No se generaliza
a RD ni a LARD (que ya se sabía independiente).

## 3. Cuánto vale
Corrección ×0,807 a los dos vecinos de rueda del ganador anterior del día (no aplica a las 8:00):
- Desarrollo (in-sample): +1,5 mbits; Top-5 20,25 → 20,54 %; Top-15 53,07 → 53,43 %; Top-5 escalonado +1,7 pp de retorno.
- Vivo: +4,6 mbits (ensamble) y +3,6 (ag12+RD), pero Top-5/Top-15 bajan 0,3-0,5 pp: con n ≈ 300-400 el cambio de
  puesto de 1-2 sorteos domina. En aciertos es invisible antes de miles de sorteos.
- Conclusión: real pero pequeña. No cambia la jugada; candidata a **sombra en vivo** (como la exposición de fecha).

## 4. Pruebas del motor por otras vías (diagnóstico)
- Calibración por puesto (1-5, 6-10, 11-15, 16-25, 26-38): todas O/E 0,91-1,13, |z| ≤ 1,1. Bien calibrado.
- Hueco del ganador, "ya salió hoy", hora, día de semana: todo |z| < 2. Ninguna hora ni día es "mala" de forma real.
- **Número = día del mes: O/E 0,45 (ensamble) y 0,34 (ag12+RD), z ≈ −2.** La señal de fecha ya conocida se ve en vivo y
  ningún motor en producción la corrige.
- Permutación (barajar ganadores dentro de la misma hora, 1.000 veces): p < 0,001 en los dos motores. La señal es real.
- Rachas: P(≤ 3 aciertos Top-15 en 13 sorteos) según el modelo ≈ 2,6-3,6 % por ventana; en vivo 6/299 y 13/383
  ventanas. Lo de esta semana está dentro de lo esperado.

## 5. Síntesis (todo lo aprendido, en una frase por pieza)
El operador de Lotto Activo genera con un RNG certificado, pero aplica filtros de presentación que se pueden medir:
1. no repite animal en el día (fuerte; el motor lo captura);
2. recicla con 1-2,5 días de hueco (el motor lo captura);
3. el 1.º del día no repite el 1.º de ayer (aplicado desde el 4-oct);
4. esquiva el número de la fecha y de la hora (sin aplicar; en vivo O/E 0,34-0,45);
5. **nuevo: esquiva los vecinos de rueda y el opuesto del ganador anterior del mismo día (O/E ≈ 0,8; vivo 0,61).**
Todo esto suma unos pocos mbits. El techo medido (hilo 9, top15_70) sigue en pie: no hay un 70 % por sorteo.
El Top-15 realista queda en el 53-55 %.

## 6. Siguiente paso propuesto (no hecho: toca producción)
Poner en sombra, junto con la fecha, la corrección H1 (×0,807 a d=1) y medir en vivo con el marcador de sombra
(decisión a n ≥ 1.000). Antes, pasar `revisor-sesgo`. El "opuesto" (d19) entra solo en sombra como diagnóstico.

## 7. Desviación de los preregistros (decisión del usuario, 2026-10-22)
El usuario decidió aplicar al motor principal las capas 4 (exposición) y 5 (rueda) **sin pasar por sombra**
(commit bef95c0 y siguiente). Queda escrito que esto se aparta de:
- `herramientas/exploracion/top15_70/PREREGISTRO_sombra_exposicion.md` (encender la exposición con n ≥ 6.000; había ~240);
- la §6 de este informe (rueda en sombra y decisión a n ≥ 1.000).
Hay que tener en cuenta además que la decisión se tomó viendo el vivo, que exposición + ventana ya se habían mirado en el
tramo de prueba (registro_final.jsonl, 2026-10-03), y que el combinado ag12+RD+exposición+rueda nunca se evaluó walk-forward
como unidad (0,807 es O/E frente al ensamble). Los factores sí son limpios: MULT en dev-A y 0,807 en [2000, 9357).
**La única evidencia limpia desde ahora es la fila «principal» del marcador frente a «ag12 + RD en esos mismos sorteos»**
(empieza en n = 0). La prueba preregistrada de ag12 (14-dic) no cambia. Revisión: `revisor-sesgo`, «aceptar con cambios»;
los cambios pedidos (comparación pareada, textos, esta constancia) están aplicados.
