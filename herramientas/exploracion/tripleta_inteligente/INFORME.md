# Tripleta inteligente y la racha de las 8:00

> **ACTUALIZACIÓN 2026-10-02 — la prueba ciega NO PASA (anexo 3).** En el único tramo que nunca se miró para
> esta tripleta (2025-12-18..2026-03-31, 102 jornadas), la 1-2-3 sola (C3) dio **+26 % por ficha [−52; +124]**
> (2,80 % de aciertos; al azar, 1,89 %), y quedó **por debajo** de las 2 tripletas de la web (A: +46 % [−11; +112]).
> **No se cambia la web**, y queda retirado el consejo de "jugar solo la primera": lo que se sostiene es la
> jugada actual (A). La tripleta tiene ventaja en los tres tramos medidos (+80/+97/+46 % para A), pero su
> tamaño es incierto y en el tramo ciego el IC cruza 0. Tamaño prudente: 0,3 % de la banca por tripleta como máximo.


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
1. ~~Juega cada día solo la primera tripleta~~ **RETIRADO por la prueba ciega:** sigue con las 2 tripletas de la web.
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

## Por qué las 8:00 aciertan más (y dónde se repite)
`porque_8am.py` → `salida_porque_8am.txt` (desarrollo, descriptivo).
- **A las 8:00 el operador trata lo de AYER como "reciente".** Los animales que salieron ayer salen a las 8:00 la
  **mitad** de lo normal (O/E 0,50), y los de hace 2-3 días **un 54 % más** (O/E 1,54). En las demás horas, lo de
  ayer sale normal o más (O/E 1,0-1,6). En la primera hora el reparto queda más "cerrado" y el motor lo aprovecha:
  le da a su Top-15 un 57 % de masa, la más alta del día.
- **Se repite en el primer sorteo de RD Internacional:** las 8:30 son la mejor hora de RD (Top-15 56,8 %,
  contra 45-52 % en casi todas las demás). Es el mismo fenómeno de "primer sorteo del día".
- Otra hora alta en los dos juegos: **17:00 en LA (56,1 %)** y **17:30 en RD (55,8 %)**. No tiene explicación
  clara: puede ser casualidad, y el plan 7 (elegir horas con dev-A) no lo confirmó.
- No hay otro "reinicio" en el día, así que el 60 % de las 8:00 no se puede fabricar en otra hora.

## Qué significa que "a las 8:00 lo de ayer cuenta como reciente" (2026-10-02, descriptivo)
`memoria_operador.py` → `salida_memoria_operador.txt` y `regimen.py` → `salida_regimen.txt`.
- **El operador lleva una lista de "recién salidos" y los esquiva.** Dentro del día esa lista son los sorteos de
  hoy: los últimos ~6 se esquivan mucho (O/E 0,20-0,44) y del 7.º al 10.º atrás, menos (0,52-0,68).
- **La noche borra la lista**, salvo en las 8:00. De 9:00 en adelante, lo de ayer sale normal o un poco más
  (O/E 1,1-1,6: es el "reciclaje"). A las 8:00, en cambio, la lista que usa es la de AYER: lo de ayer sale la
  mitad (0,50) y lo de hace 2-3 días un 54 % más.
- **No es "el primer sorteo del día", es el de las 8:00.** Antes de nov-2024 el primer sorteo era el de las 9:00,
  y NO esquivaba lo de ayer (O/E 0,98, Top-15 47,5 %). Las 8:00 se añadieron en nov-2024 con su propia regla.
- **El animal de las 8:00 queda "quemado" el resto del día**, más que cualquier otro: O/E 0,21, contra 0,46 del
  de las 9:00, y 0,59 de lo que espera el motor. El motor ya lo manda al fondo: en desarrollo nunca entró en el
  Top-5 de las horas siguientes, así que esto no cambia la jugada.
- **RD tiene su propia memoria**, que sí cruza la noche y se va apagando (repetir el de anoche: 0,24). Cada juego
  está configurado aparte.
- **La fuerza de la estructura cambia por épocas y dura meses.** mbits mensuales del ensamble: jun-nov 2025
  entre 150 y 200 (Top-15 55-58 %); feb-jun 2026 entre 57 y 92 (47-50 %). La correlación de un mes con el
  siguiente es +0,65. Pero apostar más tras un mes "fuerte" no paga: el Top-5 escalonado del mes siguiente da
  +22,3 % tras un mes fuerte y +20,2 % tras uno flojo. La fuerza vive en el fondo de la lista (quién no sale).
