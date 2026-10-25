# Pre-registro de decisiones pendientes (auditoría externa 2026-10-25)

Escrito antes de acumular datos nuevos. No toca el tramo ciego (>= 9357) ni producción.

## 1. Tripleta de ventana (12 sorteos)
- Estado: solo desarrollo (z(bloques) +6,8 / +5,85; EV 45x +80 % / +97 %). Sin entrada en `registro_final.jsonl`.
- Marcador en vivo: contar las tripletas auto-generadas (2 cada 24 h) desde esta fecha.
- Umbral de acierto: 2,22 % (pago 45x). Decisión a n = 300 tripletas por variante (A y B).
- Regla: "validada" solo si el IC 95 % inferior del acierto en vivo supera 2,22 %. Si el punto central
  queda por debajo de 2,22 %, se pausa el auto-juego. El veredicto se anota en `registro_final.jsonl`.
- Hasta entonces no se describe como validada.

## 2. Capas (fecha + rueda) en el principal
- Desde 2026-10-22 el principal = ag12+RD+capas, sin sombra previa. Se lee como "sombra que además se juega".
- Se mantienen en paralelo las filas principal y ag12+RD.
- Decisión a n = 144 sorteos contados desde 2026-10-23 18:00: diferencia de Top-15 (o mbits) principal - ag12+RD con
  IC 95 %. Si el IC excluye 0 a favor de ag12+RD, se retiran las capas del principal; si no, se mantienen.

## 3. Reciclaje por hora (H2, sombra, pendiente)
- Candidato: multiplicadores por hora sobre el grupo "salió hace 1–2 días" (9:00 x1,108; 15:00 x0,953; 16:00 x0,940; etc.).
- Evidencia: solo desarrollo, +0,99 mbits fuera de muestra (dev-B). Entra como sombra, no al principal.
- Regla propuesta: n >= 730 sorteos y z vivo > +2 con el mismo sentido. Implementación en un PR aparte.
