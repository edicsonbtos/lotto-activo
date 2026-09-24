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

### Auditoría en enjambre (2026-09-23, 4 auditores, solo lectura)
- **Top-5 "pegado": no es un bug.** Se recalcula en cada sorteo (caché por huella del
  historial + sorteo). Los bloques vienen de `intradia_v2.py:29` (HGRUPOS: 8:00 | 9-11 |
  12-15 | 16-19 × salió ayer/anteayer). Hoy el Top-5 cambió MÁS que otros días: 2,64 animales
  en común entre sorteos seguidos, contra 3,16 de media.
- **Circuito RD ↔ LA: bien.** `b1()` es idéntico a lo validado (×0,208 / ×0,62 / ×1,16), sin
  look-ahead y con las horas alineadas.
- **Corregido:** la regla de cambio en vivo *intercambiaba* el animal de RD con el 6º; lo validado
  lo *quita*, sube a los de abajo y mete al 6º como 5º. Ya están iguales la web, jugada.py y el marcador.
- **Corregido:** `P_MOD_T15` usaba 53,07 % (desarrollo); ahora 49,46 % (prueba ciega). La alarma
  de rachas del Top-15 saltaba de más.
- Calibración en vivo de LA (59 con prob): Top-5 dice 19,7 %, salió 20,3 %. Bien.
- Riesgos menores sin tocar: si LA h:00 se anota después de h:30, RD de esa hora queda sin LA;
  corregir un LA ya usado no recalcula RD.

### Qué esperar el 2026-09-24
- LA 8:00: 9, 8, 7, 15, 18 (los ganadores del 22). A las 8:00 no aplica la regla de cambio.
- RD 8:30: 3, 12, 11, 29, 7; se actualiza solo al salir LA 8:00 (con_la_h=true antes de 8:30).
- En 12 sorteos, cada juego: Top-5 ≈ 2 aciertos (80 %: 1 a 4), Top-15 ≈ 6 (4 a 8).
  Otro día en 0 Top-5: 7,4 % LA, 9,7 % RD. Top-5 escalonado LA: +18 fichas de media en el día,
  pero de −66 a +114 (80 %); 47 % de los días cierran en pérdida.

## Rachas desde el inicio del vivo (2026-09-15 a 09-23, 98 sorteos LA con orden congelado)

| Día | Top-5 | Top-15 | Escalonado (8 f/sorteo) | Ponderado (23 f) | Acum. escalonado | Acum. ponderado |
|---|---|---|---|---|---|---|
| 09-15 | 3/10 | 6/10 | +40 | +70 | +40 | +70 |
| 09-16 | 0/11 | 1/11 | −88 | −223 | −48 | −153 |
| 09-17 | 0/11 | 4/11 | −88 | −133 | −136 | −286 |
| 09-18 | 3/11 | 5/11 | +62 | +47 | −74 | −239 |
| 09-19 | 2/10 | 5/10 | +10 | +10 | −64 | −229 |
| 09-20 | 1/11 | 6/11 | −28 | −13 | −92 | −242 |
| 09-21 | 3/11 | 6/11 | +32 | +47 | −60 | −195 |
| 09-22 | 4/11 | 7/11 | +92 | +137 | +32 | −58 |
| 09-23 | 0/12 | 4/12 | −96 | −156 | −64 | −214 |

- **Top-5:** 16/98 = 16,3 % (esperado 19,5 %). Rachas de fallos, en orden:
  5, 1, **29**, 1, 2, 3, 10, 4, 3, 2, 7, 1, 1, 1, **12 (abierta)**. La de 29 (del 15 noche al 18
  mañana) es la más larga; con el modelo sano, la más larga típica en 98 sorteos es 15 y una de 29 o
  más sale el 3 % de las veces. Esos días ya se auditaron (REPORTE_JORNADA_2026-09-17.md): los
  pronósticos eran correctos, no fue el servidor.
- **Top-15:** 44/98 = 44,9 % (esperado 49,5 %; P(≤44) ≈ 21 %). Rachas de fallos: la más larga 9
  (típica 6; P ≈ 10 %). Rachas de aciertos: 6, 4, 4, 3.
- **Las rachas no se contagian:** Top-5 acierta el 12 % tras un acierto y el 17 % tras un fallo;
  Top-15, el 43 % y el 47 %. Nada de "calentarse" o "enfriarse", igual que en racha_favorito.md.
- **Por tramos:** 15-17: Top-5 3/32 (9 %); 18-22: 13/54 (24 %); 23: 0/12. Media 16 %.
- Vigilar: 3 días en 0 Top-5 de 9 y la racha de 29. Todavía compatible con un modelo sano
  (el total va dentro del margen), pero si el total baja de ~14 % con 300 sorteos, hay que revisar.
