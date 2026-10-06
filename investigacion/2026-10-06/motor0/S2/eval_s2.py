# -*- coding: utf-8 -*-
"""S2: evaluación común. Acierto Top-15 y plata (Top-15 plano, Top-15 ponderado 3-2-1, Top-5 escalonado), todas
con la regla de cambio RD (h−1):30 ("quitar y subir"; no a las 8:00), más mbits contra PROD.
Diferencias pareadas contra PROD con IC 90 % por jornadas."""
import sys
import numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
import arnes as A

SP = A.SP
_rdD = A.LE.cargar("/home/user/lotto-activo/rdint_historial.txt")
RD = {(f, int(h)): int(s) for f, h, s in zip(_rdD.fecha, _rdD.hora, _rdD.seq)}
RDV = np.array([RD.get((A.F[i], int(A.H[i]) - 1), -1) if A.H[i] >= 1 else -1 for i in range(len(A.T))])
PLANES = {"T15plano": np.ones(15), "T15pond": np.array([3, 3, 3, 2, 2] + [1] * 10, float),
          "T5esc": np.array([2, 2, 2, 1, 1], float)}


def norm(P):
    P = np.where(np.isfinite(P), P, 1 / 38); P = np.clip(P, 1e-9, None); return P / P.sum(1, keepdims=True)


def rango_rd(P, idx, cambio=True):
    """Puesto del ganador (0 = primero) tras la regla de cambio RD; 99 si el ganador es el RD quitado."""
    o = np.argsort(-P[idx], 1, kind="stable"); y = A.Y[idx]; r = RDV[idx]
    rk = np.argmax(o == y[:, None], 1)
    if not cambio:
        return rk
    rkr = np.where(r >= 0, np.argmax(o == np.maximum(r, 0)[:, None], 1), 999)
    # al quitar RD en el puesto rkr, los de detrás suben uno; el ganador = RD queda fuera de toda lista
    rk2 = np.where(rk > rkr, rk - 1, rk); rk2 = np.where((r >= 0) & (y == r), 99, rk2)
    return rk2   # vale para cualquier N: si RD está fuera del Top-N, (rk > rkr) implica rk > N también


def ic90_dias(v, idx):
    ds = A.F[idx]; u, inv = np.unique(ds, return_inverse=True); per = np.bincount(inv, v); cnt = np.bincount(inv)
    se = np.sqrt(((per - v.mean() * cnt) ** 2).sum() * len(u) / (len(u) - 1)) / len(v)
    return v.mean() - 1.645 * se, v.mean() + 1.645 * se


def ganancia(rk, plan):
    f = PLANES[plan]; n = len(f)
    return np.where(rk < n, 30 * f[np.minimum(rk, n - 1)], 0.0), f.sum()


def resumen(P, nombre, tramo, ref=None, cambio=True, sel=None):
    """sel: máscara booleana opcional (len(A.T)) de sorteos jugados."""
    P = norm(P); ref = A.PROD if ref is None else norm(ref)
    m = A.TRAMOS[tramo] if sel is None else (A.TRAMOS[tramo] & sel)
    idx = np.where(m)[0]; y = A.Y[idx]
    rk = rango_rd(P, idx, cambio); rkp = rango_rd(ref, idx, cambio)
    nd = len(np.unique(A.F[idx])); out = dict(nombre=nombre, tramo=tramo, n=len(idx), dias=nd)
    dmb = 1000 * np.log2(P[idx, y] / A.PROD[idx, y])
    out["mbits"] = 1000 * np.log2(P[idx, y] * 38).mean(); out["dmb"] = dmb.mean(); out["dmb_ic"] = ic90_dias(dmb, idx)
    h = (rk < 15).astype(float); hp = (rkp < 15).astype(float)
    out["top15"] = 100 * h.mean(); out["top15_ref"] = 100 * hp.mean(); out["d15_ic"] = tuple(100 * x for x in ic90_dias(h - hp, idx))
    out["d15"] = 100 * (h - hp).mean()
    out["top5"] = 100 * (rk < 5).mean()
    for pl in PLANES:
        g, c = ganancia(rk, pl); gp, _ = ganancia(rkp, pl)
        r = g / c - 1; rp = gp / c - 1
        out[pl] = 100 * r.mean(); out[pl + "_ic"] = tuple(100 * x for x in ic90_dias(r, idx))
        out[pl + "_ref"] = 100 * rp.mean(); out[pl + "_d"] = 100 * (r - rp).mean()
        out[pl + "_dic"] = tuple(100 * x for x in ic90_dias(r - rp, idx))
        out[pl + "_netodia"] = (g - c).sum() / nd; out[pl + "_netodia_ref"] = (gp - c).sum() / nd
    return out


def linea(o):
    return (f"{o['nombre']:16} {o['tramo']:8} n={o['n']:5d} mbits {o['mbits']:+6.1f} Δ {o['dmb']:+6.1f} "
            f"[{o['dmb_ic'][0]:+5.1f};{o['dmb_ic'][1]:+5.1f}] | Top15 {o['top15']:.1f} (PROD {o['top15_ref']:.1f}) "
            f"Δ {o['d15']:+.2f} [{o['d15_ic'][0]:+.2f};{o['d15_ic'][1]:+.2f}] | T15plano {o['T15plano']:+.1f}% "
            f"(PROD {o['T15plano_ref']:+.1f}) T15pond {o['T15pond']:+.1f}% ({o['T15pond_ref']:+.1f}) "
            f"T5esc {o['T5esc']:+.1f}% ({o['T5esc_ref']:+.1f}) Δ {o['T5esc_d']:+.1f} [{o['T5esc_dic'][0]:+.1f};{o['T5esc_dic'][1]:+.1f}]")


def mezcla(P, w):
    P = norm(P); z = (1 - w) * np.log(A.PROD) + w * np.log(P); z -= z.max(1, keepdims=True)
    e = np.exp(z); return e / e.sum(1, keepdims=True)
