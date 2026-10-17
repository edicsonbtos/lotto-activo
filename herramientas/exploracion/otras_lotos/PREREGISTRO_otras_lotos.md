# Prerregistro: motor estructural en otras loterías (2026-10-08)
Datos: scraping/resultados/consolidado_todos.csv (2026-04-11..2026-10-07, ~176 días/juego).
Modelo: tasa de salida por (cubo de hueco en sorteos desde la última salida, ya salió hoy sí/no), ajustada SOLO en la 1.ª mitad de días; se mide en la 2.ª mitad (ciega, una sola mirada).
Símbolo = animal_numero si existe, si no nombre sin acentos. Sorteos de un mismo juego ordenados por fecha/hora.
Métrica: mbits/sorteo vs uniforme 1/K y Top-5 vs 5/K; IC 95% por bloques de día (bootstrap 2000).
PASA si IC de mbits excluye 0 Y Top-5 O/E > 1 con IC > 1. Con 20 juegos, umbral Bonferroni (p<0,0025): solo entonces es candidato. Nada se aplica sin réplica en vivo.
