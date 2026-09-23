# PRE-REGISTRO — Hilo 7: RD Internacional con memoria cruzada de Lotto Activo

Escrito el 2026-09-23, rama `hilo7-rdint-cruzado`, ANTES de ver ningún resultado del modelo sobre el
histórico largo de RD Int (`datos_multiloteria/rdint_hist.csv`, bajado hoy desde 2023-09-04).

## Origen de la hipótesis (ya contaminado)
`datos_multiloteria/test_b_dependencia.md` (ventana 2026-04-13 .. 2026-09-13): RD Int (h:30) casi
nunca repite el animal de Lotto Activo de h:00 (13/1800 contra 48 esperados, z=−5,1) ni el de la hora
anterior (9/1800, z=−5,7). La dirección inversa no aparece (z=−1,4). Esa ventana ya se miró: **no
sirve para confirmar nada**.

## Tramos (fijados por fecha, antes de mirar)
| Tramo | Fechas | Uso |
|---|---|---|
| Calentamiento | 2023-09-04 .. 2024-02-29 | solo historia para el walk-forward |
| **Desarrollo** | 2024-03-01 .. 2025-06-30 | construir, elegir y ajustar TODO |
| **Prueba ciega** | 2025-07-01 .. 2026-04-12 | UNA sola mirada, al final, anotada en `registro_final.jsonl` |
| Descubrimiento | 2026-04-13 .. 2026-09-13 | ya visto; se reporta aparte como réplica, no decide |
| En vivo | 2026-09-14 en adelante | marcador real |

Walk-forward estricto: la predicción del sorteo RD Int de las h:30 del día d solo usa RD Int hasta
h−1:30 del día d y Lotto Activo hasta **h:00 del día d** (sale 30 min antes; es información legítima
si el usuario apuesta después de verlo). Nada posterior.

Tablero RD Int: el que se observe (se espera 37 números, 0..36). Azar = 1/K observado. El pago es 30x:
el equilibrio por animal es 1/30 y el del Top-3, 10 %.

## Modelos
- **B0 (solo RD Int):** evitación intradía propia + curva de hueco propia + hora, logit multinomial
  con los mismos bloques de jornada que `herramientas/modelos/secuencia_v3.py` / `intradia_v2.py`.
- **B1 (cruzado):** B0 + indicadores "el animal salió en Lotto Activo a las h:00", "…a las h−1:00", y
  "salió hoy en Lotto Activo" (conteo).

## Hipótesis y criterios de falsación
**H1 (E1, principal).** B1 mejora a B0.
- Métrica primaria: Δ log-verosimilitud en mbits por sorteo, B1 − B0, en desarrollo.
- IC95 por bootstrap de bloques de jornada (12 sorteos).
- PASA si Δ ≥ +5 mbits Y el límite inferior del IC95 es > 0, en AMBAS mitades del desarrollo.

**H2 (E1 económica).** B1 gana plata en desarrollo.
- Top-3 de B1 ≥ 10,5 % en desarrollo, Y retorno por ficha del Top-3 plano > 0 en ambas mitades.
- Además se reporta el Top-5 escalonado 2-2-2-1-1. No se elige otro plan mirando la tabla.

**H3 (E2, apuesta por valor).** Jugar solo los animales con p·30 ≥ 1,10 (umbral fijo), con fichas
proporcionales a (30p−1)/29 redondeadas a 1-3.
- PASA si el retorno por ficha es > al del Top-5 escalonado en ambas mitades del desarrollo, en
  RD Int (con B1) y/o en Lotto Activo (con la caché `calor_cache.npz`), por separado.

**H4 (E3, dirección inversa).** Lotto Activo gana al saber lo que RD Int sacó.
- Sonda: el logit congelado de ensamble_v2 (caché) + indicadores "salió en RD Int a las h−1:30" y
  "salió hoy en RD Int". Se ajusta solo el coeficiente nuevo.
- PASA si Δ ≥ +5 mbits con IC95 > 0 en ambas mitades. Se espera que FALLE (z=−1,4 en el test B).

## Reglas
- Todo contraste entre grupos de sorteos se estratifica por hora (Mantel-Haenszel).
- No se cambian umbrales, lags ni tramos después de ver los números de desarrollo. Si hay que hacerlo,
  se anota aquí con fecha y motivo ANTES de volver a correr, y cuenta como una comparación más.
- Antes de mirar la prueba ciega: auditoría de `revisor-sesgo` (fuga por la hora 8:30 / h:00,
  alineación de fechas, huecos de días sin sorteo).
- Prueba ciega: se corre UNA vez con el modelo y el plan congelados. Éxito = Top-3 de B1 > 10 % y
  Δ mbits B1−B0 con IC95 > 0. Si falla, el hilo 7 se cierra como el hilo 6.

---
## ENMIENDA 2026-09-23 (después del desarrollo, ANTES de la prueba ciega)
Motivo: la auditoría (revisor-sesgo + revisor Python) marcó grados de libertad no anotados. Se congelan así:
- **B0** = `secuencia_v3` corrido solo con RD Int, walk-forward desde la fila 2000 (elegido en dev frente a
  intradia_v2: +108 contra +105 mbits).
- **B1** = `herramientas/rdint/modelo.py` tal cual: features [LA h:00 == i], [LA (h−1):00 == i],
  [salió hoy en LA hasta h:00, binario, sin contar h ni h−1]; `cruzado(R=250, minimo=500, lam=1)`.
- **H3 / E2**: se usa la lectura LITERAL de la regla, **1 ficha plana** a cada animal con p·30 ≥ 1,10 (la
  reescala "el mejor lleva 3 fichas" se eligió mirando dev y se descarta). Cuenta como una comparación más.
- **H4** (dirección inversa), definida así: features para LA h:00 = [RD (h−1):30 == i] y [salió hoy en RD
  antes de h:00, sin contar (h−1):30]; walk-forward con `modelo.cruzado(R=250, minimo=500, lam=1)` sobre el
  logit congelado de ensamble_v2 (`calor_cache.npz`). Es el esquema principal; el ajuste por cuartos
  queda como sensibilidad. En dev pasó (+12,6 mbits), en contra de lo esperado.
- Resultado del desarrollo: H1 PASA (+19,9 mbits [+14,6, +24,8]), H2 PASA por la estimación puntual
  (Top-3 10,93 %; casi todo viene de B0), H3 frágil, H4 PASA.

### Prueba ciega (una sola corrida, `herramientas/rdint/prueba_ciega.py`)
- RD Int: filas del tramo test (2025-07-01 .. 2026-04-12), con los datos truncados al primer sorteo 'desc'.
  Éxito E1 = Top-3 de B1 > 10 % Y Δ mbits B1−B0 con IC95 > 0. Se reportan también el retorno del Top-3
  plano, el del Top-5 escalonado y el de E2 literal (informativos).
- H4: filas de Lotto Activo con fecha en [2025-07-01, 2025-12-17). Son las únicas del tramo test de RD que
  están en `calor_cache.npz`; OJO: son filas de DESARROLLO de LA, así que el ensamble no es ciego ahí; lo
  ciego es la parte RD, con coeficientes walk-forward. Éxito H4 = Δ mbits con IC95 > 0.
- Se anota en `herramientas/registro_final.jsonl`.
