---
name: lotto-nueva-idea
description: Protocolo para probar cualquier idea nueva de predicción o de apuesta en Lotto Activo sin fabricar una estadística fantasma. Úsala cuando el usuario proponga un patrón, una estrategia, una forma de elegir animales o sorteos (p. ej. "¿y si juego un animal todo el día?", "los que no han salido", "cuando va en racha"), pida mejorar las predicciones o la calibración, o antes de tocar herramientas/modelos/ o el ensamble.
---

# Probar una idea nueva sin engañarse

## Antes de medir nada: ¿ya se probó?
Estas ideas ya se probaron y quedaron cerradas. No se repiten sin una razón nueva:
- Frecuencias o animales "calientes": ruido. Markov 38×38 y PRNG/semilla: ruido.
- Operación Turing: 308 hipótesis, 0 señales. El operador tiene licencia MGA desde 2019, con RNG certificado.
- "Racha del favorito" (hilo 5): descartada. "Calor de la lista", es decir, elegir sorteos por la probabilidad del Top-N (hilo 6): **falló en prueba ciega**, con el efecto invertido.
- Rachas de aciertos o fallos: no informan. Castigar en vez de excluir al que ya salió hoy: peor.
- La calibración ya está bien (dice 3,5 % → sale 3,51 %). Recalibrar es ajustar ruido.
- Seguir un animal todo el día (elegido al abrir): +10-15 % en desarrollo, pero renovar el #1 en cada sorteo da +36 %. Es peor que la jugada actual.
- **"Animal del día" (2026-09-27, `herramientas/exploracion/animal_dia.py`, PREREGISTRO_animal_dia.md): PASÓ la ciega en acierto, NO en plata.** Top-k del ensamble al abrir el día; ¿sale alguno hoy? Reciente (254 días): k=1 38,6 % vs azar 29,5 % (z +3,2), k=2 60,6 vs 50,9 (z +3,1), k=3 72,4 vs 66,1 (z +2,1, no pasa). Sellado 2019-23: los tres pasan (+4 a +5 pp). Retorno/ficha (jugar hasta que sale): reciente +20/+9/+5 %, sellado +1/−2/−4 %; IC cruzan 0. No supera la jugada por sorteo. Ya se corrió (registro_animal_dia.jsonl): no se repite.
- **Formas de jugar y "domingo" (2026-09-27, `estrategias_v2.py`, PREREGISTRO_estrategias_v2.md, ya corrido):** 13 repartos de fichas; ninguno le gana al Top-5 escalonado de forma consistente (Kelly/valor p≥3,6 % mejor en sellado, peor en reciente). Top-15 plano pierde en los dos tramos ciegos (−1 %, −3 %). Por hora: nada. **Domingo** (en desarrollo +9 mbits contra +140): NO PASÓ a ciegas (reciente +47 al revés, sellado +1). Era ruido.
- **"El Top-15 acierta pero a otra hora" (2026-09-27, `top15_otra_hora.py`, ya corrido): NO PASA.** Los animales que estuvieron en el Top-15 de una hora anterior del día salen justo lo que el motor les da ahora: O/E 1,05 [0,98; 1,12] reciente, 1,00 [0,97; 1,03] sellado, 1,10 en vivo (99). Es memoria selectiva (igual que ag11).

- **Hilo 7, memoria cruzada (2026-09-23), CONFIRMADO y en producción:** RD Internacional (h:30) evita el animal de Lotto Activo de h:00. Pasó la prueba ciega (Top-3 12,05 %). Su tramo de prueba (2025-07-01..2026-04-12) YA SE USÓ; la réplica 2026-04-13..09-13 también se miró (Top-15). Para ideas nuevas sobre RD: desarrollo 2024-03-01..2025-06-30, y la confirmación viene del marcador en vivo de RD. La dirección inversa (Lotto Activo usando RD) FALLÓ a ciegas.
- **Regla de cambio RD (h−1):30 → Top-5 de LA h:00** (2026-09-23): se adopta sin confirmar, en vivo (quitar y subir, el 6º entra 5º). **Extenderla a las 8:00 con RD 19:30 de la víspera: DESCARTADA** (hilo7_cambio_noche.md). La noche corta el "no repetir el anterior": en desarrollo LA 8:00 repitió ese RD más que lo esperado (16 contra 9,3).
- **Hilo 8, "Lotto Activo República Dominicana" (LARD, API id 3, 14 sorteos h:00 de 8 a 21) como tercer juego cruzado (2026-09-23): DESCARTADO en desarrollo.** Ratios de repetición 0,99-1,09 con LA y RD en los 4 pares; los controles LA↔RD salen fuertes en los mismos datos. LARD es independiente. Su prueba ciega (2026-02-01..09-22) sigue SIN mirar. Datos: `datos_multiloteria/oficial_multi.csv` (API oficial desde 2025-07-01, juegos 1, 2 y 3; descargador `herramientas/lard/descargar.py`).
- **Hilo 9, "subir porcentajes" (2026-09-23): CERRADO sin mejora** (`verificacion/hilo9/INFORME.md`, reproducible con `verificar.py`). El reciclaje entre juegos de días anteriores da O/E ≈ 1,00. L3 (LA evita RD (h−2):30) y R4 (RD evita su propio día) son reales, pero aportan +1,4 y +0,3 mbits sin mover el Top-5 ni el Top-15. Un modelo flexible de 91 variables NO supera al ensamble (−38 mbits solo, −4,4 apilado; con λ=30 exploratorio da +4,5, pero el Top-5 baja). El ensamble está en el techo de estos datos. No quedan fuentes de información nueva sin probar.

