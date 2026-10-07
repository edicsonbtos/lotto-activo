# S2 en 2026, prueba hacia adelante (pre-registro, 2026-10-07, antes de ver un solo sorteo nuevo)

## Por qué
S2 (motor nuevo, LightGBM con experto normal y relajado, C-90) no pasó las pruebas ciegas en 2024-25 (C1 justo, C2 y C3 no).
Eso no lo descarta: el operador cambia de régimen y 2026 es el régimen vigente. Pero PRUEBA26 (2026-07-01..10-05) ya se miró
más de 5 veces y S2 ya se ajustó viéndola, así que NO sirve para confirmar. La confirmación de 2026 solo puede venir de
sorteos que no existían cuando se congeló S2.

## Candidato congelado
- S2 solo y S2+PROD con w = 0,75 (`investigacion/2026-10-06/motor0/S2/`). Sin reajustar hiperparámetros ni rasgos.
- Reentreno mensual estricto (el día 1 de cada mes, solo con datos anteriores). Es lo que C3 mostró que necesita (el retraso
  de 1 mes le quita el 74 % de la ventaja).
- Variante regularizada S2r (única permitida, declarada ahora): igual que S2 pero con feature_fraction 0,7 y sin los rasgos
  de importancia por debajo del rasgo aleatorio de control. Se corre junto a S2; no se elige entre las dos después.

## Datos
Sorteos de Lotto Activo con fecha ≥ 2026-10-06. Los pronósticos se congelan ANTES de cada sorteo y se guardan en
`/api/sombra` (como `ventana_8am`). No se mira nada antes de n = 730 sorteos (≈ 2 meses de 12 al día × 61 días).

## Métricas (todas contra PROD congelado en el mismo momento, estratificadas por hora)
1. Δ mbits de la mezcla w = 0,75 contra PROD, IC 90 % por bloques de jornada (12 sorteos).
2. Top-15: Δ puntos de acierto pareado.
3. Plata: Top-5 escalonado con regla de cambio RD, retorno por ficha contra el equilibrio 1/30; diferencia pareada.

## Regla de decisión (fijada ahora)
- REAL en 2026: Δ mbits con IC 90 % > 0 Y plata pareada ≥ 0 (punto) en n = 730, y lo mismo en la mitad más reciente.
- NULO: Δ mbits IC 90 % incluye 0 o es negativo en n = 730 → S2 se archiva como "ventaja de ajuste que no se sostuvo".
- Entre medias (Δ > 0 solo en puntual): se extiende hasta n = 1460 y se decide ahí, sin cambiar la regla.
- No se mira antes de n = 730 para parar por éxito. Si es negativo a n = 365 por más de −10 mbits con IC 90 % < 0, se
  puede parar por fracaso.

## Qué NO se hace
- No se usa PRUEBA26 para elegir, ajustar ni reajustar S2 ni S2r.
- No entra en la jugada en vivo mientras no esté REAL; hasta entonces solo sombra.
- Si cambia el régimen (la cola mié-vie vuelve a otro día), no se reajusta: se anota y se sigue contando.
