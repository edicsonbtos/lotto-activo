# -*- coding: utf-8 -*-
"""M4: rasgos animal-sorteo, todos con sorteos ANTERIORES a la fila i.

construir(seq, hora, dia, fecha, rd=None) -> X (n, 38, F) float32, nombres
La fila i usa solo seq[:i] (y RD de horas anteriores del mismo día). log PROD se añade aparte (lo da el arnés).
"""
import csv, os, re, sys, unicodedata
from datetime import date
import numpy as np

K = 38
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
NUM = np.array([0, -1] + list(range(1, 37)))            # "00" no coincide con ningún número
RAIZ = "/home/user/lotto-activo"
ANIMALES = {
    "DELFIN": "0", "BALLENA": "00", "CARNERO": "1", "TORO": "2", "CIEMPIES": "3", "ALACRAN": "4", "LEON": "5",
    "RANA": "6", "PERICO": "7", "RATON": "8", "AGUILA": "9", "TIGRE": "10", "GATO": "11", "CABALLO": "12",
    "MONO": "13", "PALOMA": "14", "ZORRO": "15", "OSO": "16", "PAVO": "17", "BURRO": "18", "CHIVO": "19",
    "COCHINO": "20", "GALLO": "21", "CAMELLO": "22", "CEBRA": "23", "IGUANA": "24", "GALLINA": "25", "VACA": "26",
    "PERRO": "27", "ZAMURO": "28", "ELEFANTE": "29", "CAIMAN": "30", "LAPA": "31", "ARDILLA": "32",
    "PESCADO": "33", "VENADO": "34", "JIRAFA": "35", "CULEBRA": "36"}
IDX = {p: i for i, p in enumerate(POS)}


