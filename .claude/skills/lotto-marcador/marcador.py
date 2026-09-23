# -*- coding: utf-8 -*-
"""Marcador REAL del usuario, bajado de la web en vivo, con cada estrategia en plata.

Uso: python marcador.py
Solo lee /api/mesa?offset=N (un pronóstico congelado por sorteo). No escribe nada.
"""
import json, math, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

URL = "https://lotto-activo-production.up.railway.app"
PAGO = 30


def leer(ruta):
    out = subprocess.run(["curl", "-s", "--max-time", "60", URL + ruta],
                         capture_output=True, text=True, encoding="utf-8").stdout
    return json.loads(out)


def plan(tramos):
    f = [0] * 39
    for a, b, n in tramos:
        for p in range(a, b + 1):
            f[p] = n
    return f


ESTRATEGIAS = [
    ("Top-5 escalonado 2-2-2-1-1", plan([(1, 3, 2), (4, 5, 1)]), 0.191),
    ("Top-15 ponderado 3-2-1", plan([(1, 3, 3), (4, 5, 2), (6, 15, 1)]), 0.06),
    ("Top-3 plano", plan([(1, 3, 1)]), 0.227),
    ("Top-15 plano", plan([(1, 15, 1)]), -0.011),
]


def rd():
    """Marcador en vivo de RD Internacional (h:30), leído de /api/rdint."""
    try:
        m = leer("/api/rdint")["marcador"]
    except (ValueError, KeyError):
        print("\nRD Internacional: sin /api/rdint (¿desplegado?).")
        return
    n = m["n"]
    print(f"\nRD Internacional (en vivo desde 2026-09-23): {n} sorteos puntuados")
    if not n:
        return
    print(f"Del más reciente al más viejo, puesto del ganador: {m['puestos']}")
    for t, k, azar, equil in ((3, m["top3"], 3 / 38, .10), (5, m["top5"], 5 / 38, 5 / 30), (15, m["top15"], 15 / 38, .5)):
        tasa = k / n; e = 1.96 * math.sqrt(max(tasa * (1 - tasa), 1e-9) / n)
        print(f"Top-{t:<2}: {k}/{n} = {tasa*100:.1f} % (IC95 {max(0,tasa-e)*100:.1f}-{(tasa+e)*100:.1f})"
              f" · azar {azar*100:.1f} % · equilibrio {equil*100:.1f} %")
    for p in m["planes"]:
        print(f"  {p['plan']:<28} neto {p['neto']:+6.0f} $  ({p['retorno']*100:+5.1f} %)")
    print("  Esperado (prueba ciega / réplica): Top-3 +20/+14 %, Top-5 esc. +20/+9 %, "
          "Top-15 pond. +12/+5 %, Top-15 plano +7/+2 %.")


def main():
    if "--rd" in sys.argv:
        rd()
        return
    total = leer("/api/mesa?offset=0")["total"]
    with ThreadPoolExecutor(8) as ex:
        regs = list(ex.map(lambda o: leer(f"/api/mesa?offset={o}"), range(1, total)))
    puestos = [r["winner_rank"] for r in regs
               if r.get("winner_rank") and r.get("modelo") == "ensamble_v2"]
    n = len(puestos)
    print(f"Pronósticos puntuables (ensamble_v2 con orden guardado): {n}")
    if not n:
        return
    print(f"Del más reciente al más viejo, puesto del ganador: {puestos[:30]}")
    for t, azar, equil in ((3, 3 / 38, .10), (5, 5 / 38, 5 / 30), (15, 15 / 38, .5)):
        k = sum(p <= t for p in puestos); tasa = k / n
        e = 1.96 * math.sqrt(max(tasa * (1 - tasa), 1e-9) / n)
        print(f"Top-{t:<2}: {k}/{n} = {tasa*100:.1f} % (IC95 {max(0,tasa-e)*100:.1f}-{(tasa+e)*100:.1f})"
              f" · azar {azar*100:.1f} % · equilibrio {equil*100:.1f} %")
    print("\nCon 1 ficha = 1 $:")
    for nombre, f, esperado in ESTRATEGIAS:
        ap = sum(f) * n
        neto = sum(PAGO * f[p] for p in puestos) - ap
        print(f"  {nombre:<28} neto {neto:+6.0f} $  ({neto/ap*100:+5.1f} %)  · esperado a largo plazo {esperado*100:+.0f} %")
    try:
        c = leer("/api/cambio_rd")
    except ValueError:
        c = None
    if c and c.get("n"):
        print(f"\nRegla de cambio RD (desde {c['desde']}): {c['n']} sorteos, cambió en {c['cambios']}; "
              f"ganó el de RD {c['gano_rd']}, el 6º que entró {c['gano_6']}. "
              f"Top-5 escalonado con cambio {c['con']:+.0f} $ vs sin cambio {c['sin']:+.0f} $ "
              f"({c['dif']:+.0f} $). En la prueba: RD 6 vs 6º 14 en 377 cambios.")
    print(f"\nCon {n} sorteos el ruido es enorme (el Top-3 se mueve ±{1.96*math.sqrt(.12*.88/n)*100:.0f} puntos)."
          " Hacen falta ~1.000 para concluir.")


if __name__ == "__main__":
    main()
