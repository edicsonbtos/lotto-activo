# ag02: ajusta en dev y mide UNA vez en prueba (y reporta vivo) los candidatos C1 y C2 del PREREGISTRO.md.
import sys, datetime, numpy as np
from scipy import stats
sys.path.insert(0, '/home/user/lotto-activo/herramientas'); import lotto_eval as LE
BASE = '/tmp/claude-0/-home-user-lotto-activo/fffc39ca-02e7-4d69-b0fe-674a608a5e21/scratchpad/base8'
z = np.load(BASE + '/base8.npz')
S, H, F, P, PA, E1, T = z['seq'], z['hora'], z['fecha'], z['P'], z['P_aj'], z['es_primero'], z['tramo']
n = len(S)
dd = np.array([int(f[8:10]) for f in F])
def idx(v): return np.array([LE.IDX[str(int(x))] if 0 <= x <= 36 else -1 for x in v])
OFF = {s: idx(dd + s) for s in (-1, 0, 1)}
def onehot(s):
    M = np.zeros((n, 38), bool); ok = OFF[s] >= 0; M[np.where(ok)[0], OFF[s][ok]] = True; return M
MS = {s: onehot(s) for s in (-1, 0, 1)}; WIN = MS[-1] | MS[0] | MS[1]
rows = lambda m: np.where(m)[0]
def OE(r, M, Q): return int(M[r, S[r]].sum()), float((Q[r] * M[r]).sum())
def aplicar(Q, M, m): q = Q * np.where(M, m, 1.0); return q / q.sum(1, keepdims=True)
dev, pru, viv = T == 'dev', T == 'prueba', T == 'vivo'
r_dev_rest = rows(dev & ~E1)
# multiplicadores generales (dev, no primeros, contra P)
g = {}
for s in (-1, 0, 1):
    o, e = OE(r_dev_rest, MS[s], P); g[s] = (o + .5) / (e + .5)
Bgen = PA.copy()
for s in (-1, 0, 1): Bgen = np.where(E1[:, None] & ~np.isnan(PA), aplicar(Bgen, MS[s], g[s]), Bgen)
r_dev1 = rows(dev & E1)
o, e = OE(r_dev1, WIN, Bgen); x = (o + .5) / (e + .5)
o2, e2 = OE(r_dev1, WIN, PA); m2 = (o2 + .5) / (e2 + .5)
Q1 = Bgen.copy(); Q1[E1] = aplicar(Bgen[E1], WIN[E1], x)
Q2 = PA.copy(); Q2[E1] = aplicar(PA[E1], WIN[E1], m2)
print(f"generales g(-1,0,+1) = {g[-1]:.3f} {g[0]:.3f} {g[1]:.3f}; C1 extra x = {x:.3f}; C2 m = {m2:.3f}")
rng = np.random.default_rng(20261003)
def mbits(r, Q, Qb, B=4000):
    v = 1000 * np.log2(Q[r, S[r]] / Qb[r, S[r]]); bi = rng.integers(0, len(r), (B, len(r)))
    bs = v[bi].mean(1); return v.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), (bs <= 0).mean()
def topk(r, Q, k):
    rk = np.argsort(-Q[r], 1)[:, :k]; return (rk == S[r][:, None]).any(1)
def plata(r, Q, Qb, k, B=4000):
    a, b = topk(r, Q, k), topk(r, Qb, k)
    d = (30 * a / k - 1) - (30 * b / k - 1); bi = rng.integers(0, len(r), (B, len(r))); bs = d[bi].mean(1)
    return int(b.sum()), int(a.sum()), d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
def ic(o, e):
    lo = stats.chi2.ppf(.025, 2 * o) / 2 if o else 0.0; hi = stats.chi2.ppf(.975, 2 * o + 2) / 2; return lo / e, hi / e
tramos = [('dev 9:00', rows(dev & E1 & (H == 1))), ('dev 8:00', rows(dev & E1 & (H == 0))), ('dev todo', r_dev1),
          ('PRUEBA', rows(pru & E1)), ('vivo', rows(viv & E1))]
for nom, base, Q, Qb in (('C1 específico (ventana vs B_gen)', Bgen, Q1, Bgen), ('C2 práctico (ventana vs P_aj)', PA, Q2, PA)):
    print('\n' + nom)
    for tn, r in tramos:
        o, e = OE(r, WIN, base); lo, hi = ic(o, e); p = stats.poisson.cdf(o, e)
        mb = mbits(r, Q, Qb); t5 = plata(r, Q, Qb, 5); t15 = plata(r, Q, Qb, 15)
        print(f"  {tn:9s} n={len(r):3d}  O={o:2d} E={e:5.1f} O/E={o/e:.2f} [{lo:.2f};{hi:.2f}] p_unil={p:.4f} | mbits={mb[0]:+.1f} [{mb[1]:+.1f};{mb[2]:+.1f}] P(<=0)={mb[3]:.3f}"
              f" | Top5 {t5[0]}->{t5[1]} Δret/ficha {t5[2]:+.3f} [{t5[3]:+.3f};{t5[4]:+.3f}] | Top15 {t15[0]}->{t15[1]} Δret {t15[2]:+.3f} [{t15[3]:+.3f};{t15[4]:+.3f}]")
# C2 frente a la jugada de producción también para C1 (q1 vs P_aj) — práctico
print('\nq1 (general+específico) frente a P_aj:')
for tn, r in tramos:
    mb = mbits(r, Q1, PA); t5 = plata(r, Q1, PA, 5); t15 = plata(r, Q1, PA, 15)
    print(f"  {tn:9s} mbits={mb[0]:+.1f} [{mb[1]:+.1f};{mb[2]:+.1f}] | Top5 {t5[0]}->{t5[1]} | Top15 {t15[0]}->{t15[1]} Δret15 {t15[2]:+.3f} [{t15[3]:+.3f};{t15[4]:+.3f}]")
# descriptivo: desglose por corrimiento en prueba (no decide)
print('\ndesglose prueba por corrimiento (vs P_aj, descriptivo):', {s: OE(rows(pru & E1), MS[s], PA) for s in (-1, 0, 1)})
print('demás horas en prueba, ventana vs P (descriptivo, estratificado por fila):', OE(rows(pru & ~E1), WIN, P))
