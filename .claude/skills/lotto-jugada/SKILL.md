---
name: lotto-jugada
description: Da la jugada del próximo sorteo de Lotto Activo en animales y en plata (Top-5 escalonado y Top-15 ponderado), leída de la web en vivo de Railway. Úsala cuando el usuario pregunte qué jugar, cuál es la jugada, qué animales salen, cuánto apostar, cuánto poner a cada animal, o mencione su banca o un monto (p. ej. "tengo 300 dólares").
---

# Jugada del próximo sorteo

1. Ejecuta (desde la raíz del proyecto; si el usuario dio una banca, pásala):
   `python .claude/skills/lotto-jugada/jugada.py [banca]`
   El script solo LEE `/api/mesa` en Railway con curl; no toca datos. No corras el modelo en el PC del usuario: tiene ~150 MB de RAM libres y numpy falla.
2. Presenta en español simple:
   - La **jugada recomendada**: Top-5 escalonado, con 2 fichas a los puestos 1-3 y 1 ficha a los puestos 4-5.
   - La alternativa **Top-15 ponderado** (3-2-1 fichas): para cuando el usuario quiere cobrar en la mitad de los sorteos.
   - La plata por animal si dio banca.
3. Reglas que siempre acompañan la jugada. Son cortas y no se negocian:
   - Jugar TODOS los sorteos. Saltar los "fríos" o cargar los "calientes" ya falló en prueba ciega.
   - No subir el monto para recuperar una racha. Rachas de 15 a 20 fallos seguidos son normales.
   - Del 6º al 15º cada animal acierta ~3,0 %, por debajo del 3,33 % que pide el pago 30x. El Top-15 **plano** perdió en prueba ciega (−1 %).
4. Nunca prometas ganancia. La ventaja medida en prueba ciega es real (Top-3 12,27 % contra el 10 % de equilibrio), pero pequeña, y solo se cobra con muchas jugadas.
5. Si el script dice que la web está calculando, explica que tras cada despliegue tarda 1-2 min. No es un fallo.
