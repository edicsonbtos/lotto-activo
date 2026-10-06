# M3: modelo generativo del operador con β dinámicos. Veredicto: NO MEJORA (PRUEBA26 sin usar)

Pre-registro: `PREREGISTRO.md`, sin cambios. Código: `m3.py` (rasgos y ajuste walk-forward), `corre_x.py`, `uno.py`
(una configuración), `tabla.py` (rejilla), `mezcla.py`, `final.py`, `fuga.py`, `betas.py` → `betas.txt`.
Matriz final: `scratchpad/motor2_M3.npz` (`P` = M3 solo con vm 120 y λ 30; `P_mezcla_w01` = PROD^0,9·M3^0,1; `t`).

## Modelo
Es un logit condicional sobre los 38 animales con 29 rasgos interpretables:
- ya salió hoy y hoy × avance del día;
- el sorteo anterior;
- salió hace k días, para k = 1..7;
- 8 tramos de hueco;
- las reglas del primer sorteo (primero de ayer, de hace 2 días y de hace 3 días);
- la fecha, la fecha+1, la fecha−1, la hora en reloj de 12 h y la ventana de las 8:00;
- la misma hora de ayer;
- la frecuencia de 7 y de 30 días.

A eso se suman δ por día de la semana para hoy, d1, d2 y d3, con contracción λ hacia el común. Los β se reajustan **cada día** por máxima verosimilitud ponderada con olvido 0,5^(edad/vm). El ajuste usa inicio en caliente, gradiente exacto y un Hessiano acumulado con olvido. Con 2 iteraciones por día el resultado es igual al de 5 (diferencia de 0,003 mbits).

`A.chequear_fuga`: **OK**. La prueba cubre todo el proceso: rasgos, ajuste y predicción. Cómputo total: unos 17 min de CPU.

## Rejilla (mbits sobre el azar; PROD: AJUSTE 160,8 · ELECCION 79,0 · AJ+EL 133,3)
| vm \ λ | ∞ (sin día de la semana) | 300 | 30 | 3 |
|---|---|---|---|---|
| 30 | 88,2 | 88,7 | 90,7 | 88,8 |
| 60 | 97,8 | 98,8 | 101,5 | 101,3 |
| **120** | 100,7 | 102,2 | **104,7** | 104,7 |
| 240 | 99,8 | 101,5 | 102,8 | 102,1 |
(AJ+EL agrupados.) Elegido según el pre-registro: **vm = 120 días, λ = 30**. El efecto por día de la semana suma unos
+4 mbits en AJ+EL y +7 en ELECCION (46,0 contra 39,1). La vida media corta (30 días) es claramente peor: hay pocos datos para 57 parámetros.

## Tabla de `evaluar`
| variante | tramo | Δ mbits contra PROD [IC 90 %] | Top-5 (prod) | Top-15 (prod) | ret Top-5 (prod) |
|---|---|---|---|---|---|
| M3 solo | AJUSTE | −26,3 [−38,6; −14,0] | 19,4 (21,2) | 52,2 (54,6) | +15,9 % (+29,1) |
| M3 solo | ELECCION | −33,0 [−48,8; −17,2] | 16,2 (20,1) | 48,9 (48,6) | −3,3 % (+23,4) |
| PROD^0,9·M3^0,1 | AJUSTE | +3,0 [+1,8; +4,3] | 21,2 (21,2) | 55,1 (54,6) | +30,2 % (+29,1) |
| PROD^0,9·M3^0,1 | ELECCION | +0,5 [−1,2; +2,1] | 19,9 (20,1) | 49,0 (48,6) | +21,8 % (+23,4) |

Barrido de la mezcla en ELECCION:

| w | 0,1 | 0,2 | 0,3 | 0,5 |
|---|---|---|---|---|
| Δ | +0,46 | +0,08 | −1,1 | −6,1 |

En AJUSTE el óptimo es w ≈ 0,3, con +5,3. Que el w óptimo se desplace hacia 0 en el tramo más reciente es otra señal en contra. El criterio para gastar PRUEBA26 (IC 90 % inferior > 0 en ELECCION) **no se cumple**, así que PRUEBA26 **no se miró**.

## ¿Aprende solo el cambio de día? Sí, en la dirección correcta, pero de forma débil
β_hoy efectivo (común + δ_dow), media por periodo (más negativo = más evita repetir en el día):

| periodo | lun | mar | mié | jue | vie | sáb | dom |
|---|---|---|---|---|---|---|---|
| 2024-07..2025-06 | −2,02 | −2,04 | −1,95 | −2,03 | −2,09 | −2,08 | **−1,70** |
| 2025-07..2025-11 | −2,47 | −2,47 | −2,37 | −2,44 | −2,46 | −2,47 | −2,29 |
| 2025-12..2026-06 | −2,54 | −2,47 | **−2,32** | −2,40 | **−2,27** | −2,53 | −2,49 |
| 2026-07..2026-10 | −2,25 | −2,20 | **−1,97** | −2,02 | **−1,95** | −2,23 | −2,22 |

Lectura de la tabla:
- En 2024-25 el domingo es el día relajado (+0,3 sobre el resto).
- El domingo vuelve a la norma a lo largo de 2025-07..11.
- Desde 2025-12 el relajo pasa a mié-vie (+0,15 a +0,25).
- Los cambios de β_1..β_3 por día son pequeños (±0,1-0,2) y poco claros; el detalle está en `betas.txt`.

El modelo detecta el cambio, pero con un retraso de meses (vm = 120) y con una amplitud menor que la real. Con vm o λ menores se adapta antes, pero la varianza le cuesta más de lo que gana.

Otros datos:
- Desglose de ELECCION: M3 − PROD da −48 mbits en mié-vie y −23 en el resto. El efecto por día de la semana no rescata mié-vie.
- La mezcla pierde en mié-vie (−1,3) y gana en el resto (+2,9).
- β comunes 2026-03..06:
  - repetición y primer sorteo: hoy −2,24 (+1,69 × avance), sorteo anterior −0,38, primero de ayer −1,22, primero de hace 3 días +0,64;
  - fecha y hora: fecha −0,52, fecha+1 −0,39, hora −0,33, ventana de las 8:00 −0,56;
  - huecos: hueco >130 sorteos entre −0,5 y −0,7.

  Es la estructura conocida del operador.

## Veredicto: NO MEJORA
- El modelo generativo con pocos parámetros es interpretable y se adapta, pero queda 26-33 mbits por debajo de PROD.
- Como mezcla aporta +3 en AJUSTE y +0,5 sin significancia en ELECCION.
- PRUEBA26 no se usó.
- Su valor es descriptivo: es un monitor de β_hoy por día de la semana que muestra sin supervisión el paso de domingo a mié-vie.
