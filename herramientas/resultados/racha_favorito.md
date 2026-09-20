# Racha del favorito: ¿informa? — validación walk-forward

Pre-registro: `PREREGISTRO_racha_favorito.md` (fijado antes de esta corrida).

Histórico completo en disco: 12560 sorteos.
**Recortado a desarrollo: 9357 sorteos (corte 9357). El tramo de prueba no se usa.**
Calculando la matriz walk-forward con `ensamble_v2` (el de producción)…
Listo y cacheado en `wf.npy`.

Base: **7357 sorteos** de desarrollo. Top-3 global 12.89% (azar 7,89%). Top-1 4.53%.

## Descriptivo: ¿qué tan seguido se enfrasca?

- Mismo #1 que el sorteo anterior: **53.7%** de los sorteos.
- Sorteos con racha >= 3: **2391 de 7357 (32.5%)**.

| Racha | Sorteos | Top-3 | Top-1 |
|---|---|---|---|
| 1 | 3405 | 12.48% | 4.52% |
| 2 | 1561 | 12.43% | 3.91% |
| 3 | 859 | 12.34% | 5.70% |
| 4 | 534 | 14.23% | 4.87% |
| 5 | 281 | 16.37% | 3.91% |
| 6+ | 717 | 14.09% | 4.46% |

*(La curva completa es descriptiva. El umbral de la prueba es 3, fijado en el pre-registro: elegir otro al ver esta tabla sería sobreajuste.)*

## El confusor: la racha crece con la hora

| Hora | Racha media | % con racha >= 3 |
|---|---|---|
| 1º | 3.20 | 44.1% |
| 2º | 2.15 | 20.5% |
| 3º | 2.45 | 19.7% |
| 4º | 2.71 | 38.4% |
| 5º | 2.31 | 24.1% |
| 6º | 2.33 | 20.5% |
| 7º | 2.49 | 33.9% |
| 8º | 2.73 | 40.0% |
| 9º | 2.25 | 27.9% |
| 10º | 2.55 | 32.1% |
| 11º | 2.89 | 46.8% |
| 12º | 3.07 | 46.9% |

Por eso la prueba primaria va **estratificada por hora**. Comparar crudo mezclaría el efecto de la racha con el de la hora, que es el artefacto que ya invalidó al HILO 1.

## Pruebas pre-especificadas (Bonferroni α = 0,0167)

### Crudo (referencia, NO decide)

- racha >= 3: **329/2391 = 13.76%**
- racha <= 2: **619/4966 = 12.46%**
- diferencia **+1.30 pts**, IC95 bootstrap por día [-0.24, +2.84], z = +1.55 (p = 0.1204)

### T1 (PRIMARIA) — Mantel-Haenszel estratificado por hora

| Hora | n racha>=3 | Top-3 | n racha<=2 | Top-3 |
|---|---|---|---|---|
| 1º | 164 | 29 (17.7%) | 208 | 24 (11.5%) |
| 2º | 130 | 21 (16.2%) | 505 | 60 (11.9%) |
| 3º | 125 | 11 (8.8%) | 510 | 68 (13.3%) |
| 4º | 244 | 30 (12.3%) | 391 | 35 (9.0%) |
| 5º | 153 | 24 (15.7%) | 482 | 51 (10.6%) |
| 6º | 130 | 14 (10.8%) | 505 | 67 (13.3%) |
| 7º | 215 | 18 (8.4%) | 420 | 52 (12.4%) |
| 8º | 254 | 33 (13.0%) | 381 | 46 (12.1%) |
| 9º | 177 | 31 (17.5%) | 458 | 60 (13.1%) |
| 10º | 204 | 30 (14.7%) | 431 | 61 (14.2%) |
| 11º | 297 | 40 (13.5%) | 338 | 42 (12.4%) |
| 12º | 298 | 48 (16.1%) | 337 | 53 (15.7%) |

**z_MH = +1.383**, p = 0.1666, OR_MH = 1.110

### T2 — estratificado por quintil de la probabilidad que el modelo se da a sí mismo

**z_MH = +1.107**, p = 0.2684, OR_MH = 1.087

Si T1 sobrevive pero T2 no, el efecto es redundante: sólo marca sorteos que el modelo ya señalaba como buenos.

### T3 — ¿acierta el propio animal en racha? (Top-1, estratificado por hora)

- racha >= 3: 118/2391 = 4.94%
- racha <= 2: 215/4966 = 4.33%
**z_MH = +1.131**, p = 0.2581, OR_MH = 1.145

*Variante con reset en frontera de día (descriptivo): z_MH = +0.820.*

## Veredicto según el criterio pre-comprometido

**HIPÓTESIS DESCARTADA.** |z_MH| = 1.383 < 2,0 en la prueba primaria. Según el pre-registro esto se archiva aquí: no se prueban otros umbrales de racha ni otros cortes, y no se cambia nada del modelo ni de la apuesta.

Lo que se vio en el marcador en vivo (16,7% vs 4,4% en 87 registros) era ruido de muestra pequeña con un corte elegido a posteriori.

---

Generado por `herramientas/exploracion/racha_favorito.py`. Sólo desarrollo; el tramo de prueba no se leyó.
