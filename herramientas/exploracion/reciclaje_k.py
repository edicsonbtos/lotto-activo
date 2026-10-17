# -*- coding: utf-8 -*-
"""Ver PREREGISTRO_reciclaje_k.md.  python reciclaje_k.py"""
import os, sys
from datetime import date
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(AQUI)); sys.path.insert(0, AQUI)
import lotto_eval as LE
import dia_sin_reciclaje as D0
K = 38

def medir(P, y, dia, hora, g, titulo, ks=(3, 4)):
    R = (g >= 1) & (g <= 2)
    top = np.argsort(-P, 1)[:, :15]; T = np.zeros_like(P, bool); np.put_along_axis(T, top, True, 1)
    dias = {}
    for t in range(len(y)): dias.setdefault(dia[t], []).append(t)
    rng = np.random.default_rng(11)
    def oe(a):
        a = np.array(a)
        if len(a) < 5: return None
        I = rng.integers(0, len(a), (3000, len(a))); b = a[I, 0].sum(1) / a[I, 1].sum(1)
        return a[:, 0].sum() / a[:, 1].sum(), np.percentile(b, 2.5), np.percentile(b, 97.5), len(a)
    for k in ks:
        res = {"recicla": ([], []), "no recicla": ([], [])}
        for d, ix in dias.items():
            ix = sorted(ix, key=lambda t: hora[t])
            if len(ix) < 10: continue
            a, b = ix[:k], ix[k:]
            E = sum(R[t, y[t]] - P[t, R[t]].sum() for t in a)
            c = "recicla" if E >= 1 else "no recicla" if E <= -1 else None
            if not c: continue
            res[c][0].append((sum(R[t, y[t]] for t in b), sum(P[t, R[t]].sum() for t in b)))
            res[c][1].append((sum(T[t, y[t]] for t in b), sum(P[t, T[t]].sum() for t in b)))
        for c, (m1, m2) in res.items():
            r1, r2 = oe(m1), oe(m2)
            f = lambda r: "n/d" if r is None else f"{r[0]:.2f} [{r[1]:.2f}; {r[2]:.2f}]"
            n = len(m1)
            print(f"{titulo:16s} k={k} {c:10s} días {n:4d}  O/E reciclaje {f(r1)}   O/E Top-15 {f(r2)}")

def la():
    Dd = LE.cargar(); c = np.load(os.path.join(AQUI, "calor_cache.npz"))
    P = c["P"] / c["P"].sum(1, keepdims=True); y = c["y"]; n = len(y)
    g = D0.gaps(np.asarray(Dd.seq), Dd.fecha)[LE.W:LE.W + n]
    dia = np.asarray(Dd.dia)[LE.W:LE.W + n]; hora = np.asarray(Dd.hora)[LE.W:LE.W + n]
    m = n // 2
    medir(P[:m], y[:m], dia[:m], hora[:m], g[:m], "LA 1.ª mitad"); medir(P[m:], y[m:], dia[m:], hora[m:], g[m:], "LA 2.ª mitad")

def rd():
    z = np.load(os.path.join(os.path.dirname(AQUI), "rdint", "cache_todo.npz"), allow_pickle=True)
    filas = [l.split() for l in open(os.path.join(os.path.dirname(os.path.dirname(AQUI)), "rdint_historial.txt")) if l.strip()]
    pos = {(f, int(h)): i for i, (f, h, _) in enumerate(filas)}
    seq = np.array([int(a) if a != "00" else 37 for _, _, a in filas]); g_all = D0.gaps(seq, [f for f, _, _ in filas])
    sel = np.where(z["tramo"] == "dev")[0]
    P = z["P1"][sel]; P = P / P.sum(1, keepdims=True); y = z["y"][sel]; f = z["fecha"][sel]; h = z["hora"][sel]
    idx = np.array([pos[(str(a), int(b))] for a, b in zip(f, h)])
    cod = {}
    for i, t in enumerate(idx): cod.setdefault(int(y[i]), int(seq[t]))
    perm = np.array([cod[k] for k in range(K)]); g = g_all[idx][:, perm]
    dia = np.array([date.fromisoformat(str(a)).toordinal() for a in f]); m = len(y) // 2
    medir(P[:m], y[:m], dia[:m], h[:m], g[:m], "RD 1.ª mitad"); medir(P[m:], y[m:], dia[m:], h[m:], g[m:], "RD 2.ª mitad")

if __name__ == "__main__":
    la(); rd()
