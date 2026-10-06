# A5 — ¿"mié-vie recicla menos" se convierte en mejora? (2026-10-06)
Pre-registro: `PREREGISTRO.md`. Script principal: `a5.py` → `salida.txt`. Extras NO pre-registrados (adversariales,
escritos tras ver `salida.txt`): `a5_extra.py` → `salida_extra.txt`, `a5_perm.py` → `salida_perm.txt`, `a5_bits.py` → `salida_bits.txt`.
Aviso: la hipótesis mié-vie se eligió mirando TODO 2026. AJUSTE/PRUEBA solo es fuera de muestra para los parámetros.

## Candidatas (Δmbits por sorteo contra el motor, IC 90 % por jornadas)
| | directa (ene-may → jun-oct) | inversa (jun-oct → ene-may) | ΔTop-5 / ΔTop-15 (directa) | Δ retorno T5 | veredicto |
|---|---|---|---|---|---|
| C1 reciclados ×m en mié-vie | m 0,795: **+0,5 [−3,8; +4,8]** | m 0,880: +3,2 [+1,2; +5,2] | −0,1 / −0,9 pp | −1,5 %/ficha | DUDOSO |
| C2 temperatura mié-vie | T 0,56: **+3,3 [−2,8; +10,1]** | T 0,675: +9,2 [+4,9; +13,8] | 0 / 0 (no cambia el orden) | 0 | DUDOSO |
| C3 7 multiplicadores (σ 0,10) | +1,6 [−0,4; +3,7] | +1,8 [+0,6; +3,0] | +0,1 / +0,6 pp | 0,0 | DUDOSO |
| C0a placebo (sábado) | +1,3 [+0,3; +2,4] | 0,0 [−2,1; +2,1] | | | (ruido) |
Ninguna pasa el criterio (IC > 0 en las dos direcciones). El placebo del sábado da IC > 0 en una dirección: el ruido
alcanza para eso. En las 35 ternas, mié-jue-vie es la 1.ª en ajuste pero la 7.ª de 35 en la prueba directa con C1.
Con C2 sí es la 1.ª de 35 en ambas direcciones, y aplanar otros días (o todos) EMPEORA: el exceso de confianza es propio
de mié-vie en 2026. **Dev 2024-25 va al revés:** el m de ene-may aplicado a dev da −6,7 mbits [−8,8; −4,7]; dev
habría elegido m = 1,08 y T = 1,10.

## Lo que sí es fuerte (pero no se convierte en mejora del modelo)
- Información del motor sobre el azar, mbits/sorteo: dev mié-vie +141 / resto +111; ene-may +29 / +128; jun-oct +43 / +143.
- Permutación de etiquetas de día entre jornadas de 2026, eligiendo la PEOR de 35 ternas (corrige la selección):
  Top-15 O/E 0,837 → p < 0,0002 (0 de 5000); plata −30 pp → p = 0,006, y ambas mitades a la vez p = 0,0006.
- O sea: en 2026, mié-vie el motor sabe mucho menos. Pero lo que falla NO es "cuánto reciclar": bajar los reciclados no
  sube el Top-5 ni el Top-15. Solo aplanar (C2) recupera mbits, y eso no cambia la jugada.

## Plata: "no jugar mié-vie" (Top-5 escalonado del motor, 8 fichas/sorteo)
| PRUEBA jun-oct | fichas | neto | retorno | máx. caída |
|---|---|---|---|---|
| todos los días | 11.808 | +1.422 | +12,0 % | 258 |
| sin mié-vie | 6.816 | +1.734 | +25,4 % | 138 |
| solo mié-vie | 4.992 | −312 | −6,2 % | 432 |
Mié-vie − resto: −31,7 pp [IC90 −49,6; −14,1] en PRUEBA y −29,0 [−49,5; −8,8] en AJUSTE (estratificar por hora da lo
mismo: el diseño está balanceado, 12 sorteos por jornada). En dev mié-vie rendía +26,1 % contra +23,6 %: el patrón no
existía. Con el pago 30 el azar da −21 %; mié-vie en 2026 sigue por encima del azar (~−1 %), pero no del equilibrio.

## Veredicto
**DUDOSO como mejora del modelo; REAL como descripción de 2026, sin mecanismo explotable claro.** Ninguna candidata pasa.
Valdría, como mucho, +1-3 mbits/sorteo (C2) y 0 en plata. La única palanca con dinero es dejar de apostar mié-vie
(+312 fichas y la mitad de la caída en PRUEBA), y descansa en un régimen que en 2024-25 era al revés y que se eligió
mirando 2026. Recomendación: no tocar el motor; dejar que decida el pre-registro en vivo ya escrito
(2026-10-07..2027-01-06). Si se quiere ya mismo, como mucho bajar la apuesta mié-vie (no subirla nunca), en sombra.
