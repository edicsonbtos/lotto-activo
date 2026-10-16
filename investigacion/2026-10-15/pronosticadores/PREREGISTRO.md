# PREREGISTRO: ¿el operador esquiva los animales que publican los pronosticadores?

Escrito el 2026-10-14, ANTES de descargar el histórico de "datos" y de cruzarlo con resultados.
Hasta aquí solo se miró: la estructura de las páginas, que dos sitios tienen archivo por fecha, y los
ganadores de hoy (2026-10-14) para comprobar que la página de hoy no los contiene (no los contiene).

## Hipótesis
El operador esquiva lo más jugado (día del mes O/E 0,5-0,7; hora en 12 h O/E 0,64). Si los "datos" que
publican los pronosticadores mueven la jugada, esos animales deberían salir MENOS de lo que da el motor.
Dirección preregistrada: O/E < 1. Si sale O/E > 1 con IC lejos de 1, lo primero es sospechar
contaminación (página rehecha con los resultados del día), no señal.

## Fuentes (las que se pueden reconstruir hacia atrás)
- **S1 lotoven** — `POST https://lotoven.com/datos/ fecha=AAAA-MM-DD`, bloque "Datos Lotto Activo" (y "Datos Lotto Activo RD Int").
- **S2 loteriadehoy** — `POST https://loteriadehoy.com/datos/animalitos/ fecha=AAAA-MM-DD`, tarjetas "Lotto Activo" (y "Lotto Activo Rd Int").
- **S3 pirámide juegoactivo** — determinista: dígitos DDMMAAAA, cada fila = sumas de vecinos mod 10; el
  "dato" de cada fila es la suma de sus dígitos. Se toman las 8 sumas en 0..36 (las >36 se descartan).
  Verificado con la página de hoy: 14/10/2026 → 16, 25, 17, 34, 18, 9, 10, 0 (igual a la web).
- Sin archivo y fuera de la prueba: pirámide de tuazar (5 animales con regla desconocida, solo hoy/ayer/mañana),
  Top-10 de juegoactivo (frecuencias de los últimos sorteos: equivale a "calientes/fríos", ya cerrado),
  foro El Grupo Sortario (texto libre). Railway guarda las 6 páginas desde 2026-10-02, pero la API solo
  expone si se descargaron, no el contenido.
- Cada fuente da un CONJUNTO por día (sin hora). Los repetidos cuentan una vez. 0 = Delfín, 00 = Ballena.

## Métrica
Para cada sorteo t del día d con conjunto A_d: O_t = 1[ganador ∈ A_d], E_t = Σ_{a∈A_d} p_t(a), con p_t la
probabilidad walk-forward del motor (ya incluye la exclusión de los salidos hoy y el reciclaje).
- O/E = ΣO / ΣE, estratificado por hora (Mantel-Haenszel: O/E_MH = Σ_h O_h / Σ_h E_h, se reporta además
  la tabla por hora). IC 95 % por bootstrap de jornadas (B = 4000, semilla 20261014).
- Prueba principal: **U = S1 ∪ S2 ("datos publicados") en Lotto Activo.** Secundarias: S1, S2, S3 por separado;
  RD Int (réplica, con su propia lista de datos RD y el motor P1 de `cache_todo.npz`, tramo dev).
- Secundaria de confusión: lo mismo quitando de A_d el número del día, día+1 y la hora en reloj de 12 h
  (efectos ya conocidos), para ver si queda algo propio de los pronosticadores.

## Tramos (fijados antes de mirar)
- Motor LA: `verificacion/hilo9/datos/calor_cache.npz` (filas [2000, 9357) del historial congelado).
- **Desarrollo: 2024-03-07 .. 2025-02-03** (filas [2000, 5688), dev-A). Aquí se mira libremente y se ajusta x.
- **Confirmación 1: 2025-02-04 .. 2025-12-14** (dev-B; se para el 14-12 porque desde el 15-12 las fechas del
  historial congelado están corridas). Se mide UNA vez.
- **Confirmación 2 (lo más reciente): 2026-09-15 .. 2026-10-14**, motor congelado en vivo (`/api/mesa`).
  Pocos sorteos: solo informativo, salvo efecto grande.
- El tramo de prueba del proyecto (filas ≥ 9357) no se toca.

## Umbral de falsación
- **PASA** si en confirmación 1 la U de LA da O/E < 1 con IC95 superior < 1, en la misma dirección que el desarrollo,
  y la réplica en RD (dev RD 2024-03-01..2025-06-30) no va al revés (O/E ≤ 1).
- **NO PASA** si confirmación 1 da O/E ≥ 1 o el IC95 cruza 1. Las secundarias no rescatan a la principal.
- Explotabilidad: x = O/E del desarrollo; se aplica p' ∝ p·x sobre A_d (renormalizado) en confirmación 1 y se mide
  la ganancia en mbits por sorteo (IC por jornadas). Se considera útil solo si > 0 con IC que no cruza 0.

## Potencia (antes de mirar)
SE(ln O/E) ≈ 1/√E. Con 80 % de potencia y α = 0,05 bilateral se detecta |ln O/E| ≈ 2,8/√E.
Con ~5 datos/día × 12 sorteos × 0,026 ≈ 1,5 aciertos esperados por día: desarrollo (~330 días) E ≈ 500 → O/E ≈ 0,88;
confirmación 1 (~310 días) E ≈ 470 → 0,88; confirmación 2 (30 días) E ≈ 45 → solo O/E ≲ 0,66.
