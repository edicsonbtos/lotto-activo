# -*- coding: utf-8 -*-
"""Idea del 2026-09-28: "día sin reciclaje". Ver PREREGISTRO_dia_sin_reciclaje.md.
Si la mañana trae más ganadores ausentes >=3 días de lo que el motor esperaba, ¿la tarde también?
  python dia_sin_reciclaje.py      (T1 LA dev + T2 RD dev, una sola corrida)
"""
import os, sys
from datetime import date
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.dirname(AQUI))
import lotto_eval as LE  # noqa: E402

K = 38


def medir(P, y, dia, hora, gapd, titulo):
    """gapd[t, i] = días desde la última salida de i antes del sorteo t (99 = nunca; 0 = hoy)."""
    G = gapd >= 3
    dias = {}
    for t in range(len(y)):
        d = dias.setdefault(dia[t], {"m": [0.0, 0.0], "t": [0.0, 0.0]})
        k = "m" if hora[t] <= 5 else "t"
        d[k][0] += float(G[t, y[t]]); d[k][1] += float(P[t, G[t]].sum())
    C = [(v["t"][0], v["t"][1]) for v in dias.values() if v["m"][0] - v["m"][1] >= 1.5 and v["t"][1] > 0]
    N = [(v["t"][0], v["t"][1]) for v in dias.values() if v["m"][0] - v["m"][1] < 1.5 and v["t"][1] > 0]
    rng = np.random.default_rng(7)

    def oe(arr):
        arr = np.array(arr); I = rng.integers(0, len(arr), (4000, len(arr)))
        b = arr[I, 0].sum(1) / arr[I, 1].sum(1)
        return arr[:, 0].sum() / arr[:, 1].sum(), np.percentile(b, 2.5), np.percentile(b, 97.5), arr[:, 0].sum(), arr[:, 1].sum()

    rc, rn = oe(C), oe(N)
    print(f"{titulo:22s} días C {len(C):3d}: tarde G {rc[3]:.0f} vs {rc[4]:.1f} esperados  O/E {rc[0]:.2f} [{rc[1]:.2f}; {rc[2]:.2f}]"
          f"  | días no-C {len(N):3d}: O/E {rn[0]:.2f} [{rn[1]:.2f}; {rn[2]:.2f}]")
    return rc[1] > 1


def gaps(seq, fechas):
    """(n, 38) días desde la última salida antes de t."""
    n = len(seq); out = np.full((n, K), 99, np.int16)
    ult = np.full(K, -10**6); dd = np.array([date.fromisoformat(f).toordinal() for f in fechas])
    for t in range(n):
        g = dd[t] - ult; g[ult < -10**5] = 99; out[t] = np.minimum(g, 99)
        ult[seq[t]] = dd[t]
    return out


def t1():
    D = LE.cargar(); c = np.load(os.path.join(AQUI, "calor_cache.npz"))
    P = c["P"] / c["P"].sum(1, keepdims=True); y = c["y"]; n = len(y)
    g = gaps(np.asarray(D.seq), D.fecha)[LE.W:LE.W + n]
    dia = np.asarray(D.dia)[LE.W:LE.W + n]; hora = np.asarray(D.hora)[LE.W:LE.W + n]
    assert (np.asarray(D.seq)[LE.W:LE.W + n] == y).all()
    m = n // 2
    a = medir(P[:m], y[:m], dia[:m], hora[:m], g[:m], "T1 LA 1.ª mitad")
    b = medir(P[m:], y[m:], dia[m:], hora[m:], g[m:], "T1 LA 2.ª mitad")
    print("T1:", "PASA" if a and b else "NO PASA")


def t2():
    z = np.load(os.path.join(os.path.dirname(AQUI), "rdint", "cache_todo.npz"), allow_pickle=True)
    filas = [l.split() for l in open(os.path.join(RAIZ, "rdint_historial.txt")) if l.strip()]
    pos = {(f, int(h)): i for i, (f, h, _) in enumerate(filas)}
    seq = np.array([int(a) if a != "00" else 37 for _, _, a in filas])  # codificación propia, solo para gaps
    g_all = gaps(seq, [f for f, _, _ in filas])
    sel = np.where(z["tramo"] == "dev")[0]
    P = z["P1"][sel]; P = P / P.sum(1, keepdims=True); y = z["y"][sel]
    f = z["fecha"][sel]; h = z["hora"][sel]
    idx = np.array([pos[(str(a), int(b))] for a, b in zip(f, h)])
    # mapear la codificación de la caché (índice 0..37 de LE) a la de gaps: usar el ganador como ancla
    cod = {}
    for i, t in enumerate(idx):
        cod.setdefault(int(y[i]), int(seq[t]))
    assert len(cod) == K and len(set(cod.values())) == K
    perm = np.array([cod[k] for k in range(K)])
    g = g_all[idx][:, perm]
    dia = np.array([date.fromisoformat(str(a)).toordinal() for a in f])
    m = len(y) // 2
    a = medir(P[:m], y[:m], dia[:m], h[:m], g[:m], "T2 RD 1.ª mitad")
    b = medir(P[m:], y[m:], dia[m:], h[m:], g[m:], "T2 RD 2.ª mitad")
    print("T2:", "PASA" if a and b else "NO PASA")


if __name__ == "__main__":
    t1(); t2()
