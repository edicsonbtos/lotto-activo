# -*- coding: utf-8 -*-
"""Hilo 9, paso 2 (PREREGISTRO_hilo9_subir.md): lo que pasó el paso 1 (R4 y L3) como término softmax con un
coeficiente walk-forward (reajuste cada 250 filas, sólo con filas pasadas). Sólo desarrollo.

  R4  RD:  P = softmax(log P1 + c·[salió en RD hoy antes de h])
  L3  LA:  P = softmax(log P_ens + c·[RD (h−2):30 == i])

Métricas: Δ mbits por mitades (pasa si ≥ +5 e IC95 > 0 en ambas) y retorno por ficha del Top-5
escalonado 2-2-2-1-1 (IC95 por jornadas). Secundario (no decide): con la regla de cambio en vigor.
Uso: python herramientas/hilo9/paso2.py  -> herramientas/resultados/hilo9_paso2.md
"""
import os, sys
from collections import defaultdict
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import residuos as RS
LE, DT, HERR, RAIZ = RS.LE, RS.DT, RS.HERR, RS.RAIZ

SALIDA = os.path.join(HERR, "resultados", "hilo9_paso2.md")
F5 = np.array([2, 2, 2, 1, 1]); GRID = np.arange(-3.0, 1.001, 0.02)


def ajustar(logP, X, y, R=250):
    """logP (n,38), X (n,38) 0/1. Devuelve log-prob del ganador con c walk-forward y la serie de c."""
    n = len(y); out = np.zeros(n); cs = []; Pn = np.zeros_like(logP)

    def lp(c, idx):
        z = logP[idx] + c * X[idx]; z = z - z.max(1, keepdims=True)
        return z - np.log(np.exp(z).sum(1, keepdims=True))
    for k0 in range(0, n, R):
        idx = np.arange(k0, min(k0 + R, n))
        if k0 == 0:
            c = 0.0
        else:
            past = np.arange(0, k0); sel = X[past].any(1)
            past = past[sel]
            c = max(GRID, key=lambda c: lp(c, past)[np.arange(len(past)), y[past]].sum()) if len(past) else 0.0
        cs.append((k0, c)); L = lp(c, idx); Pn[idx] = np.exp(L); out[idx] = L[np.arange(len(idx)), y[idx]]
    return out, cs, Pn


def top5_ret(P, y, cambio=None):
    """Retorno por ficha del Top-5 escalonado; cambio: lista de animal a sacar (o -1) por fila."""
    orden = np.argsort(-P, 1, kind="stable")[:, :6]; r = np.zeros(len(y))
    for t in range(len(y)):
        top = list(orden[t])
        if cambio is not None and cambio[t] >= 0 and cambio[t] in top[:5]:
            top = [a for a in top[:5] if a != cambio[t]] + [top[5]]
        top = top[:5]
        r[t] = (30 * F5[top.index(y[t])] if y[t] in top else 0) - F5.sum()
    return r / F5.sum() * 100, orden


def bloque(nombre, base, nuevo, y, dia, extra_ret):
    rng = np.random.default_rng(20260924)
    d = (nuevo - base) / np.log(2) * 1000
    u, g = np.unique(dia, return_inverse=True); mitad = len(u) // 2

    def ic(v, sel):
        du = np.unique(g[sel]); S = np.bincount(g[sel], v[sel], len(u)); N = np.bincount(g[sel], None, len(u))
        bs = [S[k].sum() / N[k].sum() for k in (rng.choice(du, len(du)) for _ in range(2000))]
        return v[sel].mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
    L = ["\n## %s\n" % nombre, "| tramo | n | Δ mbits | IC95 | ≥ +5 e IC > 0 |", "|---|---|---|---|---|"]
    ok = []
    for nom, sel in (("dev completo", np.ones(len(d), bool)), ("1ª mitad", g < mitad), ("2ª mitad", g >= mitad)):
        mu, lo, hi = ic(d, sel); ok.append(mu >= 5 and lo > 0)
        L.append("| %s | %d | %+.2f | [%+.2f, %+.2f] | %s |" % (nom, sel.sum(), mu, lo, hi, "sí" if ok[-1] else "no"))
    L += ["", "| jugada (Top-5 escalonado) | retorno/ficha | Δ contra base | IC95 de Δ |", "|---|---|---|---|"]
    r0 = extra_ret[0][1]
    for nom, r in extra_ret:
        mu, lo, hi = ic(r - r0, np.ones(len(r), bool))
        L.append("| %s | %+.2f %% | %+.2f pp | [%+.2f, %+.2f] |" % (nom, r.mean(), mu, lo, hi))
    return L, all(ok[1:])


