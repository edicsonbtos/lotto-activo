# -*- coding: utf-8 -*-
"""Evalua el marcador real de predicciones.json contra el azar (nula exacta)."""
import json, os
from math import comb, sqrt

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
d = json.load(open(os.path.join(RAIZ, "predicciones.json"), encoding="utf-8"))
r = [x for x in d["registros"] if x.get("salio") is not None]
n = len(r)
print(f"predicciones resueltas: {n}")

def binom_sf(k_, n_, p):
    return sum(comb(n_, i) * p**i * (1 - p)**(n_ - i) for i in range(k_, n_ + 1))

print(f"\n{'top':>5} {'aciertos':>9} {'tasa':>7} {'azar':>7} {'z':>6} {'p-valor':>8}")
for k in (1, 3, 5, 10, 15):
    us = [x for x in r if len(x.get("orden_completo") or x.get("top3")) >= k]
    hits = sum(1 for x in us if x["salio"] in (x.get("orden_completo") or x.get("top3"))[:k])
    m = len(us)
    p0 = k / 38
    esp = m * p0
    sd = sqrt(m * p0 * (1 - p0)) or 1
    print(f"Top-{k:<2} {hits:>4}/{m:<3} {hits/m*100:>6.1f}% {p0*100:>6.1f}% {(hits-esp)/sd:>+5.2f} {binom_sf(hits, m, p0):>8.3f}")

print("\ndetalle por sorteo:")
for x in r:
    orden = x.get("orden_completo") or x.get("top3")
    pos = orden.index(x["salio"]) + 1 if x["salio"] in orden else 0
    marca = "TOP-3" if 0 < pos <= 3 else (f"top-{pos}" if pos else "fuera de 38??")
    print(f"  {x['fecha']} h{x['hora']:>2}  salio {x['salio']:>2}   {marca}")

# ROI con pago 30x apostando top-3 plano
hits3 = sum(1 for x in r if x["salio"] in (x.get("orden_completo") or x.get("top3"))[:3])
roi = (30 * hits3 - 3 * n) / (3 * n)
print(f"\nROI Top-3 plano (pago 30x): {hits3} aciertos en {n} -> {roi*100:+.1f}%")
hits1 = sum(1 for x in r if (x.get("orden_completo") or x.get("top3"))[0] == x["salio"])
roi1 = (30 * hits1 - n) / n
print(f"ROI Top-1 plano (pago 30x): {hits1} aciertos en {n} -> {roi1*100:+.1f}%")

print("\n--- tripletas ---")
for x in d.get("tripletas", []):
    est = x.get("estado")
    anul = " ANULADA" if x.get("anulado") else ""
    extra = {k: v for k, v in x.items() if k in ("aciertos", "gano", "salio")}
    print(f"  {x.get('inicio_fecha')} h{x.get('inicio_hora')}  {est}{anul} {extra}")
