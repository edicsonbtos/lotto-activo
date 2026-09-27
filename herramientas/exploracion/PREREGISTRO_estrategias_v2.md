# PRERREGISTRO — formas de jugar con el motor actual y patrón "domingo" (2026-09-27)

Script: `estrategias_v2.py` (dev ya visto; `ciega` se corre UNA vez → `registro_estrategias_v2.jsonl`).

## Lo visto en desarrollo [2000, 9357)
1. **Estrategias** (13 formas de repartir fichas con las mismas probabilidades del ensamble). En riesgo ajustado
   (Sharpe por sorteo ×100, completo) el Top-5 escalonado actual 9,35 empata arriba con "valor p ≥ 3,6 %" 9,48 y
   "Kelly proporcional" 9,41; Top-3 8,61; Top-15 ponderado 8,93; Top-15 plano 6,14. Ninguna le gana con claridad.
2. **Por hora**: no hay hora mejor que se repita entre mitades (p. ej. 9:00 −0,8 % y +49,5 %). No se prueba nada por hora.
3. **Domingo** (hallazgo nuevo): el motor rinde casi como el azar.
   - mbits del ganador: domingo +9, resto de días +111 a +155.
   - Top-5 observado − esperado: −7,5 pts (z −4,1) y −3,0 pts (z −1,6) en cada mitad.
   - Top-5 escalonado: domingo −22,9 % / +13,6 %; resto +25,0 % / +32,5 %.
   - Mecanismo candidato: el domingo el operador repite más en el día (0,965 repeticiones/día contra 0,595).
   - Quincena, diciembre, otros días: nada que se repita entre mitades.

## Hipótesis primaria (H-dom)
"El domingo el motor da menos señal que el resto de la semana."
- Métrica: Δ = mbits medios del ganador (domingo) − mbits medios (lunes a sábado).
- Tramos ciegos: reciente (historial filas [9357, 12511), sin días de fecha corrida) y sellado 2019-2023.
- IC por bootstrap de jornadas, juntando los dos tramos (cada tramo con su propio Δ, se promedia ponderando por sorteos de domingo).
- **PASA si el IC95 del Δ conjunto queda entero bajo 0 Y el Δ es negativo en los dos tramos.** Si no → NO PASA.

## Secundarias (sin veredicto, descriptivas)
- Repeticiones en el día, domingo contra el resto, en cada tramo.
- Top-5 escalonado: retorno por ficha el domingo y el resto de días.
- Sharpe por sorteo de las 13 estrategias en cada tramo (¿sigue arriba el escalonado?).

Regla práctica que se adoptaría si pasa: **no jugar (o jugar menos) los domingos.** Si no pasa, no se cambia nada.
Salvedad: el tramo reciente ya se usó para el ensamble, ag12 y "animal del día"; el sellado, para ag12 y "animal del día".
Ninguno se usó para esta hipótesis.
