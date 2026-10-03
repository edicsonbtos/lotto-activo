# En vivo y formas de jugar (2026-10-03, hasta las 4 PM)

Reproducción walk-forward del motor (validada contra los congelados) sobre el historial del volumen.
`vivo.py` y `estr.py` leen `hist_hoy.txt` y `wf_hoy.npz` (generado con `../top15_8am_vs_dia/1_walkforward.py`).

## Top-15 en vivo
- Desde el 15-sep: **100/225 = 44,4 %**. El motor esperaba 51,6 %, P = 0,019. Contra lo que el Top-15 rindió
  de verdad en prueba (49,5 %), P = 0,07.
- 15-24 sep: 45,0 %. 25 sep-3 oct: 43,8 %. No hay caída reciente: está igual de bajo desde el primer día.
- En prueba, el 17 % de las ventanas de 7 días quedaron en ≤ 45 % (rango de 32 % a 64 %).
- Lectura: es una racha floja, sumada al exceso de confianza ya medido (el motor promete ~3 pp más de lo que da).

## Retorno por ficha (paga 30)

| estrategia | dev | prueba [IC 95 %] | vivo |
|---|---|---|---|
| Top-1 | +33 % | +20 % [0; +41] | +20 % |
| **Top-2** | **+34 %** | **+28 % [+14; +43]** | 0 % |
| Top-3 | +27 % | +22 % [+11; +33] | −16 % |
| Top-5 escalonado (actual) | +24 % | +18 % [+10; +27] | −12 % |
| valor p > 4 % | +31 % | +30 % [+15; +47] | −1 % |
| Top-15 ponderado | +12 % | +6 % [+1; +10] | −11 % |
| Top-15 plano | +6 % | −1 % [−4; +2] | −11 % |

Riesgo en prueba (peor racha de fallos / caída máxima): Top-2, 85 fallos / 186 fichas. Top-5 escalonado,
29 / 418. Top-15 ponderado, 13 / ~400.

El umbral del 4 % se eligió entre 3 probados, así que hay algo de selección. Top-2 y "valor" no tienen
pre-registro. Antes de cambiar la jugada hay que pre-registrarlos y confirmarlos en vivo (`gestion_banca.VIGILANCIA`).
