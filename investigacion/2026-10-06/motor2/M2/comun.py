# -*- coding: utf-8 -*-
"""M2: rasgos de calendario y categorías de regla por fila de A.T (solo usan sorteos anteriores)."""
import sys, numpy as np
from datetime import date, timedelta
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
import arnes as A
K = 38
IDX = {c: i for i, c in enumerate(["0", "00"] + [str(i) for i in range(1, 37)])}
FER = set("""2024-01-01 2024-02-12 2024-02-13 2024-03-28 2024-03-29 2024-04-19 2024-05-01 2024-06-24 2024-07-05
2024-07-24 2024-10-12 2024-12-24 2024-12-25 2024-12-31 2025-01-01 2025-03-03 2025-03-04 2025-04-17 2025-04-18
2025-04-19 2025-05-01 2025-06-24 2025-07-05 2025-07-24 2025-10-12 2025-12-24 2025-12-25 2025-12-31 2026-01-01
2026-02-16 2026-02-17 2026-04-02 2026-04-03 2026-04-19 2026-05-01 2026-06-24 2026-07-05 2026-07-24""".split())

SEQ = np.asarray(A.D.seq); DIA = np.asarray(A.D.dia); T = A.T; n = len(T)
Y, F, H, DOW = A.Y, A.F, A.H, A.DOW
assert (SEQ[T] == Y).all()

# --- categorías de regla (máscaras n×38) ---
HOY = np.zeros((n, K), bool); AYAA = np.zeros((n, K), bool)
porDia = {}
for t in range(len(SEQ)): porDia.setdefault(DIA[t], []).append(t)
pos = {t: i for i, t in enumerate(T)}
for i, t in enumerate(T):
    d = DIA[t]
    for u in porDia[d]:
        if u < t: HOY[i, SEQ[u]] = True
    for dd in (d - 1, d - 2):
        for u in porDia.get(dd, ()): AYAA[i, SEQ[u]] = True
AYAA &= ~HOY
FECHA = np.zeros((n, K), bool); HORA12 = np.zeros((n, K), bool)
DOM = np.array([int(x[8:10]) for x in F])
for i in range(n):
    for m in (DOM[i] - 1, DOM[i], DOM[i] + 1):
        if 1 <= m <= 36: FECHA[i, IDX[str(m)]] = True
    h12 = (H[i] + 8 - 1) % 12 + 1; HORA12[i, IDX[str(h12)]] = True
CATS = {"M3_hoy": HOY, "M4_ayaa": AYAA, "M5_fecha": FECHA, "M6_hora": HORA12}

# --- grupos de calendario por fecha ---
def _ultimo(d):
    nx = (d.replace(day=28) + timedelta(days=4)); return (nx - timedelta(days=nx.day)).day

def libre(d): return d.weekday() >= 5 or d.isoformat() in FER

def atributos(fs):
    """dict nombre -> bool por fecha (str)."""
    out = {}
    for f in fs:
        d = date.fromisoformat(f); dm = d.day; ul = _ultimo(d)
        # racha de días libres que contiene d
        lw = False
        if libre(d):
            a = d; b = d
            while libre(a - timedelta(days=1)): a -= timedelta(days=1)
            while libre(b + timedelta(days=1)): b += timedelta(days=1)
            lw = (b - a).days + 1 >= 3
        out[f] = dict(G_pago=dm in (1, 15, 16, 30, 31), G_q15=dm in (15, 16), G_q30=dm in (30, 31, 1),
                      G_vq=d.weekday() == 4 and dm in (13, 14, 15, 28, 29, 30, 31), G_ini=dm <= 3, G_fin=dm > ul - 3,
                      G_fer=f in FER, G_lw=lw, G_finde=d.weekday() >= 5, G_vie=d.weekday() == 4,
                      G_mvf=d.weekday() in (2, 3, 4))
    return out

UF = np.unique(F); ATR = atributos(UF)
GRUPOS = list(next(iter(ATR.values())).keys())
TARDE = H >= 5
DAYID = np.searchsorted(UF, F)

def mascara(g, attr=ATR):
    return np.array([attr[f][g] for f in F])

PROD = A.PROD
O15 = np.argsort(-PROD, 1, kind="stable")
TOP15 = np.zeros_like(PROD, bool); np.put_along_axis(TOP15, O15[:, :15], True, 1)
CATS_ALL = dict(M1_top15=TOP15, **CATS)
MB = 1000 * np.log2(38 * PROD[np.arange(n), Y])
MBc = MB.copy()   # estratificado por hora dentro de cada tramo
for tr in ("AJUSTE", "ELECCION", "PRUEBA26", "ANTIGUO"):
    m = A.TRAMOS[tr]
    for h in range(12):
        k = m & (H == h)
        if k.any(): MBc[k] -= MB[k].mean()
