# PRE-REGISTRO — Ronda 4: ¿se esquivan los números de "La Pirámide de Hoy"?

Escrito el 2026-10-01, antes de calcular. Script: `ronda4.py`.

## Por qué
La ronda 2 mostró que en LA sale menos el número del día (y el de mañana), y la ronda 3 que lo mismo pasa en RD
y en otros tres operadores. Si los operadores esquivan lo que más se juega, otro candidato público y calculable
es **"La Pirámide de Hoy"**, que publican tuazar.com y juegoactivo.com cada día a partir de la fecha. Desde
este equipo no se pueden abrir esas páginas (el proxy las bloquea), así que se usa la versión más común del
método, fijada aquí antes de mirar:

- Fila 1: los 8 dígitos de la fecha DDMMAAAA (01-10-2026 → 0 1 1 0 2 0 2 6).
- Cada fila siguiente: la suma de cada par de dígitos vecinos, quedándose con la última cifra (módulo 10).
  Así hasta que quedan 2 dígitos (filas de 8, 7, 6, 5, 4, 3 y 2 dígitos).
- **PIR-punta**: el número de 2 cifras de la última fila.
- **PIR-pares**: todos los números de 2 cifras formados por dígitos vecinos en las filas de 4, 3 y 2 dígitos.
- En los dos casos solo cuentan los números 1..36 y se quitan los que coinciden con el día o con el día+1,
  para no repetir la ronda 2.

## Prueba
- LA: O/E con el esperado del ensamble, en dev-A [2000, 5688) y en dev-B [5688, 9357).
- RD: O/E con el esperado del modelo B1 de RD, en el desarrollo de RD (2024-03-01..2025-06-30).
- **Pasa** si O/E < 1 en las tres series y el IC por bootstrap de jornadas al 98,75 % (Bonferroni por
  2 variantes × 2 series de confirmación) no contiene 1, tanto en dev-B de LA como en RD.
- Si no pasa, no se prueban otras variantes de la pirámide: no hay forma de saber cuál usan las páginas.
