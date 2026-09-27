# r2_a04_top15_optimo: NO PASA. El Top-15 por probabilidad de ag12 V1 ya es el óptimo (ángulo cerrado)

Pregunta: con la P de ag12 V1 fija, ¿se puede armar un Top-15 mejor que los 15 animales de mayor probabilidad?
El prerregistro (`PREREGISTRO.md`) se escribió antes de correr. Hubo 3 variantes y una sola corrida (10 s).
Datos: solo filas [2000, 9357), n = 7357. No se tocó el sellado ni las filas >= 9357.
Reproducir: `set PYTHONIOENCODING=utf-8 && python motor_nuevo/r2_a04_top15_optimo/experimento.py` (salida en `consola.txt`, `resultados.json`).

## Por qué, en teoría, no se puede (salvo que la P esté mal ordenada)
- En cada sorteo sale exactamente un animal, así que P(acierta el Top-15) = suma de las 15 probabilidades. No hay término
  de correlación: "sale i" y "sale j" son excluyentes. La correlación entre animales no puede mejorar un Top-N de un solo sorteo.
- Una recalibración monotónica aplicada igual a los 38 animales (temperatura, isotónica, Platt) no cambia el orden, así que
  deja el Top-15 idéntico. Comprobado (D4): con T = 0,7 y T = 1,5 el ΔTop-15 es exactamente 0,000000 y cambian 0 animales;
  solo empeoran los mbits (−16,17 y −14,98).
- Entonces solo reordenar puede ayudar, y solo si ag12 ordena mal en algún eje. Los diagnósticos dicen que no.

## Diagnósticos de P_V1 (IC95 por bootstrap de jornadas)
- D1: Top-15 esperado por la propia P = 54,95 % [54,81 ; 55,09]. Observado = 54,78 % [53,66 ; 55,94]. Observado − esperado
  = −0,17 pp [−1,28 ; +1,00]. La P predice bien su propio Top-15.
- D2: aciertos por puesto 1..38 frente a lo esperado: chi² = 32,1 (37 gl, p = 0,70). Ningún |z| > 2,2 (el peor es el
  puesto 30: 111 contra 136,0, z −2,17, lo esperable entre 38). Frontera 11-20: 2165 contra 2109,4.
- D3: fiabilidad por deciles de p: de 0,686 % → 0,597 % hasta 4,694 % → 4,593 %. Ligera sobreconfianza en los
  extremos, pero monótona, así que no cambia el orden.

## Variantes (cross-fit anidado en los mismos 5 bloques de jornada; control: el reajuste reproduce P_V1 con una diferencia máxima de 2,0e-13)
Referencia ag12 V1: +141,78 mbits, Top-15 54,78 %, Top-5 22,13 %.

| Variante | Δ mbits [IC95] | mitad 1 / mitad 2 | ΔTop-15 en pp [IC95] | mitades Top-15 | Forward (bloques 2-4, n=4560): Δ mbits / ΔTop-15 pp | Barra |
|---|---|---|---|---|---|---|
| V1 recalibración por puesto (primaria) | −2,95 [−5,29 ; −0,45] | −3,66 / −2,25 | −0,15 [−0,79 ; +0,53] (54,63 %) | −0,68 / +0,38 | −8,09 [−11,75 ; −4,56] / −0,11 [−1,03 ; +0,81] | NO |
| V2 mezcla geométrica con el ensamble | −0,80 [−1,36 ; −0,23] | −1,02 / −0,58 | +0,00 [−0,16 ; +0,16] (54,78 %) | −0,08 / +0,08 | −1,59 [−2,91 ; −0,22] / +0,07 [−0,35 ; +0,46] | NO |
| V3 sesgo por animal (38 interceptos, λ=30) | −0,81 [−3,29 ; +1,67] | +0,53 / −2,15 | −0,19 [−0,83 ; +0,48] (54,59 %) | −0,63 / +0,24 | −2,69 [−7,00 ; +1,64] / +0,07 [−0,85 ; +0,99] | NO |

Animales cambiados por sorteo en el Top-15: V1 1,34 · V2 0,09 · V3 1,49. Top-5: V1 22,16 %, V2 22,16 %, V3 21,78 %.
Top-5 escalonado Δ por ficha: V1 +0,36 pp [−2,25 ; +3,11] · V2 +0,00 · V3 −1,68 pp [−4,91 ; +1,64].
Parámetros de V2 por pliegue: (a, b) ≈ (+0,02, +0,04), (+0,02, +0,02), (+0,01, +0,04), (+0,01, −0,03), (+0,00, +0,00). La mezcla
óptima con el ensamble es casi cero: ag12 ya contiene lo que el ensamble aporta. V3: desviación típica de los sesgos por animal
0,08-0,09 y cambia de signo entre pliegues (ruido).

## Veredicto
Ninguna variante supera al Top-15 por probabilidad de ag12 V1. Todas tienen Δ mbits ≤ 0 y ΔTop-15 con IC que cruza 0.
La P de ag12 V1 está bien calibrada en el orden (D1, D2) y la teoría dice que, con una P calibrada, los 15 de mayor p son
el Top-15 óptimo. Para subir el Top-15 hace falta más información (mejor P), no otra forma de elegir los 15. Ángulo cerrado.
