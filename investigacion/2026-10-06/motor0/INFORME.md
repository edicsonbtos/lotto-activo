# Proyecto "motor 0" (2026-10-06): Top-15 y cuándo jugar
Criterios fijados antes de empezar en `BRIEF.md`. Referencia: Top-5 escalonado de PROD con la regla de cambio de RD
(retorno por ficha +31,0 / +24,9 / +15,3-18,6 % en AJUSTE / ELECCION / PRUEBA26).

## S1: selector de sorteos ("cuándo jugar el Top-15"). NO MEJORA
- El meta-modelo apenas supera a la constante (AUC 0,51-0,56), y lo poco que gana es el día de la semana, ya conocido.
- Jugar el Top-15 solo cuando el selector lo dice da, contra la referencia, −21 fichas por día (plano) y −11 (ponderado) en
  ELECCION. Para igualar a la referencia, el Top-15 plano necesitaría un 62,5 % de acierto, y no pasa del 52 %.
- La racha de la mañana NO predice la tarde (correlación −0,06 a +0,01).
- Aparte: la regla de cambio de RD aplicada también al Top-15 suma +2-3 pp (por pre-registrar).

## S2: motor desde cero (LightGBM, sin PROD ni RD dentro; un experto para días normales y otro para relajados). DUDOSO, mejor resultado del día
| tramo | Δ mbits contra PROD | Δ Top-15 | Top-5 escalonado con RD: S2+PROD 0,75 (PROD) |
|---|---|---|---|
| AJUSTE | +12,6 (mezcla +21,2) | +0,0 (mezcla +0,8) | +30,6 % (+31,0 %) |
| ELECCION | +11,7 (mezcla +17,8) | **+2,4 [+0,2; +4,7]** | **+34,2 %** (+25,0 %) |
| PRUEBA26 (contaminada) | +11,7 (mezcla +16,8) | +2,9 (mezcla +3,9 [+1,4; +6,3]) | +24,7 % (+15,3 %) |
- Es el primer motor hecho desde cero que iguala o supera a PROD. Atacar el Top-15 directamente (lambdarank) vuelve a fallar
  (−25 mbits). El softmax y la mezcla de expertos funcionan.
- La ganancia se concentra en los días relajados de 2026 (mié-vie +5,7 pp en ELECCION; resto +0,2).
- No es "por mucho" y PRUEBA26 no es ciega. **Siguiente paso: sombra en vivo** de la mezcla S2+PROD (w = 0,75) con la regla
  de RD en Top-5 y Top-15, comparada en plata contra la jugada actual. Hace falta lightgbm en Railway y entrenarlo fuera de
  línea cada mes.
