# Preregistro ag4 (descriptivo, no decide nada)
- Parte 1: ~11 metricas por juego (LA, RD) de la ventana 2026-10-16..2026-10-23 vs todas las ventanas historicas de igual numero de sorteos (desde 2025-07-01), diferencia observado-esperado; se marca percentil <5 o >95. Esperados por azar: ~2 de 22 fuera.
- Parte 2: Top-5 / Top-15 en vivo (mesa la y principal) por dia de semana y por hora, chi2 de homogeneidad (df=g-1) y tasa esperada = suma de prob del Top-k. Sin umbral de decision; solo describir.
- Parte 3: retorno por ficha Top-5 escalonado 2-2-2-1-1 (paga 30x/ficha) y Top-3 plano por dia de semana.
- Codigo 0 del CSV mezcla "0" y "00" (peso 2/38). Prev=0 se omite en vecinos de rueda.
