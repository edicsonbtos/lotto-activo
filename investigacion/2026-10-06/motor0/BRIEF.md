# Proyecto "motor 0" (2026-10-06): un motor nuevo, centrado en el TOP-15 y en CUÁNDO jugar
Lee primero `../motor2/BRIEF.md` (contexto, reglas y arnés). Usa el mismo arnés: `../motor2/arnes.py`.

Objetivo del usuario: un motor de PRUEBAS que supere por mucho al actual en el Top-15, eligiendo bien la hora y el día
con la información que ya conocemos, con otra metodología y teniendo en cuenta las rachas de la mañana.

## Cómo se juzga (fijo, antes de empezar)
- Jugada de referencia actual: Top-5 escalonado de PROD con la regla de cambio de RD (ver `../motor2/incremento.py`).
  Retorno por ficha: AJUSTE +31,0 %, ELECCION +24,9 %.
- Jugada "Top-15 plano" (1 ficha a cada uno de 15 animales, pago 30): empata con un acierto del 50 %. PROD acierta 54,6 %
  en AJUSTE y 48,6 % en ELECCION.
- Métrica principal: **retorno por ficha** de la estrategia completa (qué sorteos jugar × qué 15 animales × cuántas fichas),
  con IC 90 % por jornadas, y **fichas netas por día** (para no premiar estrategias que casi no juegan). Secundarias:
  Top-15 en los sorteos jugados y mbits.
- Elige SOLO con AJUSTE (jul-25..feb-26) y ELECCION (mar-jun-26).
- **PRUEBA26 (jul-oct-26) YA NO ES CIEGA**: se miró 5+ veces y el régimen mié-vie y la regla de RD se descubrieron con
  2026. Puedes mirarla UNA vez al final con la versión congelada, registrándola, pero debe reportarse como
  "contaminada". La confirmación real será en vivo desde el 2026-10-07.
- Escribe solo en tu carpeta (motor0/<tu_id>/) y en el scratchpad. Pre-registro antes de mirar resultados. Sin git, sin red,
  sin tocar producción. ≤ 40 min de CPU. lightgbm 4.7 y sklearn 1.9 están instalados.
- Matrices disponibles en el scratchpad: PROD (arnes.PROD), motor2_M4.npz (LightGBM sobre PROD), motor2_M6.npz,
  motor2_M1.npz (incluye q de modo relajado si lo guardó; si no, recalcula con ../motor2/M1/m1.py), M5_bases.npz
  (submodelos), rdint_historial.txt en la raíz del repo (RD, índice de hora 0..11 = 8:30..19:30).
