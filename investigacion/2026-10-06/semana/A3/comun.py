import sys, numpy as np
from datetime import date
sys.path.insert(0, "/home/user/lotto-activo/herramientas"); import lotto_eval as LE
SP = "/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad"
K = 38
D = LE.cargar(SP + "/hist_0605.txt"); SEQ = np.asarray(D.seq); DIA = np.asarray(D.dia); HORA = np.asarray(D.hora)
z = np.load(SP + "/prod_0605.npz", allow_pickle=True)
P, t, y, f, h = z["P"], z["t"], z["y"].astype(int), z["f"], z["h"].astype(int)
assert (SEQ[t] == y).all()
n = len(SEQ)
# estado antes de cada sorteo del historial
G = np.empty((n, K), np.int64); LD = np.empty((n, K), np.int64); HOY = np.empty((n, K), np.int64)
last = np.full(K, -10**6); lastd = np.full(K, -10**6); cnt = np.zeros(K, np.int64); cur = None
for T in range(n):
    if DIA[T] != cur: cnt[:] = 0; cur = DIA[T]
    G[T] = T - last; LD[T] = DIA[T] - lastd; HOY[T] = cnt
    v = SEQ[T]; last[v] = T; lastd[v] = DIA[T]; cnt[v] += 1
G, LD, HOY = G[t], LD[t], HOY[t]
# día calendario anterior: ¿salió el día d-1 / d-2 (cualquier hora)?
dd = {}
for T in range(n): dd.setdefault(DIA[T], set()).add(SEQ[T])
dia_t = DIA[t]
AY = np.zeros((len(t), K), bool); AA = np.zeros((len(t), K), bool); D3 = np.zeros((len(t), K), bool)
for i, d in enumerate(dia_t):
    for a in dd.get(d - 1, ()): AY[i, a] = True
    for a in dd.get(d - 2, ()): AA[i, a] = True
    for a in dd.get(d - 3, ()): D3[i, a] = True
HOYB = HOY > 0
dow = np.array([date.fromisoformat(x).weekday() for x in f])
MVF = np.isin(dow, [2, 3, 4])
DEV = t < 9357; A26 = f >= "2026-01-01"
ud, dayid = np.unique(dia_t, return_inverse=True)
o = np.argsort(-P, 1, kind="stable"); RK = np.argmax(o == y[:, None], 1)
IN15 = RK < 15; M15 = np.take_along_axis(P, o[:, :15], 1).sum(1)
TOP15 = np.zeros_like(P, bool); np.put_along_axis(TOP15, o[:, :15], True, 1)
rows = np.arange(len(t))

def cats():
    C = {}
    for lo, hi in ((1, 12), (13, 24), (25, 36), (37, 60), (61, 120), (121, 10**9)):
        C[f"retraso {lo}-{hi if hi < 10**8 else '+'}"] = (G >= lo) & (G <= hi)
    C["salió hoy antes"] = HOYB
    C["salió ayer (no hoy)"] = AY & ~HOYB
    C["anteayer, no ayer"] = AA & ~AY & ~HOYB
    C["ayer o anteayer (no hoy)"] = (AY | AA) & ~HOYB
    C[">=4 días sin salir"] = ~HOYB & ~AY & ~AA & ~D3
    return C

def boot_ratio(Oa, Ea, Ob, Eb, ida, idb, B=2000, seed=1):
    """ratio (ΣOa/ΣEa)/(ΣOb/ΣEb) con bootstrap por días (ida/idb = id de día por sorteo)."""
    rng = np.random.default_rng(seed)
    def agg(O, E, ids):
        u, inv = np.unique(ids, return_inverse=True)
        return np.bincount(inv, O), np.bincount(inv, E)
    oa, ea = agg(Oa, Ea, ida); ob, eb = agg(Ob, Eb, idb)
    r = (oa.sum() / ea.sum()) / (ob.sum() / eb.sum())
    rs = []
    for _ in range(B):
        ia = rng.integers(0, len(oa), len(oa)); ib = rng.integers(0, len(ob), len(ob))
        rs.append((oa[ia].sum() / ea[ia].sum()) / (ob[ib].sum() / eb[ib].sum()))
    lo, hi = np.percentile(rs, [2.5, 97.5])
    return r, lo, hi

def boot_oe(O, E, ids, B=2000, seed=2):
    rng = np.random.default_rng(seed)
    u, inv = np.unique(ids, return_inverse=True); o_ = np.bincount(inv, O); e_ = np.bincount(inv, E)
    rs = [o_[i].sum() / e_[i].sum() for i in (rng.integers(0, len(o_), len(o_)) for _ in range(B))]
    return o_.sum() / e_.sum(), *np.percentile(rs, [2.5, 97.5])
