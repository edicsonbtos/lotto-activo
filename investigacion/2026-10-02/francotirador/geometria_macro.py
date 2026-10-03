# -*- coding: utf-8 -*-
"""Verifica 'Geometría y macro-estacionalidad' (PREREGISTRO_geometria_macro.md). Solo desarrollo."""
import json, os, sys
from datetime import date
import numpy as np
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

K, B = 38, 5000
F5 = np.array([2, 2, 2, 1, 1] + [0] * (K - 5))
z = np.load(os.path.join(RAIZ, "herramientas", "exploracion", "calor_cache.npz"))
P, y = z["P"], z["y"]
la = LE.cargar(); a, b = LE.W, LE.CORTE_FIJO
seq = la.seq; hora = la.hora[a:b]; fecha = np.array(la.fecha)[a:b]
n = len(y); ar = np.arange(n); rng = np.random.default_rng(20261002)
LO, HI = 100 * 0.00625 / 2, 100 - 100 * 0.00625 / 2   # IC 99,375 %
u = np.unique(fecha); mit = np.isin(fecha, u[: len(u) // 2])
num = np.array([0 if l == "00" else int(l) for l in LE.POS]); term = num % 10
res = {}


def boot(nu, de, g):
    uu, gi = np.unique(g, return_inverse=True)
    N = np.bincount(gi, nu, len(uu)); D = np.bincount(gi, de, len(uu))
    k = rng.integers(0, len(uu), (B, len(uu)))
    bs = N[k].sum(1) / D[k].sum(1)
    return N.sum() / D.sum(), np.percentile(bs, [LO, HI])


orden = np.argsort(-P, 1, kind="stable")
puesto = (orden == y[:, None]).argmax(1)
ret5 = 30 * F5[puesto] - F5.sum()
hit5 = (puesto < 5)
S = -np.sort(-P, 1)

# G1 ----------------------------------------------------------------
brecha = S[:, :-1] - S[:, 1:]
k_cl = np.array([int(np.argmax(r > 0.002)) + 1 if (r > 0.002).any() else K for r in brecha])
ret_cl = 30 * (puesto < k_cl) - k_cl
ret_f5 = 30 * (puesto < 5) - 5
d1, ic1 = boot(ret_cl - ret_f5, (k_cl + 5) / 2.0, fecha)       # por ficha (media de fichas)
dif = ret_cl - ret_f5
m1 = [(dif[mm].sum() / ((k_cl + 5) / 2.0)[mm].sum()) for mm in (mit, ~mit)]
pas1 = ic1[0] > 0 and min(m1) > 0
print(f"G1 clúster eps=0,002: k medio {k_cl.mean():.2f} (min {k_cl.min()}, máx {k_cl.max()}); distribución k: " + ", ".join(f"{k}:{(k_cl==k).mean()*100:.0f}%" for k in np.unique(k_cl)[:8]))
print(f"   retorno/ficha clúster {ret_cl.sum()/k_cl.sum()*100:+.1f} %, Top-5 plano {ret_f5.sum()/(5*n)*100:+.1f} %, Top-5 escalonado {ret5.sum()/(8*n)*100:+.1f} %")
print(f"   dif clúster-Top5 plano (por ficha media) {d1*100:+.1f} pp IC[{ic1[0]*100:+.1f};{ic1[1]*100:+.1f}] mitades {m1[0]*100:+.1f}/{m1[1]*100:+.1f} -> {'PASA' if pas1 else 'NO PASA'}")
res["G1"] = dict(k_medio=float(k_cl.mean()), ret_cl=float(ret_cl.sum() / k_cl.sum()), ret_f5=float(ret_f5.sum() / (5 * n)), dif=d1, ic=ic1.tolist(), mitades=m1, pasa=bool(pas1))


# G2 ----------------------------------------------------------------
def reordena(cond_fn):
    nuevo = orden.copy(); cambia = np.zeros(n, bool)
    for i in range(n):
        o = orden[i]
        j = cond_fn(o)
        if j is not None:
            quinto = o[4]; nuevo[i, 4] = o[j]; nuevo[i, j] = quinto; cambia[i] = True
    return nuevo, cambia


def cond_term(o):
    if term[o[4]] in term[o[:4]]:
        for j in range(5, K):
            if term[o[j]] not in term[o[:4]]: return j
    return None


def cond_par(o):
    pr = num[o[:5]] % 2
    if (pr == pr[0]).all():
        for j in range(5, K):
            if num[o[j]] % 2 != pr[0]: return j
    return None


for nom, fn in [("G2a terminación", cond_term), ("G2b paridad", cond_par)]:
    nuevo, cambia = reordena(fn)
    pu = (nuevo == y[:, None]).argmax(1)
    r1 = 30 * F5[pu] - F5.sum()
    d, ic = boot(r1 - ret5, np.full(n, 8.0), fecha)
    mm = [((r1 - ret5)[m].sum() / (8 * m.sum())) for m in (mit, ~mit)]
    pas = ic[0] > 0 and min(mm) > 0
    print(f"{nom}: cambia en {cambia.mean()*100:.0f} % de sorteos; acierto Top-5 {hit5.mean()*100:.2f} % -> {(pu<5).mean()*100:.2f} %; retorno {ret5.sum()/(8*n)*100:+.1f} % -> {r1.sum()/(8*n)*100:+.1f} %; dif {d*100:+.2f} pp IC[{ic[0]*100:+.2f};{ic[1]*100:+.2f}] mitades {mm[0]*100:+.1f}/{mm[1]*100:+.1f} -> {'PASA' if pas else 'NO PASA'}")
    res[nom] = dict(cambia=float(cambia.mean()), dif=d, ic=ic.tolist(), mitades=mm, pasa=bool(pas))

# G3 ----------------------------------------------------------------
e5 = S[:, :5].sum(1); h5 = hit5.astype(float); horas = np.unique(hora)
fe_d = [date.fromisoformat(f) for f in fecha]
dia = np.array([d.day for d in fe_d]); mes = np.array([d.month for d in fe_d])
import calendar
ult = np.array([calendar.monthrange(d.year, d.month)[1] for d in fe_d])
FEST = {(1, 1), (4, 19), (5, 1), (6, 24), (7, 5), (7, 24), (10, 12), (12, 24), (12, 25), (12, 31)}
dias_set = {
    "G3a quincena (15 y 30)": (dia == 15) | (dia == 30),
    "G3b fin de mes (últimos 2 días)": dia >= ult - 1,
    "G3c festivos de fecha fija": np.array([(d.month, d.day) in FEST for d in fe_d]),
}
uu, gi = np.unique(fecha, return_inverse=True)


def oe_mh(mask, w):
    nu = de = 0.0
    for h in horas:
        m = mask & (hora == h)
        nu += (h5 * w)[m].sum(); de += (e5 * w)[m].sum()
    return nu / de


for nom, M in dias_set.items():
    bs = [oe_mh(M, np.bincount(rng.integers(0, len(uu), len(uu)), minlength=len(uu))[gi].astype(float)) for _ in range(1500)]
    ic = np.percentile(bs, [LO, HI]); v = oe_mh(M, np.ones(n)); hh = [oe_mh(M & mit, np.ones(n)), oe_mh(M & ~mit, np.ones(n))]
    rr = ret5[M].sum() / (8 * M.sum())
    pas = (ic[0] > 1 or ic[1] < 1) and (hh[0] - 1) * (hh[1] - 1) > 0 and (hh[0] - 1) * (v - 1) > 0
    print(f"{nom}: n={M.sum()} sorteos ({len(np.unique(fecha[M]))} jornadas); O/E Top-5 {v:.3f} IC[{ic[0]:.3f};{ic[1]:.3f}] mitades {hh[0]:.3f}/{hh[1]:.3f}; retorno {rr*100:+.1f} % (resto {ret5[~M].sum()/(8*(~M).sum())*100:+.1f} %) -> {'PASA' if pas else 'NO PASA'}")
    res[nom] = dict(n=int(M.sum()), oe=v, ic=ic.tolist(), mitades=hh, ret=float(rr), pasa=bool(pas))

# G4 ----------------------------------------------------------------
def alternancia(clase, nombre, lag=1):
    c = clase[np.arange(K)]                      # clase por animal (-1 = excluido)
    t = np.arange(a, b)
    prev = seq[t - lag]
    ok = (c[prev] >= 0) & (c[y] >= 0)
    # esperado: Σ P sobre animales de clase opuesta a la del previo (renormalizado sobre animales con clase >=0)
    opp = (c[None, :] != c[prev][:, None]) & (c[None, :] >= 0)
    valid = c[None, :] >= 0
    esp = (P * opp).sum(1) / (P * valid).sum(1)
    obs = (c[y] != c[prev]).astype(float)
    v, ic = boot(obs[ok], esp[ok], fecha[ok])
    hh = [obs[ok & mm].sum() / esp[ok & mm].sum() for mm in (mit, ~mit)]
    return v, ic, hh, ok.sum()


par = np.where(num == 0, -1, num % 2)
mag = np.where(num == 0, -1, (num > 18).astype(int))
for nom, cl in [("G4a paridad", par), ("G4b magnitud", mag)]:
    v, ic, hh, nn = alternancia(cl, nom)
    pas = (ic[0] > 1 or ic[1] < 1) and (hh[0] - 1) * (hh[1] - 1) > 0 and (hh[0] - 1) * (v - 1) > 0
    v2, ic2, _, _ = alternancia(cl, nom, lag=2)
    print(f"{nom}: n={nn}; O/E alternancia {v:.3f} IC[{ic[0]:.3f};{ic[1]:.3f}] mitades {hh[0]:.3f}/{hh[1]:.3f}; control lag 2: {v2:.3f} IC[{ic2[0]:.3f};{ic2[1]:.3f}] -> {'PASA' if pas else 'NO PASA'}")
    res[nom] = dict(oe=v, ic=ic.tolist(), mitades=hh, control_lag2=v2, pasa=bool(pas))

json.dump(res, open(os.path.join(os.path.dirname(__file__), "geometria_macro_dev.json"), "w"), indent=1, default=float)
