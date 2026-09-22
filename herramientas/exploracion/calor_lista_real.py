# -*- coding: utf-8 -*-
"""El calor de la lista REAL: ¿avisa el ensamble de cuándo su Top-15 es bueno?

Idea. Antes de cada sorteo el modelo reparte probabilidad entre los 38
animales. La suma de las 15 mayores es su propia apuesta sobre si el Top-15
acertará. A eso lo llamamos CALOR de la lista. Se conoce ANTES del sorteo.

Tres preguntas, en este orden:

  1. CALIBRACIÓN: cuando el modelo dice 55 %, ¿acierta el 55 %? Si no está
     calibrado, todo lo demás sobra.
  2. ¿VARÍA? Si el calor es casi constante, no hay nada que seleccionar.
  3. SELECCIÓN: jugando solo los sorteos con calor por encima de un umbral,
     ¿se supera el 50 % de equilibrio con el intervalo ENTERO por encima?

También se mide la pregunta de las rachas sobre el modelo real: ¿el calor de
la lista cae tras una racha de aciertos, como pasaba con la regla de ventana?

Walk-forward sobre desarrollo [2000, 9357). NO toca el tramo de prueba.
"""
import os, sys
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERR = os.path.join(RAIZ, "herramientas")
sys.path.insert(0, HERR)
import lotto_eval as LE          # noqa: E402

PAGO = 30
TOPN = int(sys.argv[1]) if len(sys.argv) > 1 else 15
EQUILIBRIO = TOPN / PAGO         # jugar N animales a 30x: se empata en N/30
#   Top-15 -> 50,0 %   ·   Top-5 -> 16,7 %   ·   Top-3 -> 10,0 %


def ic95(k, n):
    if not n:
        return 0.0, 0.0
    t = k / n
    e = 1.96 * (t * (1 - t) / n) ** 0.5
    return 100 * (t - e), 100 * (t + e)


def main():
    datos = LE.cargar(os.path.join(RAIZ, "historial.txt"))
    print(f"historial: {len(datos)} sorteos · desarrollo [{LE.W}, {LE.CORTE_FIJO})")
    print("calculando el ensamble walk-forward (esto tarda)...", flush=True)
    modelo = LE.cargar_modelo(os.path.join(HERR, "modelos", "ensamble_v2.py"))
    P = modelo.predecir(datos, LE.W)
    y = datos.seq[LE.W:]
    fin = LE.CORTE_FIJO - LE.W
    P, y = P[:fin], y[:fin]
    n = len(P)

    orden = np.argsort(-P, axis=1)
    top = orden[:, :TOPN]
    acierto = np.array([y[i] in top[i] for i in range(n)], dtype=int)
    calor = np.sort(P, axis=1)[:, -TOPN:].sum(axis=1)   # masa del Top-15

    print(f"\nn = {n}   ·   Top-15 real = {100*acierto.mean():.2f} %")
    print(f"calor medio = {100*calor.mean():.2f} %   (si el modelo se cree a sí mismo,")
    print(f"                                          debería coincidir con la tasa)")

    print("\n" + "=" * 70)
    print("1. CALIBRACIÓN — ¿cumple el modelo lo que promete?")
    print("=" * 70)
    qs = np.quantile(calor, [0, .2, .4, .6, .8, 1.0])
    print(f"\n{'tramo de calor':<22}{'n':>7}{'promete':>10}{'cumple':>10}{'IC95':>18}")
    print("-" * 70)
    for i in range(5):
        lo_c, hi_c = qs[i], qs[i + 1]
        m = (calor >= lo_c) & (calor <= hi_c) if i == 4 else (calor >= lo_c) & (calor < hi_c)
        if m.sum() == 0:
            continue
        k, nn = int(acierto[m].sum()), int(m.sum())
        lo, hi = ic95(k, nn)
        print(f"{100*lo_c:>6.1f}-{100*hi_c:<14.1f}{nn:>7}{100*calor[m].mean():>9.1f}%"
              f"{100*k/nn:>9.1f}%{lo:>9.1f}-{hi:<8.1f}")

    print("\n" + "=" * 70)
    print("2. ¿VARÍA EL CALOR LO BASTANTE PARA SELECCIONAR?")
    print("=" * 70)
    print(f"\n  mínimo {100*calor.min():.1f} %  ·  p10 {100*np.quantile(calor,.1):.1f} %"
          f"  ·  mediana {100*np.median(calor):.1f} %"
          f"  ·  p90 {100*np.quantile(calor,.9):.1f} %  ·  máximo {100*calor.max():.1f} %")
    print(f"  desviación típica: {100*calor.std():.2f} pp")
    print(f"  sorteos con calor >= {100*EQUILIBRIO:.1f} % (equilibrio): {(calor>=EQUILIBRIO).sum()} "
          f"de {n} ({100*(calor>=EQUILIBRIO).mean():.1f} %)")

    print("\n" + "=" * 70)
    print(f"3. SELECCION — jugar solo cuando la lista esta caliente (Top-{TOPN})")
    print("=" * 70)
    print(f"\n{'umbral':<10}{'sorteos':>9}{'% del total':>13}{'acierta':>10}{'IC95':>18}{'':>4}")
    print("-" * 70)
    umbrales = [0.0] + [float(q) for q in np.quantile(calor, np.arange(.1, .96, .1))]
    for u in umbrales:
        m = calor >= u
        if m.sum() < 100:
            continue
        k, nn = int(acierto[m].sum()), int(m.sum())
        lo, hi = ic95(k, nn)
        veredicto = f"  SUPERA {100*EQUILIBRIO:.0f}" if lo > 100 * EQUILIBRIO else ""
        print(f"{100*u:>5.1f}%{nn:>13}{100*m.mean():>12.1f}%{100*k/nn:>9.1f}%"
              f"{lo:>9.1f}-{hi:<8.1f}{veredicto}")
    print("-" * 70)
    print(f"'SUPERA {100*EQUILIBRIO:.0f}' = el intervalo ENTERO por encima del equilibrio "
          f"({100*EQUILIBRIO:.1f} %).")
    print("Sin eso, no hay nada que explotar: el margen cabe dentro del ruido.")

    print("\n" + "=" * 70)
    print("4. ¿CAE EL CALOR TRAS UNA RACHA DE ACIERTOS? (como en la regla)")
    print("=" * 70)
    print(f"\n{'racha previa':<26}{'n':>7}{'calor sig.':>13}{'acierta':>10}")
    print("-" * 60)
    for etiq, val in (("k ACIERTOS seguidos", 1), ("k FALLOS seguidos", 0)):
        print(f"  -- {etiq} --")
        for k in range(0, 5):
            idx = [i for i in range(k, n - 1)
                   if not k or all(acierto[i - j] == val for j in range(k))]
            if len(idx) < 60:
                break
            sig = [i + 1 for i in idx]
            print(f"  {k:<24}{len(idx):>7}{100*calor[sig].mean():>12.2f}%"
                  f"{100*acierto[sig].mean():>9.1f}%")


if __name__ == "__main__":
    main()
