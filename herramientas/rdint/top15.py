# -*- coding: utf-8 -*-
"""Hilo 7: Top-15 (y los otros planes) en RD Internacional, por tramo.

Uso (cada etapa en su propio proceso para no llenar la RAM):
  python herramientas/rdint/top15.py modelo    -> cache_todo.npz (P0, P1, y, hora, dia, tramo)
  python herramientas/rdint/top15.py reporte   -> resultados/hilo7_top15.md

B0 = secuencia_v3 (solo RD Int), B1 = modelo.cruzado (R=250, minimo=500, lam=1), walk-forward
desde la fila 2000 con los datos truncados al primer sorteo 'vivo' (cal+dev+test+desc).
El plan recomendado se elige mirando SOLO 'dev'; 'test' ya se miro una vez (prueba ciega del
hilo 7) y 'desc' nunca se uso para ajustar ni elegir nada.
"""
import os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.dirname(AQUI)
sys.path.insert(0, HERR); sys.path.insert(0, AQUI)
import lotto_eval as LE
import datos as DT
import modelo as MB
import correr_modelo as CM

CACHE = os.path.join(AQUI, "cache_todo.npz")
SALIDA_MD = os.path.join(HERR, "resultados", "hilo7_top15.md")
PAGO = LE.PAGO
TRAMOS = ["dev", "test", "desc"]

# plan -> fichas por puesto (0..14)
def _fichas(bloques):
    f = np.zeros(15)
    for a, b, v in bloques:
        f[a - 1:b] = v
    return f

PLANES = [
    ("Top-3 plano", _fichas([(1, 3, 1)])),
    ("Top-5 escalonado 2-2-2-1-1", np.r_[2, 2, 2, 1, 1, np.zeros(10)]),
    ("Top-15 plano", _fichas([(1, 15, 1)])),
    ("Top-15 ponderado 3-2-1", _fichas([(1, 3, 3), (4, 5, 2), (6, 15, 1)])),
]
GRUPOS = [("1º-3º", 0, 3), ("4º-5º", 3, 5), ("6º-10º", 5, 10), ("11º-15º", 10, 15)]


def etapa_modelo():
    t0 = time.time()
    rd, la_h, la_h1, la_hoy, tramo = DT.cargar()
    n_fin = int(np.flatnonzero(tramo == "vivo")[0])
    assert set(np.unique(tramo[:n_fin])) <= {"cal", "dev", "test", "desc"}
    rd = rd.prefijo(n_fin)
    P0, P1, hist = MB.predecir(CM.modelo_b0("secuencia_v3"), rd, la_h[:n_fin], la_h1[:n_fin],
                               la_hoy[:n_fin], CM.DESDE, R=250, minimo=500, lam=1.0)
    D = CM.DESDE
    np.savez_compressed(CACHE, P0=P0.astype(np.float32), P1=P1.astype(np.float32),
                        y=np.asarray(rd.seq)[D:], hora=np.asarray(rd.hora)[D:], dia=np.asarray(rd.dia)[D:],
                        tramo=tramo[D:n_fin], fecha=np.array(rd.fecha[D:]), b_final=hist[-1][1], desde=D)
    print("cache_todo: %d filas (%s .. %s) en %.0f s; b final %s"
          % (len(P0), rd.fecha[D], rd.fecha[-1], time.time() - t0, np.round(hist[-1][1], 3).tolist()))


def posiciones(P, y):
    orden = LE.rankings(P)
    return np.argmax(orden == y[:, None], axis=1)


def retorno(pos, f):
    """retorno por ficha, por sorteo."""
    gana = np.where(pos < 15, f[np.minimum(pos, 14)], 0)
    return (PAGO * gana - f.sum()) / f.sum()


def pct(x):
    return ("%+.1f %%" % (100 * x)).replace(".", ",")


def pc(x):
    return ("%.2f %%" % (100 * x)).replace(".", ",")


