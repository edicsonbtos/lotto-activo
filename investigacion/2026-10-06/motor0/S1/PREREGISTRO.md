# S1 · Selector de sorteos (CUÁNDO jugar el Top-15) · PRE-REGISTRO (escrito antes de mirar resultados)
Arnés: `../../motor2/arnes.py`. Tramos: AJUSTE (jul-25..feb-26) y ELECCION (mar-jun-26). ANTIGUO solo como pasado de
entrenamiento. PRUEBA26 NO se evalúa salvo que la parte 1 pase en ELECCION (regla de motor2: si no gana, no se gasta); si se
mira, una vez, registrada y marcada "contaminada".

## Objetivo y etiqueta
y = 1 si el ganador cae en el Top-15 del motor (orden estable de P). Dos motores por separado: PROD y M4 (motor2_M4.npz).
Antes de 2025-07 M4 = PROD (no se reentrenó ahí), así que para M4 el entrenamiento previo usa en la práctica etiquetas de PROD.

## Rasgos (todos con información anterior a la hora h:00 del sorteo)
1. hora (0..11) y día de la semana.
2. Modo relajado: prior π_d y posterior q_h del filtro V3 de `../../motor2/M1/m1.py` con sus parámetros congelados
   (`final.json`). Desviación declarada: esos 9 parámetros se ajustaron en AJUSTE; su fuga sobre la etiqueta Top-15 es indirecta.
3. Rendimiento de HOY: sorteos ya resueltos hoy, aciertos Top-15 de hoy, O−E de hoy (aciertos − masa Top-15 esperada).
   Últimos días: O−E del Top-15 en los últimos 1, 3, 7 y 28 días (completos, anteriores a hoy).
4. Repeticiones de hoy (ganadores de hoy que ya habían salido hoy) y reciclaje de hoy (ganadores de hoy que salieron ayer o anteayer).
5. Masa del Top-15, entropía de P (bits) y p1 (máximo).
6. Rendimiento reciente por hora (EWMA del O−E a esta misma hora en días pasados, vida media 30 días) y por día de la
   semana (EWMA del O−E diario en ese día de la semana, vida media 4 semanas); EWMA global diaria (vida media 7 días).
7. RD (h−1):30: disponible (h ≥ 1 y dato en rdint_historial.txt) y si su animal está dentro del Top-15 del motor.
   Aviso: el pronóstico se congela antes de RD (h−1):30; el selector se decidiría después de RD (h−1):30 y antes de h:00.

## Modelos (walk-forward, reajuste mensual: el modelo del mes m usa solo filas con fecha < día 1 de m)
- C0 constante: tasa de acierto Top-15 del pasado de entrenamiento (con el mismo olvido).
- C1 masa: P̂ = masa del Top-15 (el motor ya calibrado; R6/hilo 6 dicen que no repite).
- LR: logística L2 (C = 0,05, rasgos estandarizados, hora y día one-hot), pesos con vida media 365 días.
- GBM: LightGBM binario pequeño (7 hojas, 150 árboles, tasa 0,03, ≥ 200 filas por hoja, L2 = 10), mismos pesos.
- Calibración: Platt sobre los últimos 90 días del entrenamiento (modelo ajustado sin esos 90 días) y aplicada al modelo
  reajustado con todo el pasado.
Criterio para "seguir" (parte 1 PASA): en ELECCION, Δ log-loss contra C0 < 0 con IC 90 % por jornadas entero bajo 0,
el mismo signo en AJUSTE, y AUC > 0,5 con IC 90 % (bootstrap por días) sin tocar 0,5. Se reporta también contra C1.
El modelo oficial (LR o GBM) se elige por log-loss en ELECCION.

## Estrategias (parte 2), filas con RD disponible como en `incremento.py`, AJUSTE y ELECCION
- REF: Top-5 escalonado de PROD (2-2-2-1-1) con la regla de cambio RD (h−1):30, todos los sorteos.
- T15 plano (15 fichas) y T15 ponderado 3-3-3-2-2-1×10 (23 fichas), todos los sorteos, PROD y M4.
- T15 plano / ponderado solo si P̂ ≥ u, u ∈ {0,50; 0,52; 0,54; 0,56; 0,58; 0,60}; u se elige en AJUSTE maximizando fichas
  netas por día; se reportan todos los u en ELECCION por transparencia, pero vale el elegido.
- Graduado: multiplicador 0 si P̂ < 0,50; 1 si [0,50; 0,55); 2 si [0,55; 0,60); 3 si ≥ 0,60 sobre el T15 plano.
- REF + T15 plano cuando P̂ ≥ u (informativo).
Métricas: retorno por ficha (IC 90 % bootstrap por jornadas), fichas netas por día, máxima caída (fichas), % de sorteos jugados,
Top-15 en los sorteos jugados.
VEREDICTO: MEJORA si la parte 1 pasa Y una estrategia con selector supera en ELECCION (a) a la REF en fichas netas por día y
(b) a su versión "todos los sorteos" en retorno por ficha, ambas con IC 90 % pareado por jornadas > 0. DUDOSO si las
estimaciones puntuales son mejores pero algún IC cruza 0. NO MEJORA en otro caso.

## Rachas de la mañana (parte 3)
Mañana = 8:00-12:00 (h 0..4); tarde = 13:00-19:00 (h 5..11). Para sorteos de la tarde: (a) tabla descriptiva del O−E de la
tarde por aciertos de la mañana (0-1, 2, 3, 4-5 de 5) en cada tramo; (b) logística walk-forward base (hora, día, masa) contra
base + O−E de la mañana, y contra base + q de M1 + O−E de la mañana. Pasa si Δ log-loss < 0 con IC 90 % bajo 0 en AJUSTE y ELECCION.
