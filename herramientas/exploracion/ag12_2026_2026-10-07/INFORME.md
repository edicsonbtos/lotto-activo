# ag12 en 2026 — réplica de estabilidad y tramo fresco (2026-10-07)

Criterio escrito antes de calcular: `PREREGISTRO.md`. Todo es reproducible con los scripts de esta carpeta
(`bajar_fresco.py` → `calcular_fresco.py` → `analizar.py` → `extra_regla.py`, `cruce_sombra.py`; salidas en `salida_analizar.txt`, `resultados.json`).
No se tocó producción, historial, predicciones ni `servidor.py`; sin commit ni push. Nada se reajustó.

## Veredicto
| Pregunta | Veredicto |
|---|---|
| **ag12 V1 frente al ensamble** (criterio preregistrado) | **NO CONCLUYENTE, con signo a favor.** Fresco Δ +22,7 mbits, IC90 [−1,9; +44,7] cruza 0 (n=249, no puede decidir); los 3 trimestres son positivos; la réplica (no virgen) da +20,1 [IC90 +13,1; +27,0]. |
| **ag12_rd** (ag12 + regla RD) | **NO CONCLUYENTE** (mismo motivo; fresco IC90 [−1,4; +45,2] en mbits frente a ensamble_rd). |
| **Regla RD en Top-15** (independiente de ag12) | **PASA en sentido formal, pero frágil**: fresco +1,57 pp/ficha IC90 [+0,49; +3,13], trimestres +2,8/+2,1/+2,5, réplica +2,47 [+1,59; +3,36]; el volteo de signo en el fresco solo da p=0,12 (n=249 es poco). La prueba sólida es la réplica, que ya estaba vista. |
| **Hipótesis mié–vie** | **NO se sostiene en 2026**: mié–vie +17,0 vs resto +22,7 mbits, contraste −5,7 [−21,8; +10,5], p permutación 0,49. El +15 de desarrollo no se replicó. No usar. |

Lo que SÍ se puede decir con honestidad: ag12 no se rompió en 2026 (9 de 9 meses y 7 de 7 días de la semana con Δ>0, los 3 trimestres >0, placebos
limpios), pero **no hay prueba virgen**: la réplica es la 2.ª ciega partida en rebanadas, y el único tramo fresco es demasiado corto para decidir.

## 1. Datos y reproducibilidad
- Réplica: filas 9357..12510 (2026-01-01..2026-09-16) con fechas corregidas en memoria y sin los días tocados por la corrección: n=2.959 sorteos, 247 jornadas.
  (La 2.ª ciega usó 3.055 porque incluía diciembre 2025.) Declarada **réplica de estabilidad**, no prueba virgen.
- Fresco: filas ≥12511 = 2026-09-16 8:00..2026-10-07 13:00, n=249, 22 jornadas. Bajados de la fuente oficial; 84 filas contrastadas con `oficial_multi.csv`
  y 8 con el historial local: 0 discrepancias. RD Int fresco (257 sorteos) sin discrepancias en el solape.
- Matrices recalculadas desde la fila 9357 con el mismo código: coinciden **exactamente** (diferencia máxima 0,0) con las guardadas de la 2.ª ciega para ensamble, ag12 V1 y V0.
- Modelos: ensamble_v2 con pesos de producción, ag12 con `parametros_V1.json` (λ=30, ajustados con filas <9357), sin ningún reajuste.

## 2. ag12 V1 − ensamble congelado (Δ mbits e IC95 por bloques de jornada; Top-N en pp; Top-5 escalonado en pp de retorno por ficha)
| Tramo | n | Δ mbits [IC95] | Top-3 | Top-5 | Top-15 [IC95] | Top-5 esc. pp/ficha [IC95] |
|---|---|---|---|---|---|---|
| **Réplica 2026 (ene–16 sep)** | 2.959 | **+20,1 [+11,8; +28,3]** | +0,44 | +1,69 | +2,10 [+0,5; +3,7] | +8,0 [−0,1; +16,2] |
| **Fresco (16 sep–7 oct)** | 249 | **+22,7 [−6,2; +49,3]** (IC90 [−1,9; +44,7]) | +4,82 | +3,61 | +6,43 [+0,4; +12,1] | +31,6 [+7,5; +55,4] |
| Todo 2026 | 3.208 | +20,3 [+12,5; +28,5] | +0,78 | +1,84 | +2,43 [+0,9; +4,0] | +9,8 [+2,2; +17,8] |

