# -*- coding: utf-8 -*-
"""Verifica el texto 'Estrategia Francotirador' (ver PREREGISTRO_francotirador.md). Solo desarrollo."""
import json, os, sys
import numpy as np
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

K, B = 38, 5000
F5 = np.array([2, 2, 2, 1, 1] + [0] * (K - 5))
z = np.load(os.path.join(RAIZ, "herramientas", "exploracion", "calor_cache.npz"))
P, y = z["P"], z["y"]
la = LE.cargar(); a, b = LE.W, LE.CORTE_FIJO
hora, dow = la.hora[a:b], la.dow[a:b]
fecha = np.array(la.fecha)[a:b]; seq = la.seq
n = len(y); rng = np.random.default_rng(20261002)
LO, HI = 100 * 0.0071 / 2, 100 - 100 * 0.0071 / 2   # IC 99,29 %

H = -(P * np.log2(P + 1e-12)).sum(1)
S = -np.sort(-P, 1)
orden = np.argsort(-P, 1, kind="stable")
puesto = (orden == y[:, None]).argmax(1)
ret = 30 * F5[puesto] - F5.sum()          # por sorteo (8 fichas)
cob = {k: S[:, :k].sum(1) for k in (3, 5, 7, 15)}
res = {}


def boot(num, den, g):
    u, gi = np.unique(g, return_inverse=True)
    N = np.bincount(gi, num, len(u)); D = np.bincount(gi, den, len(u))
    k = rng.integers(0, len(u), (B, len(u)))
    bs = N[k].sum(1) / D[k].sum(1)
    return N.sum() / D.sum(), np.percentile(bs, [LO, HI])


def cuantil_por_hora(v, frac, menor=True):
    sel = np.zeros(n, bool)
    for h in np.unique(hora):
        m = hora == h; w = v[m]
        umb = np.quantile(w, frac if menor else 1 - frac)
        sel[m] = (w <= umb) if menor else (w >= umb)
    return sel


# V1 --------------------------------------------------------------
print(f"n={n} sorteos, jornadas={len(np.unique(fecha))}")
print(f"V1 entropía: min {H.min():.3f} med {np.median(H):.3f} max {H.max():.3f} (máx teórico {np.log2(K):.3f}); <4,1 bits: {(H<4.1).sum()}; >4,2: {(H>4.2).sum()}")
for k in (3, 5, 7, 15):
    print(f"V1 masa Top-{k}: med {np.median(cob[k]):.3f} máx {cob[k].max():.3f}; >=0,60: {(cob[k]>=.6).sum()}; >=0,15: {(cob[k]>=.15).sum()}")
res["V1"] = dict(Hmin=H.min(), Hmed=float(np.median(H)), Hmax=H.max(), n_H_lt_41=int((H < 4.1).sum()),
                 masa_max={k: float(cob[k].max()) for k in cob}, n_ge60={k: int((cob[k] >= .6).sum()) for k in cob})
print(f"retorno por ficha Top-5 (todos): {ret.sum()/(8*n)*100:+.2f} %")

