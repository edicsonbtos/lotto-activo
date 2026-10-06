"""A5: ¿mié-vie recicla menos -> mejora del motor? Ajuste ene-may 2026, prueba jun-oct 2026, y al revés.
Uso: python3 a5.py <SP>   (lee hist_0605.txt y prod_0605.npz; solo lectura)"""
import sys, itertools, numpy as np
from datetime import date
sys.path.insert(0, "/home/user/lotto-activo/herramientas"); import lotto_eval as LE
S = sys.argv[1]
D = LE.cargar(S + "/hist_0605.txt"); YS = np.asarray(D.seq); FD = np.array(D.fecha)
z = np.load(S + "/prod_0605.npz", allow_pickle=True); P, t, y, f, h = z["P"], z["t"], z["y"], z["f"], z["h"]
P = np.clip(P, 1e-9, None); P = P / P.sum(1, keepdims=True)
n = len(t)
# reciclados: salieron en las 2 jornadas previas (como semana2.py)
fu = np.unique(FD); di = {d: i for i, d in enumerate(fu)}; dn = np.array([di[x] for x in FD])
R = np.zeros((n, 38), bool)
for i, T in enumerate(t):
    R[i, np.unique(YS[(dn >= dn[T] - 2) & (dn < dn[T])])] = True
yr = R[np.arange(n), y]; prec = (P * R).sum(1)
dow = np.array([date.fromisoformat(d).weekday() for d in f])
lPy = np.log2(P[np.arange(n), y])
AJ = (f >= "2026-01-01") & (f <= "2026-05-31"); PR = (f >= "2026-06-01") & (f <= "2026-10-05"); DEV = t < 9357
MVF = np.isin(dow, [2, 3, 4])
FICH = np.array([2, 2, 2, 1, 1])
rng0 = np.random.default_rng(0); B = 4000

def dlog_mult(m, rows):  # Δlog2 P(y) por sorteo para multiplicador m (array por fila) sobre reciclados
    m = np.where(rows, m, 1.0)
    return np.log2(np.where(yr, m, 1.0)) - np.log2(1 + (m - 1) * prec)

def dlog_temp(T, rows):
    lp = np.log(P); a = T * lp; a -= a.max(1, keepdims=True); lz = np.log(np.exp(a).sum(1))
    new = (a[np.arange(n), y] - lz) / np.log(2)
    return np.where(rows, new - lPy, 0.0)

def P_mult(m, rows):
    m = np.where(rows, m, 1.0)[:, None]; Q = P * np.where(R, m, 1.0); return Q / Q.sum(1, keepdims=True)

def P_temp(T, rows):
    Q = P ** T; Q /= Q.sum(1, keepdims=True); return np.where(rows[:, None], Q, P)

def ranks(Q):
    o = np.argsort(-Q, 1, kind="stable"); return np.argmax(o == y[:, None], 1)

RK0 = ranks(P)

def ganancia(rk):  # fichas netas por sorteo, Top-5 escalonado 8 fichas
    return np.where(rk < 5, 30 * FICH[np.minimum(rk, 4)], 0) - 8.0

def boot(v, mask):  # IC 90 % por jornadas de la media de v sobre mask
    ds, inv = np.unique(f[mask], return_inverse=True); per = np.bincount(inv, v[mask]); nn = mask.sum()
    idx = rng0.integers(0, len(per), (B, len(per))); b = per[idx].sum(1) / nn
    return v[mask].mean(), np.percentile(b, 5), np.percentile(b, 95)

GRID_M = np.round(np.arange(0.30, 2.0001, 0.005), 3); GRID_T = np.round(np.arange(0.50, 1.5001, 0.005), 3)

def fit_mult(fit, days):
    rows = np.isin(dow, days)
    ll = [dlog_mult(m, rows)[fit].sum() for m in GRID_M]; return GRID_M[int(np.argmax(ll))]

def fit_temp(fit, days):
    rows = np.isin(dow, days)
    ll = [dlog_temp(T, rows)[fit].sum() for T in GRID_T]; return GRID_T[int(np.argmax(ll))]

def fit_c3(fit, sig=0.10):
    ms = np.ones(7)
    for d in range(7):
        rows = dow == d
        obj = [dlog_mult(m, rows)[fit].sum() * np.log(2) - np.log(m) ** 2 / (2 * sig ** 2) for m in GRID_M]
        ms[d] = GRID_M[int(np.argmax(obj))]
    return ms

