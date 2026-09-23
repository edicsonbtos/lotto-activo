---
name: lotto-marcador
description: Revisa el marcador REAL de Lotto Activo (pronósticos congelados en Railway) y dice cuánto habría ganado o perdido cada estrategia (Top-5 escalonado, Top-15 ponderado, Top-3, Top-15 plano), con intervalos de confianza. Úsala cuando el usuario pregunte cómo va, si está ganando, si el modelo funciona, cuántos aciertos lleva, o afirme que "a simple vista" acierta mucho en algún Top-N.
---

# Marcador en vivo

1. Ejecuta `python .claude/skills/lotto-marcador/marcador.py`. Solo lee la web de Railway. El `historial.txt` local va atrasado respecto a producción, así que no lo uses para esto.
2. Cuenta siempre tres cosas:
   - **n**: cuántos sorteos puntuables hay.
   - **La tasa frente al azar y frente al equilibrio.** Acertar más que el azar no basta: hay que superar el equilibrio (N/30).
   - **El neto en plata de cada estrategia**, comparado con su esperado a largo plazo.
3. Si el usuario cree ver un patrón ("acierta mucho en el Top-11"), muéstrale la lista de puestos del ganador: los aciertos se recuerdan y los fallos no. Recuérdale además que una lista al azar ya cae en el Top-13 el 34 % de las veces.
4. Con menos de ~1.000 sorteos no concluyas nada. Di que el resultado está dentro del ruido si el IC95 cubre tanto el equilibrio como la tasa esperada.
5. No propongas cambiar el modelo por lo que se vea aquí. La regla pre-comprometida (`gestion_banca.VIGILANCIA`) exige 3 meses seguidos en contra en la carrera mensual.