# F1-F3 -----------------------------------------------------------
u = np.unique(fecha); mit = np.isin(fecha, u[: len(u) // 2])
for nom, v, frac, menor in [("F1 entropía 20% menor", H, .20, True), ("F2 entropía 10% menor", H, .10, True), ("F3 masa Top-5 20% mayor", cob[5], .20, False)]:
    s = cuantil_por_hora(v, frac, menor)
    r, ic = boot(ret[s], np.full(s.sum(), 8.0), fecha[s])
    dd = np.where(s, ret, 0.0) / s.mean() - ret
    d, dic = boot(dd, np.full(n, 8.0), fecha)
    m1 = ret[s & mit].sum() / (8 * (s & mit).sum()); m2 = ret[s & ~mit].sum() / (8 * (s & ~mit).sum())
    oe = (puesto[s] < 5).sum() / S[s][:, :5].sum()
    pasa = ic[0] > 0 and dic[0] > 0 and m1 > 0 and m2 > 0
    print(f"{nom}: n={s.sum()} ret {r*100:+.1f} % IC[{ic[0]*100:+.1f};{ic[1]*100:+.1f}]  dif vs todos {d*100:+.1f} pp IC[{dic[0]*100:+.1f};{dic[1]*100:+.1f}]  mitades {m1*100:+.1f}/{m2*100:+.1f}  O/E Top-5 {oe:.3f}  acierto Top-5 {(puesto[s]<5).mean()*100:.1f} % (modelo {S[s][:, :5].sum(1).mean()*100:.1f} %) -> {'PASA' if pasa else 'NO PASA'}")
    res[nom] = dict(n=int(s.sum()), ret=r, ic=ic.tolist(), dif=d, dic=dic.tolist(), mitades=[m1, m2], oe=oe, pasa=bool(pasa))

# F4: 8:00 ---------------------------------------------------------
m8 = hora == 0
print(f"\nF4 8:00: n={m8.sum()} desde {fecha[m8][0]}")
hit15 = puesto < 15
v, ic = boot(hit15[m8].astype(float), cob[15][m8], fecha[m8])
r8, ic8 = boot(ret[m8], np.full(m8.sum(), 8.0), fecha[m8])
print(f"  Top-15 acierto {hit15[m8].mean()*100:.1f} % (modelo esperaba {cob[15][m8].mean()*100:.1f} %), O/E {v:.3f} IC[{ic[0]:.3f};{ic[1]:.3f}] -> {'PASA' if ic[0] > 1 else 'NO PASA'}")
print(f"  Top-5 escalonado en las 8:00: {r8*100:+.1f} % IC[{ic8[0]*100:+.1f};{ic8[1]*100:+.1f}]")
p = hit15[m8].mean(); nn = m8.sum()
mx = cur = 0
for t in hit15[m8]:
    cur = cur + 1 if t else 0; mx = max(mx, cur)
print(f"  P(12 aciertos Top-15 seguidos desde un punto dado) = {p**12*100:.3f} %; racha máxima real de 8:00 en desarrollo: {mx}")
# simulación: racha máx esperada con n días y tasa p
sim = []
for _ in range(2000):
    xs = rng.random(nn) < p; m_ = c_ = 0
    for t in xs:
        c_ = c_ + 1 if t else 0; m_ = max(m_, c_)
    sim.append(m_)
sim = np.array(sim)
print(f"  Racha máxima por azar en {nn} días con p={p:.3f}: mediana {np.median(sim):.0f}, P(>=12) = {(sim>=12).mean()*100:.1f} %, P(>=mx real) = {(sim>=mx).mean()*100:.1f} %")
res["F4"] = dict(n=int(nn), acierto=float(p), oe=v, ic=ic.tolist(), ret=r8, ic_ret=ic8.tolist(), racha_max=mx, p_racha12_azar=float((sim >= 12).mean()))

# F5: lunes (O/E Top-5 estratificado por hora) ---------------------
hit5 = (puesto < 5).astype(float); e5 = cob[5]
horas = np.unique(hora)


def oe_mh(mask, w=None):
    w = np.ones(n) if w is None else w
    num = den = 0.0
    for h in horas:
        m = mask & (hora == h)
        num += (hit5 * w)[m].sum(); den += (e5 * w)[m].sum()
    return num / den


lun = dow == 0
uu, gi = np.unique(fecha, return_inverse=True)
bs = []
for _ in range(1500):
    cnt = np.bincount(rng.integers(0, len(uu), len(uu)), minlength=len(uu))[gi].astype(float)
    bs.append(oe_mh(lun, cnt))
ic_l = np.percentile(bs, [LO, HI]); r_l = oe_mh(lun); h1 = oe_mh(lun & mit); h2 = oe_mh(lun & ~mit)
print(f"\nF5 lunes: n={lun.sum()} O/E Top-5 {r_l:.3f} IC[{ic_l[0]:.3f};{ic_l[1]:.3f}] mitades {h1:.3f}/{h2:.3f} -> {'PASA' if (ic_l[0] > 1 or ic_l[1] < 1) and (h1-1)*(h2-1) > 0 else 'NO PASA'}")
res["F5"] = dict(oe=r_l, ic=ic_l.tolist(), mitades=[h1, h2])

# F6: fríos >12 días -----------------------------------------------
dd_ = la.dia; ult = np.full(K, -10**6); frio = np.zeros((len(seq), K), bool)
for t, (s_, d_) in enumerate(zip(seq, dd_)):
    frio[t] = (d_ - ult) > 12; ult[s_] = d_
Fm = frio[a:b]
obs6 = Fm[np.arange(n), y]; esp6 = (P * Fm).sum(1)
v6, ic6 = boot(obs6.astype(float), esp6, fecha)
print(f"F6 fríos>12d: {Fm.sum(1).mean():.2f} por sorteo, salieron {obs6.sum()} vs modelo {esp6.sum():.1f} vs azar {Fm.sum()/K:.1f}; O/E ensamble {v6:.3f} IC[{ic6[0]:.3f};{ic6[1]:.3f}] -> {'PASA' if ic6[0] > 1 else 'NO PASA'}")
res["F6"] = dict(obs=int(obs6.sum()), esp_ens=float(esp6.sum()), esp_azar=float(Fm.sum() / K), oe=v6, ic=ic6.tolist())

# F7: autocorrelación de la sorpresa --------------------------------
sor = -np.log2(P[np.arange(n), y] + 1e-12)
xs, ys = [], []
for h in horas:
    ii = np.where(hora == h)[0]
    s_ = sor[ii] - sor[ii].mean(); xs.append(s_[:-1]); ys.append(s_[1:])
xs, ys = np.concatenate(xs), np.concatenate(ys)
rho = np.corrcoef(xs, ys)[0, 1]
bs = []
for _ in range(1500):
    k = rng.integers(0, len(xs), len(xs)); bs.append(np.corrcoef(xs[k], ys[k])[0, 1])
ic7 = np.percentile(bs, [LO, HI])
print(f"F7 autocorr. sorpresa lag-1 por hora: rho {rho:+.4f} IC[{ic7[0]:+.4f};{ic7[1]:+.4f}] -> {'PASA' if ic7[0] > 0 or ic7[1] < 0 else 'NO PASA'}")
res["F7"] = dict(rho=rho, ic=ic7.tolist())

json.dump(res, open(os.path.join(os.path.dirname(__file__), "francotirador_dev.json"), "w"), indent=1, default=float)