- **"Top-15 al 70 %" (2026-10-01, `herramientas/exploracion/top15_70/INFORME.md`, 4 rondas pre-registradas, dev-A elige y dev-B mide): IMPOSIBLE por sorteo.** Hacen falta ≥ 275 mbits y el mejor modelo llega a 177 (dev-B, 2025). Ningún modelo da jamás ≥ 70 % de masa a su Top-15 (máx. 68 %). Planes cerrados: exclusión dura del día, todos los RD de hoy, chorro LA+RD con rechazo, LightGBM y LambdaRank, horas buenas (dev-A eligió las 17:00 y no replicó), otras loterías (h−1) como fuente, "La Pirámide de Hoy". ag12 reajustado solo con dev-A + RD: +25,5 mbits y +1,3 pp de Top-15 (p = 0,03, no pasa Bonferroni). El 70 % solo se alcanza cambiando la forma de jugar: Top-22 (74 %) o Top-15 en dos sorteos (80 % "al menos uno").
- **SEÑAL NUEVA (2026-10-01, ronda 2 pre-registrada): el operador esquiva el número de la FECHA y el de la HORA.** Número = día del mes: O/E 0,71 en dev-A y 0,51 en dev-B [0,35; 0,68]. Hora en reloj de 12 h: 0,91 y 0,64. Placebos: día+1 0,66, día−1 0,87, día+2 0,87, el resto ~1; hora en 24 h 1,10. Se replica en RD (día 0,78), La Granjita 0,47, Selva Plus 0,68 y Guácharo 0,32; **no en LARD** (0,96). Hipótesis: los operadores esquivan lo más jugado. Como corrección sobre ag12 suma +6 mbits y +0,8 pp (descriptivo). Pendiente: sombra en vivo, y guardar los "datos" que publican los pronosticadores para probarlos.

- **SEÑAL (2026-10-03, `investigacion/2026-10-03/primer_sorteo_ayer/`): el primer sorteo del día casi nunca repite el primer sorteo de ayer.** 3 veces en 1.082 días (unas 28 por azar). Contra el motor: O/E 0,12 en dev y 0,19 en prueba (P total 9·10⁻⁵). Solo pasa en el primer sorteo: en las demás horas, "misma hora de ayer" da O/E 1,06. El motor lo captura a medias, porque el retraso 12 tiene un peso compartido entre horas. Además, el primer sorteo de hace 3 días sale de más (O/E 1,45-1,89 en las dos eras). **APLICADO desde 2026-10-04** en `prediccion.ajuste_primer_sorteo` (×0,272 y ×1,736, ajustados en dev): +22 mbits por primer sorteo en prueba [−3; +48]. Los registros guardan `scores_base` para auditarlo. El 7.º de ayer se descartó por inestable. El vivo está pre-registrado en el INFORME. "Salió ayer" en general y "hace 2-3 sorteos" a las 8:00 ya están bien calibrados (O/E 0,7-1,2).

- **Enjambre 8:00 (2026-10-03, `investigacion/2026-10-03/enjambre_8am/INFORME.md`, 10 agentes, ya corrido): sin ventaja nueva confirmada.**
  - **NULOS:** memoria completa del primer sorteo (233 rasgos), distribución marginal, relaciones numéricas de noche a
    mañana, bolsa o balanceo de primeros sorteos, temperatura a las 8:00, regla cruzada de primer sorteo entre juegos,
    modelo especializado del primer sorteo (−19 mbits) y regla por días abiertos o por día de la semana.
  - **Forense:** la regla "primero de ayer" es REAL (API oficial sola 1/422; RD 1/422; LARD no).
  - **Ventana {día−1, día, día+1} a las 8:00 (×0,59 sobre exposición): PROMETEDOR.** Desde 2024-T3 sale O/E 0,40; antes,
    1,4-1,7. La auditoría no la deja entrar en la jugada. **En sombra desde 2026-10-04** (`/api/sombra` → `ventana_8am`,
    decisión a n = 730). No se vuelve a medir en prueba.
  - **"Salió ayer o anteayer" ×1,3 en el primer sorteo:** prueba O/E 1,12, p ≈ 0,09; solo vigilancia.
  - **RD esquiva su propio primero de ayer** (O/E 0,32): hilo pendiente para el motor de RD.