def etapa_reporte():
    z = np.load(CACHE)
    P0 = LE.normalizar(z["P0"].astype(np.float64)); P1 = LE.normalizar(z["P1"].astype(np.float64))
    y, dia, tr, fecha = z["y"], z["dia"], z["tramo"], z["fecha"]
    rng = np.random.default_rng(15)
    pos = {"B1": posiciones(P1, y), "B0": posiciones(P0, y)}
    R = {}   # (modelo, plan, tramo) -> (m, lo, hi)
    for mod in ("B1", "B0"):
        for nombre, f in PLANES:
            r = retorno(pos[mod], f)
            for t in TRAMOS:
                s = tr == t
                R[(mod, nombre, t)] = CM.boot_media(r[s], dia[s], rng)
    # tasa por puesto y grupo (B1)
    G = {}
    for t in TRAMOS:
        s = tr == t
        for g, a, b in GRUPOS:
            v = ((pos["B1"][s] >= a) & (pos["B1"][s] < b)).astype(float) / (b - a)
            G[(g, t)] = CM.boot_media(v, dia[s], rng)
    porp = {t: [(pos["B1"][tr == t] == k).mean() for k in range(15)] for t in TRAMOS}
    info = {t: (int((tr == t).sum()), len(np.unique(dia[tr == t])), fecha[tr == t][0], fecha[tr == t][-1])
            for t in TRAMOS}
    acierto = {(nm, t): (pos["B1"][tr == t] < int((f > 0).sum())).mean() for nm, f in PLANES for t in TRAMOS}
    # plan elegido SOLO por dev (retorno por ficha medio)
    elegido = max((nm for nm, _ in PLANES), key=lambda nm: R[("B1", nm, "dev")][0])
    # ganancia por sorteo (en fichas) en dev, para el criterio de "cuanta plata"
    gan = {(nm, t): R[("B1", nm, t)][0] * f.sum() for nm, f in PLANES for t in TRAMOS}

    L = []; di = L.append
    di("# RD Internacional (h:30): ¿conviene jugar Top-15?\n")
    di("Generado por `herramientas/rdint/top15.py` el %s. Modelo: B1 = secuencia_v3 sobre RD Int + lo que "
       "salió en Lotto Activo a las h:00 (media hora antes). Paga 30 por 1.\n" % time.strftime("%Y-%m-%d"))
    di("## En corto\n")
    di("Retorno por cada ficha apostada (más es mejor; 0 % = ni ganas ni pierdes):\n")
    di("| Forma de jugar | Fichas por sorteo | Desarrollo | Prueba (ya vista) | Réplica nueva (abr–sep 2026) |")
    di("|---|---|---|---|---|")
    for nm, f in PLANES:
        di("| %s%s | %d | %s | %s | %s |" % ("**" + nm + "**" if nm == elegido else nm, "", int(f.sum()),
                                          *[pct(R[("B1", nm, t)][0]) for t in TRAMOS]))
    di("")
    rs = [R[("B1", "Top-15 plano", t)] for t in TRAMOS]
    rp = [R[("B1", "Top-15 ponderado 3-2-1", t)] for t in TRAMOS]
    di("- **Top-15 en RD Int:** acierta %s de las veces en la réplica, y el plano deja %s por ficha en la réplica "
       "nueva; el ponderado 3-2-1, %s. En Lotto Activo el Top-15 plano daba −1 %% en la prueba ciega y el "
       "ponderado ~+6 %%." % (pc(acierto[("Top-15 plano", "desc")]), pct(rs[2][0]), pct(rp[2][0])))
    di("- **Plan recomendado para RD Int (elegido mirando solo el desarrollo): %s.** En la réplica nueva "
       "dio %s por ficha (IC95 %s a %s)." % (elegido, pct(R[("B1", elegido, "desc")][0]),
                                            pct(R[("B1", elegido, "desc")][1]), pct(R[("B1", elegido, "desc")][2])))
    mejor15 = ("ponderado 3-2-1" if R[("B1", "Top-15 ponderado 3-2-1", "dev")][0] >= R[("B1", "Top-15 plano", "dev")][0]
               else "plano")
    di("- Entre las dos formas de Top-15, en desarrollo rinde más el **%s** (%s contra %s por ficha); "
       "en la réplica: ponderado %s, plano %s." % (mejor15, pct(max(rp[0][0], rs[0][0])), pct(min(rp[0][0], rs[0][0])),
                                                   pct(rp[2][0]), pct(rs[2][0])))
    pos_desc = [nm for nm, _ in PLANES if R[("B1", nm, "desc")][1] > 0]
    di("- Cuidado: en la réplica (%d sorteos) %s. Todos los planes quedan en positivo, pero la réplica sola "
       "es corta para confirmarlo; junto con la prueba ciega el cuadro es coherente."
       % (info["desc"][0], "ningún plan tiene el IC95 entero por encima de 0" if not pos_desc else
          "solo %s tiene el IC95 entero por encima de 0" % ", ".join(pos_desc)))
    di("- Lo que suma Lotto Activo: sin él (B0, solo RD Int), el Top-15 plano pierde en dev (%s) y en la réplica "
       "(%s). La información de Lotto Activo de las h:00 es lo que empuja el Top-15 a positivo."
       % (pct(R[("B0", "Top-15 plano", "dev")][0]), pct(R[("B0", "Top-15 plano", "desc")][0])))
    di("- Las cifras de 'Prueba' no son una prueba nueva (ese tramo ya se miró una vez). La 'Réplica nueva' "
       "(%s .. %s) nunca se usó para ajustar ni elegir el modelo: es la mejor comprobación disponible."
       % (info["desc"][2], info["desc"][3]))

    di("\n## Detalle\n")
    di("### Tramos\n")
    di("| tramo | sorteos | días | desde | hasta | uso |")
    di("|---|---|---|---|---|---|")
    uso = {"dev": "desarrollo: aquí se elige el plan", "test": "prueba ciega del hilo 7 (ya mirado una vez): informativo",
           "desc": "nunca usado para ajustar ni elegir: réplica"}
    for t in TRAMOS:
        n, nd, a, b = info[t]
        di("| %s | %d | %d | %s | %s | %s |" % (t, n, nd, a, b, uso[t]))
    di("\nPredicciones walk-forward desde la fila %d con los datos truncados al primer sorteo 'vivo'. "
       "Coeficientes de B1 al final: %s (h:00, (h-1):00, antes hoy). IC95 por bootstrap de días (%d remuestreos)."
       % (int(z["desde"]), np.round(z["b_final"], 3).tolist(), CM.NBOOT))

    di("\n### Retorno por ficha con IC95, B1\n")
    di("| plan | fichas | " + " | ".join(TRAMOS) + " |")
    di("|---|---|---|---|---|")
    for nm, f in PLANES:
        di("| %s | %d | %s |" % (nm, int(f.sum()), " | ".join(
            "%s [%s, %s]" % tuple(pct(v) for v in R[("B1", nm, t)]) for t in TRAMOS)))
    di("\nGanancia media por sorteo, en fichas (B1): " + "; ".join(
        ("%s: %s" % (nm, ", ".join("%s %+.2f" % (t, gan[(nm, t)]) for t in TRAMOS))).replace(".", ",")
        for nm, _ in PLANES) + ".")
    di("\nTasa de acierto del plan (el ganador cae dentro de los animales jugados), B1: " + "; ".join(
        "%s: %s" % (nm, ", ".join("%s %s" % (t, pc(acierto[(nm, t)])) for t in TRAMOS)) for nm, _ in PLANES) + ".")

    di("\n### Lo mismo con B0 (solo RD Int, sin Lotto Activo)\n")
    di("| plan | " + " | ".join(TRAMOS) + " |")
    di("|---|---|---|---|")
    for nm, _ in PLANES:
        di("| %s | %s |" % (nm, " | ".join("%s [%s, %s]" % tuple(pct(v) for v in R[("B0", nm, t)]) for t in TRAMOS)))

    di("\n### Acierto por puesto (B1) frente al equilibrio 1/30 = 3,33 %\n")
    di("Cada animal jugado a 1 ficha gana dinero solo si su puesto acierta más del 3,33 %.\n")
    di("| puestos | " + " | ".join(TRAMOS) + " |")
    di("|---|---|---|---|")
    for g, _, _ in GRUPOS:
        di("| %s (c/u) | %s |" % (g, " | ".join("%s [%s, %s]" % tuple(pc(v) for v in G[(g, t)]) for t in TRAMOS)))
    di("\n| puesto | " + " | ".join(TRAMOS) + " |")
    di("|---|---|---|---|")
    for k in range(15):
        di("| %dº | %s |" % (k + 1, " | ".join(pc(porp[t][k]) for t in TRAMOS)))

    di("\n### Comparación con Lotto Activo\n")
    di("| plan | Lotto Activo (prueba ciega) | RD Int réplica (desc) | RD Int prueba (test) |")
    di("|---|---|---|---|")
    la = {"Top-3 plano": "+22,7 %", "Top-5 escalonado 2-2-2-1-1": "+19,1 %", "Top-15 plano": "−1,1 %",
          "Top-15 ponderado 3-2-1": "~+6 %"}
    for nm, _ in PLANES:
        di("| %s | %s | %s | %s |" % (nm, la[nm], pct(R[("B1", nm, "desc")][0]), pct(R[("B1", nm, "test")][0])))

    di("\n## Notas de honestidad\n")
    di("- El tramo **test** ya se miró una vez (prueba ciega del hilo 7, `hilo7_prueba_ciega.md`). Sus cifras aquí "
       "son informativas, no una nueva prueba.")
    di("- El tramo **desc** (2026-04-13 .. 2026-09-13) nunca se usó para ajustar ni elegir el modelo ni el plan: "
       "es la mejor réplica disponible. B0/B1 se congelaron antes (pre-registro y enmienda del hilo 7).")
    di("- El plan recomendado (**%s**) se eligió por el mayor retorno por ficha en **dev**, igual que en Lotto "
       "Activo (`estrategia_top5.md`). Se compararon %d planes fijados de antemano; no se buscaron proporciones."
       % (elegido, len(PLANES)))
    di("- Retorno por ficha no es lo mismo que plata total: un plan con más fichas puede ganar más por sorteo "
       "aunque rinda menos por ficha, pero también arriesga más y sus rachas malas son más largas.")
    with open(SALIDA_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    et = sys.argv[1] if len(sys.argv) > 1 else ""
    if et == "modelo":
        etapa_modelo()
    elif et == "reporte":
        etapa_reporte()
    else:
        sys.exit(__doc__)
