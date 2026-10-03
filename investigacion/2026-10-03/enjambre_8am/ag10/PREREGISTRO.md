# PREREGISTRO ag10 — Forense del hallazgo "el primer sorteo no repite el primero de ayer"

Escrito antes de correr cualquier comparación. No envío candidatos a prueba (papel forense).

## Hipótesis nula de trabajo (la que intento demostrar): el hallazgo es un ARTEFACTO de datos
A. Código: algún paso (ETL, scraper, auto_resultado, fuente_oficial, servidor.registrar/deshacer,
   corrección de fechas 2026-09-29, faltantes 2026-10-03) descarta, corrige o desplaza un primer sorteo
   cuando coincide con el de ayer (o desplaza fechas de modo que cambie qué es "ayer").
B. Datos: hist_la.txt difiere de la API oficial (oficial_multi.csv, juego 1, 2025-07-01..2026-09-22) y/o de
   lottoactivo.csv (LH+TZ, 2026-04-13..) en los primeros sorteos, y en particular hay días en que la fuente
   externa muestra primero(hoy) = primero(ayer) y el historial no.
C. Patrón en la fuente externa sola: si la API oficial por sí sola NO muestra el déficit, es artefacto.
   Controles: RD Internacional (juego 2 y rdint_hist.csv desde 2023-09) y LARD (juego 3).
D. Re-derivar 0,272 / 1,736 en dev (logit L2=1 sobre el ensamble) y comprobar que P_aj fila t solo usa
   primeros sorteos de días anteriores (tp < t, fecha anterior).

## Métricas
- B: nº de (fecha, hora) discrepantes; nº en primer sorteo; nº de "repeticiones primero-ayer" que la fuente
  externa tiene y el historial no (y viceversa).
- C: conteo crudo k/N de primero(hoy)=primero(ayer) frente a azar N/38 (Poisson exacto unilateral), y contra
  "misma hora de ayer" en las demás horas. En la API oficial sola y en los juegos control.
- D: multiplicadores re-derivados vs producción (tolerancia ±10 % relativo en el log); test de fuga
  estructural en las 911 filas de primer sorteo con motor.

## Criterios de decisión (fijados ahora)
- ARTEFACTO (veredicto NULO) si se cumple cualquiera de: (A) hay código que elimine/corrija repeticiones;
  (B) ≥ 2 repeticiones primero-ayer presentes en la fuente oficial y ausentes en el historial, o las
  discrepancias del primer sorteo explican ≥ 1/2 del déficit; (C) la API oficial sola da un conteo compatible
  con el azar (p unilateral ≥ 0,05 con N ≈ 420) Y la diferencia con el historial se debe a discrepancias;
  (D) fuga en P_aj.
- CONFIRMADO (= sin artefacto) si: no hay código culpable, 0 repeticiones perdidas, la API oficial sola
  reproduce el déficit (p < 0,05 contra azar) y no hay fuga. Los controles RD/LARD solo se reportan
  (un déficit en ellos sería pista de mecanismo del operador, no de artefacto nuestro).
- Si la API sola no tiene potencia (déficit presente pero p ≥ 0,05) y A, B, D limpios: CONFIRMADO con salvedad.
