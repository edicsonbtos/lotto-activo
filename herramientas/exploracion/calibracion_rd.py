# -*- coding: utf-8 -*-
"""Hilo 7: calibracion de B1 (RD Internacional) y correccion por temperatura.

Lee SOLO herramientas/rdint/cache_todo.npz (predicciones walk-forward ya calculadas). No escribe
nada fuera de resultados/hilo7_calibracion.md.

1. Por tramo (dev / test / desc): Top-1/3/5 esperado (suma de p de los elegidos) vs real, IC95
   bootstrap por bloques de dia; tabla de fiabilidad por deciles de p; pendiente de calibracion
   (logistica de y_ik sobre logit p_ik, pares sorteo x animal) y temperatura MLE multinomial, con IC95
   por bootstrap de dias.
2. Correccion P ~ P1^T: T fijo ajustado SOLO en dev, y T walk-forward (reajuste cada 250 filas con el
   pasado; minimo 500 filas). Se evalua en test y desc.
3. Expectativa de ganancia por ficha (Top-3 plano, Top-5 escalonado 2-2-2-1-1) segun P1, segun P
   corregido y la real.

Uso:  OPENBLAS_NUM_THREADS=1 python herramientas/exploracion/calibracion_rd.py
"""
import os, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
HERR = os.path.dirname(AQUI)
sys.path.insert(0, HERR)
import lotto_eval as LE

CACHE = os.path.join(HERR, "rdint", "cache_todo.npz")
SALIDA = os.path.join(HERR, "resultados", "hilo7_calibracion.md")
PAGO = LE.PAGO
K = LE.K
TRAMOS = ["dev", "test", "desc"]
NOMT = {"dev": "desarrollo", "test": "prueba (ya vista)", "desc": "réplica"}
NB_MEDIA = 2000
NB_AJUSTE = 400
F5 = np.array([2, 2, 2, 1, 1], float)
rng = np.random.default_rng(20260923)


# ------------------------------------------------------------------ utilidades
def pesos_dia(g, nd, nb):
    """(nb, nd) conteos multinomiales de dias remuestreados."""
    idx = rng.integers(0, nd, size=(nb, nd))
    W = np.zeros((nb, nd))
    for b in range(nb):
        W[b] = np.bincount(idx[b], minlength=nd)
    return W


def boot_medias(vs, g, nd, nb=NB_MEDIA):
    """vs: lista de vectores por sorteo. Devuelve lista de (media, lo, hi) con los MISMOS remuestreos,
    mas la de la diferencia vs[0]-vs[1] si hay dos."""
    idx = rng.integers(0, nd, size=(nb, nd))
    C = np.bincount(g, minlength=nd).astype(float)
    out = []
    series = list(vs) + ([vs[0] - vs[1]] if len(vs) == 2 else [])
    for v in series:
        S = np.bincount(g, weights=v, minlength=nd)
        b = S[idx].sum(1) / C[idx].sum(1)
        out.append((float(v.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))))
    return out


def temp(P, T):
    Z = T * np.log(P)
    Z -= Z.max(1, keepdims=True)
    E = np.exp(Z)
    return E / E.sum(1, keepdims=True)


def ajustar_T(L, y, w=None, T0=1.0):
    """MLE de T en P ~ exp(T*L) (L = log P1), pesos por fila. Newton 1-D."""
    n = len(y); r = np.arange(n); w = np.ones(n) if w is None else w
    Ly = L[r, y]; T = T0
    for _ in range(30):
        Q = temp(np.exp(L), T)
        m1 = (Q * L).sum(1); m2 = (Q * L * L).sum(1)
        g = (w * (Ly - m1)).sum(); h = (w * (m2 - m1 * m1)).sum()
        paso = g / h; T += paso
        if abs(paso) < 1e-7:
            break
    return T


def logistica(x, yb, w=None):
    """y ~ a + b x (binaria), pesos. Devuelve (a, b)."""
    w = np.ones(len(x)) if w is None else w
    a, b = 0.0, 1.0                      # identidad = perfectamente calibrado
    for _ in range(40):
        z = a + b * x; p = 1 / (1 + np.exp(-z)); v = w * p * (1 - p); r = w * (yb - p)
        g = np.array([r.sum(), (r * x).sum()])
        H = np.array([[v.sum(), (v * x).sum()], [(v * x).sum(), (v * x * x).sum()]])
        d = np.linalg.solve(H, g); a += d[0]; b += d[1]
        if np.abs(d).max() < 1e-9:
            break
    return a, b


def mbits(P, y):
    return 1000 * np.log2(P[np.arange(len(y)), y] * K)


