# -*- coding: utf-8 -*-
"""TAREA 5 -- DETECTOR DE CAMBIO DE POLITICA.

Si el operador cambia f, hay que enterarse en semanas, no en meses.

Que hace: recorre el historial en ventanas moviles de 500 sorteos y mide,
en cada ventana, la tasa de salida por REGIMEN DE HUECO (los tramos de la
curva con mas senal). Compara contra el IC95 de referencia medido en el
tramo de DESARROLLO. Da la ALARMA si un regimen se sale de su intervalo en
DOS ventanas consecutivas (una sola puede ser ruido).

Solo LEE historial.txt. No toca nada: ni el historial, ni predicciones.json,
ni el backtest, ni el modelo.

Uso:
    python monitor_politica.py                # ultimas ventanas
    python monitor_politica.py --todas        # historia completa del monitor
    python monitor_politica.py --ventana 750  # otro tamano de ventana
"""
import argparse, json, math, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import lotto_eval as LE

K = 38
P0 = 1.0 / K
VENTANA = 500
PASO = 250
# Regimenes de la curva f(hueco). Se leen de politica_f.json si existe.
REGIMENES_POR_DEFECTO = [(1, 8), (8, 12), (12, 30), (30, 110), (110, 10 ** 7)]


def wilson(k, n, z=1.959964):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def regimenes():
    ruta = os.path.join(AQUI, "resultados", "politica_f.json")
    try:
        with open(ruta, encoding="utf-8") as f:
            b = json.load(f)["bordes_regimen"]
        if len(b) >= 2:
            return [(b[i], b[i + 1] if i + 1 < len(b) else 10 ** 7) for i in range(len(b))]
    except Exception:
        pass
    return REGIMENES_POR_DEFECTO


def estado_huecos(seq):
    n = len(seq)
    gap = np.zeros((n, K), dtype=np.int64)
    last = np.full(K, -1)
    for t in range(n):
        vis = last >= 0
        gap[t, vis] = t - last[vis]
        gap[t, ~vis] = 10 ** 6
        last[seq[t]] = t
    return gap


