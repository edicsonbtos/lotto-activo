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

- **Hilo 7, memoria cruzada (2026-09-23), CONFIRMADO y en producción:** RD Internacional (h:30) evita el animal de Lotto Activo de h:00. Pasó la prueba ciega (Top-3 12,05 %). Su tramo de prueba (2025-07-01..2026-04-12) YA SE USÓ; la réplica 2026-04-13..09-13 también se miró (Top-15). Para ideas nuevas sobre RD: desarrollo 2024-03-01..2025-06-30, y la confirmación viene del marcador en vivo de RD. La dirección inversa (Lotto Activo usando RD) FALLÓ a ciegas.
- **Regla de cambio RD (h−1):30 → Top-5 de LA h:00** (2026-09-23): se adopta sin confirmar, en vivo (quitar y subir, el 6º entra 5º). **Extenderla a las 8:00 con RD 19:30 de la víspera: DESCARTADA** (hilo7_cambio_noche.md). La noche corta el "no repetir el anterior": en desarrollo LA 8:00 repitió ese RD más que lo esperado (16 contra 9,3).
- **Hilo 8, "Lotto Activo República Dominicana" (LARD, API id 3, 14 sorteos h:00 de 8 a 21) como tercer juego cruzado (2026-09-23): DESCARTADO en desarrollo.** Ratios de repetición 0,99-1,09 con LA y RD en los 4 pares; los controles LA↔RD salen fuertes en los mismos datos. LARD es independiente. Su prueba ciega (2026-02-01..09-22) sigue SIN mirar. Datos: `datos_multiloteria/oficial_multi.csv` (API oficial desde 2025-07-01, juegos 1, 2 y 3; descargador `herramientas/lard/descargar.py`).

La única estructura real conocida: el operador **evita repetir el animal el mismo día** y **recicla con 1 a 2,5 días de hueco**. El ensamble ya la captura.

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
