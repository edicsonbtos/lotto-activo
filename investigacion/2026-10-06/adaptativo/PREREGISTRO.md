# Pre-registro: ajuste adaptativo de "repetición en el día" por día de la semana (2026-10-06, antes de medir)
Motivo: enjambre `../semana/` (A3: de mié a vie de 2026 el operador repite en el día; en 2024-25, el domingo).
Base: motor de producción walk-forward (`prod_0605.npz`, sin fuga).

**Candidata AD(K, a).** Para el sorteo t (día d, día de la semana w), tomar los K días anteriores con el mismo w
(estrictamente antes de d). En ellos, O = ganadores que ya habían salido ese mismo día y E = suma de la probabilidad
del motor sobre esos animales. Factor r = (O + a) / (E + a), recortado a [0,5; 3]. Multiplicar por r la probabilidad
de los animales que ya salieron hoy y renormalizar. Solo usa el pasado.
**Control GL(K, a):** igual, pero con los últimos K·7 días sin mirar el día de la semana (sin estacionalidad semanal).

**Elección:** K ∈ {4, 8, 13, 26} y a ∈ {3, 10, 30}, eligiendo en dev-A (filas 2000-5687) por mbits. La elección se fija
antes de ver nada más.
**Pruebas:** dev-B (5688-9356), 2026 (≥ 2026-01-01) y, aparte, domingos de dev-B y mié-vie de 2026.
**Pasa** si Δmbits contra el motor tiene IC 90 % por jornadas > 0 en dev-B Y en 2026, y AD supera a GL en 2026. En ese
caso se audita con revisor-sesgo y, si la auditoría pasa, se propone encenderlo en producción. Si no pasa, no se toca.

## Añadido antes de medir: temperatura global
p^T renormalizado, con T ajustada por máxima verosimilitud SOLO en dev-A. Pasa si Δmbits tiene IC 90 % > 0 en dev-B y
en 2026, y si el Top-15 prometido se acerca al real en los dos. No cambia el orden, así que la jugada y la plata siguen
iguales. Solo afecta a los porcentajes que se muestran.
