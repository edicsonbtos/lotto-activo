---
name: backtest
description: Evaluación walk-forward de modelos de Lotto Activo sobre historial.txt (Top-1/3/5, IC 95 %, p-valores bajo nula exacta, log-verosimilitud, ROI con pago 30x, prueba de fuga y estabilidad por cuartos)
disable-model-invocation: true
argument-hint: "[modelo.py ...] [--final]"
---

# /backtest

Mide modelos de predicción con el protocolo fijo de `herramientas/lotto_eval.py`.

## Pasos

1. Si `$ARGUMENTS` está vacío, evalúa todos los modelos:
   `python herramientas/lotto_eval.py herramientas/modelos/*.py`
   Si trae rutas, pásalas tal cual. Nunca añadas `--final` por tu cuenta.
2. Solo si el usuario escribió `--final`: antes, muestra cuántas veces se ha mirado ya el tramo de prueba (`herramientas/registro_final.jsonl`) y recuerda que cada mirada adicional reduce la validez del resultado. Luego ejecuta con `--final`.
3. Presenta una tabla por modelo: Top-1 (tasa, IC 95 %, p), Top-3 (tasa vs 7,89 %), mbits/sorteo, ROI Top-1 con pago 30x y Top-3 por cuartos.
4. Interpreta con honestidad:
   - Umbral de rentabilidad Top-1 con pago 30x: 3,33 %. Si el límite inferior del IC 95 % no lo supera, di que **no hay evidencia de rentabilidad**, aunque la media lo supere.
   - Compara siempre con `hazard_actual` (el modelo en producción) y con `uniforme`.
   - Diferencias de Top-3 menores a ~1 pp en el tramo de desarrollo están dentro del ruido.
   - Si un modelo dice "FUGA DE DATOS", sus números no valen nada.
5. Si el cambio es al modelo en producción, recomienda lanzar el subagente `revisor-sesgo` antes de aceptarlo.

No modifiques `historial.txt` ni `predicciones.json`.
