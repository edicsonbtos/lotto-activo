from comun import *
import importlib.util
from scipy.optimize import minimize
spec = importlib.util.spec_from_file_location("iv2", "/home/user/lotto-activo/herramientas/modelos/intradia_v2.py")
iv2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(iv2)
tabs, Dn = iv2.construir(D, {}); F = Dn[t]
# (a) ablación aproximada de los rasgos de semana natural: quitar su aporte al log-odds del ensamble
W_INTRA = 0.5158691954066458          # peso de intradia_v2 en pesos_ensamble.json
B_SEM = (-0.131, +0.034)              # coeficientes semana_actual / semana_anterior ajustados al 1-ene-2026 (salida_m4)
def top15(Q, m):
    oq = np.argsort(-Q, 1, kind="stable"); rk = np.argmax(oq == y[:, None], 1)
    return (rk < 15)[m].sum() / np.take_along_axis(Q, oq[:, :15], 1).sum(1)[m].sum(), (rk < 15)[m].mean()
lg = np.log(P) - W_INTRA * (B_SEM[0] * F[:, :, 4] + B_SEM[1] * F[:, :, 5])
Q = np.exp(lg - lg.max(1, keepdims=True)); Q /= Q.sum(1, keepdims=True)
print("(a) Ablación de 'semana natural' (aporte quitado del log-odds):")
for era, me in (("dev", DEV), ("2026", A26)):
    for g, gm in (("MVF", MVF), ("SM", ~MVF)):
        m = me & gm; a0, h0 = top15(P, m); a1, h1 = top15(Q, m)
        print(f"   {era:4} {g:3} Top-15 O/E con {a0:.3f} ({h0*100:.1f}%)  sin {a1:.3f} ({h1*100:.1f}%)")
print(f"   cambio medio |Δ log P| por animal: {np.abs(np.log(Q)-np.log(P)).mean():.3f}")
# (b) regla simple DESCRIPTIVA (no confirmatoria): en MVF, P_i × a si salió hoy, × b si salió anteayer-no-ayer.
# ajuste en 2026-T1, evaluación en 2026-T2+T3 (todo 2026 ya está mirado: solo da el orden de magnitud)
Mh = HOYB.astype(float); Ma = (AA & ~AY & ~HOYB).astype(float)
def aplica(par, m):
    la, lb = par; L = np.log(P[m]) + la * Mh[m] + lb * Ma[m]; L -= L.max(1, keepdims=True); E = np.exp(L); return E / E.sum(1, keepdims=True)
def nll(par, m): Qm = aplica(par, m); return -np.log(Qm[np.arange(m.sum()), y[m]]).sum()
fit = (f >= "2026-01-01") & (f <= "2026-03-31"); tst = (f >= "2026-04-01")
print("\n(b) Regla simple descriptiva (ajuste 26-T1, prueba 26-T2+T3):")
for g, gm in (("MVF", MVF), ("SM", ~MVF)):
    r = minimize(nll, [0, 0], args=(fit & gm,), method="Nelder-Mead"); a, b = np.exp(r.x)
    m = tst & gm; Qm = aplica(r.x, m); ym = y[m]; ii = np.arange(m.sum())
    mb = 1000 * np.log2(Qm[ii, ym] / P[m][ii, ym])
    u, inv = np.unique(dayid[m], return_inverse=True); sd = np.bincount(inv, mb); cn = np.bincount(inv)
    rng = np.random.default_rng(4); bs = [sd[i].sum() / cn[i].sum() for i in (rng.integers(0, len(sd), len(sd)) for _ in range(2000))]
    oq = np.argsort(-Qm, 1, kind="stable"); h15 = (np.argmax(oq == ym[:, None], 1) < 15).mean()
    print(f"   {g:3}: ×{a:.2f} si salió hoy, ×{b:.2f} si salió anteayer → prueba {mb.mean():+.1f} mbits [{np.percentile(bs,2.5):+.1f}; {np.percentile(bs,97.5):+.1f}],"
          f" Top-15 {IN15[m].mean()*100:.1f}% → {h15*100:.1f}%")