def cargar_rd():
    """{(fecha, h): idx} de RD Internacional (h:30), del CSV histórico y de oficial_multi (juego 2)."""
    d = {}
    def sa(t):
        return re.sub(r"[^A-Z]", "", unicodedata.normalize("NFD", (t or "").upper()))
    with open(os.path.join(RAIZ, "datos_multiloteria", "rdint_hist.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            c = ANIMALES.get(sa(r["animal"]))
            if c is not None:
                d[(r["fecha"], int(r["hora"][:2]) - 8)] = IDX[c]
    with open(os.path.join(RAIZ, "datos_multiloteria", "oficial_multi.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["juego"] == "2" and r["codigo"] in IDX:
                d.setdefault((r["fecha"], int(r["hora"][:2]) - 8), IDX[r["codigo"]])
    return d


def construir(seq, hora, dia, fecha, rd=None):
    seq = np.asarray(seq); hora = np.asarray(hora); dia = np.asarray(dia); n = len(seq)
    F = {}
    def put(nm, arr):
        F[nm] = arr
    # --- conteos acumulados (C[i] = conteos en seq[:i])
    OH = np.zeros((n, K), np.int32); OH[np.arange(n), seq] = 1
    C = np.zeros((n + 1, K), np.int32); C[1:] = np.cumsum(OH, 0)
    for w in (12, 36, 120, 360):
        lo = np.maximum(np.arange(n) - w, 0)
        put(f"frec{w}", (C[:n] - C[lo]).astype(np.float32))
    # --- por día: lista de (hora, animal) en orden
    porDia = {}
    for i in range(n):
        porDia.setdefault(int(dia[i]), []).append((int(hora[i]), int(seq[i])))
    def resumen_dia(d):
        """(conteo (38,), hora de la última salida (38,) o -1, primer animal o -1, reps, reciclaje)"""
        L = porDia.get(d, [])
        cnt = np.zeros(K); hu = -np.ones(K)
        for h, a in L:
            cnt[a] += 1; hu[a] = h
        prim = L[0][1] if L and L[0][0] == 0 else -1
        return cnt, hu, prim, len(L)
    cache = {}
    def rd_(d):
        if d not in cache:
            cache[d] = resumen_dia(d)
        return cache[d]
    def reg_dia(d):
        """repeticiones del día completo y fracción reciclada (salió en d-1 o d-2)"""
        L = porDia.get(d, [])
        if len(L) < 6:
            return np.nan, np.nan
        cnt = np.bincount([a for _, a in L], minlength=K)
        reps = len(L) - (cnt > 0).sum()
        prev = (rd_(d - 1)[0] + rd_(d - 2)[0]) > 0
        rec = np.mean([prev[a] for _, a in L])
        return reps, rec
    regc = {}
    def reg(d):
        if d not in regc:
            regc[d] = reg_dia(d)
        return regc[d]

    nm_ani = ["gap1", "gap2", "gapdias", "hora_ult", "veces_hoy", "hora_ult_hoy", "sorteos_desde_hoy",
              "veces_ayer", "hora_ult_ayer", "veces_d2", "veces_d3", "prim_ayer", "prim_d3",
              "num_fecha", "num_fecha1", "num_hora", "num_mes", "rd1", "rd2"]
    nm_glo = ["hora", "dow", "dia_mes", "k_hoy", "reps_hoy", "recic_hoy", "reps_dow8", "recic_dow8", "reps_7d",
              "recic_7d", "hay_rd"]
    A = {k: np.zeros((n, K), np.float32) for k in nm_ani}
    G = {k: np.zeros(n, np.float32) for k in nm_glo}
    last = -np.ones(K, np.int64) * 10**6; last2 = -np.ones(K, np.int64) * 10**6
    lastdia = -np.ones(K) * 10**4; lasth = -np.ones(K)
    for i in range(n):
        d = int(dia[i]); h = int(hora[i]); f = fecha[i]
        dt = date.fromisoformat(f)
        A["gap1"][i] = np.minimum(i - last, 500); A["gap2"][i] = np.minimum(i - last2, 1000)
        A["gapdias"][i] = np.minimum(d - lastdia, 60); A["hora_ult"][i] = lasth
        hoy = [(hh, a) for hh, a in porDia[d] if hh < h]
        cnt = np.zeros(K); hu = -np.ones(K)
        for hh, a in hoy:
            cnt[a] += 1; hu[a] = hh
        A["veces_hoy"][i] = cnt; A["hora_ult_hoy"][i] = hu
        A["sorteos_desde_hoy"][i] = np.where(hu >= 0, h - hu, -1)
        c1, h1, p1, _ = rd_(d - 1); c2 = rd_(d - 2)[0]; c3, _, p3, _ = rd_(d - 3)
        A["veces_ayer"][i] = c1; A["hora_ult_ayer"][i] = h1; A["veces_d2"][i] = c2; A["veces_d3"][i] = c3
        if p1 >= 0: A["prim_ayer"][i, p1] = 1
        if p3 >= 0: A["prim_d3"][i, p3] = 1
        A["num_fecha"][i] = NUM == dt.day; A["num_fecha1"][i] = NUM == dt.day + 1
        A["num_hora"][i] = NUM == ((8 + h - 1) % 12 + 1); A["num_mes"][i] = NUM == dt.month
        G["hora"][i] = h; G["dow"][i] = dt.weekday(); G["dia_mes"][i] = dt.day; G["k_hoy"][i] = len(hoy)
        G["reps_hoy"][i] = len(hoy) - (cnt > 0).sum()
        prev = (c1 + c2) > 0
        G["recic_hoy"][i] = np.mean([prev[a] for _, a in hoy]) if hoy else np.nan
        r8 = [reg(d - 7 * k) for k in range(1, 9)]
        G["reps_dow8"][i] = np.nanmean([x[0] for x in r8]) if any(np.isfinite(x[0]) for x in r8) else np.nan
        G["recic_dow8"][i] = np.nanmean([x[1] for x in r8]) if any(np.isfinite(x[1]) for x in r8) else np.nan
        r7 = [reg(d - k) for k in range(1, 8)]
        G["reps_7d"][i] = np.nanmean([x[0] for x in r7]) if any(np.isfinite(x[0]) for x in r7) else np.nan
        G["recic_7d"][i] = np.nanmean([x[1] for x in r7]) if any(np.isfinite(x[1]) for x in r7) else np.nan
        hay = 0
        for j, nm in ((1, "rd1"), (2, "rd2")):
            v = rd.get((f, h - j)) if (rd is not None and h - j >= 0) else None
            if v is None:
                A[nm][i] = np.nan
            else:
                A[nm][i] = 0; A[nm][i, v] = 1; hay = 1
        G["hay_rd"][i] = hay
        a = int(seq[i])                      # actualizar estado DESPUÉS de construir la fila i
        last2[a] = last[a]; last[a] = i; lastdia[a] = d; lasth[a] = h
    X = np.concatenate([np.stack([A[k] for k in nm_ani], 2),
                        np.repeat(np.stack([G[k] for k in nm_glo], 1)[:, None, :], K, 1)], 2)
    X = np.concatenate([X, np.stack([F[k] for k in F], 2)], 2).astype(np.float32)
    return X, nm_ani + nm_glo + list(F)
