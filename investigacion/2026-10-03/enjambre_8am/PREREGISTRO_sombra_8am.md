# Pre-registro: sombra de la ventana de fecha a las 8:00 (escrito el 2026-10-03, antes del primer sorteo puntuable)

La cuenta empieza con el sorteo de las 8:00 del **2026-10-04**. No se ha visto ningún dato posterior a 2026-09-29.

## Qué se mide
`/api/sombra` → bloque `ventana_8am`. Solo sorteos de las 8:00 (hora 0) resueltos desde 2026-10-04.
- Base: `ensamble_exp`, es decir, el pronóstico congelado (`scores`, que ya lleva el ajuste del primer sorteo) por
  `exposicion.aplicar` (multiplicadores congelados del 2026-10-01).
- Variante: `exposicion.aplicar_8am`, que es la base × **0,59** a los números día−1, día y día+1 (solo 1..36; el día 1 no
  toca el "0"). El 0,59 se ajustó solo en dev: (25 + 0,5) / (42,7 + 0,5), sobre P_aj × exposición, en los primeros sorteos.
  **Congelado.**
- Se reportan:
  - `ventana_obs` (veces que el ganador cayó en la ventana);
  - `ventana_esp` (suma de las probabilidades de la base en la ventana);
  - O/E;
  - Top-5 de la base y de la variante;
  - diferencia en mbits (variante − base) con IC 90 % por jornadas.

## Criterio
- **Freno (solo para apagar):** desde n ≥ 180 primeros sorteos, se mira una vez por trimestre. Si **O/E ≥ 1,0**, la
  variante se descarta. Esto cubre una vuelta al régimen de 2023-2024T2, cuando la ventana salía de más.
- **Decisión única a n = 730** (≈ 2028-10):
  - **Pasa** si se cumplen las dos condiciones:
    - Poisson unilateral p < 0,05 de O contra E (con E ≈ 48, O ≤ 36);
    - límite inferior del IC 90 % por jornadas de la diferencia en mbits > 0.
  - **Potencia** (auditoría revisor-sesgo): 0,85 si la razón real es 0,64; 0,54 si es 0,75 (maldición del ganador).
- Nada cambia la jugada sin el OK del usuario. La variante no entra en la jugada antes de pasar.

## Por qué no se aplica ya a la jugada
- La auditoría (revisor-sesgo, 2026-10-03) da un p corregido honesto de ≈ 0,1 para la parte propia de las 8:00, y de
  ≈ 1 en la familia de 30 contrastes del día.
- Entre 2023-09 y 2024-T2 la ventana salía de MÁS en el primer sorteo (1,42-1,68 contra el azar). Desde 2024-T3 sale
  de menos (0,40, estable en 9 trimestres). Es un cambio de régimen elegido a posteriori.
- El salto del Top-5 de 54 a 61 en prueba no se vio en dev (134 → 137).
