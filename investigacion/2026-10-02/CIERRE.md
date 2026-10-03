# Cierre del ciclo de investigación (2026-10-02)

Estado: **investigación cerrada. El modelo y la estrategia (Top-5 escalonado 2-2-2-1-1) quedan SIN cambios.**

## Lo medido hoy (solo desarrollo [2000, 9357), todo preregistrado en esta carpeta y en `francotirador/`)
- Ataque al generador (`ataque_generador/`): uniformidad, fechas especiales, transiciones 38x38, entropía aproximada y 5 pruebas tipo NIST con 5 bits por sorteo: sin señal.
- Dieharder real: no instalado (necesita millones de bits, hay ~31.000). `dieharder_mini.py`: gap y poker fallan, y es la regla ya conocida de no repetir animal en el día
  (5 distintos en 5 sorteos seguidos: 90,2 % contra 75,8 % por azar). Es estructura del operador, no un defecto explotable que el ensamble no capture.
- LSTM: peor que el ensamble (entropía cruzada −4,7 %); mezclado, +0,9 mbits en E1 y −1,0 en E2, IC incluye 0. Autoencoder: 4 anómalos por mitad, no medible. Clustering espectral: p = 0,67.
- Francotirador (entropía, contrarian, geometría macro): sin señal (ver `francotirador/INFORME.md`).

## Qué NO se afirma
- No se afirma "máximo teórico" ni "edge perfecto": se afirma que con estos datos no se encontró nada que supere al ensamble.
- El +19 % (ciega) / +24 % (desarrollo) es una estimación con IC; la confirmación es el marcador en vivo.

## Seguimiento en vivo (ya existe, no se duplica)
- Web de Railway: registra el pronóstico congelado y el resultado; `python .claude/skills/lotto-marcador/marcador.py` (y `--rd`) da ROI por estrategia con IC, calibración y señal en mbits.
- Las 8:00 sin expectativas especiales: `herramientas/exploracion/en_vivo_manana_8am.py` y `en_vivo_por_hora.py`.
- Regla pre-comprometida de cambio: `gestion_banca.VIGILANCIA` (3 meses seguidos en contra).
