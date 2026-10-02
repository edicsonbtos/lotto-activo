# La brecha de 2026 (2026-10-02)

Pre-registro: `PREREGISTRO_brecha_2026.md` (commit 1762e87, antes de calcular; anexo 207cd42 antes del barrido de
interacciones). Scripts: `brecha_2026.py` (batería pre-registrada), `brecha_2026_interacciones.py` (anexo),
`brecha_2026_extra.py` (descriptivo posterior). Salidas en `*_salida.txt` y `brecha_2026.json`.
Datos: Lotto Activo, RD y LARD oficiales hasta el 2026-09-29 (LARD hasta el 22-sep). No se tocó producción.

## La respuesta corta

**En 2025 la brecha era que el operador casi no repetía animal en el mismo día (0,25 de lo normal).** En 2026 esa
brecha se cerró a la mitad (~0,50) y el motor, que la aprendió en 2025, quedó sobreconfiado.

**La brecha de 2026 son dos cosas que el Top-15 de la web todavía no usa:**
1. **Lotto Activo esquiva el animal que acaba de salir en RD Internacional media hora antes (RD (h−1):30).** Sale
   **0,35 veces** lo que el motor le da (en 2025 era 0,54): la brecha se abrió más. En todo 2026, a las 11:00 y a
   las 13:00 no salió ni una vez. De las 110 variables probadas es la única que pasó el filtro y se confirmó en la
   segunda mitad del año (ene-may 0,32 → jun-sep 0,41, p < 0,0001).
2. **Esquiva los números de la fecha y de la hora** (día−1, día, día+1, hora en reloj de 12 h, mes). Los
   multiplicadores se congelaron con datos de 2024 y nunca vieron 2026: en 2026 suman **+4,8 mbits [+1,9; +7,5]**.

**Cuánto vale:** la web hoy solo saca al animal de RD del Top-5 (lo baja al 6º y sigue dentro del Top-15). Dejando
el Top-5 tal cual y armando los puestos 6-15 con las dos correcciones (el animal de RD sale del Top-15 entero):

| Tramo | Top-15 hoy | Top-15 con la brecha | Diferencia [IC95] | Top-15 ponderado por ficha |
|---|---|---|---|---|
| 2026 entero (3.323 sorteos) | 49,26 % | **51,43 %** | **+2,17 pp [+1,38; +2,98]** | +5,4 % → **+8,2 %** (+2,83 [+1,81; +3,89]) |
| ene-may 2026 | 49,38 % | 51,82 % | +2,45 [+1,41; +3,54] | +6,7 % → +9,9 % |
| jun-sep 2026 (confirmación) | 49,11 % | 50,89 % | +1,78 [+0,57; +2,92] | +3,6 % → +5,9 % |
| Vivo 14-29 sep (192) | 45,83 % | 51,04 % | +5,21 [+2,60; +7,81] | −9,0 % → −2,2 % |
| 2025 (referencia) | 54,41 % | 55,45 % | +1,04 [+0,32; +1,78] | +16,1 % → +17,5 % |

El Top-5 no cambia (19,47 % en 2026, +18 % por ficha con el escalonado). Sacar el animal de RD de todo el Top-15
mejora el Top-15 en 9 de los 10 meses de 2026.

**Lo que no hay:** ninguna otra variable ni combinación con la hora pasa (barrido de 268 interacciones: máximo
|z| 3,43 contra 4,12 exigido). LightGBM con las 110 variables tampoco: +1,2 mbits [−8,0; +10,3]. El techo sigue
siendo ~51 % de Top-15. El 70 % no está.

## 1. Cómo se buscó (todo el poder de cálculo, sin engañarse)
- **110 variables** que se conocen antes de cada sorteo:
  - huecos en sorteos y en días, conteos recientes;
  - repetición en el día y lo que salió ayer y anteayer a cada hora;
  - secuencia (vecinos, cifras);
  - RD y LARD de antes;
  - fecha y hora;
  - cada uno de los 38 animales;
  - cinco específicas de las 8:00.
- Se compara contra lo que **el motor** espera: así sale solo lo que el motor no sabe.
- **Descubrir en ene-may 2026, confirmar una sola vez en jun-sep 2026.** El umbral se sacó de 2.000 simulaciones
  en las que el ganador sale de las propias probabilidades del motor. Eso corrige por haber probado 110 cosas a la
  vez: hace falta |z| > 3,60 y no basta con 2.
- Resultado: 2 candidatas. "Salió hoy" (O/E 1,34) **no se confirma** (en jun-sep fue 0,89: la repetición en el día
  va y viene). "RD (h−1):30" **se confirma**.
- Anexo: 268 combinaciones variable × franja horaria con el mismo método. Ninguna pasa.
- Fuerza bruta: logit con 66 variables (−7,2 mbits) y LightGBM (+1,2 [−8,0; +10,3]). Ninguno mejora al ensamble.

## 2. El perfil de 2025 contra el de 2026 (O/E contra el azar, sin modelo)

| Comportamiento del operador | 2025 | 2026 ene-may | 2026 jun-sep |
|---|---|---|---|
| Repite un animal que ya salió hoy | 0,25-0,37 | ~0,49 | ~0,40 |
| Repite el de RD de media hora antes | 0,55 | **0,32** | **0,41** |
| Sale el número del día del mes | 0,56 | 0,65 | 0,92 |
| Sale el número de mañana (día+1) | 0,70 | 0,71 | 0,73 |
| Sale el número de la hora (12 h) | 0,64 | 0,75 | 0,76 |
| Repite el de hace 7 días a la misma hora | 0,87 | 0,69 | 0,79 |