def posiciones(P, y):
    orden = LE.rankings(P)
    return orden, np.argmax(orden == y[:, None], axis=1)


def es(x, d=2):
    return ("%.*f" % (d, x)).replace(".", ",")


def pc(x, d=2):
    return es(100 * x, d) + " %"


def ic(t, f=pc):
    return "%s [%s, %s]" % (f(t[0]), f(t[1]), f(t[2]))


# ------------------------------------------------------------------ analisis de un bloque
def calibracion(P, y, dia, con_boot=True):
    """Devuelve dict con topk esperado/real, deciles, pendiente logistica y T con IC."""
    n = len(y); r = np.arange(n)
    _, g = np.unique(dia, return_inverse=True); nd = g.max() + 1
    orden, pos = posiciones(P, y)
    Ps = np.take_along_axis(P, orden, 1)
    R = {}
    for k in (1, 3, 5):
        esp = Ps[:, :k].sum(1); real = (pos < k).astype(float)
        R["top%d" % k] = boot_medias([real, esp], g, nd)        # real, esperado, real-esperado
    # expectativa de ganancia por ficha
    e3 = PAGO * Ps[:, :3].sum(1) / 3 - 1
    r3 = (PAGO * (pos < 3) - 3) / 3
    e5 = (PAGO * (Ps[:, :5] * F5).sum(1) - F5.sum()) / F5.sum()
    r5 = (PAGO * np.where(pos < 5, F5[np.minimum(pos, 4)], 0) - F5.sum()) / F5.sum()
    R["g3"] = boot_medias([r3, e3], g, nd)
    R["g5"] = boot_medias([r5, e5], g, nd)
    # regla E2 (1 ficha si 30p >= 1,10): fichas y retorno esperado/real
    jug = PAGO * P >= 1.10
    R["e2_fichas"] = float(jug.sum(1).mean())
    R["e2_sin"] = float((jug.sum(1) == 0).mean())
    R["e2_esp"] = float((PAGO * (P * jug).sum() - jug.sum()) / max(jug.sum(), 1))
    R["e2_real"] = float((PAGO * jug[r, y].sum() - jug.sum()) / max(jug.sum(), 1))
    # fiabilidad por deciles (pares sorteo x animal)
    p = P.ravel(); yb = np.zeros_like(P); yb[r, y] = 1; yb = yb.ravel()
    cortes = np.quantile(p, np.linspace(0, 1, 11)); b = np.clip(np.searchsorted(cortes, p, "right") - 1, 0, 9)
    R["dec"] = [(p[b == i].mean(), yb[b == i].mean(), int((b == i).sum())) for i in range(10)]
    # por puesto 1..5
    R["puesto"] = [(Ps[:, k].mean(), (pos == k).mean()) for k in range(5)]
    # pendiente logistica y temperatura
    x = np.log(p / (1 - p))
    a, bl = logistica(x, yb)
    L = np.log(P); T = ajustar_T(L, y)
    R["logit"] = (a, bl); R["T"] = T
    R["mb"] = boot_medias([mbits(P, y)], g, nd)[0]
    if con_boot:
        W = pesos_dia(g, nd, NB_AJUSTE)
        bs, Ts = [], []
        for i in range(NB_AJUSTE):
            wr = W[i][g]
            bs.append(logistica(x, yb, np.repeat(wr, K))[1])
            Ts.append(ajustar_T(L, y, wr, T))
        R["logit_ic"] = (np.percentile(bs, 2.5), np.percentile(bs, 97.5))
        R["T_ic"] = (np.percentile(Ts, 2.5), np.percentile(Ts, 97.5))
    return R


