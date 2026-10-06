# -*- coding: utf-8 -*-
"""M6: rasgos walk-forward (máscaras 38 por fila) de reglas candidatas del operador. Ver PREREGISTRO.md.
construir(seq, hora, fecha, rd, filas) -> (nombres, familias, M bool (nrasgos, nfilas, 38), DEF bool (nrasgos, nfilas))
Todo lo que usa la fila t sale de seq[:t] (mismo día antes de la hora, días anteriores) o de RD de horas < h.
"""
import numpy as np
from datetime import date, timedelta

POS = ["0", "00"] + [str(i) for i in range(1, 37)]
V = np.array([0, -1] + list(range(1, 37)))           # valor numérico; 00 = -1 (sin aritmética)
ROJO = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
RUEDA = [0, 28, 9, 26, 30, 11, 7, 20, 32, 17, 5, 22, 34, 15, 3, 24, 36, 13, 1, -1, 27, 10, 25, 29, 12, 8, 19, 31,
         18, 6, 21, 33, 16, 4, 23, 35, 14, 2]       # rueda americana (-1 = 00)


def _rel():
    R = {}
    n = 38
    def mk(f):
        M = np.zeros((n, n), bool)
        for p in range(n):
            for a in range(n):
                if a != p or f is _igual:
                    M[p, a] = bool(f(p, a))
        return M
    def _igual(p, a): return p == a
    def num(f):
        return lambda p, a: V[p] >= 0 and V[a] >= 0 and f(V[p], V[a])
    def rev(x):
        r = int(f"{x:02d}"[::-1])
        return r if r <= 36 else -9
    def color(x):
        return "v" if x <= 0 else ("r" if x in ROJO else "n")
    def pano(x):  # fila, columna en paño de ruleta (1..36); 0/00 arriba
        return ((x - 1) // 3, (x - 1) % 3) if x >= 1 else None
    pos_r = {v: i for i, v in enumerate(RUEDA)}
    def drueda(p, a):
        d = abs(pos_r[V[p]] - pos_r[V[a]]); return min(d, 38 - d)
    R["igual"] = mk(_igual)
    R["pm1"] = mk(num(lambda x, y: abs(x - y) == 1))
    R["mas1"] = mk(num(lambda x, y: y == x + 1))
    R["menos1"] = mk(num(lambda x, y: y == x - 1))
    R["pm2"] = mk(num(lambda x, y: abs(x - y) == 2))
    R["ultdig"] = mk(num(lambda x, y: x % 10 == y % 10))
    R["decena"] = mk(num(lambda x, y: x // 10 == y // 10))
    R["espejo"] = mk(num(lambda x, y: rev(x) == y and x % 11 != 0))
    R["sumadig"] = mk(num(lambda x, y: x // 10 + x % 10 == y // 10 + y % 10))
    R["comp36"] = mk(num(lambda x, y: x + y == 36))
    R["comp37"] = mk(num(lambda x, y: x + y == 37))
    R["color"] = mk(lambda p, a: color(V[p]) == color(V[a]))
    R["docena"] = mk(num(lambda x, y: x >= 1 and y >= 1 and (x - 1) // 12 == (y - 1) // 12))
    R["columna"] = mk(num(lambda x, y: x >= 1 and y >= 1 and (x - 1) % 3 == (y - 1) % 3))
    R["paridad"] = mk(num(lambda x, y: x >= 1 and y >= 1 and x % 2 == y % 2))
    R["mitad"] = mk(num(lambda x, y: x >= 1 and y >= 1 and (x > 18) == (y > 18)))
    def pn(kind):
        def f(x, y):
            a, b = pano(x), pano(y)
            if a is None or b is None: return False
            dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
            return {"h": dr == 0 and dc == 1, "v": dr == 1 and dc == 0, "d": dr == 1 and dc == 1}[kind]
        return num(f)
    R["pano_h"] = mk(pn("h")); R["pano_v"] = mk(pn("v")); R["pano_d"] = mk(pn("d"))
    R["pano_any"] = R["pano_h"] | R["pano_v"] | R["pano_d"]
    R["rueda1"] = mk(lambda p, a: drueda(p, a) == 1)
    R["rueda2"] = mk(lambda p, a: drueda(p, a) == 2)
    return R


REL = _rel()
NUM2IDX = {v: i for i, v in enumerate(V)}


def construir(seq, hora, fecha, rd, filas, chequeo_hasta=None):
    """rd: dict {(fecha, h): idx} de RD Internacional. filas: índices de sorteo a puntuar.
    chequeo_hasta: si se da, se usa solo seq[:chequeo_hasta] (para la prueba de fuga ya basta con el diseño)."""
    seq = np.asarray(seq); hora = np.asarray(hora); n = len(seq)
    por_dia = {}
    for t in range(n):
        por_dia.setdefault(fecha[t], -np.ones(12, int))
    # índice de sorteo por (fecha, hora)
    tidx = {(fecha[t], int(hora[t])): t for t in range(n)}
    nf = len(filas)
    nombres, fam, masks, defs = [], [], [], []

    def add(nom, fa, M, Dm):
        nombres.append(nom); fam.append(fa); masks.append(M); defs.append(Dm)

    def ref_de(t, f, h):  # ganador (f,h) si es anterior a t
        u = tidx.get((f, h))
        return int(seq[u]) if (u is not None and u < t) else -1

    ayer = {}
    for f in set(fecha):
        ayer[f] = (date.fromisoformat(f) - timedelta(days=1)).isoformat()
    refs = {k: -np.ones(nf, int) for k in ["L1", "L2", "L3", "AYER_MISMA", "AYER_ULT", "AYER_ULT_8", "RD1", "RD2"]}
    hoy_prev = np.zeros((nf, 38), bool); rd_hoy = np.zeros((nf, 38), bool); rd_hoy_def = np.zeros(nf, bool)
    hh = np.array([int(hora[t]) for t in filas]); ff = [fecha[t] for t in filas]
    hoyw = -np.ones((nf, 12), int); ayerw = -np.ones((nf, 12), int)
    for j, t in enumerate(filas):
        f, h = fecha[t], int(hora[t]); fa = ayer[f]
        for k in range(12):
            if k < h: hoyw[j, k] = ref_de(t, f, k)
            ayerw[j, k] = ref_de(t, fa, k)
        for L in (1, 2, 3):
            if h - L >= 0: refs[f"L{L}"][j] = hoyw[j, h - L]
        refs["AYER_MISMA"][j] = ayerw[j, h]
        ult = next((ayerw[j, k] for k in range(11, -1, -1) if ayerw[j, k] >= 0), -1)
        refs["AYER_ULT"][j] = ult
        if h == 0: refs["AYER_ULT_8"][j] = ult
        if h >= 1:
            refs["RD1"][j] = rd.get((f, h - 1), -1)
            if h >= 2: refs["RD2"][j] = rd.get((f, h - 2), -1)
            r = [rd.get((f, k), -1) for k in range(h)]
            if any(x >= 0 for x in r):
                rd_hoy_def[j] = True
                for x in r:
                    if x >= 0: rd_hoy[j, x] = True
        for k in range(h):
            if hoyw[j, k] >= 0: hoy_prev[j, hoyw[j, k]] = True
    famref = {"L1": "a", "L2": "a", "L3": "a", "AYER_MISMA": "c", "AYER_ULT": "c", "AYER_ULT_8": "c", "RD1": "d", "RD2": "d"}
    for rn, r in refs.items():
        d = r >= 0
        for nm, R in REL.items():
            fa = famref[rn]
            if nm.startswith("pano") or nm.startswith("rueda"):
                fa = "b" if rn in ("L1", "L2", "L3") else fa
            M = np.zeros((nf, 38), bool); M[d] = R[r[d]]
            add(f"{rn}:{nm}", fa, M, d)
    # suma / diferencia de h-1 y h-2
    v1, v2 = V[np.maximum(refs["L1"], 0)], V[np.maximum(refs["L2"], 0)]
    d = (refs["L1"] >= 0) & (refs["L2"] >= 0) & (v1 >= 0) & (v2 >= 0)
    for nm, val in (("suma", (v1 + v2) % 37), ("dif", np.abs(v1 - v2))):
        M = np.zeros((nf, 38), bool); jj = np.where(d)[0]; M[jj, [NUM2IDX[x] for x in val[jj]]] = True
        add(f"L12:{nm}", "a", M, d)
    add("RD_hoy_antes", "d", rd_hoy.copy(), rd_hoy_def)

    # (e) pares del mismo día y transiciones, aprendidos en los 365 días previos al mes de la fila
    meses = sorted(set(f[:7] for f in ff))
    dias_ord = sorted(set(fecha)); dia_pos = {f: i for i, f in enumerate(dias_ord)}
    Mdia = np.zeros((len(dias_ord), 38), bool)
    for t in range(n): Mdia[dia_pos[fecha[t]], seq[t]] = True
    tr_p, tr_a, tr_f = [], [], []
    for t in range(1, n):
        if fecha[t] == fecha[t - 1] and hora[t] == hora[t - 1] + 1:
            tr_p.append(seq[t - 1]); tr_a.append(seq[t]); tr_f.append(fecha[t])
    tr_p, tr_a, tr_f = np.array(tr_p), np.array(tr_a), np.array(tr_f)
    dias_arr = np.array(dias_ord)
    eviF, busF, tbaj, talt, tcero = (np.zeros((nf, 38), bool) for _ in range(5))
    eviD = np.zeros(nf, bool); trD = np.zeros(nf, bool)
    off = ~np.eye(38, dtype=bool)
    for mes in meses:
        ini = mes + "-01"; d0 = (date.fromisoformat(ini) - timedelta(days=365)).isoformat()
        sel = (dias_arr >= d0) & (dias_arr < ini)
        X = Mdia[sel].astype(float); N = X.shape[0]
        C = X.T @ X; na = X.sum(0); E = np.outer(na, na) / N
        # esperado bajo "sin repetición" aproximado por independencia de presencias diarias
        lift = (C + 5) / (E + 5)
        lo, hi = np.quantile(lift[off], [0.1, 0.9])
        ev = (lift <= lo) & off; bu = (lift >= hi) & off
        st = (tr_f >= d0) & (tr_f < ini)
        Tm = np.zeros((38, 38)); np.add.at(Tm, (tr_p[st], tr_a[st]), 1)
        fa_ = np.bincount(tr_a[st], minlength=38) / max(st.sum(), 1)
        Et = Tm.sum(1, keepdims=True) * fa_[None, :]
        lt = (Tm + 3) / (Et + 3)
        tlo, thi = np.quantile(lt[off], [0.1, 0.9])
        jj = np.array([j for j in range(nf) if ff[j][:7] == mes])
        for j in jj:
            out = np.where(hoy_prev[j])[0]
            if len(out):
                eviD[j] = True
                eviF[j] = ev[out].any(0) & ~hoy_prev[j]; busF[j] = bu[out].any(0) & ~hoy_prev[j]
            p = refs["L1"][j]
            if p >= 0:
                trD[j] = True
                tbaj[j] = (lt[p] <= tlo) & off[p]; talt[j] = (lt[p] >= thi) & off[p]; tcero[j] = (Tm[p] == 0) & off[p]
    add("par_evita", "e", eviF, eviD); add("par_busca", "e", busF, eviD)
    add("trans_baja", "e", tbaj, trD); add("trans_alta", "e", talt, trD); add("trans_cero", "e", tcero, trD)

    # (f) ausencia en sorteos
    last = -np.ones(38, int) * 10 ** 6; gap = np.zeros((n, 38), int); sf = set(filas)
    for t in range(n):
        gap[t] = t - last; last[seq[t]] = t
    G = gap[filas]; dall = np.ones(nf, bool)
    for th in (48, 72, 96, 120, 150, 200):
        add(f"gap>={th}", "f", G >= th, dall)
    rk = np.argsort(np.argsort(-G, 1, kind="stable"), 1)
    add("gap_rank1", "f", rk == 0, dall); add("gap_rank1-3", "f", rk < 3, dall)

    # (g) parejas de horas
    for h1 in range(12):
        for h2 in range(h1 + 1, 12):
            sel = (hh == h2) & (hoyw[:, h1] >= 0)
            r = hoyw[:, h1]
            for nm in ("igual", "pm1", "ultdig"):
                M = np.zeros((nf, 38), bool); M[sel] = REL[nm][r[sel]]
                add(f"par_h{h1}-h{h2}:{nm}", "g", M, sel)
    for h1 in range(12):
        for h2 in range(12):
            sel = (hh == h2) & (ayerw[:, h1] >= 0)
            r = ayerw[:, h1]
            M = np.zeros((nf, 38), bool); M[sel] = REL["igual"][r[sel]]
            add(f"ayer_h{h1}-hoy_h{h2}:igual", "g", M, sel)

    # (z) controles conocidos (fecha/hora) fuera de las 8:00
    dm = np.array([int(f[8:10]) for f in ff]); h12 = (hh + 8 - 1) % 12 + 1
    for nm, num in (("dia-1", dm - 1), ("dia", dm), ("dia+1", dm + 1), ("dia+2", dm + 2), ("hora12", h12)):
        sel = (hh >= 1) & (num >= 1) & (num <= 36)
        M = np.zeros((nf, 38), bool); jj = np.where(sel)[0]; M[jj, [NUM2IDX[x] for x in num[jj]]] = True
        add(f"z:{nm}", "z", M, sel)
    return nombres, fam, np.array(masks), np.array(defs)
