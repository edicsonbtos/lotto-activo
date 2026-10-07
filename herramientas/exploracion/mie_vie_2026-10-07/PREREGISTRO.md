# Preregistro (escrito ANTES de ver ningun resultado por dia) - 2026-10-07
Hipotesis del usuario: miercoles-viernes (dow 2,3,4) es mas flojo para el ensamble_v2.
- Datos: SOLO desarrollo, filas [2000,9357) del historial, P walk-forward de herramientas/exploracion/calor_cache.npz (no existe arnes.py; el equivalente es lotto_eval.cargar + esa cache). No se tocan filas >=9357.
- Prueba UNICA preregistrada: metrica = mbits/sorteo (1000*log2(38*P[y])) del ensamble; contraste mie-vie menos resto; H1: diferencia < 0.
  Umbral de falsacion: IC95 por bootstrap de bloques de dia que excluya 0 Y p de permutacion (etiquetas de dow permutadas dentro de cada semana, 20000) < 0.05.
- Secundarias (descriptivas, no son la prueba): Top-5 y Top-15 (Mantel-Haenszel estratificado por hora) y los 7 dias por separado (Bonferroni x7, alfa 0.05/7).
- Confusores: hora del dia (estratificar), feriados (excluirlos como sensibilidad), dias incompletos.
- Si hay debilidad: separar modelo vs operador (calibracion O/E de la masa de P + estructura del operador por dia); ajuste de aplanado P^a (a fijado hacia delante, ventana expansiva por ano) se mide solo en datos posteriores a su ajuste.
- ag12: no hay cache walk-forward en el repo; no se mide.
- Marcador en vivo: se mira si hay datos locales y se informa; no se usa para elegir.
