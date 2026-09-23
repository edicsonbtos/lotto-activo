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
