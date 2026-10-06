# Enjambre "día de la semana" (2026-10-06): 6 agentes, A1-A6 (cada uno con PREREGISTRO.md e INFORME.md)

## Veredicto conjunto: el efecto es REAL en 2026; que persista es DUDOSO; no hay corrección que funcione
| agente | pregunta | veredicto |
|---|---|---|
| A1 | ¿Cada día por separado? ¿Sobrevive a la búsqueda? | Mié-vie O/E 0,82-0,85; peor terna, p < 5·10⁻⁵; 10/10 meses de 2026 |
| A2 | ¿Se replica en otros juegos (sin motor)? | En LA 2026, RR 0,85 (p 0,0002); en 5 juegos NO se replica (1 de 5 pasa) |
| A3 | ¿Mecanismo? | **Mié-vie el operador deja de evitar repetir el animal en el día** (O/E 1,68 contra 0,73); explica el 65 % |
| A4 | ¿Cuándo cambió? | Domingo malo 2024-07..2025-07, 4 meses neutros, mié-vie malo desde 2025-12 (cortes con p 0,0005) |
| A5 | ¿Se convierte en mejora? | Ninguna corrección pasa en las dos direcciones; saltar mié-vie da +25 % contra +12 % (jun-oct), pero en dev era al revés |
| A6 | ¿Fantasma de la búsqueda? | z −5,15, el máximo de ~110 particiones; p familiar < 10⁻⁴. Para la mitad del efecto: ~226 jornadas en vivo |

## Mecanismo
El motor castiga al animal que ya salió hoy, porque normalmente el operador casi no repite en el día. En 2026, de
miércoles a viernes, se repite el doble (1,11 repeticiones por día contra 0,52 de sábado a martes; el azar puro daría 1,60)
y ganan más los animales fríos. Esos días se parecen al azar y el motor pierde casi toda su ventaja (+36 mbits contra
+135). En 2024-25 lo mismo pasaba los domingos. El "día relajado" del operador cambia de lugar cada 10-13 meses,
sin avisar. Las demás loterías no lo comparten, salvo un eco leve en La Granjita y en RD.

## Qué se hace
- El motor y la jugada NO cambian. Las correcciones simples se sobreajustan (A3, A5).
- Pre-registro en vivo ampliado (sustituye al de `../reciclaje/INFORME.md`):
  - Desde el 2026-10-07, con los pronósticos congelados de Railway.
  - **Primaria:** Top-15 O/E mié-vie contra el resto.
  - **Mecanismo:** repetición en el mismo día, O/E contra el motor, mié-vie contra el resto.
  - **Mirada intermedia el 2027-01-06** (92 jornadas, potencia 0,94 si el efecto es el entero). Solo puede *confirmar el
    efecto entero* si la diferencia del Top-15 es ≤ −6 pp con IC 95 % que no toca 0, y la repetición mié-vie es ≥ 1,3.
  - **Decisión final el 2027-05-31** (~226 jornadas, potencia 80 % para la mitad del efecto). Se confirma con
    diferencia ≤ −3 pp e IC 90 % < 0. Se descarta si la diferencia es ≥ −1 pp.
  - **Freno:** si dos meses seguidos dan una diferencia ≥ 0, se da por terminado el régimen.
- Si el usuario decide, por prudencia, apostar menos de miércoles a viernes antes de la confirmación, es una decisión
  suya. Que quede registrado que en 2024-25 esos eran los mejores días.