Niveles en la réplica: ensamble Top-3/5/15 = 12,54 / 19,80 / 49,68 %; ag12 = 12,98 / 21,49 / 51,77 %. Fresco: 10,44 / 17,27 / 46,59 % contra 15,26 / 20,88 / 53,01 %.

**Por trimestre** (Δ mbits [IC95]): T1 ene–mar **+27,0** [+12,5; +41,7] · T2 abr–jun **+18,6** [+4,3; +33,0] · T3 jul–16 sep **+14,0** [−0,2; +27,5]. Signo igual en los tres,
con tendencia a la baja (27 → 19 → 14) que luego vuelve a +22,7 en el fresco: no se puede descartar un encogimiento, ni afirmarlo.

**Por mes** (n≈190-370 cada uno, IC anchos): ene +34,5 · feb +6,7 · mar +38,9 · abr +22,4 · may +19,1 · jun +14,2 · jul +9,3 · ago +20,4 · sep(1–16) +10,6.
Nueve de nueve positivos; solo ene y mar tienen el IC95 entero >0. No es un único mes quien sostiene el resultado (feb, jul y sep son los flojos).

**Por día de la semana** (Δ mbits, réplica+fresco): lun +27,8 · mar +16,7 · **mié +16,3 · jue +6,9 · vie +27,9** · sáb +31,7 · dom +14,7. Todos positivos.
**Hipótesis única declarada (mié–vie > resto): +17,0 vs +22,7; contraste −5,7 [−21,8; +10,5], p=0,49** (solo réplica: −9,7 [−26,3; +6,8], p=0,27). Rechazada para 2026.
(En Top-5 escalonado mié–vie sí sale más, +17,9 vs +3,9 pp/ficha, pero esa métrica es la ruidosa y el jueves aporta +30 con n=444: no es evidencia.)

## 3. Potencia del tramo fresco
Error típico del Δ en el fresco: **14,3 mbits** (22 jornadas). **Efecto mínimo detectable** con IC90 unilateral 5 % y potencia 80 %: **35,5 mbits**.
Potencia si el efecto real es +19,4: 39 %; +10: 17 %; +5: 10 %. O sea: ni aunque ag12 valga lo de la ciega este tramo podía confirmarlo (salvo suerte).
La réplica entera (SE 4,2) tiene EMD 10,5 mbits y potencia 77 % para +10: por eso allí sí se ve.

## 4. Placebos (todos coherentes con un efecto real, ninguno "pasa" por fuga o artefacto)
- Volteo de signo por jornada: réplica p<0,0001; fresco p unilateral 0,07 (dos colas 0,14).
- Efecto de par invertido (coeficientes T1–R3 con signo cambiado): Δ **−17,2** [−24,8; −9,3] en la réplica y −48,3 en el fresco (cae mucho, como debe si el mecanismo es real).
- Rasgos de par barajados entre jornadas de la misma hora (30 veces): media +0,95 (sd 2,1) en la réplica, −8,8 en el fresco: cero.
- Prueba directa del mecanismo (O/E de repetir un par reciente bajo el ensamble, 2026): T2 (s1→i a 2-7 d) **O/E 0,60, z −5,1**; T1 0,32; R2 0,70; fresco T2 O/E 0,26 (z −2,6).
  El mecanismo existe en 2026 y es el mismo de desarrollo; lo que no se sabe es cuánto de eso se convierte en ventaja jugable con n pequeño.

## 5. ag12_rd y reglas RD
- **ag12_rd como lo mide la sombra (multiplicadores 0,50/0,75) frente al ensamble:** réplica +32,2 [+23,6; +40,4]; fresco +28,2 [−7,0; +60,3].
  **Base justa (ensamble con los mismos multiplicadores):** réplica +20,2 [+12,0; +28,5]; fresco +23,2 [−5,8; +49,3]. Es decir, ~+12 mbits del "ag12_rd" son de la parte RD, no de ag12.
- **Jugada real (Top-5 escalonado + regla de cambio RD, ag12 frente a ensamble, pp/ficha):** réplica **+9,0 [+0,6; +17,2]** (p volteo 0,016); fresco +31,6 [+7,1; +55,7] (p 0,017, pero n=249);
  todo 2026 **+10,75 [+3,0; +18,7]**; por trimestre +4,7 / +12,4 / +10,1 (todos >0, IC95 cruzan 0). La regla sola sobre el ensamble: +1,5 [+0,2; +2,8] pp/ficha.