def informe(nombre, dl, Q, test, tocadas):
    mb, lo, hi = boot(1000 * dl, test)
    rk = ranks(Q)
    t5 = (rk < 5).astype(float) - (RK0 < 5); t15 = (rk < 15).astype(float) - (RK0 < 15)
    g = (ganancia(rk) - ganancia(RK0)) / 8
    a5 = boot(100 * t5, test); a15 = boot(100 * t15, test); ag = boot(100 * g, test)
    tt = test & tocadas; mbt = 1000 * dl[tt].mean() if tt.any() else 0
    print(f"  {nombre:34} Δmbits/sorteo {mb:+6.2f} [IC90 {lo:+6.2f}; {hi:+6.2f}]  (por sorteo tocado {mbt:+6.2f}) | "
          f"ΔTop-5 {a5[0]:+5.2f} pp [{a5[1]:+.2f}; {a5[2]:+.2f}]  ΔTop-15 {a15[0]:+5.2f} pp [{a15[1]:+.2f}; {a15[2]:+.2f}]  "
          f"Δretorno T5 {ag[0]:+5.2f} %/ficha [{ag[1]:+.2f}; {ag[2]:+.2f}]")
    return mb, lo, hi, ag[0]

rng5 = np.random.default_rng(5); dpl = int(rng5.integers(7))
while dpl in (2, 3, 4): dpl = int(rng5.integers(7))
NM = "lun mar mié jue vie sáb dom".split()
print(f"n AJUSTE {AJ.sum()} sorteos ({len(set(f[AJ]))} días), PRUEBA {PR.sum()} ({len(set(f[PR]))} días); día placebo C0a = {NM[dpl]}")
for k in (AJ, PR, DEV):
    a = k & MVF; b = k & ~MVF
    print(f"  reciclados O/E: mié-vie {yr[a].sum()/prec[a].sum():.3f}  resto {yr[b].sum()/prec[b].sum():.3f}")

RES = {}
for lab, fit, test in (("DIRECTA: ajuste ene-may -> prueba jun-oct", AJ, PR), ("INVERSA: ajuste jun-oct -> prueba ene-may", PR, AJ)):
    print("\n== " + lab)
    m1 = fit_mult(fit, [2, 3, 4]); T2 = fit_temp(fit, [2, 3, 4]); m3 = fit_c3(fit); m0 = fit_mult(fit, [dpl])
    print(f"  parámetros: C1 m = {m1:.3f} | C2 T = {T2:.3f} | C3 m_d = " + " ".join(f"{NM[d]} {m3[d]:.3f}" for d in range(7)) + f" | C0a ({NM[dpl]}) m = {m0:.3f}")
    rmv = MVF
    RES[(lab, "C1")] = informe("C1 mult. reciclados mié-vie", dlog_mult(m1, rmv), P_mult(m1, rmv), test, rmv) + (m1,)
    RES[(lab, "C2")] = informe("C2 temperatura mié-vie", dlog_temp(T2, rmv), P_temp(T2, rmv), test, rmv) + (T2,)
    mm = m3[dow]; allr = np.ones(n, bool)
    RES[(lab, "C3")] = informe("C3 mult. por día (σ=0,10)", dlog_mult(mm, allr), P_mult(mm, allr), test, allr) + (None,)
    rp = dow == dpl
    RES[(lab, "C0a")] = informe(f"C0a placebo C1 en {NM[dpl]}", dlog_mult(m0, rp), P_mult(m0, rp), test, rp) + (m0,)
    # C0b: las 35 ternas
    tab = []
    for tr in itertools.combinations(range(7), 3):
        r = np.isin(dow, tr); mt = fit_mult(fit, list(tr)); dl = dlog_mult(mt, r)
        tab.append((tr, mt, 1000 * dl[fit].mean(), 1000 * dl[test].mean()))
    ins = np.array([x[2] for x in tab]); oos = np.array([x[3] for x in tab])
    k = [i for i, x in enumerate(tab) if x[0] == (2, 3, 4)][0]
    print(f"  C0b 35 ternas: Δmbits en ajuste (in-sample) mediana {np.median(ins):+.2f}, máx {ins.max():+.2f}; en prueba mediana {np.median(oos):+.2f}, "
          f"p90 {np.percentile(oos,90):+.2f}, máx {oos.max():+.2f}")
    print(f"      terna mié-jue-vie: in-sample {ins[k]:+.2f} (puesto {int((ins>ins[k]).sum())+1}/35), prueba {oos[k]:+.2f} (puesto {int((oos>oos[k]).sum())+1}/35)")
    top = sorted(tab, key=lambda x: -x[3])[:5]
    print("      mejores en prueba: " + "; ".join(f"{'-'.join(NM[d] for d in x[0])} m={x[1]:.2f} {x[3]:+.2f}" for x in top))