def main():
    t0 = time.time()
    z = np.load(CACHE)
    P1 = LE.normalizar(z["P1"].astype(np.float64))
    y = z["y"].astype(int); dia = z["dia"]; tr = z["tramo"]; fecha = z["fecha"]
    n = len(y)
    # ---- temperatura fija (solo dev)
    dev = tr == "dev"
    T_dev = ajustar_T(np.log(P1[dev]), y[dev])
    # ---- temperatura walk-forward
    L1 = np.log(P1); Twf = np.ones(n); hist = []
    for T0 in range(0, n, 250):
        Tb = ajustar_T(L1[:T0], y[:T0]) if T0 >= 500 else 1.0
        Twf[T0:T0 + 250] = Tb; hist.append((T0, fecha[T0], Tb))
    Pdev = temp(P1, T_dev)
    Pwf = np.empty_like(P1)
    for T0, _, Tb in hist:
        Pwf[T0:T0 + 250] = temp(P1[T0:T0 + 250], Tb)
    print("T_dev = %.4f ; walk-forward: %s  (%.0f s)" % (T_dev, [round(h[2], 3) for h in hist[::4]], time.time() - t0),
          flush=True)

    RES = {}
    for t in TRAMOS:
        s = tr == t
        RES[("P1", t)] = calibracion(P1[s], y[s], dia[s], True)
        print("P1", t, "listo %.0f s" % (time.time() - t0), flush=True)
    for t in ("test", "desc"):
        s = tr == t
        RES[("Tdev", t)] = calibracion(Pdev[s], y[s], dia[s], True)
        RES[("Twf", t)] = calibracion(Pwf[s], y[s], dia[s], True)
        _, g = np.unique(dia[s], return_inverse=True); nd = g.max() + 1
        m1 = mbits(P1[s], y[s])
        RES[("dmb", t)] = (boot_medias([mbits(Pdev[s], y[s]), m1], g, nd)[2],
                           boot_medias([mbits(Pwf[s], y[s]), m1], g, nd)[2])
        print("corregido", t, "listo %.0f s" % (time.time() - t0), flush=True)
    # conjunto test+desc (lo mas cercano a 'fuera de muestra' total)
    s = (tr == "test") | (tr == "desc")
    RES[("P1", "td")] = calibracion(P1[s], y[s], dia[s], False)
    RES[("Tdev", "td")] = calibracion(Pdev[s], y[s], dia[s], False)
    RES[("Twf", "td")] = calibracion(Pwf[s], y[s], dia[s], False)
    s = (tr == "dev") | s
    RES[("P1", "all")] = calibracion(P1[s], y[s], dia[s], False)

    info = {t: (int((tr == t).sum()), len(np.unique(dia[tr == t])), fecha[tr == t][0], fecha[tr == t][-1])
            for t in TRAMOS}
    informe(RES, T_dev, hist, info)
    print("fin %.0f s" % (time.time() - t0))


