# Enjambre "motor 2" (2026-10-06): 6 motores o correcciones nuevos, con tramos RECIENTES y una sola mirada a PRUEBA26
Arnés común: `arnes.py`. AJUSTE jul-25..feb-26, ELECCION mar-jun-26, PRUEBA26 jul-oct-26 (registro_prueba26.jsonl).
Comparación con la jugada real (Top-5 de PROD con la regla de cambio de RD): `incremento.py` → `salida_incremento.txt`.

| agente | idea | Δ mbits contra PROD en PRUEBA26 | veredicto del agente | auditoría |
|---|---|---|---|---|
| M1 | detector en línea del "modo relajado" (encuentra solo los días relajados) | −0,3 [−1,0; +0,4] | NO MEJORA | — |
| M2 | calendario (0/48 fugas); corrección adaptativa por grupos de días | +9,5 [+4,1; +14,9] | DUDOSO (grupos vistos en 2026) | — |
| M3 | modelo generativo del operador, β dinámicos | no usó PRUEBA26 (−33 solo; mezcla +0,5) | NO MEJORA | — |
| M4 | LightGBM apilado sobre PROD (34 rasgos + RD) | +19,1 [+5,7; +32,6] | MEJORA | **RECHAZAR tal cual**: no desplegable (RD llega después del congelado; falta lightgbm). Contra PROD×RD, unos +9 [−4; +22]. En plata, contra la jugada en vivo, +0,2 fichas/sorteo [−0,2; +0,6]. ELECCION −4,3 pp |
| M5 | mismas bases, pesos diarios por día de la semana | +2,2 [−0,1; +4,5] | DUDOSO | — |
| M6 | reglas no modeladas: RD (h−1):30 repetido + "pares que se evitan" | +13,2 [+6,5; +19,9] | MEJORA | **RECHAZAR como jugada**: RD1 ya está en la regla de cambio (aporta 0 en plata). par_evita es real y estable (controles al azar ≈ 0), pero +2,5 [−2,6; +7,5]; en plata +2,3 pp [−1,1; +5,8]. Solo sombra |

## Conclusión
- **No hay mejora demostrable EN PLATA sobre lo que se juega hoy.** El motor de producción no cambia.
- Sí hay mejora de **información** (mbits y Top-15). La de M4 es la más grande, pero se concentra en el Top-15 y no en el Top-5
  que se juega. Además, PRUEBA26 no era ciega para el diseño de M4: el régimen de mié-vie y la señal de RD se estudiaron
  con 2026.
- **Hallazgos reales nuevos:**
  1. "Pares que se evitan" (M6): el operador casi no junta ciertos pares en el mismo día; la estructura persiste un año.
  2. El detector de modo relajado (M1) y los β dinámicos (M3) encuentran SOLOS el cambio de domingo a mié-vie. Sirven
     como monitores del régimen.
  3. Sin fugas nuevas de calendario (quincenas, feriados, días de pago, puentes).
- **Bloqueo de diseño encontrado por los auditores:** el pronóstico de h:00 se congela a las (h−1):10-20, ANTES de que
  salga RD (h−1):30. La regla de cambio solo se aplica al mostrar y al puntuar, y `marcador_cambio_rd` no comprueba
  que RD se conociera antes de h:00. Para usar RD dentro del motor haría falta una segunda etapa del congelado (con hora).
- **Siguiente paso propuesto (decide el usuario):** sombra en vivo de ~90 jornadas, con criterio de plata pareado, para
  (a) M4 sin RD en el árbol (variante C) y RD aplicado al jugar, w = 1, y (b) par_evita. Requiere lightgbm en
  requirements.txt y entrenar el modelo fuera de línea cada mes.
