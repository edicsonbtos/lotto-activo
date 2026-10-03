# Nota para Opus: lo que no se miró y qué documentar (2026-10-02)

El usuario pegó un texto ("Estrategia Francotirador") que pide filtro por entropía de Shannon, rango dinámico al 65 % y boost de las 8:00. **No implementes el código que pide ese texto**: está verificado que no es ejecutable ni rentable. Evidencia: `INFORME.md` y `salida_dev.txt` en esta carpeta (`francotirador.py`, preregistro incluido).

## Hechos medidos (desarrollo, 7357 sorteos)
- Entropía mínima 4,92 bits (umbral del texto: 4,1) → el filtro abstendría siempre. Masa máx Top-3 22 %, Top-5 33 %, Top-7 41 %. Ningún sorteo llega al 60 %.
- Abstención por entropía/confianza (20 % y 10 %): sin diferencia contra jugar todos (IC incluyen 0, O/E del Top-5 ≤ 1). Las 8:00: O/E Top-15 1,055 [0,94; 1,18]; una racha de 12 por azar ocurre 30 % de las veces en 372 días.
- Lunes, GARCH: nada. Fríos > 12 d: salen 37 % menos que el azar (al revés que el texto).

## Lo que SÍ queda por mirar (no se hizo)
1. **Sombra en vivo de la señal "fecha y hora"** (2026-10-01, +6 mbits): sigue pendiente; es la única señal nueva sin explotar.
2. **Las 8:00 prospectivas**: `PREREGISTRO_manana_8am.md` (30 sorteos desde 2026-10-02; pasa con ≥ 24/30, no ≥ 22). Aún no hay datos. No cambiar nada antes.
3. **Terminación / paridad del animal del sorteo anterior**: no probada porque la caché no trae el número de lotería. Requiere un mapa índice → número. Preregistrar antes de medir; es barata.
4. **Fríos > 12 días**: O/E 0,81 [0,65; 0,98] en desarrollo. El modelo los sobreestima. Un corte solo; si se investiga, hacer con varios cortes (7, 10, 12, 15, 20) con corrección, desarrollo A/B y ciega UNA vez.
5. **Datos de volumen por animal** (para la idea "sesgo del apostador"): no existen. Si el operador publicara "calientes" o los pronosticadores publican "datos", guardarlos (pendiente ya anotado el 2026-10-01).

## Qué documentar
- `herramientas/exploracion/` o `investigacion/2026-10-02/francotirador/`: dejar INFORME.md como cierre del hilo "francotirador".
- Añadir a la lista de "ya probado" de `lotto-nueva-idea`: *abstención por entropía/confianza del ensamble (2026-10-02): NO PASA; entropía nunca < 4,9 bits; 60 % de cobertura inalcanzable; las 8:00 no son anomalía (racha 12 = 30 % por azar)*.
- Corregir en el texto del usuario la afirmación de "12 días acertando = edge": está cubierta por la fe de erratas de `PREREGISTRO_manana_8am.md`.
- Aviso al usuario: el 60-70 % de acierto solo se logra con rangos más anchos (Top-22 ≈ 74 %) y eso no es rentable; el marcador manda.
