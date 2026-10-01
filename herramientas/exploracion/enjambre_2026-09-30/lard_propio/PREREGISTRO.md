# PREREGISTRO — Camino 3: LARD con su propio modelo (2026-09-30)

Escrito ANTES de medir nada sobre LARD con estos modelos. No se cambia después de ver resultados.

## Pregunta
¿Se puede predecir Lotto Activo República Dominicana (LARD, API oficial juego id 3, 14 sorteos h:00 de 8 a 21)
con SU PROPIO historial, usando la misma maquinaria que funciona en Lotto Activo (evitar repetir el mismo día,
reciclar con 1-2,5 días de hueco)?

## Datos
`datos_multiloteria/oficial_multi.csv`, juego 3. 449 días completos (14 sorteos cada uno), 2025-07-01..2026-09-22.
- DESARROLLO: 2025-07-01..2026-01-31. Se evalúa desde 2025-09-19 (los primeros 80 días = 1120 sorteos son
  calentamiento: el modelo necesita ~700 sorteos de pasado para sus ventanas largas).
- PRUEBA CIEGA (intacta, se mira UNA vez): 2026-02-01..2026-09-22 (3276 sorteos).
  Sub-ventana secundaria, misma mirada: 2026-04-01..2026-09-22 ("últimos 6 meses" que pide el usuario).
- Si se logran bajar 2026-09-23..09-29 a un archivo propio (sin tocar el CSV compartido), se reportan
  aparte como anexo descriptivo (98 sorteos, sin poder estadístico).

## Candidatos (todos walk-forward estricto, reajuste cada 250 sorteos, sin fuga)
- U: uniforme 1/38 (referencia).
- H: `hazard_actual` (tasa por tramo de retraso) ajustado con el historial de LARD.
- B: `secuencia_v3` (motor de LA) ajustado SOLO con el historial de LARD.
- C: `secuencia_v3` con coeficientes ajustados en Lotto Activo (historial.txt hasta 2025-06-30, ya pasado
  para todo, sin datos de LARD) y aplicados tal cual a LARD (transferencia).
- M: mezcla 50/50 de B y C.
Se elige UN ganador en desarrollo: el de más mbits. Solo ese va a la prueba ciega (los demás se reportan
en la ciega como descriptivo, sin decidir nada).

## Métricas
1. Principal: mbits por sorteo frente al uniforme (log-verosimilitud), IC 95 % por bootstrap de bloques de
   jornada (bloque = 1 día = 14 sorteos de LARD; el equivalente a las 12 de LA), 2000 réplicas, semilla 7.
2. Top-3 (tasa vs 7,89 %), Top-5 escalonado 2-2-2-1-1 (8 fichas) y Top-15 plano (15 fichas):
   retorno por ficha pagando 30 (y el pago de equilibrio = fichas / fichas esperadas sobre el ganador).
   Pago LARD: 30x según elbrujodelosanimalitos.com (fuente no oficial); si no fuera 30 vale el pago de equilibrio.
3. Por hora: mbits por hora (14 horas) como descriptivo.

## Umbral de falsación (PASA / NO PASA)
PASA si, en la ciega 2026-02-01..2026-09-22, el ganador de desarrollo tiene:
  (a) mbits > 0 con el extremo inferior del IC 95 % de bloques > 0, y
  (b) z de log-verosimilitud >= 3.
Si además el retorno por ficha del Top-5 escalonado o del Top-15 tiene IC > 0, se dice "gana plata"; si no,
"señal sin plata". Cualquier otra cosa: NO PASA. La sub-ventana de 6 meses no puede rescatar un NO PASA.
Si el ganador de desarrollo no supera +5 mbits con IC>0 en desarrollo, la ciega se corre igual (una vez) para
dejar constancia, pero el resultado esperado es NO PASA.
