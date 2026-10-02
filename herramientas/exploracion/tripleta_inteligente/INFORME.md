# Tripleta inteligente y la racha de las 8:00

Fecha: 2026-10-02. Reglas escritas antes de medir: `PREREGISTRO.md` (más anexos 1 y 2), con sus huellas en
`registro.jsonl`. No se tocó producción.

## En pocas palabras
1. **La tripleta es la jugada donde el motor rinde más.** Lo normal es que el casino se quede con ~10,6 % (con
   la apuesta simple se queda con 21 %), y el motor multiplica su ventaja por tres: acertar 3 animales en
   12 sorteos es acertar tres veces seguidas.
   Retorno por ficha de las 2 tripletas que muestra hoy la web (A):

   | Tramo | Retorno por ficha |
   |---|---|
   | 2025 (dev-B) | **+80 %** [+44; +120] |
   | abr-sep 2026 | **+97 %** [+44; +155] |
   | *Comparación: Top-5 escalonado simple* | *~+19 %* |

2. **Mejor jugar UNA tripleta (la 1-2-3) que dos.** La segunda (4-5-6) es más floja.

   | Tramo | Solo 1-2-3 (C3) | Diferencia con A |
   |---|---|---|
   | 2025 | **+121 %** | +41 pp [+2,5; +81], pasa |
   | 2026 | **+149 %** [+60; +247] | +51 pp [−3; +106] |

   Gana en los dos tramos y cuesta la mitad.
3. **La hora de compra no importa** (Q1: ninguna hora se distingue). La de las 8:00, que cubre el día entero,
   no es mejor.
4. **Sacar el número del día y el de mañana NO sirve en la tripleta.** En 2025 sumó +18 pp, pero en 2026 restó
   (−18 pp sobre A). La regla del anexo 1 la "adopta" porque C3 + lista negra quedó por encima de A. Pero el
   desglose muestra que lo que funciona es C3: la lista negra le resta (C3 sola +149 %, con lista negra +134 %).
   **Recomendación: C3 sin lista negra.**
5. **Por qué "no salió como pensabas":** una tripleta 1-2-3 acierta ~5 % de las veces, es decir, 1 de cada ~20
   días. Pasar 2 semanas sin cobrar ocurre la mitad de las veces y un mes entero, 1 de cada 5. Cada acierto paga
   45 fichas, así que la plata se hace en pocos golpes grandes.

## La racha de las 8:00
Datos hasta 2026-09-29, con el ensamble recalculado:
- Del 21 al 29 de septiembre, **las 9 madrugadas seguidas salieron en el Top-15** (puestos 2, 11, 8, 12, 6, 1,
  6, 10 y 12), y las 9 con un animal que había salido hacía 1-3 días. Desde el 14-09: Top-15 11/16, Top-5 3/16.
- **¿Es raro?** No tanto. A las 8:00 el Top-15 acierta el 60,8 % de las veces (es la mejor hora). 9 seguidas
  tienen una probabilidad del 1,1 %, y en el desarrollo hubo 2 rachas de 9 o más; la más larga fue de 16.
  Hueco de 1-3 días: 65 % de las madrugadas, y una racha de 11 aparece ~1 vez cada 372 madrugadas.
- **¿Sirve para la próxima?** No. Después de 3 aciertos seguidos, el siguiente acierta el 60,5 % de las veces
  (lo mismo de siempre). Después de 5 seguidos con hueco de 1-3 días, el siguiente lo tiene el 58 % de las
  veces, por debajo del 65 % normal. Las rachas no traen inercia.
- **Lo que sí vale:** las 8:00 son la hora con el Top-15 más alto (60,8 %, contra ~53 % del resto). "Hueco de
  1-3 días" no sirve para elegir: lo cumplen ~25 de los 38 animales, y el motor ya les da el 76 % de su
  probabilidad.

## Cómo usar mejor el dinero con esto
1. **Juega cada día solo la primera tripleta que muestra la web** (la 1-2-3). No hace falta cambiar nada.
2. **Tamaño:** ~0,3-0,5 % de la banca por tripleta. Sale de 1/4 de Kelly con la tasa más prudente (3,6 %, el
   límite bajo de 2026). Con una banca de 1.000 $, unos 3-5 $ por tripleta.
3. **Una al día, no varias seguidas.** Las tripletas de horas vecinas comparten sorteos y animales: si una
   falla, fallan todas juntas. Una por día (ventanas que no se pisan) es lo que deja medir y dimensionar bien.
4. **No dobles después de perder.** Con 1 acierto cada ~20 días, doblar te quiebra antes de que llegue el
   acierto.
5. **Pregunta en tu agencia la regla exacta** (¿12 sorteos desde que compras o hasta el cierre del día? ¿hay
   tripleta para RD Internacional?). Todo lo de arriba supone 12 sorteos seguidos desde la compra.

## Archivos
`medir.py` → `resultados.json`, `salida.txt` (2025). `replica_2026.py` → `replica_2026.json`,
`salida_replica_2026.txt` (corre una sola vez; anotada en `herramientas/registro_final.jsonl`).
`racha_8am.py` → `salida_racha_8am.txt`.