- **Regla RD en Top-15 (Top-15 ponderado 3-3-3-2-2-1×10, con − sin, pp/ficha):** ensamble: réplica **+2,47 [+1,59; +3,36]**, fresco +1,57 [0,00; +3,46], trimestres +2,78 / +2,10 / +2,52.
  Sobre ag12: réplica +2,25 [+1,19; +3,26], fresco +2,10. Conteos del fresco: 98 cambios, ganó el de RD 1 vez y el 16.º 3 veces (réplica: 1.067 cambios, 9 y 53).
  Placebo con el animal de RD barajado: réplica real +2,47 contra media −0,11 (sd 0,54), p=0,001; fresco p=0,20.
  El efecto en 2026 (+2,4) es más del doble que en desarrollo (+0,97 en 2024-25): ya estaba visto, no tomarlo como estimación de futuro.

## 6. Cruce con la sombra en vivo (solo descriptivo; NO independiente del fresco)
`/api/sombra` (n=135 desde 2026-09-26): ag12 113,1 vs ensamble 112,6 mbits (Δ +0,5); Top-15 51,1 vs 46,7 %; ag12_rd 116,9.
La misma retro-cuenta partida: **16-25 sep (n=112, antes de la sombra): Δ +46,4 [+13,1; +78,0]; 26 sep–7 oct (n=137, las mismas fechas que la sombra): Δ +3,4 [−41,2; +40,1]**.
Consistente con el vivo (+0,5 vs +3,4; pequeñas diferencias de 8:00 y de n). Conclusión: **toda la ganancia del fresco viene de los primeros 112 sorteos; en las fechas de la sombra es ≈0**,
tan ruidoso como todo lo demás (error típico ~20). No decide nada, ni a favor ni en contra.

## 7. Cuánto n falta y qué atajos son legítimos
Con la σ por sorteo medida (≈234 mbits) y IC90 unilateral 5 % con potencia 80 %: **+19,4 → 900 sorteos; +15 → 1.505; +10 → 3.385; +5 → 13.540**.
Descontando los 249 de hoy: +19,4 → ~650 más (~54 días, hacia 2026-12-01); **+10 → ~3.140 más (~260 días, ~junio de 2027)**. A 12 sorteos/día.
(La sombra preregistrada cuenta desde 2026-09-26: n≥931 hacia el 2026-12-14; esa regla no se cambia con este análisis.)

Atajos: **no hay uno que valga.**
- Agrupar con RD Int con el mismo mecanismo: ya medido, Δ +0,5 [−3,1; +4,2] (ciega 3) → no aporta señal que sumar; LARD −14. Sumarlos solo diluye.
- Agrupar épocas: la sellada 2019-2023 dio −1,2 y 2026 +20: heterogéneo (z≈4,4 en la auditoría); promediarlas no es legítimo.
- Reducir la varianza evaluando solo mié–vie o solo ciertas horas: sería una variante nueva sobre datos ya mirados, y además mié–vie no se replicó.
- Lo único más potente y limpio es la prueba directa del mecanismo (O/E, ya hecha: z −5,1 en 2026), pero responde "¿el operador evita pares?" (sí), no "¿ag12 gana en la jugada?".
- Seguir la sombra con la regla de "no concluyente" preregistrada de antemano (seguir hasta ~3.400 con el mismo criterio o descartar) es el camino honesto.

## 8. Límites que hay que tener presentes
1. La réplica NO es prueba virgen (filas ≥9357 ya fueron la 2.ª ciega de ag12); aquí solo se mide estabilidad.
2. El fresco son 22 jornadas: el bootstrap por jornadas es optimista con tan pocos bloques (por eso se contrasta con volteo de signo y permutación).
3. Las 135 filas de la sombra están dentro del fresco; no son una segunda confirmación.
4. Se miraron muchos cortes (9 meses, 7 días, 3 trimestres): solo el criterio preregistrado (fresco + trimestres) cuenta como veredicto; el resto es descripción.
5. El fresco usa fechas sin corregir en el cálculo de los rasgos (igual que la 2.ª ciega); la auditoría midió que eso es inocuo (Δ 26,90 vs 26,91).
