# PREREGISTRO ag2 — "reinicio semanal / la casa empieza debiendo" (2026-10-23)

Escrito ANTES de calcular ningún O/E de esta familia. Lo único mirado: BRIEF_COMUN, SKILL lotto-nueva-idea,
INFORME y PREREGISTRO de pronosticadores (2026-10-15), y el código de carga de `bateria/dev.py` y `analizar.py`.
Ideas cerradas que NO se repiten: lunes, domingo, día de semana (como número), quincena, festivos, días buenos/malos y rachas.
Lo nuevo aquí es la INTERACCIÓN de rasgos ya conocidos (esquive de repetición, número=fecha) con la posición en la semana,
y la compensación tras "pago" de la casa.

## Datos y cortes
- Motor: `verificacion/hilo9/datos/calor_cache.npz` (P walk-forward), historial congelado, filas [2000, 9357).
  Se descartan fechas > 2025-12-14 (el INFORME de pronosticadores documenta que desde el 15-12 las fechas del historial
  congelado están corridas; el número=día del mes necesita fecha correcta). Filas ≥ 9357: no se tocan.
- R2 usa los datos publicados (`pronosticadores/datos/publicados.jsonl`), que cubren LA 2024-03-01..2025-12-14: SÍ cubren
  los dos tramos. Se adopta la partición del INFORME: dev-A = 2024-03-07..2025-02-03, dev-B = 2025-02-04..2025-12-14.
  El vivo de ese INFORME (2026-09..10) no se reutiliza.
- R1 y R3 usan la misma partición (A/B por fecha, mismo corte 2025-02-04) para que las tres hipótesis compartan tramos.
  (No es la mediana de días de la batería; se fija aquí porque R2 la exige y así la familia es homogénea.)

## Familia (6 pruebas, Bonferroni: α = 0,05/6 = 0,0083 -> |z| ≥ 2,64)
Todo contraste entre grupos de sorteos se estratifica por hora (Mantel-Haenszel de razón de tasas con exposición E):
RR_MH = [Σ_h O1h·E0h/(E1h+E0h)] / [Σ_h O0h·E1h/(E1h+E0h)]. z = ln RR_MH / SE, con SE del bootstrap por jornada
(B = 2000, semilla 20261023). O = aciertos del rasgo, E = Σ P_motor sobre el rasgo.

- Rasgo F1 "ya salió hoy": animales ya sorteados antes ese día (solo sorteos con al menos uno previo). 
- Rasgo F2 "número = fecha": números {día del mes, día+1} (ya conocido; 0 y 00 nunca).
- **R1a**: RR de F1, fin de semana (vie-dom) frente a inicio (lun-mar). Hipótesis de reinicio: RR ≠ 1 (dos colas).
- **R1b**: igual con F2.
  Descriptivo (no cuenta en la familia): mitad (mié-jue), y la tabla por día de semana.
- **R2a**: sorteo s del día d, s no es el primero. Estado = el sorteo inmediatamente anterior del mismo día "pagó" si su ganador
  ∈ U_d (U = lotoven ∪ loteriadehoy, el conjunto del día, ya sea con 1 o 2 fuentes; días sin U se omiten).
  Rasgo medido en s: ganador ∈ U_d, E = Σ P sobre U_d. RR = O/E tras pago frente a O/E tras no pago. Hipótesis de la casa
  compensando: RR < 1. Se mide a dos colas para el umbral.
- **R2b**: nivel de día. Día d con U_d y d−1 con U_{d−1} (consecutivos). "Pérdida ayer" = ≥ 2 sorteos de d−1 con ganador ∈ U_{d−1}
  (regla fijada a priori, ~tercio superior). Rasgo en d: ganador ∈ U_d. RR = O/E con pérdida ayer frente a sin pérdida. Hipótesis: RR < 1.
- **R3a**: por semana calendaria (lun-dom completa, 7 días presentes) en la partición, estadístico del lunes: T = (O/E del Top-5
  del ensamble el lunes) − (O/E del Top-5 de mar-dom), agrupando semanas (ΣO/ΣE en cada grupo). Test por permutación DENTRO de la
  semana (se reasigna al azar cuál de los 7 días es "lunes"), 20000 permutaciones, p a dos colas. Hipótesis de reinicio: T < 0 (lunes más débil).
- **R3b**: igual con F1 (ya salió hoy), donde "más débil" = O/E mayor, T > 0.
  Para R3 el umbral de la familia es p_perm ≤ 0,0083 en el total y p ≤ 0,05 en CADA mitad con el mismo signo.
  Además se reporta, solo descriptivo, la serie semanal del O/E y su autocorrelación.

## Umbral de PASA (por prueba)
Mismo signo en dev-A y dev-B con |z| ≥ 2 en cada mitad (R3: p ≤ 0,05 en cada mitad) Y |z| total ≥ 2,64 (R3: p_perm total ≤ 0,0083).
Con R2a/R2b y la dirección preregistrada (RR < 1) además debe cumplirse esa dirección.
Si pasa -> réplica RD (desarrollo 2024-03-01..2025-06-30, línea base uniforme sobre animales aún no salidos, como `replica_juegos.py`); para R2
solo si hay datos RD publicados (los hay en publicados.jsonl: "Lotto Activo RD Int"). Z de 2,5 sin réplica no es señal.

## Potencia (aproximada, antes de mirar)
F1 (ya salió hoy) tiene E pequeño por construcción (el motor ya le da poco), así que R1a/R3b serán poco potentes; se reporta E.
F2 acumula unos 2/38 por sorteo ≈ 0,05 x 7000 sorteos ≈ 350 esperados en total, ~100 por grupo: solo detectaría RR ≲ 0,6 ó ≳ 1,6.
R2: E total de U ≈ 0,1/sorteo -> ~800 aciertos esperados; separado por estado, RR ≈ 0,85 detectable.
Si el contraste no tiene potencia lo digo (no se interpreta ausencia de efecto como "no existe").
