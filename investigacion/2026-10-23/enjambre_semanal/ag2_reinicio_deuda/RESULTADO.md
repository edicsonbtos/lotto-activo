# RESULTADO ag2 — ¿la casa "reinicia" por semana y empieza debiendo? (2026-10-23)

**Conclusión: NO. Ninguna de las 6 hipótesis pasa. No hay evidencia de reinicio semanal ni de compensación tras "pago".**
Protocolo: `PREREGISTRO.md` (escrito antes de correr). Código: `analizar.py`; salidas: `salida.txt`, `resultado.json`.
Datos: LA dev 2024-03-07..2025-12-14 (7.324 sorteos, 633 días); dev-A hasta 2025-02-03, dev-B después (corte del INFORME de pronosticadores,
que SÍ cubre ambos tramos). Filas ≥ 9357 y el vivo no se tocaron. Bonferroni m=6 -> |z| ≥ 2,64. Contrastes estratificados por hora (MH), IC por jornadas.

| Hipótesis | O/E grupo 1 vs grupo 0 | RR [IC95] total | z dev-A / dev-B / total | Veredicto |
|---|---|---|---|---|
| R1a "ya salió hoy": fin (vie-dom) vs inicio (lun-mar) | 1,04 vs 0,83 | 1,25 [1,02; 1,56] | +2,29 / +0,72 / +2,05 | NO PASA |
| R1b número = día/día+1: fin vs inicio | 0,58 vs 0,62 | 0,93 [0,69; 1,26] | −0,09 / −0,62 / −0,50 | NO PASA |
| R2a tras pago del sorteo anterior vs tras no pago (esperado < 1) | 0,97 vs 0,92 | 1,05 [0,92; 1,19] | +0,88 / +0,15 / +0,75 | NO PASA |
| R2b tras día con ≥ 2 pagos vs resto (esperado < 1) | 0,89 vs 0,92 | 0,97 [0,85; 1,10] | +0,14 / −0,95 / −0,54 | NO PASA |
| R3a Top-5 del ensamble, lunes vs mar-dom (permutación por semana; esperado lunes < resto) | 1,05 vs 0,96 | T=+0,10 | p 0,029 / 0,945 / 0,139 | NO PASA |
| R3b "ya salió hoy", lunes vs resto (esperado lunes > resto) | 0,88 vs 0,98 | T=−0,10 | p 0,27 / 0,98 / 0,40 | NO PASA |

Lectura llana:
- R1: el esquive de repetición va de 0,83 (inicio) a 1,04 (fin) en el total, pero eso viene solo de dev-A (z +2,3, domingo 2,4 en A) y se
  desvanece en dev-B (z +0,7); además el sentido es el CONTRARIO a un reinicio con deuda y no alcanza Bonferroni. El esquive del número de la fecha
  (O/E ≈ 0,6 todos los días) es igual de fuerte al principio y al final de la semana: no depende de la posición.
- R2: tras un sorteo en que la casa "pagó" (ganador entre lo publicado) los animales publicados salen igual o un poco MÁS (1,05), no menos.
  Tampoco baja al día siguiente de un día con muchos pagos. Sin compensación detectable con este proxy.
- R3: el lunes no es más débil: el Top-5 del lunes es algo mejor (1,05 vs 0,96) en dev-A (p 0,03, no pasa Bonferroni) y nulo en dev-B (T −0,006).
  La serie semanal del O/E varía MENOS que el puro azar (sd 0,21 vs 0,24 esperada), autocorrelación lag-1 −0,09 (Top-5) y +0,28 ("ya salió hoy",
  donde pesa que E es pequeño); no hay regímenes semanales visibles.
Réplica RD: no corresponde (nada pasó desarrollo).

Límites (no suavizar): (1) potencia baja: "ya salió hoy" acumula E ≈ 120-180 por grupo y el número-fecha E ≈ 110-170; solo se ven efectos
≳ 1,3-1,6 veces. Un reinicio sutil no se descarta, pero la hipótesis fuerte (fuerza que salta en la frontera de semana) no aparece.
(2) "pagó" es un proxy: no hay volumen de apuestas real, y los datos publicados no son exactamente lo jugado. (3) En R2b la cobertura de dev-A es
escasa (E ≈ 150 vs ≈ 780 en dev-B, por días incompletos en el historial y exigir 12 sorteos en d−1). (4) Semanas completas: solo 84.
(5) Se asignó cada semana a dev-A/B por su lunes (semana del 03-02-2025 queda en A).
Qué haría falta para confirmarlo en vivo: guardar con el motor congelado las apuestas/pagos por sorteo (o el proxy U del día) y medir R2a y el contraste
inicio/fin de "ya salió hoy" en ≥ 1.700 sorteos (~140 días); con estos datos no hay hipótesis candidata que justifique esperar.