- **Día de la semana (2026-10-06, `investigacion/2026-10-06/semana/INFORME.md`, enjambre de 6, ya corrido): REAL en 2026, sin corrección útil.** De mié a vie el operador deja de evitar repetir el animal en el día (O/E contra el motor 1,68 contra 0,73) y el motor cae a Top-15 O/E 0,82-0,85 (z −5,15; p familiar < 10⁻⁴). En 2024-25 lo mismo pasaba el DOMINGO (2024-07..2025-07); el día cambia sin avisar. No se replica en otros juegos. Correcciones C1-C3: no pasan en las dos direcciones. Pre-registro en vivo: mirada 2027-01-06 y decisión 2027-05-31. No se vuelve a medir en 2026. **Ajustes probados el mismo día (`investigacion/2026-10-06/adaptativo/`): factor adaptativo de "ya salió hoy" por día de la semana, NO pasa dev-B; temperatura global, NO pasa (la T óptima cambia de era). El motor no se toca.**

- **Enjambre "motor 2" (2026-10-06, `investigacion/2026-10-06/motor2/INFORME.md`, tramos recientes, arnés común `arnes.py`): ninguna mejora EN PLATA sobre la jugada en vivo.** M4 (LightGBM sobre PROD) da +19 mbits contra PROD, pero contra PROD×RD unos +9 y en plata +0,2 fichas por sorteo [−0,2; +0,6]; además no es desplegable (RD llega después del congelado). M6: "pares que se evitan" es real (+2-4 mbits), solo sombra. M1/M3: detectan solos el día relajado, pero no mejoran. M2: 0/48 fugas de calendario. **PRUEBA26 (jul-oct-26) ya se usó 5+ veces: no se vuelve a usar para elegir.**

- **Motor nuevo S2 desde cero (2026-10-06, `investigacion/2026-10-06/motor0/` y `ciego/`): NO CONFIRMADO en las pruebas ciegas.** LightGBM con un experto normal y otro relajado. En 2026 da +12 mbits y +2,4 pp de Top-15. En el tramo antiguo, la mezcla con PROD da +7,4 [+1,5; +13,4] (pasa justo), pero en plata es +1,0 pp [−4,5; +6,4]. En RD Internacional −4,2. Batería Turing: sin fuga, pero con un hueco de 1 mes la ventaja cae un 74 % y un rasgo de ruido entra en el puesto 6 de 38 (sobreajuste). Selector "cuándo jugar el Top-15" (S1): no mejora; la mañana no predice la tarde. El sellado 2019-23 NO está en este servidor (falta `motor_nuevo/sellado/sellado_la.txt`).

Estructura real conocida: el operador **evita repetir el animal el mismo día** y **recicla con 1 a 2,5 días de hueco**. El ensamble ya lo captura. Desde 2026-10-01 se sabe además que **esquiva el número de la fecha (hoy y mañana) y el de la hora**. El ensamble NO lo captura; está pendiente de sombra en vivo.

## Cómo medir
1. **Solo en el tramo de desarrollo** [2000, 9357). El tramo de prueba (≥ 9357) ya se miró 5 veces (`herramientas/registro_final.jsonl`). No se mira más para elegir nada.
2. Reutiliza la caché walk-forward `herramientas/exploracion/calor_cache.npz` (P 7357×38, y). Para alinear hora y día, usa `lotto_eval.cargar(...).hora/.dia[LE.W:]`.
3. **Pre-registra** en `herramientas/exploracion/PREREGISTRO_<idea>.md` la métrica, el corte y el umbral de falsación, ANTES de mirar resultados.
4. Para comparar modelos usa mbits, no Top-3: el Top-3 no tiene potencia. Todo contraste entre grupos de sorteos se **estratifica por hora** (Mantel-Haenszel); el test crudo da 88 % de falsos positivos.
5. Para estrategias de apuesta, mide **retorno por ficha contra el equilibrio 1/30 por animal**, no la tasa de acierto. Reporta por mitades del tramo, con IC por bloques de jornada (12 sorteos).
6. Un efecto con z de 2,5 a 3,4 replicado en vistas correlacionadas **no basta**: el hilo 6 lo tenía y era ruido.
7. Si el cambio toca el modelo en producción, el registro o `deshacer()`, lanza el subagente `revisor-sesgo` antes de aceptarlo.
8. La confirmación final viene del **marcador en vivo** (skill `lotto-marcador`), no de otra mirada al tramo de prueba.

## El PC del usuario
Tiene ~150 MB de RAM libres y numpy/OpenBLAS falla ahí. Scripts cortos (la caché ocupa poco) sí corren. Los largos se añaden a `HERRAMIENTAS` en `servidor.py` para que el usuario los ejecute desde la web de Railway con "Ejecutar".
