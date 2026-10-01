# PREREGISTRO — Camino 1: reentrenamiento con peso a lo reciente (Lotto Activo)

Escrito el 2026-09-30 ANTES de calcular ninguna variante. No se cambia después de ver resultados.

## Antecedente que obliga a ser honesto
`lotto-activo-motor/motor_nuevo/ag04_no_estacionario` (2026-09-25) ya probó en desarrollo que adaptar más rápido
los PESOS del ensamble (Kalman, olvido corto) y dos submodelos rápidos (intradia, haz) da +0,2 a +0,6 mbits: nada.
Lo nuevo aquí: (a) también se acelera **secuencia_v3**, el submodelo con más peso (~0,64), que ag04 no tocó;
(b) ventana móvil dura de 6 meses; (c) reentreno semanal; (d) la mirada única a los últimos 6 meses.

## Datos
`historial_la.txt` de esta carpeta = historial.txt con la corrección de fechas 2026-09-29 (igual que servidor.py)
+ API oficial desde 2026-09-16 hasta 2026-09-29 (12.671 sorteos). Verificado: 5.147 sorteos comunes con la API, 0 diferencias.

## Línea base ("ensamble fijo")
ensamble_v2 tal cual: intradia_v2 + secuencia_v3 + haz_v1 con sus parámetros de producción, combinados con
`ensamble.ajustar_pesos` (R=250, tau=3000, λ=5), submodelos desde la fila 1000. Ya reentrena walk-forward.

## Variantes (4, fijadas ahora)
- **V1 semivida corta**: secuencia_v3 tau=1000; intradia_v2 tau=500, ventana=2500; haz_v1 vida_media=1000,
  ventana=3000, cada=250; combinador tau=1000.
- **V2 ventana móvil de 6 meses** (~2.200 sorteos, todos con el mismo peso): secuencia_v3 solo últimos 2.200
  (tau=None); intradia_v2 tau=None, ventana=2200; haz_v1 vida_media=1e9, ventana=2200, cada=250; combinador
  con peso 1 en los últimos 2.200 sorteos y 0 antes.
- **V3 reentreno semanal** (84 sorteos = 7 días × 12): secuencia_v3 R=84; intradia_v2 R=84; haz_v1 cada=84;
  combinador R=84. Olvidos de producción.
- **V4 mezcla lenta + rápida**: 6 componentes (los 3 de producción + los 3 de V1), combinador de producción.

## Elección (solo desarrollo, filas [2000, 9357))
Todo es walk-forward (entrenar hasta T, predecir el bloque siguiente, avanzar). Métrica: Δ mbits frente a la
línea base (log2(38·p(sale)) por sorteo × 1000). IC95 por bootstrap de jornadas (día = 12 sorteos), B=2000.
**Barra de desarrollo**: Δ ≥ +3 mbits, IC95 inferior > 0 y Δ > 0 en las dos mitades.
Se elige la variante con mayor Δ en desarrollo (aunque no pase la barra: entonces se informa como NO PASA,
y la confirmación queda solo como información).

## Confirmación única (2026-04-01 .. 2026-09-29, 2.111 sorteos)
Se corre UNA sola vez, con la variante elegida y la línea base, walk-forward sobre todos los datos.
ADVERTENCIA: para LA las filas ≥ 9357 (desde 2025-12-17) ya se miraron varias veces en otros hilos (registro_final,
prueba reciente de ag12, filtros de la tarde...). Este resultado es una **réplica débil**, no una prueba limpia.
El juez final es el marcador en vivo.

Se reporta, total y por mes: mbits, Top-5 y Top-15 (tasa), retorno por ficha del Top-5 escalonado 2-2-2-1-1 (8 fichas),
del Top-15 ponderado 3-3-3-2-2-1×10 (23 fichas) y del Top-15 plano (15 fichas), paga 30.
Δ con IC95 por bootstrap de jornadas.

**PASA** solo si: la variante pasó la barra de desarrollo **y** en la confirmación Δ mbits > 0 con IC95 inferior > 0.
**NO PASA** en cualquier otro caso. Un Top-5/Top-15 mejor sin mbits significativo no cuenta.

Informativo (no decide): "ensamble congelado al 2026-03-31" (sin reentrenar en los 6 meses) para ver cuánto
importa reentrenar.

## Qué falsa la hipótesis
Si ninguna variante pasa la barra de desarrollo, o la confirmada da Δ ≤ 0 o IC que cruza 0: el operador no cambia
de costumbre a una velocidad que un reentreno más frecuente o más corto aproveche; el ensamble ya se adapta lo suficiente.
RD Internacional: fuera de este preregistro (su tramo de confirmación también está gastado); no se mide.
