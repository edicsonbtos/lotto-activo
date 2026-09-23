# Diario del vivo: Lotto Activo (h:00) y RD Internacional (h:30)

Bitácora de lo que pasa en el marcador en vivo, día por día. **No es evidencia para cambiar
el modelo:** las rachas de aciertos o fallos ya se probaron y no predicen el siguiente sorteo
(ver `racha_favorito.md`). Sirve para ver si algo se rompe y para no juzgar el modelo por un
día suelto. Solo cuentan pronósticos congelados antes del sorteo.

Referencia (prueba ciega): LA Top-5 19,5 %, Top-15 49,5 %. RD Top-5 ≈ 17-20 %, Top-15 ≈ 50 %.
En 12 sorteos, un día con **0 aciertos en el Top-5** pasa 1 de cada 13-14 días (7,4 %);
con **4 o menos en el Top-15**, 1 de cada 5 días (20 %).

## Por día — Lotto Activo (ensamble_v2)

| Día | Sorteos | Top-5 | Top-15 | Puesto medio del ganador |
|---|---|---|---|---|
| 2026-09-15 | 10 | 3 | 6 | 13,6 |
| 2026-09-16 | 11 | 0 | 1 | 27,3 |
| 2026-09-17 | 11 | 0 | 4 | 20,1 |
| 2026-09-18 | 11 | 3 | 5 | 16,9 |
| 2026-09-19 | 10 | 2 | 5 | 15,1 |
| 2026-09-20 | 11 | 1 | 6 | 18,5 |
| 2026-09-21 | 11 | 3 | 6 | 13,1 |
| 2026-09-22 | 11 | 4 | 7 | 12,3 |
| 2026-09-23 | 12 | 0 | 4 | 19,8 |
| **Total** | **98** | **16 (16,3 %)** | **44 (44,9 %)** | |

Lo esperado en 98 sorteos: Top-5 ≈ 19 (margen de 9 a 23 aciertos), Top-15 ≈ 48.
Va algo por debajo, dentro de lo normal. Días en 0 Top-5: 3 de 9 (el azar da ~1 de 13).
Es de lo que hay que vigilar, pero 9 días todavía no alcanzan para decir que algo cambió.

## 2026-09-23

**Lotto Activo: 0 de 12 en el Top-5, 4 de 12 en el Top-15.** Racha abierta: 12 sorteos sin
Top-5 y 6 sin Top-15.

| Hora | Salió | Puesto | Top-5 congelado |
|---|---|---|---|
| 8:00 | 16 Oso | 9 | 30 24 19 36 31 |
| 9:00 | 3 Ciempiés | 31 | 7 9 2 18 4 |
| 10:00 | 36 Culebra | 14 | 2 18 0 8 7 |
| 11:00 | 28 Zamuro | 19 | 18 10 8 29 35 |
| 12:00 | 34 Venado | 15 | 30 12 23 31 24 |
| 1:00 | 2 Toro | 9 | 30 23 31 12 24 |
| 2:00 | 29 Elefante | 21 | 23 12 30 24 31 |
| 3:00 | 4 Alacrán | 21 | 23 19 31 5 24 |
| 4:00 | 17 Pavo | 24 | 9 18 8 10 15 |
| 5:00 | 5 León | 17 | 9 8 18 10 35 |
| 6:00 | 4 Alacrán | 34 | 9 7 15 18 8 |
| 7:00 | 27 Perro | 23 | 9 7 15 18 13 |

Por qué falló:
- **El Top-5 se quedó pegado:** 30-12-23-31-24 de 12:00 a 3:00 y 9-18-8-7 de 4:00 a 7:00. Esos
  animales no salieron en LA en todo el día. Todos llevaban 1 o 2 días sin salir, la ventana
  en que el operador suele "reciclar" y que el modelo premia. Hoy el reciclaje no llegó a LA:
  31, 30 y 23 salieron en **RD** (11:30, 12:30 y 3:30), no en LA. Ojo: "si salió hoy en RD, LA ya no lo
  da" es justo lo que probó H4 (LA usando lo de RD del día) y **falló a ciegas**; un día no la revive.
- **Alacrán (4) repitió en el día** (3:00 y 6:00). El operador casi nunca repite el mismo
  día, por eso el modelo lo tenía en el puesto 34. Ese sorteo no se podía acertar.
- 3 ganadores en los puestos 9, 14 y 15: cerca, pero fuera del Top-5.
- Un día así pasa 1 de cada 13-14 días con el modelo funcionando bien.

**Regla de cambio RD:** actuó 2 veces (12:00 sacó a 31, 1:00 sacó a 30; en los dos entró 19).
No ganó ninguno de los cuatro. Diferencia: 0 fichas.

**RD Internacional:** en vivo con congelado desde las 4:30. Puestos del ganador: 7 (4:30),
12 (5:30), 4 (6:30), 22 (7:30). Top-5 1 de 4, Top-15 3 de 4. Ponderado +28 fichas.

**LA ↔ RD entrelazados, hoy:** en la secuencia de 24 sorteos (LA 8:00, RD 8:30, LA 9:00…)
ningún animal se repitió de un sorteo al siguiente (el azar daría ~0,6). Salieron 21 animales
distintos de 24; el azar da ~18. Coincide con lo descubierto: el operador evita repetir
también entre los dos juegos.
