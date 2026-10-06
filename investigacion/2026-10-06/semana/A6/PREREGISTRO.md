# Pre-registro A6 (abogado del diablo): ¿mié-vie es una estadística fantasma? (2026-10-06, antes de calcular)

Datos: `prod_0605.npz` (motor de producción reconstruido, walk-forward). Tramo principal: 2026 (f ≥ 2026-01-01).
Unidad de remuestreo: la jornada (día de calendario completo, con sus sorteos y sus horas).

## Estadístico por celda
Residuo por sorteo r = acierto − esperado por el motor (Top-15: 1[puesto<15] − masa Top-15). Varianza del motor
v = p(1−p). Para todas las particiones salvo "hora", el residuo se centra DENTRO de cada hora (r − media 2026 de r
en esa hora): es un contraste celda-contra-resto estratificado por hora (equivale a Mantel-Haenszel con efectos
fijos de hora). z_celda = Σ_celda r_c / sqrt(Σ_celda v · (1 − n_celda/n)). Para "hora" se centra con la media global.
También se informa la z cruda contra el motor (la del hallazgo original), solo como referencia.

## Familia (todo lo que alguien pudo mirar)
día de la semana (7), pares de días consecutivos (7, cíclicos, grupo vs resto), tríos consecutivos (7), laborable vs
fin de semana (2), día del mes (31), decena (3: 1-10, 11-20, 21-31), semana del mes (5: (día−1)//7), mes (10),
quincena (2), día par/impar (2), hora (12), hora × fin de semana (24). Estadístico de la familia: max |z| sobre todas
las celdas de todas las particiones.

## Nulo
10.000 permutaciones que barajan las etiquetas de calendario (fecha → día de semana, día del mes, mes...) entre las
jornadas de 2026; cada jornada conserva sus sorteos, horas y residuos. p familiar = P(max|z|_perm ≥ max|z|_obs).
Se informa también el p de permutación del contraste concreto mié-vie vs resto y la posición del |z| ≈ 4 de un día
suelto (jueves) dentro de la distribución nula del máximo.

## Umbrales (fijados ahora)
- p familiar ≥ 0,05 → el hallazgo es compatible con búsqueda (RUIDO o DUDOSO según el resto).
- p familiar < 0,01 Y aparece en ≥ 3 de las 4 métricas restantes (Top-5, Top-3, mbits, retorno Top-5 escalonado) con
  z contraste mié-vie ≤ −2 Y en la segunda reconstrucción (`vivo_rk.npz`) → candidato REAL (pendiente de vivo).
- Lo demás → DUDOSO.
- Métricas secundarias: mismo contraste mié-vie vs resto estratificado por hora, IC 95 % por bootstrap de jornadas.
  mbits: r = log2(38·p_y) − Σ p log2(38 p). Retorno Top-5 escalonado (2,2,2,1,1 fichas, pago 30): r = ganancia/8 −
  esperado del motor.
- Chequeo extra: bajo el nulo, ¿con qué frecuencia la mejor celda elegida además "se repite" en los 3 trimestres
  (signo negativo y O/E ≤ 0,90 en cada uno)? Mide cuánto vale el argumento de "estable en 3 trimestres".
- Mismo barrido en dev (t < 9357) para ver qué máximos aparecen allí sin que haya nada real conocido.

## Potencia
Efecto supuesto = la mitad del observado (diferencia de tasa Top-15 mié-vie vs resto). Varianza por jornada estimada
de los datos (incluye correlación dentro del día). α = 0,05 bilateral y unilateral, potencia 80 %. Se calcula también
la potencia del plan en vivo ya registrado (07-oct a 06-ene).
