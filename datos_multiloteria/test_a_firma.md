# TEST A — Firma de politica por loteria

Ventana: 2026-04-13 .. 2026-09-13 (5 meses). N = tablero observado
(ver tableros.md). FDR: Benjamini-Hochberg q=0.05 entre las 15
celdas (5 loterias x 3 subtests). Umbral: |z| > 3 y p_fdr < 0.05.

## Referencia control — Lotto Activo en historial.txt (12.502 sorteos, 3 anos, solo lectura)
- a) evitacion intradia: z = -19.83 (p=0)  esperado 1607.0 vs observado 823
- b) bump 13-27: z = -2.07 (p=0.038)  observado 4193 vs esperado 4297.7
- c) chi2 primero: 62.0 (p=0.0045), n=1081, top=0 (62 veces)

## lottoactivo — **MISMA FIRMA que el control**
- senal: a_evitacion_intradia (z=-7.59)

## lottoactivordint — **MISMA FIRMA que el control**
- senal: a_evitacion_intradia (z=-11.17)

## lagranjita — **MISMA FIRMA que el control**
- senal: a_evitacion_intradia (z=-4.71)

## selvaplus — **DISTINTA (senal con signo/patron diferente)**
- senal: b_bump_13_27 (z=+26.13)
- senal: c_chi2_primero (z=chi2)

## guacharoactivo — **MISMA FIRMA que el control**
- senal: a_evitacion_intradia (z=-7.34)

| loteria | N | subtest | estadistico | p | p_fdr | senal |
|---|---|---|---|---|---|---|
| lottoactivo | 37 | a_evitacion_intradia | z=-7.59 | 3.31e-14 | 1.24e-13 | SIG |
| lottoactivo | 37 | b_bump_13_27 | z=-1.31 | 0.192 | 0.319 | no |
| lottoactivo | 37 | c_chi2_primero | chi2=43.9 | 0.172 | 0.319 | no |
| lottoactivordint | 37 | a_evitacion_intradia | z=-11.17 | 0 | 0 | SIG |
| lottoactivordint | 37 | b_bump_13_27 | z=-0.03 | 0.978 | 0.994 | no |
| lottoactivordint | 37 | c_chi2_primero | chi2=27.6 | 0.841 | 0.994 | no |
| lagranjita | 37 | a_evitacion_intradia | z=-4.71 | 2.51e-06 | 6.28e-06 | SIG |
| lagranjita | 37 | b_bump_13_27 | z=-0.45 | 0.656 | 0.894 | no |
| lagranjita | 37 | c_chi2_primero | chi2=22.7 | 0.959 | 0.994 | no |
| selvaplus | 100 | a_evitacion_intradia | z=-0.61 | 0.542 | 0.812 | no |
| selvaplus | 100 | b_bump_13_27 | z=+26.13 | 0 | 0 | SIG |
| selvaplus | 100 | c_chi2_primero | chi2=296.9 | 1.23e-21 | 6.13e-21 | SIG |
| guacharoactivo | 76 | a_evitacion_intradia | z=-7.34 | 2.2e-13 | 6.59e-13 | SIG |
| guacharoactivo | 76 | b_bump_13_27 | z=-1.33 | 0.185 | 0.319 | no |
| guacharoactivo | 76 | c_chi2_primero | chi2=47.6 | 0.994 | 0.994 | no |

## Clasificacion final
- **lottoactivo**: MISMA FIRMA que el control
- **lottoactivordint**: MISMA FIRMA que el control
- **lagranjita**: MISMA FIRMA que el control
- **selvaplus**: DISTINTA (senal con signo/patron diferente)
- **guacharoactivo**: MISMA FIRMA que el control