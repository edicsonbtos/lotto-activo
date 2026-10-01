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
        api = leer("/api/rdint"); m = api["marcador"]
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
    t = api.get("seguimiento_top21")
    if t and t["hora_1830"]["n"]:
        x = t["hora_1830"]; ic = x["ic95"]
        print(f"  En observación, sin plata (PREREGISTRO_vivo.md, regla B): Top-21 de las 18:30 desde {t['desde']}: "
              f"{x['aciertos']}/{x['n']} = {x['tasa']*100:.1f} % (IC95 {ic[0]*100:.1f}-{ic[1]*100:.1f}; empata al 70 %), "
              f"neto {x['neto_fichas']:+d} fichas. Resto de horas: {t['resto']['tasa'] and t['resto']['tasa']*100 or 0:.1f} %. "
              f"Se juzga a los {t['juicio_en']} sorteos: {t['veredicto']}.")


def validar(regs):
    """Señal (mbits del ganador frente al azar) y calibración (lo que el modelo esperaba vs lo que salió).

    Solo usa registros con la probabilidad de los 38 animales congelada.
    """
    mb, esp, pue = [], [], []
    for r in regs:
        if r.get("modelo") != "ensamble_v2" or not r.get("winner_rank"):
            continue
        ps = {a["num"]: a.get("prob") for a in r.get("animales", [])}
        if len(ps) != 38 or not all(ps.values()) or r.get("winner_num") not in ps:
            continue
        s = sum(ps.values())
        mb.append(1000 * math.log2(ps[r["winner_num"]] / s * 38))
        esp.append(sorted((p / s for p in ps.values()), reverse=True))
        pue.append(r["winner_rank"])
    n = len(mb)
    if n < 2:
        return
    m = sum(mb) / n
    e = 1.96 * math.sqrt(sum((x - m) ** 2 for x in mb) / (n - 1) / n)
    print(f"\nValidación ({n} sorteos con las 38 probabilidades guardadas):")
    print(f"  Señal: {m:+.0f} mbits por sorteo (IC95 {m-e:+.0f} a {m+e:+.0f}) · azar 0 · prueba ciega +90")
    for t in (3, 5, 15, 23):
        ex = sum(sum(p[:t]) for p in esp) / n
        ob = sum(k <= t for k in pue) / n
        print(f"  Calibración Top-{t:<2}: el modelo esperaba {ex*100:4.1f} % · salió {ob*100:4.1f} %"
              f" · equilibrio {t/30*100:4.1f} %")


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
    try:
        c = leer("/api/cambio_rd15")
    except ValueError:
        c = None
    if c and c.get("n"):
        print(f"Regla RD en el Top-15 (PREREGISTRO_vivo.md, regla A, desde {c['desde']}): {c['n']} sorteos, cambió en "
              f"{c['cambios']} (se juzga a los {c['juicio']}: {c['veredicto']}); ganó el de RD {c['gano_rd']}, el 16º que entró "
              f"{c['gano_16']}. Top-15 {c['top15_con']} con regla vs {c['top15_sin']} sin; ponderado {c['dif_pond']:+.0f} $.")
    validar(regs)
    print(f"\nCon {n} sorteos el ruido es enorme (el Top-3 se mueve ±{1.96*math.sqrt(.12*.88/n)*100:.0f} puntos)."
          " Hacen falta ~1.000 para concluir.")


if __name__ == "__main__":
    main()
