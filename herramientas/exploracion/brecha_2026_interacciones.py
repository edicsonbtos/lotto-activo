# -*- coding: utf-8 -*-
"""Anexo de PREREGISTRO_brecha_2026.md: barrido variable × tramo horario, mismo protocolo (nulo por simulación,
descubrir en 2026-A, confirmar una vez en 2026-B). Salida: brecha_2026_interacciones_salida.txt"""
import os, sys
from multiprocessing import Pool
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI); sys.path.insert(0, os.path.join(os.path.dirname(AQUI)))
import lotto_eval as LE  # noqa: E402
import hora_8am_ciega as H8  # noqa: E402
import brecha_2026 as B  # noqa: E402

GRUPOS = (("8:00", [0]), ("9-11", [1, 2, 3]), ("12-15", [4, 5, 6, 7]), ("16-19", [8, 9, 10, 11]))
LINEAS = []


def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LINEAS.append(s)


def main():
    B.log = H8.log = lambda *a: None
    H8.armar_historial(); D, Pall = H8.walk_forward(); RD, LARD = B.cargar_rd_lard()
    F = np.array(D.fecha); n0 = LE.W
    sel = {k: np.nonzero((F[n0:] >= a) & (F[n0:] < b))[0] for k, (a, b) in B.TRAMOS.items() if k != "2025"}
    filas = np.concatenate([sel["2026-A"], sel["2026-B"]]) + n0
    X, nombres = B.bateria(D, RD, LARD, list(filas))
    base = [f for f, nm in enumerate(nombres) if not nm.startswith(("A ", "M "))]
    hora = np.asarray(D.hora)[filas]
    XI = np.zeros((len(filas), len(base) * len(GRUPOS), B.K), bool); nomI = []
    for gi, (g, hs) in enumerate(GRUPOS):
        m = np.isin(hora, hs)
        for k, f in enumerate(base):
            XI[m, gi * len(base) + k] = X[m, f]
        nomI += [f"{nombres[f]} × {g}" for f in base]
    nA = len(sel["2026-A"])
    P = Pall[filas - n0]; P = P / P.sum(1, keepdims=True); y = np.asarray(D.seq)[filas]; dia = np.asarray(D.dia)[filas]
    XA, PA, yA = XI[:nA], P[:nA], y[:nA]
    O, E, V, _ = B.oe(XA, PA, yA)
    z = np.where(V > 0, (O - E) / np.sqrt(np.maximum(V, 1e-12)), 0)
    with Pool(4) as pool:
        nulo = np.concatenate(pool.map(B._sim, [(B.SEMILLA + 10 + s, B.N_SIM // 4, XA, PA, E, V) for s in range(4)]))
    umbral = float(np.percentile(nulo, 95))
    log(f"Barrido: {XI.shape[1]} interacciones; 2026-A n={nA}, 2026-B n={len(y) - nA}; "
        f"percentil 95 del máximo |z| bajo el nulo = {umbral:.2f}")
    oeA = O / np.maximum(E, 1e-12)
    cand = [f for f in range(XI.shape[1]) if abs(z[f]) > umbral and abs(oeA[f] - 1) >= 0.10]
    log("Las 15 interacciones con mayor |z| en 2026-A:")
    for f in np.argsort(-np.abs(z))[:15]:
        log(f"  {nomI[f]:<60} O/E {oeA[f]:.2f}  z {z[f]:+.2f}  {'CANDIDATA' if f in cand else ''}")
    XB, PB, yB, dB = XI[nA:], P[nA:], y[nA:], dia[nA:]
    for f in cand:
        q = np.einsum("ti,ti->t", XB[:, f], PB); o = XB[np.arange(len(yB)), f, yB].astype(float)
        bb = B.boot_ratio(dB, o, q); r = o.sum() / q.sum()
        p = float(np.mean(bb >= 1)) if oeA[f] < 1 else float(np.mean(bb <= 1))
        ok = (r < 1) == (oeA[f] < 1) and p < 0.05 / len(cand)
        log(f"  Confirmar {nomI[f]:<52} 2026-B {r:.2f} [IC95 {np.percentile(bb, 2.5):.2f}; {np.percentile(bb, 97.5):.2f}] "
            f"p={p:.4f} => {'CONFIRMADA' + (' (ya conocida: RD)' if 'RD (h-1):30' in nomI[f] else '') if ok else 'no'}")
    with open(os.path.join(AQUI, "brecha_2026_interacciones_salida.txt"), "w", encoding="utf-8") as fo:
        fo.write("\n".join(LINEAS) + "\n")


if __name__ == "__main__":
    main()
