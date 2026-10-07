# Prueba ciega SELLADA de S2 (2019-01-07 .. 2023-09-03). PRE-REGISTRO escrito ANTES de correr nada

Datos: `sellado_2019_2023.txt` (15.166 filas, pegadas por el usuario desde la fuente; sin 8:00, horas 1..11; huecos reales
en abr/may-2023 se respetan). Nunca estuvieron en el servidor ni en ninguna investigación: ni S2 ni el ensamble de
producción se construyeron, ajustaron o eligieron mirándolos. Hasta hoy nadie ha mirado un solo resultado de ellos.

## Qué se corre (todo congelado, sin tocar nada)
- **S2**: código de `../../2026-10-06/motor0/S2` (rasgos M4 sin RD + nuevos, objetivo C, vida 90, reentreno mensual,
  mismos hiperparámetros). ρ = valor calibrado con 2025 (parámetro congelado). Walk-forward sobre la serie sellada sola.
- **Base**: `ensamble_v2` walk-forward (W = 2000), SIN ajuste de primer sorteo ni de 8:00 (no existen en esa era).
- **Mezcla**: p ∝ base^(0,25)·S2^(0,75) (w = 0,75, fijado en ELECCION de 2026).
- Sin regla RD (no hay RD de esa era): todo "cambio = False".
- Tramo evaluado: 2020-01-01 .. 2023-09-03 (2019 queda como calentamiento de S2). Un solo run; sin segundas versiones.

## Métricas
mbits contra uniforme y Δ pareado contra la base, Top-15 y Top-5, plata (T15 plano, T5 escalonado 2-2-2-1-1),
IC 90 % por jornadas (días). Cortes por año (2020, 2021, 2022, 2023) solo descriptivos.

## Veredicto (fijado ahora)
- **CONFIRMADO**: mezcla con Δ mbits IC90 inferior > 0 en todo el tramo, Δ Top-15 ≥ 0 (IC no negativo), y Δ mbits > 0 en
  al menos 3 de los 4 años.
- **DUDOSO**: Δ mbits > 0 pero algún criterio anterior falla.
- **NO CONFIRMADO**: Δ mbits ≤ 0 o IC superior ≤ 0.
- Lo mismo se informa para S2 solo (w = 1); el veredicto oficial es el de la mezcla.
- Si ambos (base y S2) quedan ≈ 0 mbits contra uniforme, se anota: el régimen de esa era era casi azar para estos rasgos.
