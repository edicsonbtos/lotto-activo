# -*- coding: utf-8 -*-
"""Control 3 del hilo 7: desalineacion horaria. x con LA desplazado k horas (k = -2..+2).
k > 0 usa sorteos de Lotto Activo POSTERIORES al RD de h:30: diagnostico, NO jugable.
Criterio en herramientas/resultados/hilo7_controles.md (fijado antes de correr).
Uso: python herramientas/exploracion/controles_rd3.py [lift|modelo] [k ...]
  lift   -> lift de la senal (a) por desfase, total y por anio (barato)
  modelo -> Delta mbits walk-forward del B1 reajustado con x desplazado (un k por proceso si falta RAM)
"""
import sys
import numpy as np
import controles_rd_comun as C

KS = [-2, -1, 0, 1, 2]
ANIOS = ["2024", "2025", "2026"]


def etiqueta(k):
    return "k=%+d%s" % (k, "  (FUTURO, no jugable)" if k > 0 else "")


def lift():
    d = C.cargar_cache(); la = C.la_dict()
    P0, y, dia, tr, fecha, hora = d["P0"], d["y"], d["dia"], d["tramo"], d["fecha"], d["hora"]
    ev = tr != "cal"; rng = np.random.default_rng(303); ar = np.arange(len(y))
    anio = np.array([f[:4] for f in fecha])
    for k in KS:
        _, lh = C.construir_X(fecha, hora, la, k=k)
        ok = ev & (lh >= 0)
        num = (y == lh).astype(float); den = np.where(lh >= 0, P0[ar, np.maximum(lh, 0)], 0.0)
        partes = []
        for nombre, s in [("total", ok)] + [(a, ok & (anio == a)) for a in ANIOS]:
            m, lo, hi = C.boot_razon(num[s], den[s], dia[s], rng)
            partes.append("%s %.3f [%.3f, %.3f] (%d/%.1f, n=%d)"
                          % (nombre, m, lo, hi, int(num[s].sum()), den[s].sum(), int(s.sum())))
        print(etiqueta(k) + "\n   " + "\n   ".join(partes), flush=True)
    # misma cobertura para todos los k: solo horas con dato en los cinco desfases (h = 2..9)
    print("\nMisma cobertura (h 10:30..17:30, horas con dato para todos los k):")
    for k in KS:
        _, lh = C.construir_X(fecha, hora, la, k=k)
        ok = ev & (lh >= 0) & (hora >= 2) & (hora <= 9)
        num = (y == lh).astype(float); den = np.where(lh >= 0, P0[ar, np.maximum(lh, 0)], 0.0)
        m, lo, hi = C.boot_razon(num[ok], den[ok], dia[ok], rng)
        print("   %s  lift %.3f [%.3f, %.3f]  n=%d" % (etiqueta(k), m, lo, hi, int(ok.sum())), flush=True)


def modelo(ks):
    d = C.cargar_cache(); la = C.la_dict()
    P0, y, dia, tr, fecha, hora = d["P0"], d["y"], d["dia"], d["tramo"], d["fecha"], d["hora"]
    ev = tr != "cal"; rng = np.random.default_rng(304)
    anio = np.array([f[:4] for f in fecha])
    for k in ks:
        X, _ = C.construir_X(fecha, hora, la, k=k)
        P1, hist = C.MB.cruzado(P0, X, y, R=250, minimo=500, lam=1.0)
        del X
        v = C.delta(P1, P0, y); del P1
        partes = ["total %+.2f [%+.2f, %+.2f]" % C.boot(v[ev], dia[ev], rng)]
        for a in ANIOS:
            s = ev & (anio == a)
            partes.append("%s %+.2f [%+.2f, %+.2f]" % ((a,) + C.boot(v[s], dia[s], rng)))
        print("%s  Δ mbits %s | b final %s" % (etiqueta(k), "  ".join(partes),
                                               np.round(hist[-1][1], 3).tolist()), flush=True)


if __name__ == "__main__":
    et = sys.argv[1] if len(sys.argv) > 1 else "lift"
    ks = [int(a) for a in sys.argv[2:]] or KS
    lift() if et == "lift" else modelo(ks)