def tasas(gap, seq, sl, regs):
    """Tasa de salida por regimen en el tramo sl."""
    G = gap[sl]
    y = seq[sl]
    gano = np.zeros(G.shape, dtype=bool)
    gano[np.arange(len(y)), y] = True
    out = []
    for lo, hi in regs:
        m = (G >= lo) & (G < hi)
        nn = int(m.sum())
        kk = int((m & gano).sum())
        out.append((kk, nn))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ventana", type=int, default=VENTANA)
    ap.add_argument("--paso", type=int, default=PASO)
    ap.add_argument("--todas", action="store_true")
    a = ap.parse_args()

    datos = LE.cargar()
    seq = datos.seq.astype(np.int64)
    n = len(seq)
    regs = regimenes()
    gap = estado_huecos(seq)

    # ---- referencia: el tramo de DESARROLLO
    ref = tasas(gap, seq, slice(LE.W, LE.CORTE_FIJO), regs)
    print("=" * 74)
    print(" MONITOR DE POLITICA f     historial = %d sorteos" % n)
    print("=" * 74)
    print(" Referencia: desarrollo [%d, %d), %d sorteos. Ventana movil: %d, paso %d."
          % (LE.W, LE.CORTE_FIJO, LE.CORTE_FIJO - LE.W, a.ventana, a.paso))
    print()
    print(" %-14s %10s %10s %18s" % ("regimen", "n ref", "tasa ref", "IC95 de referencia"))
    print(" " + "-" * 60)
    ic = []
    for (lo, hi), (kk, nn) in zip(regs, ref):
        l, h = wilson(kk, nn)
        ic.append((l, h))
        print(" hueco %-8s %10d %9.3f%% %8.3f%% - %.3f%%"
              % ("%d-%s" % (lo, "inf" if hi > 10 ** 6 else hi - 1), nn, 100 * kk / nn,
                 100 * l, 100 * h))
    print()

    # ---- ventanas moviles sobre TODO el historial (incluye datos nuevos en vivo)
    #
    # OJO con el criterio. Comparar el PUNTO de la ventana contra el IC95 de la
    # referencia esta MAL: la referencia tiene 7357 sorteos y la ventana solo
    # 500, asi que la ventana es ~4 veces mas ruidosa y se sale de la banda por
    # puro azar una y otra vez. Hay que contrastar la DIFERENCIA entre las dos
    # proporciones, con su propio error estandar.
    inicios = list(range(LE.W, n - a.ventana + 1, a.paso))
    if not a.todas:
        inicios = inicios[-12:]
    Z_ALARMA = 3.0
    print(" VENTANAS MOVILES   (z = ventana contra referencia; ! = |z| > %.1f)" % Z_ALARMA)
    print(" %-14s %s" % ("fin de ventana", "   ".join(
        "R%d tasa    z" % (i + 1) for i in range(len(regs)))))
    print(" " + "-" * (14 + 16 * len(regs)))
    fuera_prev = [False] * len(regs)
    alarmas = []
    for t0 in inicios:
        sl = slice(t0, t0 + a.ventana)
        tt = tasas(gap, seq, sl, regs)
        celdas, fuera_now = [], []
        for i, ((kk, nn), (kr, nr)) in enumerate(zip(tt, ref)):
            r = kk / nn if nn else 0.0
            rr = kr / nr
            se = math.sqrt(r * (1 - r) / nn + rr * (1 - rr) / nr) if nn else 1.0
            z = (r - rr) / se if se > 0 else 0.0
            f = abs(z) > Z_ALARMA
            fuera_now.append(f)
            celdas.append("%5.2f%% %+5.1f%s" % (100 * r, z, "!" if f else " "))
            if f and fuera_prev[i]:
                alarmas.append((datos.fecha[t0 + a.ventana - 1], i, r, rr, z))
        print(" %-14s %s" % (datos.fecha[t0 + a.ventana - 1], "   ".join(celdas)))
        fuera_prev = fuera_now
    print()
    print(" Umbral |z| > %.1f: con %d regimenes y ~%d ventanas al ano, se espera menos de"
          % (Z_ALARMA, len(regs), int(365 * 12 / a.paso)))
    print(" una falsa alarma AISLADA al ano; exigir DOS seguidas la hace practicamente nula.")
    print()
    if alarmas:
        print(" *** ALARMA: regimen desviado |z|>%.1f en DOS ventanas consecutivas ***" % Z_ALARMA)
        for fecha, i, r, rr, z in alarmas[-8:]:
            lo, hi = regs[i]
            print("   %s  R%d (hueco %d-%s): %.3f%% contra %.3f%% de referencia  z=%+.1f"
                  % (fecha, i + 1, lo, "inf" if hi > 10 ** 6 else hi - 1, 100 * r, 100 * rr, z))
        print()
        print("   Que hacer: NO tocar el modelo todavia. Confirmar con una ventana mas y")
        print("   con la carrera mensual (consejo_carrera.py). La politica pudo cambiar.")
    else:
        print(" SIN ALARMAS: ningun regimen se desvio |z|>%.1f dos ventanas seguidas." % Z_ALARMA)
        peor = max((abs((kk / nn - kr / nr) / math.sqrt(kk / nn * (1 - kk / nn) / nn +
                                                        kr / nr * (1 - kr / nr) / nr))
                    for (kk, nn), (kr, nr) in zip(tasas(gap, seq, slice(inicios[-1],
                                                  inicios[-1] + a.ventana), regs), ref) if nn), default=0)
        print(" Desviacion mas grande en la ultima ventana: |z| = %.1f." % peor)
    print("=" * 74)


if __name__ == "__main__":
    main()