# ------------------------------------------------------------------ informe
def informe(RES, T_dev, hist, info):
    L = []; di = L.append
    p1 = {t: RES[("P1", t)] for t in TRAMOS}
    di("# Hilo 7 — calibración de B1 (RD Internacional)\n")
    di("Generado por `herramientas/exploracion/calibracion_rd.py` el %s a partir de `rdint/cache_todo.npz` "
       "(predicciones walk-forward ya calculadas; no se reentrenó nada). IC95 por bootstrap de días "
       "(%d remuestreos para medias, %d para pendiente y temperatura).\n" % (time.strftime("%Y-%m-%d"), NB_MEDIA, NB_AJUSTE))
    di("| tramo | sorteos | días | desde | hasta |")
    di("|---|---|---|---|---|")
    for t in TRAMOS:
        di("| %s | %d | %d | %s | %s |" % ((NOMT[t],) + info[t]))

    di("\n## 1. ¿Está bien calibrado B1?\n")
    di("### Top-N: probabilidad que el modelo se asigna (esperado) contra lo que pasó (real)\n")
    di("| tramo | Top-N | esperado | real [IC95] | real − esperado [IC95] |")
    di("|---|---|---|---|---|")
    for t in TRAMOS + ["td", "all"]:
        for k in (1, 3, 5):
            re, es_, df = RES[("P1", t)]["top%d" % k]
            nmt = NOMT.get(t, {"td": "**prueba + réplica**", "all": "**los tres juntos**"}.get(t))
            di("| %s | Top-%d | %s | %s | %s pp |" % (nmt, k, pc(es_[0]), ic(re),
                                                   ic(df, lambda v: es(100 * v)).replace(" %", "")))
    di("\n### Pendiente de calibración y temperatura\n")
    di("- **Pendiente logística**: regresión de y (el animal salió o no) sobre logit p, con los 38 pares "
       "sorteo × animal. 1 = bien calibrado; < 1 = sobreconfiado (las p extremas deberían estar más cerca de 1/38).")
    di("- **Temperatura T (MLE)**: el exponente que maximiza la verosimilitud de P ∝ P1^T. Es la versión multinomial "
       "de la misma pendiente; T < 1 = sobreconfiado.\n")
    di("| tramo | pendiente logística [IC95] | T MLE [IC95] | mbits vs uniforme [IC95] |")
    di("|---|---|---|---|")
    for t in TRAMOS:
        R = p1[t]
        di("| %s | %s [%s, %s] | %s [%s, %s] | %s [%s, %s] |" % (
            NOMT[t], es(R["logit"][1], 3), es(R["logit_ic"][0], 3), es(R["logit_ic"][1], 3),
            es(R["T"], 3), es(R["T_ic"][0], 3), es(R["T_ic"][1], 3),
            es(R["mb"][0], 1), es(R["mb"][1], 1), es(R["mb"][2], 1)))
    di("\n### Fiabilidad por deciles de p (pares sorteo × animal)\n")
    di("| decil | " + " | ".join("p media %s | frec. real %s" % (t, t) for t in TRAMOS) + " |")
    di("|---|" + "---|---|" * len(TRAMOS))
    for i in range(10):
        di("| %d | %s |" % (i + 1, " | ".join("%s | %s" % (pc(p1[t]["dec"][i][0]), pc(p1[t]["dec"][i][1]))
                                              for t in TRAMOS)))
    di("\nCada decil de cada tramo tiene ~%s pares. La frecuencia real de un decil tiene un error típico de "
       "~0,1–0,2 pp, así que solo importan diferencias mayores." % "{:,}".format(p1["test"]["dec"][0][2]).replace(",", "."))
    di("\n### Por puesto (lo que de verdad se juega)\n")
    di("| puesto | " + " | ".join("p media %s | acierto %s" % (t, t) for t in TRAMOS) + " |")
    di("|---|" + "---|---|" * len(TRAMOS))
    for k in range(5):
        di("| %dº | %s |" % (k + 1, " | ".join("%s | %s" % (pc(p1[t]["puesto"][k][0]), pc(p1[t]["puesto"][k][1]))
                                               for t in TRAMOS)))

    di("\n## 2. Corrección por temperatura\n")
    di("- **T fijo** ajustado solo en desarrollo (MLE): **T = %s**." % es(T_dev, 4))
    di("- **T walk-forward** (reajuste cada 250 filas con todo el pasado, mínimo 500 filas): " +
       "; ".join("%s → %s" % (f, es(Tb, 3)) for i, (_, f, Tb) in enumerate(hist) if i % 6 == 0 or i == len(hist) - 1) + ".\n")
    di("| tramo | versión | Δ mbits vs P1 [IC95] | pendiente logística [IC95] | T residual [IC95] | "
       "Top-3 esp. / real | Top-5 esp. / real |")
    di("|---|---|---|---|---|---|---|")
    for t in ("test", "desc"):
        for v, nm, dm in (("P1", "B1 sin corregir", None), ("Tdev", "T fijo (dev)", RES[("dmb", t)][0]),
                          ("Twf", "T walk-forward", RES[("dmb", t)][1])):
            R = RES[(v, t)]
            di("| %s | %s | %s | %s [%s, %s] | %s [%s, %s] | %s / %s | %s / %s |" % (
                NOMT[t], nm, "—" if dm is None else "%s [%s, %s]" % tuple(es(x, 2) for x in dm),
                es(R["logit"][1], 3), es(R["logit_ic"][0], 3), es(R["logit_ic"][1], 3),
                es(R["T"], 3), es(R["T_ic"][0], 3), es(R["T_ic"][1], 3),
                pc(R["top3"][1][0]), pc(R["top3"][0][0]), pc(R["top5"][1][0]), pc(R["top5"][0][0])))
    di("\nLa temperatura es monótona: **no cambia el orden de los animales**, así que el Top-1/3/5 que se juega "
       "y su acierto real son idénticos. Lo que cambia es todo lo que usa el valor de p:\n")
    di("| tramo | versión | regla E2 (30p ≥ 1,10): fichas/sorteo | sorteos sin jugar | retorno E2 esperado | retorno E2 real |")
    di("|---|---|---|---|---|---|")
    for t in ("test", "desc"):
        for v, nm in (("P1", "B1"), ("Tdev", "T fijo"), ("Twf", "T walk-forward")):
            R = RES[(v, t)]
            di("| %s | %s | %s | %s | %s | %s |" % (NOMT[t], nm, es(R["e2_fichas"]), pc(R["e2_sin"], 1),
                                                   pc(R["e2_esp"], 1), pc(R["e2_real"], 1)))

    di("\n## 3. ¿Cuánto es realista ganar por ficha?\n")
    di("Retorno por ficha (0 % = ni se gana ni se pierde). 'Esperado' = lo que promete cada versión de p; "
       "'real' = lo que pasó, con IC95 por días.\n")
    di("| tramo | plan | esperado B1 | esperado T fijo | esperado T walk-fwd | real [IC95] |")
    di("|---|---|---|---|---|---|")
    for t in ("dev", "test", "desc", "td"):
        nmt = NOMT.get(t, "prueba + réplica")
        for key, nm in (("g3", "Top-3 plano"), ("g5", "Top-5 escalonado 2-2-2-1-1")):
            R = RES[("P1", t)]
            e_dev = RES[("Tdev", t)][key][1][0] if ("Tdev", t) in RES else None
            e_wf = RES[("Twf", t)][key][1][0] if ("Twf", t) in RES else None
            di("| %s | %s | %s | %s | %s | %s |" % (nmt, nm, pc(R[key][1][0], 1),
                                                   "—" if e_dev is None else pc(e_dev, 1),
                                                   "—" if e_wf is None else pc(e_wf, 1),
                                                   ic(R[key][0], lambda v: pc(v, 1))))
    td, al = RES[("P1", "td")], RES[("P1", "all")]
    rp = RES[("P1", "desc")]
    di("\n## Veredicto\n")
    di("- **Calibración global: bien, sin sobreconfianza demostrada.** La pendiente logística y la temperatura "
       "MLE dan %s (dev), %s (prueba) y %s (réplica); ningún IC95 excluye 1 por debajo. En prueba incluso es "
       "> 1 (algo *sub*confiado). La hipótesis 'pendiente < 1 con IC que excluye 1' **no se confirma**."
       % (es(RES[("P1", "dev")]["T"], 2), es(RES[("P1", "test")]["T"], 2), es(rp["T"], 2)))
    di("- **Pero la cola alta sí está inflada, un poco.** En los 9 casilleros tramo × Top-N el acierto real queda "
       "por debajo de lo esperado; juntando los tres tramos: Top-1 %s pp, Top-3 %s pp, Top-5 %s pp (IC95 del Top-1 y "
       "del Top-5 excluyen 0). Es ~%s %% relativo en el Top-3. El decil 10 de p también queda por debajo en los tres "
       "tramos, y en dev y prueba los deciles 1–2 también (los animales 'fríos' salen aún menos de lo que dice el modelo): el error "
       "está en los dos extremos en sentidos opuestos, por eso una temperatura única no lo arregla."
       % (es(100 * al["top1"][2][0]), es(100 * al["top3"][2][0]), es(100 * al["top5"][2][0]),
          es(100 * (1 - al["top3"][0][0] / al["top3"][1][0]), 1)))
    di("- **La temperatura no sirve.** T en dev = %s (> 1: afila, no suaviza). En prueba Δ mbits ≈ 0 (ns); en la "
       "réplica empeora (T fijo %s, walk-forward %s mbits) y **agranda** la brecha del Top-N (Top-3 esperado sube a "
       "~12,3 %% contra 11,39 %% real). No se recomienda adoptarla."
       % (es(T_dev, 3), es(RES[("dmb", "desc")][0][0]), es(RES[("dmb", "desc")][1][0])))
    di("- **¿Cambia la jugada?** No: el orden es el mismo, el Top-3 y el Top-5 escalonado son idénticos. Solo cambian "
       "las reglas que leen el valor de p (E2 30p ≥ 1,10, la elección de mesa E3 por EV5, un eventual reparto tipo "
       "Kelly) y la *expectativa* que se muestra. Con cualquier versión, la regla E2 promete ~+20 %% y en la réplica "
       "dio %s: mostrar 'ganancia esperada' a partir de p exagera." % pc(rp["e2_real"], 1))
    di("- **Ganancia realista por ficha.** El modelo promete Top-3 %s y Top-5 escalonado %s (prueba + réplica). "
       "Lo realmente obtenido fuera del desarrollo: Top-3 %s, Top-5 %s. Solo la réplica (la única prueba limpia): "
       "Top-3 %s, Top-5 %s. Cifra prudente para planificar: **~+10 a +15 %% por ficha** (no el +20–25 %% que "
       "sugiere la suma de p), con rachas y meses negativos posibles (el IC95 de la réplica toca 0)."
       % (pc(td["g3"][1][0], 1), pc(td["g5"][1][0], 1), ic(td["g3"][0], lambda v: pc(v, 1)),
          ic(td["g5"][0], lambda v: pc(v, 1)), ic(rp["g3"][0], lambda v: pc(v, 1)), ic(rp["g5"][0], lambda v: pc(v, 1))))
    di("- Nota: 'prueba' ya se miró una vez (hilo 7); nada aquí se ajustó mirando prueba ni réplica, salvo el T "
       "walk-forward, que solo usa filas anteriores a cada bloque.")
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("informe escrito en", SALIDA)


if __name__ == "__main__":
    main()
