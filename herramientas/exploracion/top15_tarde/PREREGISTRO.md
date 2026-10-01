# PRERREGISTRO — Top-15 de los dos últimos sorteos con descarte (2026-10-01)

Escrito ANTES de calcular cualquier métrica de la idea. Las predicciones walk-forward (`predecir.py`) se
generan aparte y no miden nada de lo que aquí se pregunta.

## La idea (del usuario)
En los **dos últimos sorteos del día** de los dos juegos que se juegan
(Lotto Activo 18:00 y 19:00 = hora 10 y 11; RD Internacional 18:30 y 19:30 = hora 10 y 11) se descartan:
1. **HOY**: los animales que ya salieron hoy en ese mismo juego ("no repite").
2. **HERMANO**: el último resultado del otro juego. Para LA h:00 es RD (h−1):30 del mismo día; para RD h:30
   es LA h:00 del mismo día (sale 30 minutos antes).
3. **FRÍO(4)**: los animales que llevan **más de 4 días de calendario** sin salir en ese juego
   (fecha de hoy − fecha de su última salida > 4). Un animal que salió hoy no es frío.

El Top-15 filtrado es el orden del modelo actual con los descartados enviados al final (conservan su orden
entre ellos): se juegan los 15 primeros. Si quedan menos de 15 sin descartar, los huecos se llenan con los
mejores descartados, para que siempre se comparen 15 animales contra 15. Se informa cuántas veces pasa.

## Lo que ya se sabía (declarado para no engañarse)
- `PREREGISTRO_filtros_tarde.md` (2026-09-29) probó lo mismo con **FRÍO(7)**: no pasó. Su prueba ciega
  usó LA filas ≥ 9357 y RD 2025-07-01..2026-09-13, es decir, **ya miró 2026** con una variante parecida.
- `top15_70/INFORME.md`, plan 1: sacar del Top-15 lo que salió hoy en LA no mejora (todas las horas).
- La regla RD (h−1):30 viene de H4b, descubierta mirando filas de LA ≥ 9357.
Por eso la prueba en 2026 es una **réplica débil**; el juez definitivo es el marcador en vivo.

## Modelo actual (comparador)
- LA: `ensamble_v2` walk-forward (pesos reajustados en 2000 + k·250), historial con fechas corregidas
  (`enjambre_2026-09-30/reentreno/historial_la.txt`, hasta 2026-09-29). En la web la regla RD solo
  reordena el 5º y el 6º, así que **el Top-15 que juega la web es el Top-15 del ensamble**.
- RD: B1 = B0 (secuencia_v3 solo RD) · exp(b·x) con b walk-forward (como `cache_todo.npz`). Producción usa b
  congelado (ajustado con datos hasta 2026-04-12); el walk-forward evita que 2026 se use para ajustar b.

## Tramos
- **Desarrollo (se mira primero, elige):** LA filas [2000, 9357) (2024-03-07..2025-12-19); RD tramo `dev`
  (2024-03-01..2025-06-30). Solo horas 10 y 11.
- **Ciego 2026 (UNA vez, `python top15_tarde.py ciega`, se niega a repetir):** 2026-01-01..2026-09-29,
  los dos juegos, horas 10 y 11. Se informa por mitades (hasta 2026-05-15 y después), sin veredicto aparte.

## Hipótesis y umbrales (bootstrap pareado por jornada, 10.000 réplicas; 4 pruebas → IC 98,75 %)
- **H1 (la idea tal cual): HOY ∪ HERMANO ∪ FRÍO(4).** Por juego: Δ = acierto Top-15 filtrado − acierto Top-15
  actual. **PASA** si el IC 98,75 % de Δ queda entero por encima de 0.
- **H2 (la mejor del desarrollo).** En desarrollo se miden 23 variantes por juego: las 7 combinaciones no
  vacías de {HOY, HERMANO, FRÍO(d)} con d ∈ {3, 4, 5, 6, 7} cuando entra FRÍO. Se elige la de mayor Δ en
  desarrollo (empates: menos reglas; luego d = 4). Solo se prueba en 2026 si su Δ de desarrollo es > 0 y no es
  la misma que H1. Mismo criterio de PASA.
- Potencia declarada: con ~540 sorteos por juego en 2026, el IC 98,75 % de Δ medirá unos ±3 a ±4 puntos.
  Una mejora real de 1 punto **no se puede ver** en 2026; si H1 no pasa, eso no prueba que el efecto sea 0,
  y se mira el desarrollo (más sorteos) para el tamaño.

## Descriptivo (sin veredicto)
- **D1. ¿El modelo ya lo sabe?** Por grupo (HOY; HERMANO que no está en HOY; FRÍO(4) que no está en los
  anteriores; lo que queda): salidas observadas contra lo esperado por azar (1/38) y por el modelo (suma de P).
- **D2. Qué lleva hoy el Top-15 actual:** cuántos animales de HOY, HERMANO y FRÍO(4) trae de media, cuántas
  veces ganó uno de ellos, y cuántas veces ganó uno de los que entran a reemplazarlos.
- **D3. Calibración del Top-15 actual:** probabilidad que el modelo le da a su Top-15 (suma de P) contra el
  acierto real; horas 10-11 y todas las horas; desarrollo y 2026.
- **D4. Hasta dónde llega el Top-15:** acierto de cada variante; Top-N necesario para 50/60/70 %;
  jugar plano todo lo que queda (C).
- **D5. Retorno por ficha** del Top-15 ponderado (3-3-3-2-2 + 1×10 = 23 fichas) y del Top-15 plano, actual
  y filtrado, con IC 95 %. Mismas reglas en todas las horas, para contexto.
