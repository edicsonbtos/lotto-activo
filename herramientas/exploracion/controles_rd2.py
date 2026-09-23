# -*- coding: utf-8 -*-
"""Control 2 del hilo 7: placebo de dias cruzados (LA de OTRO dia, misma hora).
Criterio en herramientas/resultados/hilo7_controles.md (fijado antes de correr).
Uso: python herramientas/exploracion/controles_rd2.py [semilla_ini=1 semilla_fin=19]
(con poca RAM se puede partir en tandas; el p de permutacion se junta a mano)
"""
import sys, time
from datetime import date, timedelta
import numpy as np
import controles_rd_comun as C


def main(s0=1, s1=19):
    d = C.cargar_cache(); la = C.la_dict()
    P0, y, dia, tr, fecha, hora = d["P0"], d["y"], d["dia"], d["tramo"], d["fecha"], d["hora"]
    ev = tr != "cal"; rng = np.random.default_rng(202)
    t0 = time.time()
    # control de reproduccion: x real -> debe dar el P1 del cache
    X, _ = C.construir_X(fecha, hora, la)
    P1r, hist = C.MB.cruzado(P0, X, y, R=250, minimo=500, lam=1.0)
    print("reproduccion: max|P1 - cache| = %.2e (%.0f s); b final %s"
          % (np.abs(P1r - d["P1"]).max(), time.time() - t0, np.round(hist[-1][1], 3).tolist()), flush=True)
    real = C.delta(P1r, P0, y)
    print("REAL  Δ total %+.2f [%+.2f, %+.2f]" % C.boot(real[ev], dia[ev], rng))
    del X, P1r

    def correr(nombre, fuente):
        X, _ = C.construir_X(fecha, hora, la, fuente=fuente)
        P1, hist = C.MB.cruzado(P0, X, y, R=250, minimo=500, lam=1.0)
        v = C.delta(P1, P0, y)
        m = C.boot(v[ev], dia[ev], rng)
        pt = {t: C.boot(v[tr == t], dia[tr == t], rng) for t in ("dev", "test", "desc")}
        print("%s  Δ total %+.2f [%+.2f, %+.2f]  |  " % ((nombre,) + m)
              + "  ".join("%s %+.2f [%+.2f, %+.2f]" % ((t,) + pt[t]) for t in pt)
              + "  | b final %s" % np.round(hist[-1][1], 3).tolist(), flush=True)
        return m[0]

    menos7 = [(date.fromisoformat(f) - timedelta(days=7)).isoformat() for f in fecha]
    if s0 == 1:
        correr("d-7", menos7)
    # permutaciones de fechas (sin la propia): cada fecha recibe el LA de otra fecha
    uf = np.unique(fecha); pos = {f: i for i, f in enumerate(uf)}; idx = np.array([pos[f] for f in fecha])
    perm = []
    for s in range(s0, s1 + 1):
        r = np.random.default_rng(s)
        while True:
            p = r.permutation(len(uf))
            if not np.any(p == np.arange(len(uf))):
                break
        perm.append(correr("perm%02d" % s, uf[p][idx]))
    perm = np.array(perm); rm = real[ev].mean()
    print("permutaciones: media %+.2f, de %.2f, min %+.2f, max %+.2f; real %+.2f; p = %d/%d"
          % (perm.mean(), perm.std(), perm.min(), perm.max(), rm, 1 + (perm >= rm).sum(), len(perm) + 1))
    print("tiempo total %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:3]))
