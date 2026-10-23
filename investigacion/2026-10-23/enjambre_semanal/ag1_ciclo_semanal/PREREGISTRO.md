# Preregistro ag1 — ciclo semanal en todas las horas (2026-10-23)
Escrito ANTES de correr nada. Datos LA: filas [2000, 9357) de `verificacion/hilo9/datos/historial.txt`, P = `calor_cache.npz`
(ensamble walk-forward). dev-A = primera mitad de días, dev-B = segunda (corte = mediana de días, como `bateria/dev.py`).
Filas >= 9357 NO se tocan. El historial previo a la fila 2000 solo se usa como memoria (rezagos 7/14 días, semana en curso).

## Familia (6 pruebas -> Bonferroni: alfa 0,05/6 = 0,0083, |z| total >= 2,64)
Todas con métrica O/E = Σ observado / Σ P del ensamble; z = (O-E)/sqrt(Σ E(1-E)); IC95 con bootstrap por jornada (2000).
- S1 misma hora (slot), hace 7 días: máscara = {ganador de (fecha-7, mismo slot)}. Se excluyen filas sin ese dato.
- S2 igual con 14 días (control/réplica de S1).
- S3 máscara = conjunto de animales que salieron en CUALQUIER hora el mismo día de la semana pasada (fecha-7).
- S4a "bolsa semanal", semana que inicia lunes (reinicio al primer sorteo del lunes). Máscara = animales AÚN NO salidos en la semana
  en curso (antes de la fila). Métrica primaria = z de TENDENCIA estratificada por hora: Σ (obs-E)·c / sqrt(Σ E(1-E)·c²), con
  c = posición de día (1..7) menos su media dentro de la hora. Descriptivo: O/E por tercio (días 1-2, 3-5, 6-7).
- S4b igual con semana que inicia domingo (posición domingo=1).
- S5 cobertura semanal: nº de animales distintos por semana completa (84 sorteos presentes) vs simulación (2000 réplicas) que
  muestrea cada fila de P; dentro del día el simulado excluye (y renormaliza) los animales que ya salieron en la simulación ese día
  (el ensamble sabe que no se repite en el día). z = (media observada - media simulada)/sd de la media simulada. Limitación declarada:
  la simulación no reproduce el reciclaje entre días (P está condicionada a la historia real).
No se agrega nada más a la familia. Cualquier descomposición extra (por hora, por tercio, variantes) es descriptiva y no cuenta.

## Criterio PASA (desarrollo)
Mismo signo en dev-A y dev-B, |z| >= 2 en cada mitad y |z| total >= 2,64. Para S4 el z es el de tendencia; para S5 el de cobertura.
## Réplica (solo lo que pase)
RD 2024-03-01..2025-06-30 (`rdint_hist.csv`, mismo slot por hora h:30). Línea base = uniforme sobre los animales aún no salidos
ese día (en la simulación de S5, uniforme sin repetir en el día). Se exige mismo sentido y |z| >= 2 (alfa 0,05 sobre lo que pasó
desarrollo, Bonferroni por el número que pasó). Un z de 2,5 sin réplica NO es señal.
