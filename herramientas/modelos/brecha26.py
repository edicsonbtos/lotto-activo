# -*- coding: utf-8 -*-
"""Top-15 con la "brecha 2026" (herramientas/exploracion/INFORME_brecha_2026.md). EN SOMBRA desde 2026-10-03
(herramientas/exploracion/PREREGISTRO_sombra_brecha26.md): no cambia la jugada.

- Top-5: el de producción, tal cual (orden congelado con el cambio RD del Top-5 ya aplicado).
- Puestos 6-15: ensamble × exposición (multiplicadores congelados en dev-A, exposicion.py), sin los 5 de arriba y
  sin el animal de RD (h−1):30, que queda 16º. A las 8:00 no hay RD de la misma mañana: solo la exposición.

Usa el congelado, el calendario y RD (h−1):30 (sale antes de LA h:00): se puede aplicar al puntuar sin fuga.

orden(orden_prod, scores, fecha, hora, rd) -> lista con los 38 índices.
  orden_prod: 38 índices (0 = "0", 1 = "00", 2.. = "1".."36"); scores: 38 probabilidades del ensamble;
  fecha 'AAAA-MM-DD'; hora 0..11 (0 = 8:00); rd: índice del animal de RD (h−1):30 o None.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exposicion  # noqa: E402

K = 38


def orden(orden_prod, scores, fecha, hora, rd):
    if len(orden_prod) != K or len(scores) != K:
        raise ValueError("hacen falta el orden y las probabilidades de los 38 animales")
    top5 = list(orden_prod[:5])
    q = exposicion.aplicar(scores, fecha, int(hora))
    rd = rd if (rd is not None and int(hora) >= 1) else None
    fuera = set(top5) | ({rd} if rd is not None else set())
    resto = sorted((i for i in range(K) if i not in fuera), key=lambda i: (-q[i], i))
    cola = [rd] if rd is not None and rd not in top5 else []
    return top5 + resto[:10] + cola + resto[10:]