La tabla completa (110 variables × 3 tramos, contra el motor y contra el azar) está en `brecha_2026_salida.txt`.

## 3. Las 8:00
- **2025:** fue la mejor hora casi todo el año, de 55 % a 80 % de Top-15 cada mes de enero a octubre.
- **Nov-2025 a jun-2026:** cayó a la media (feb-2026: 25 %).
- **Jul-ago 2026:** volvió a subir (58 % y 65 %).
- **En vivo:** el ganador estuvo dentro del Top-15 de las 8:00 los 9 días del 21 al 29-sep. Según el usuario, la
  racha sigue hasta el 02-oct.
- Todos esos ganadores habían salido hace 1 a 3 días. Es el reciclaje que el motor ya premia.
- **¿Van por temporadas?** En 2026, tras 30 mañanas buenas las 8:00 aciertan 50,5 %, y tras 30 mañanas flojas
  también 50,5 %. En 2025-2026 juntos sale +9 pp, pero solo porque 2025 fue bueno entero y 2026 no. No sirve para
  saber qué mañana jugar.
- La racha se sigue juzgando con la H1 de `PREREGISTRO_manana_8am.md`.

## 4. Qué haría con esto (nada cambia sin tu OK)
1. **Proponer a producción el "Top-15 con la brecha 2026":** Top-5 igual que hoy. Los puestos 6-15 se ordenan con
   el ensamble × exposición (multiplicadores congelados de `herramientas/modelos/exposicion.py`), sin el animal de
   RD (h−1):30 (de 9:00 a 19:00; a las 8:00 no aplica). Antes de subirlo:
   - pasa por el auditor `revisor-sesgo`;
   - se pone en sombra en `/api/sombra` con un pre-registro propio, porque la forma "híbrida" se eligió viendo 2026.
   Lo que la respalda: las dos señales se fijaron antes de 2026 y se confirmaron en 2026.
2. **No tocar el Top-5:** ninguna de las dos señales lo mejora en 2026.
3. La sombra `exposicion` en vivo (desde el 02-10) ya mide la parte de la fecha. Esto añade la parte de RD.

## 5. Límites
- 2026 hasta el 13-sep es el tramo de prueba y ya se había mirado para otras cosas. Esta mirada queda anotada en
  `herramientas/registro_final.jsonl`. La separación ene-may / jun-sep se fijó antes de calcular.
- El efecto RD se conocía (hilo 7, H4b). Lo nuevo es:
  - que en 2026 es más fuerte que en 2025;
  - que es la única brecha que sobrevive a una búsqueda amplia;
  - que aplicado al Top-15 entero da plata (+1,6 pp por ficha solo con RD).
- La versión híbrida (Top-5 intacto) se eligió después de ver que la exposición bajaba un poco el Top-5 en 2026.
  Por eso su cifra es optimista. El juez es el vivo.
- No hay vivo después del 29-sep en este equipo (el proxy bloquea la web de Railway).

## 6. Auditoría (`revisor-sesgo`, 2026-10-02) y lo que se corrigió
Sin fuga de futuro (se barajó el futuro en 3 cortes: las 110 variables no cambian), horas bien indexadas y la sombra
reproduce el análisis al decimal. Ningún bloqueante. Lo que señaló y se hizo:
- **La regla de utilidad pre-registrada NO se cumplió y este informe no lo decía.** El criterio era Δmbits > 0 con
  IC95 sin tocar 0: "Ensamble + confirmadas" dio **+8,6 [−1,3; +16,7]**, "+ candidatas" −0,1 [−11,7; +10,2] y
  LightGBM +1,2 [−8,0; +10,3]. Según su propio pre-registro, la brecha **no está demostrada como útil para jugar**.
  El híbrido por Top-15 (49,26 → 51,43 %) es **exploratorio**: su forma se eligió viendo 2026. La entrada en
  `registro_final.jsonl` queda corregida con una nota.
- **Qué aporta cada señal.** Solo sacar el animal de RD del Top-15: **+1,2 pp [IC90 +0,8; +1,6]** en 2026. Con
  exposición encima: +2,17 pp. La exposición tiene su propia sombra (decide a n ≥ 6.000) y **no se enciende por
  esta vía**.
- **Mirada única fijada** a los primeros 1.600 sorteos; registros malos aislados; potencia realista (+1,0 a +1,8 pp).
- Lo confirmado usaba RD 19:30 de la víspera a las 8:00; la sombra no (a las 8:00 la O/E de 2026 es 0,97: inocuo).
- El nulo por simulación supone el motor calibrado y en 2026 está sobreconfiado (z ≈ −3,5), así que el umbral es
  algo anticonservador: "D hueco 0 días" (z = umbral) era descalibración, no brecha. La confirmación en jun-sep lo frenó.
- La confirmación de RD no es fresca: el efecto se conocía (hilo 7; control del 2026-10-01).
- No se verifica que RD (h−1):30 estuviera disponible antes de LA h:00 en cada sorteo; se vigila con `sorteos_con_rd`.
- Las cifras del híbrido salen ahora de `brecha_2026_hibrido.py` (pasa 2026 por el mismo código de la sombra).
