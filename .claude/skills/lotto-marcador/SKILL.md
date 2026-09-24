---
name: lotto-marcador
description: Revisa el marcador REAL de Lotto Activo (h:00) y de RD Internacional (h:30) (pronósticos congelados en Railway) y dice cuánto habría ganado o perdido cada estrategia (Top-5 escalonado, Top-15 ponderado, Top-3, Top-15 plano), con intervalos de confianza. Úsala cuando el usuario pregunte cómo va, si está ganando, si el modelo funciona, cuántos aciertos lleva, o afirme que "a simple vista" acierta mucho en algún Top-N.
---

# Marcador en vivo

1. Ejecuta `python .claude/skills/lotto-marcador/marcador.py`. Solo lee la web de Railway. El `historial.txt` local va atrasado respecto a producción, así que no lo uses para esto.
2. Cuenta siempre tres cosas:
   - **n**: cuántos sorteos puntuables hay.
   - **La tasa frente al azar y frente al equilibrio.** Acertar más que el azar no basta: hay que superar el equilibrio (N/30).
   - **El neto en plata de cada estrategia**, comparado con su esperado a largo plazo.
3. Si el usuario cree ver un patrón ("acierta mucho en el Top-11"), muéstrale la lista de puestos del ganador: los aciertos se recuerdan y los fallos no. Recuérdale además que una lista al azar ya cae en el Top-13 el 34 % de las veces.
4. El bloque "Validación" es la prueba más rápida de que el modelo funciona en vivo. La **Señal** son los mbits que el modelo le dio al ganador: azar = 0, prueba ciega = +90, y con ~70 sorteos ya se distingue del azar. La **Calibración** compara lo que el modelo esperaba con lo que salió. Lo que se debe esperar en vivo es lo que el modelo dice; la tasa del Top-N contada a mano sirve menos. Solo cuenta registros con las 38 probabilidades, así que su n es menor.
5. Con menos de ~1.000 sorteos no concluyas nada. Di que el resultado está dentro del ruido si el IC95 cubre tanto el equilibrio como la tasa esperada.
6. No propongas cambiar el modelo por lo que se vea aquí. La regla pre-comprometida (`gestion_banca.VIGILANCIA`) exige 3 meses seguidos en contra en la carrera mensual.

## RD Internacional
Si pregunta por RD Internacional o "el internacional", corre `python .claude/skills/lotto-marcador/marcador.py --rd`.
El marcador de RD empezó el 2026-09-23: con n pequeño todo es ruido. Compáralo con lo esperado que imprime el script.
El equilibrio y la regla de no concluir con menos de ~1.000 sorteos son los mismos.