# descriptivo: el C1 ajustado en ene-may aplicado a dev 2024-25
m1 = fit_mult(AJ, [2, 3, 4]); print("\n== EXTRA (descriptivo): C1 con m de ene-may aplicado a dev 2024-25")
informe(f"C1 m={m1:.3f} en dev", dlog_mult(m1, MVF), P_mult(m1, MVF), DEV, MVF)
print(f"  m que habría elegido dev: {fit_mult(DEV,[2,3,4]):.3f}")

# Estrategia no jugar mié-vie
print("\n== Estrategia Top-5 escalonado del motor: jugar todos los días vs no jugar mié-vie")
g0 = ganancia(RK0)
for lab, m in (("PRUEBA jun-oct", PR), ("AJUSTE ene-may", AJ)):
    for nom, sel in (("todos los días", m), ("sin mié-vie", m & ~MVF), ("solo mié-vie", m & MVF)):
        ds = sorted(set(f[m])); cum = np.cumsum([g0[sel & (f == d)].sum() for d in ds])
        dd = np.max(np.maximum.accumulate(np.concatenate([[0], cum])) - np.concatenate([[0], cum]))
        print(f"  {lab} {nom:15}: fichas jugadas {8*sel.sum():6.0f}  neto {g0[sel].sum():+7.0f}  retorno {100*g0[sel].sum()/(8*sel.sum()):+6.1f} %/ficha  máx. caída {dd:5.0f} fichas")
    # diferencia mié-vie − resto, IC por jornadas, cruda y estratificada por hora
    ds = np.array(sorted(set(f[m]))); dmv = np.array([date.fromisoformat(d).weekday() in (2, 3, 4) for d in ds])
    G = np.zeros((len(ds), 12)); C = np.zeros((len(ds), 12)); ix = {d: i for i, d in enumerate(ds)}
    for i in np.where(m)[0]: G[ix[f[i]], h[i]] += g0[i] / 8; C[ix[f[i]], h[i]] += 1
    def dif(idx):
        a = idx[dmv[idx]]; b = idx[~dmv[idx]]
        cr = G[a].sum() / C[a].sum() - G[b].sum() / C[b].sum()
        st = np.mean([G[a, k].sum() / max(C[a, k].sum(), 1) - G[b, k].sum() / max(C[b, k].sum(), 1) for k in range(12)])
        return cr, st
    base = dif(np.arange(len(ds))); bs = np.array([dif(rng0.integers(0, len(ds), len(ds))) for _ in range(2000)])
    print(f"  {lab}: retorno/ficha mié-vie − resto: crudo {100*base[0]:+.1f} pp [IC90 {100*np.percentile(bs[:,0],5):+.1f}; {100*np.percentile(bs[:,0],95):+.1f}], "
          f"estratificado por hora {100*base[1]:+.1f} pp [IC90 {100*np.percentile(bs[:,1],5):+.1f}; {100*np.percentile(bs[:,1],95):+.1f}]")

print("\n== VEREDICTO por candidata (criterio pre-registrado)")
for c in ("C1", "C2", "C3", "C0a"):
    d = RES[("DIRECTA: ajuste ene-may -> prueba jun-oct", c)]; i = RES[("INVERSA: ajuste jun-oct -> prueba ene-may", c)]
    pasa = d[1] > 0 and i[1] > 0 and d[3] >= 0 and i[3] >= 0
    fr = d[0] <= 0 or (d[4] is not None and i[4] is not None and (d[4] - 1) * (i[4] - 1) < 0)
    print(f"  {c}: directa {d[0]:+.2f} [{d[1]:+.2f}; {d[2]:+.2f}], inversa {i[0]:+.2f} [{i[1]:+.2f}; {i[2]:+.2f}] -> {'PASA' if pasa else ('FRACASA' if fr else 'DUDOSO')}")
