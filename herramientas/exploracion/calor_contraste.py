# -*- coding: utf-8 -*-
"""¿El calor de la lista separa de verdad los sorteos buenos de los malos?

La tabla acumulada de calor_lista_real.py engaña un poco: cada fila contiene a
la siguiente, así que la mejora parece suave y continua aunque no lo sea. Aquí
se mira el contraste limpio:

  * Tasa por DECIL de calor (deciles disjuntos, no acumulados).
  * Test de dos muestras: mitad caliente vs mitad fría. El corte es la MEDIANA,
    elegida de antemano y no ajustada, así que no hay pesca de umbral.
  * Tendencia a lo largo de los deciles (Cochran-Armitage).

Cachea la salida del ensamble en calor_cache.npz: la primera vez tarda, las
siguientes son instantáneas.

Walk-forward sobre desarrollo [2000, 9357). NO toca el tramo de prueba.
"""
import math, os, sys
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERR = os.path.join(RAIZ, "herramientas")
AQUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(AQUI, "calor_cache.npz")
sys.path.insert(0, HERR)
import lotto_eval as LE          # noqa: E402

PAGO = 30


def matriz():
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        print(f"(cache: {os.path.basename(CACHE)})")
        return z["P"], z["y"]
    datos = LE.cargar(os.path.join(RAIZ, "historial.txt"))
    print("calculando el ensamble walk-forward (solo la primera vez)...", flush=True)
    modelo = LE.cargar_modelo(os.path.join(HERR, "modelos", "ensamble_v2.py"))
    P = modelo.predecir(datos, LE.W)
    y = datos.seq[LE.W:]
    fin = LE.CORTE_FIJO - LE.W
    P, y = np.asarray(P[:fin]), np.asarray(y[:fin])
    np.savez_compressed(CACHE, P=P, y=y)
    return P, y


def ic95(k, n):
    t = k / n
    e = 1.96 * (t * (1 - t) / n) ** 0.5
    return 100 * (t - e), 100 * (t + e)


def analizar(P, y, topn):
    equil = topn / PAGO
    n = len(P)
    orden = np.argsort(-P, axis=1)[:, :topn]
    acierto = np.array([y[i] in orden[i] for i in range(n)], dtype=int)
    calor = np.sort(P, axis=1)[:, -topn:].sum(axis=1)

    print("\n" + "=" * 72)
    print(f"TOP-{topn}   ·   tasa global {100*acierto.mean():.2f} %   ·   "
          f"equilibrio {100*equil:.1f} %")
    print("=" * 72)

    print(f"\nPor DECIL de calor (disjuntos, del más frío al más caliente):")
    print(f"{'decil':<8}{'calor medio':>13}{'n':>7}{'acierta':>10}{'IC95':>18}")
    print("-" * 60)
    bordes = np.quantile(calor, np.linspace(0, 1, 11))
    tasas = []
    for i in range(10):
        m = (calor >= bordes[i]) & (calor < bordes[i + 1]) if i < 9 else (calor >= bordes[i])
        k, nn = int(acierto[m].sum()), int(m.sum())
        lo, hi = ic95(k, nn)
        tasas.append(k / nn)
        print(f"{i+1:<8}{100*calor[m].mean():>12.2f}%{nn:>7}{100*k/nn:>9.2f}%"
              f"{lo:>9.2f}-{hi:<8.2f}")

    med = np.median(calor)
    cal, fri = calor >= med, calor < med
    kc, nc = int(acierto[cal].sum()), int(cal.sum())
    kf, nf = int(acierto[fri].sum()), int(fri.sum())
    tc, tf = kc / nc, kf / nf
    se = (tc * (1 - tc) / nc + tf * (1 - tf) / nf) ** 0.5
    z = (tc - tf) / se
    print(f"\n  MITAD CALIENTE vs MITAD FRÍA (corte = mediana, fijado de antemano)")
    print(f"    caliente: {100*tc:.2f} %  ({kc}/{nc})")
    print(f"    fría:     {100*tf:.2f} %  ({kf}/{nf})")
    print(f"    diferencia: {100*(tc-tf):+.2f} pp   z = {z:.2f}   "
          f"p(una cola) = {0.5*math.erfc(z/2**0.5):.4f}")

    # tendencia sobre deciles (Cochran-Armitage con pesos 1..10)
    x = np.arange(1, 11)
    nn_d = np.array([int(((calor >= bordes[i]) & (calor < bordes[i+1])).sum())
                     if i < 9 else int((calor >= bordes[i]).sum()) for i in range(10)])
    kk_d = np.array([int(acierto[(calor >= bordes[i]) & (calor < bordes[i+1])].sum())
                     if i < 9 else int(acierto[calor >= bordes[i]].sum()) for i in range(10)])
    pbar = kk_d.sum() / nn_d.sum()
    xbar = (nn_d * x).sum() / nn_d.sum()
    num = ((x - xbar) * (kk_d - nn_d * pbar)).sum()
    den = (pbar * (1 - pbar) * (nn_d * (x - xbar) ** 2).sum()) ** 0.5
    print(f"\n  TENDENCIA sobre los 10 deciles: z = {num/den:.2f}"
          f"   (p una cola = {0.5*math.erfc((num/den)/2**0.5):.4f})")

    ev = lambda t: (PAGO * t - topn) / topn * 100
    print(f"\n  En dinero (pago {PAGO}x, apuesta igual por animal):")
    print(f"    jugando todo:            EV {ev(acierto.mean()):+.1f} %")
    print(f"    jugando la mitad caliente: EV {ev(tc):+.1f} %  "
          f"(IC bajo {ev(ic95(kc,nc)[0]/100):+.1f} %)")


if __name__ == "__main__":
    P, y = matriz()
    print(f"n = {len(P)} sorteos de desarrollo")
    for topn in (3, 5, 15):
        analizar(P, y, topn)
