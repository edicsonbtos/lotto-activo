# PRERREGISTRO — "animal del día" (2026-09-27)

Idea del usuario: antes del primer sorteo, decir 1, 2 o 3 animales de los que **al menos uno sale en el día**, sin importar la hora.

## Método congelado (candidato A, el único que va a la prueba)
- Ranking del día = probabilidades de ensamble_v2 para el **primer sorteo** del día (walk-forward, solo días anteriores).
- Se eligen los k primeros, k = 1, 2, 3.
- El candidato B (tabla de días desde la última aparición) quedó **descartado en desarrollo** (por debajo del azar en la 2.ª mitad) y no se prueba.

## Resultado en desarrollo (ya visto, `python animal_dia.py dev`)
| | 1.ª mitad | 2.ª mitad |
|---|---|---|
| k=1 | 32,9 % vs 27,7 % (z +2,12) | 36,7 % vs 29,9 % (z +2,59) |
| k=2 | 54,3 % vs 48,2 % (z +2,19) | 60,0 % vs 51,5 % (z +2,99) |
| k=3 | 70,4 % vs 63,3 % (z +2,67) | 75,4 % vs 66,8 % (z +3,21) |

## Métrica primaria y umbral de falsación
- Por k: aciertos del día contra el azar exacto del día, 1 − C(38−D, k)/C(38, k) (D = animales distintos ese día).
  z = (aciertos − esperados) / √Σp(1−p).
- **PASA para k si z ≥ 2,39** (Bonferroni por 3 k, bilateral 0,05/3). Si z < 2,39 → NO PASA para ese k.
- Secundaria (sin veredicto): retorno por ficha jugando 1 ficha por animal en cada sorteo **hasta que sale**, paga 30, IC95 por bootstrap de días.

## Tramos ciegos para esta idea (cada uno se corre UNA vez, `python animal_dia.py ciega`)
1. **Primario — época reciente**: historial.txt filas [9357, 12511), 2025-12-17..2026-09-16, sin los días de fecha corrida
   (misma lista EXCLUIR que motor_nuevo/reciente). P = `motor_nuevo/reciente/P_ens_reciente.npy` (ensamble_v2 congelado).
2. **Secundario — tramo sellado 2019-01-07..2023-09-03**: `motor_nuevo/sellado/sellado_la.txt` desde la fila 2000,
   P = `motor_nuevo/sellado/P_ens_sellado.npy`. Época vieja (días de 10-11 sorteos), el ensamble rinde la mitad ahí.

Honestidad: esos tramos ya se usaron para evaluar el ensamble y ag12, pero **nunca para esta idea**. La idea y el método se
fijaron solo con el desarrollo. La confirmación definitiva sería el marcador en vivo.
