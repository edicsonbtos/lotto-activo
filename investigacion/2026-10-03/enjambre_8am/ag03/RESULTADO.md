VEREDICTO: PROMETEDOR (solo C1, que es el efecto "fecha" ya conocido). La hipótesis propia de ag03 da NULO: el primer sorteo NO tiene otra distribución marginal.

# ag03 — ¿El primer sorteo tiene otra distribución marginal?

## Qué se miró (≈ 95 contrastes en cal/dev, sin tocar prueba)
- 55 contrastes en `explorar_dev.py` (A: contra 1/38, B: contra las demás horas, C: contra P_aj por era, D: era 9:00 contra 8:00,
  E: popularidad). Además 23 de dispersión por hora (`dispersion_dev.py`), ~15 de ajuste (`ajuste_dev.py`) y C3.
- Agrupaciones: animal (chi², 37 gl), 0/00, par/impar, bajo/alto (1-18/19-36), docenas, columnas, rojo/negro de la ruleta americana,
  4 y 2 sectores contiguos del cilindro americano, 1-31 contra 32-36. Popularidad: número = día del mes, día±1, hora en reloj de 12 h y mes.
- "Datos publicados" (`scraping/datos_publicados.py`): solo se guardan en el volumen de Railway desde el 2026-10-01. No hay copia
  local, así que no hay animales "populares" que probar. El único indicio de popularidad es el de la fecha y la hora (SKILL, 2026-10-01).

## Dev: la distribución marginal del primer sorteo es indistinguible del azar y del motor
| contraste (primer sorteo) | resultado |
|---|---|
| chi² por animal contra 1/38 (cal+dev, n = 818) | 17,9 / 37 gl. Por era: 9:00 29,3 (p 0,81) y 8:00 32,7 (p 0,67) |
| 0/00 · par · bajo · docenas · columnas · color · sectores · 1-31 | p entre 0,33 y 0,98 contra 1/38. Contra las demás horas, p entre 0,24 y 1,00 |
| contra P_aj (dev, n = 635), las 22 categorías | O/E entre 0,93 y 1,19, todos los p > 0,30. chi² por animal (O contra E) 25,3 / 37 gl, p 0,93 |
| era 9:00 contra 8:00 | animal p 0,16. Mínimo por agrupación: 1-31, p 0,12. Residuos por animal entre eras: ρ −0,23 (p 0,16) |
| dispersión por hora (23 franjas) | el primer sorteo no se aparta: P(chi² ≤ obs) es 0,19 a las 9:00 y 0,33 a las 8:00 |
| motor en el primer sorteo | +135 mbits contra la uniforme (9:00 +48, 8:00 +197). En las demás horas, +121 |

El chi² conjunto de 17,9 es bajo (cola inferior ≈ 0,003). Sale de que las dos eras se compensan entre sí (ρ −0,23, n.s.). Dentro de
cada era no hay subdispersión. Con unos 95 contrastes, eso no pasa la corrección. **Ningún contraste de la distribución marginal tiene p < 0,05.**

Lo único con p < 0,05 en dev fue la "popularidad" por fecha. En el primer sorteo, día+1 dio O/E 0,35 (p 0,004, Holm ≈ 0,20), el día
del mes 0,57 y la hora 12 h 0,79. Pero no es propio del primer sorteo: en las demás horas de dev, el día da 0,61 y día+1 da 0,69. Es la
señal ya conocida del 2026-10-01, que el motor no captura. Así nacieron C1 y C2. C3 prueba si el primer sorteo la esquiva *más*.

## Candidatos (pre-registrados en `PREREGISTRO.md`, multiplicadores de dev en `multiplicadores_dev.json`)
- C1_fecha: código = día ×0,607 y código = día+1 ×0,661 (ajustados en todas las horas de dev).
- C2_fecha_hora: C1 más código = hora 12 h ×0,777.
- C3_primer_esquiva_mas: día ×0,584 y día+1 ×0,368 (ajustados solo en los primeros sorteos). Se contrasta contra el motor ya corregido con C1.

| cand. | dev 9:00 O/E | dev 8:00 O/E | PRUEBA O/E [IC] (n = 261) | p unil. | mbits/primer prueba [IC] | Top-5 | Top-15 | vivo (15) |
|---|---|---|---|---|---|---|---|---|
| C1 | 0,56 | 0,39 | 7/14,0 = **0,50** [0,20; 1,03] | **0,032** | +10,7 [−3,8; +23,1] | 54 → 57 | 132 → 132 | 0/0,8 · +30 mbits |
| C2 | 0,60 | 0,54 | 14/20,9 = 0,67 [0,37; 1,12] | 0,073 | +9,6 [−5,2; +23,0] | 54 → 58 | 132 → 131 | 0/1,3 · +40 mbits |
| C3 | 0,86 | 0,61 | 7/9,0 = 0,77 [0,31; 1,59] | 0,32 | +12,4 [−11,0; +31,9] | 54 → 58 | 132 → 133 | 0/0,6 · +44 mbits |

Dev completo (n = 635): C1 da +12,1 mbits [+2,8; +20,0], Top-5 134 → 137 y Top-15 358 → 370. Parte de la ganancia de dev está
dentro de la muestra, porque los multiplicadores usan todas las horas de dev, incluidos estos 635 sorteos.

En plata (prueba, Top-k plano, pago 30, IC por días), el cambio de retorno por ficha de C1 es Top-5 +6,9 % [−2,3; +18,4] y Top-15 +0,0 %
[−3,1; +3,1]. Son 3 aciertos más de Top-5 en 261 días, y el IC cruza el 0.

## Lectura
- C1 cumple el criterio de PROMETEDOR: p 0,032 < 0,05, con el mismo signo en las dos eras. No llega a CONFIRMADO, que exige p < 0,0017.
  C2 y C3 dan NULO.
- C3 da NULO, y por eso el primer sorteo no esquiva la fecha más que las demás horas. La señal de fecha es global y no distingue el primer sorteo.
- Por eso, lo que pasa no apoya la hipótesis de ag03. Es una réplica fuera de muestra, en los primeros sorteos de prueba, del efecto
  "esquiva el número de la fecha" ya registrado en el SKILL (pendiente de sombra en vivo).

## Recomendación
- Para producción: nada específico del primer sorteo. Cerrar la idea "distribución marginal distinta del primer sorteo" con ~95 contrastes y 0 señales.
- El esquive de fecha (día y día+1, ×0,61 y ×0,66) sigue siendo la mejora más barata pendiente. Afecta a todas las horas: en las demás
  horas de dev suma +5,8 mbits por sorteo. Su lugar es el seguimiento ya previsto (sombra en vivo / `revisor-sesgo`), no un ajuste solo de las 8:00.

Scripts: `comun.py`, `explorar_dev.py` (.out), `dispersion_dev.py`, `ajuste_dev.py` (.out), `ajuste_dev2.py`, `prueba.py` (.out), todos en esta carpeta.