def tasas(P, y):
    rk = (P > P[np.arange(len(y)), y][:, None]).sum(1) + 1
    return "Top-3 %.2f %% · Top-5 %.2f %% · Top-15 %.2f %%" % tuple(100 * (rk <= k).mean() for k in (3, 5, 15))


def main():
    la = LE.cargar(RS.ruta(RAIZ, "historial.txt"))
    la_d = defaultdict(dict)
    for f, h, s in zip(la.fecha, la.hora, la.seq):
        la_d[f][int(h)] = int(s)
    rd, *_ = DT.cargar()
    rd_d = defaultdict(dict)
    for f, h, s in zip(rd.fecha, rd.hora, rd.seq):
        rd_d[f][int(h)] = int(s)
    out = ["# Hilo 9 — paso 2: R4 y L3 como término del modelo (sólo desarrollo, walk-forward)\n"]

    # ---------------- R4 (RD)
    T = np.load(RS.ruta(HERR, "rdint", "cache_todo.npz")); s = T["tramo"] == "dev"
    P1 = T["P1"][s].astype(float); P1 /= P1.sum(1, keepdims=True)
    y = T["y"][s]; hr = T["hora"][s]; fe = T["fecha"][s]; dia = T["dia"][s]
    X = np.zeros_like(P1)
    for t, (f, h) in enumerate(zip(fe, hr)):
        for hh, a in rd_d.get(f, {}).items():
            if hh < h:
                X[t, a] = 1
    base = np.log(P1[np.arange(len(y)), y]); nuevo, cs, Pn = ajustar(np.log(np.clip(P1, 1e-12, 1)), X, y)
    r0, _ = top5_ret(P1, y); r1, _ = top5_ret(Pn, y)
    L, ok_r4 = bloque("R4 — RD: + c·[salió en RD hoy]", base, nuevo, y, dia,
                      [("B1 (en uso)", r0), ("B1 + R4", r1)])
    out += L + ["", "c walk-forward: " + ", ".join("%d:%.2f" % p for p in cs[::4]) +
                " (×%.2f al final)" % np.exp(cs[-1][1]),
                "Tasas: B1 %s | B1+R4 %s" % (tasas(P1, y), tasas(Pn, y)), "**R4 paso 2: %s**" % ("PASA" if ok_r4 else "NO PASA")]

    # ---------------- L3 (LA)
    C = np.load(RS.ruta(HERR, "exploracion", "calor_cache.npz")); PL = C["P"]; yl = C["y"]
    fl = np.array(la.fecha[LE.W:LE.W + len(yl)]); hl = np.asarray(la.hora)[LE.W:LE.W + len(yl)]
    dl = np.asarray(la.dia)[LE.W:LE.W + len(yl)]
    m = (fl < RS.LA_FIN) & np.array([f in rd_d for f in fl])
    PL, yl, fl, hl, dl = PL[m], yl[m], fl[m], hl[m], dl[m]
    PL = PL / PL.sum(1, keepdims=True)
    X = np.zeros_like(PL); cam1 = np.full(len(yl), -1); cam2 = np.full(len(yl), -1)
    for t, (f, h) in enumerate(zip(fl, hl)):
        dd = rd_d.get(f, {})
        if h >= 2 and (h - 2) in dd:
            X[t, dd[h - 2]] = 1; cam2[t] = dd[h - 2]
        if h >= 1 and (h - 1) in dd:
            cam1[t] = dd[h - 1]
    base = np.log(PL[np.arange(len(yl)), yl]); nuevo, cs, Pn = ajustar(np.log(np.clip(PL, 1e-12, 1)), X, yl)
    r0, _ = top5_ret(PL, yl); r1, _ = top5_ret(Pn, yl)
    rc, _ = top5_ret(PL, yl, cam1); rc3, _ = top5_ret(Pn, yl, cam1)
    L, ok_l3 = bloque("L3 — LA: + c·[RD (h−2):30]", base, nuevo, yl, dl,
                      [("ensamble (base)", r0), ("ensamble + L3", r1),
                       ("secundario: base + regla de cambio (en uso)", rc),
                       ("secundario: + L3 + regla de cambio", rc3)])
    out += L + ["", "c walk-forward: " + ", ".join("%d:%.2f" % p for p in cs[::4]) +
                " (×%.2f al final)" % np.exp(cs[-1][1]),
                "Tasas: base %s | +L3 %s" % (tasas(PL, yl), tasas(Pn, yl)), "**L3 paso 2: %s**" % ("PASA" if ok_l3 else "NO PASA")]
    txt = "\n".join(out)
    print(txt, flush=True)
    with open(SALIDA, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    main()
