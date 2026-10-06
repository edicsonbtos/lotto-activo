# -*- coding: utf-8 -*-
"""S1: meta-modelo P(ganador en Top-15) walk-forward con reajuste mensual. Parte 1 y parte 3.
Uso: python modelo.py   -> ajusta, guarda <SP>/S1_pred.npz y escribe la evaluación (AJUSTE y ELECCION)
"""
import sys, os, json, warnings
from datetime import date, timedelta
import numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
import arnes as A  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
import lightgbm as lgb  # noqa: E402
warnings.filterwarnings("ignore")

SP = A.SP; n = len(A.T)
Z = np.load(SP + "/S1_rasgos.npz", allow_pickle=True)
NOM = list(Z["nombres"])
ORD = np.array([date.fromisoformat(x).toordinal() for x in A.F])
MESES = [f"{y}-{m:02d}" for y, m in [(2025, k) for k in range(7, 13)] + [(2026, k) for k in range(1, 11)]]
CONT = [f for f in NOM if f not in ("hora", "dow")]


def matriz(nm, cols=None, onehot=True):
    cols = cols or NOM
    X = [Z[f"{nm}__{f}"] for f in cols if f not in ("hora", "dow")]
    if onehot:
        if "hora" in cols: X += [(A.H == h).astype(float) for h in range(1, 12)]
        if "dow" in cols: X += [(A.DOW == d).astype(float) for d in range(1, 7)]
    else:
        if "hora" in cols: X.append(A.H.astype(float))
        if "dow" in cols: X.append(A.DOW.astype(float))
    return np.column_stack(X)


def lr_fit(X, y, w, C=0.05):
    mu = np.average(X, 0, w); sd = np.sqrt(np.average((X - mu) ** 2, 0, w)) + 1e-9
    m = LogisticRegression(C=C, max_iter=2000).fit((X - mu) / sd, y, sample_weight=w / w.mean())
    return lambda Xn: m.decision_function((Xn - mu) / sd), m


def gbm_fit(X, y, w):
    m = lgb.LGBMClassifier(n_estimators=150, learning_rate=0.03, num_leaves=7, min_child_samples=200, reg_lambda=10,
                           colsample_bytree=0.8, subsample=0.8, subsample_freq=1, verbose=-1, n_jobs=4, random_state=0)
    m.fit(X, y, sample_weight=w / w.mean())
    return lambda Xn: m.predict(Xn, raw_score=True), m


def platt(s, y):
    m = LogisticRegression(C=1e4).fit(s[:, None], y); return lambda z: m.predict_proba(z[:, None])[:, 1]


def walk(X, y, fitter, filas=None, hl=365.0):
    """Predicciones walk-forward mensuales calibradas con Platt (últimos 90 días del pasado)."""
    filas = np.ones(n, bool) if filas is None else filas
    p = np.full(n, np.nan); p0 = np.full(n, np.nan); ult = None
    for ms in MESES:
        o = date.fromisoformat(ms + "-01").toordinal(); m_te = (np.char.startswith(A.F.astype(str), ms)) & filas
        if not m_te.any(): continue
        tr = (ORD < o) & filas; cal = tr & (ORD >= o - 90); tr_in = tr & (ORD < o - 90)
        w = 0.5 ** ((o - ORD) / hl)
        f_in, _ = fitter(X[tr_in], y[tr_in], w[tr_in]); cl = platt(f_in(X[cal]), y[cal])
        f_all, ult = fitter(X[tr], y[tr], w[tr])
        p[m_te] = cl(f_all(X[m_te]))
        p0[m_te] = np.average(y[tr], weights=w[tr])
    return p, p0, ult


def ll(p, y): p = np.clip(p, 1e-6, 1 - 1e-6); return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def auc(s, l):
    from scipy.stats import rankdata
    r = rankdata(s); n1 = l.sum(); n0 = len(l) - n1
    return (r[l == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


RNG = np.random.default_rng(7)


def auc_ic(s, l, m, B=400):
    ds = A.F[m]; u, inv = np.unique(ds, return_inverse=True); idx = [np.where(inv == k)[0] for k in range(len(u))]
    s = s[m]; l = l[m]; out = []
    for _ in range(B):
        b = np.concatenate([idx[k] for k in RNG.integers(0, len(u), len(u))]); out.append(auc(s[b], l[b]))
    return auc(s, l), np.percentile(out, 5), np.percentile(out, 95)


def informe(nombre, y, preds, base, tramos=("AJUSTE", "ELECCION"), filas=None, lineas=None):
    filas = np.ones(n, bool) if filas is None else filas
    for tr in tramos:
        m = A.TRAMOS[tr] & filas & ~np.isnan(preds[base])
        l0 = ll(preds[base][m], y[m])
        txt = f"  [{nombre}] {tr:8} n={m.sum():5d} acierto {y[m].mean()*100:.1f}% | logloss {base} {l0.mean():.4f}"
        for k, p in preds.items():
            if k == base: continue
            lk = ll(p[m], y[m]); d = lk - l0; lo, hi = A._ic90(d, m)
            a, alo, ahi = auc_ic(p, y, m)
            txt += f"\n      {k:10} logloss {lk.mean():.4f} Δ {1000*d.mean():+6.2f} m [{1000*lo:+6.2f};{1000*hi:+6.2f}]  AUC {a:.3f} [{alo:.3f};{ahi:.3f}]  P̂ media {p[m].mean():.3f}"
        print(txt); lineas is not None and lineas.append(txt)


def calibracion(p, y, m, bins=(0, .45, .48, .50, .52, .54, .56, .58, .60, 1)):
    out = []
    for a, b in zip(bins[:-1], bins[1:]):
        mm = m & (p >= a) & (p < b)
        if mm.sum(): out.append(f"[{a:.2f},{b:.2f}) n={mm.sum()} P̂={p[mm].mean():.3f} real={y[mm].mean():.3f}")
    return " | ".join(out)


if __name__ == "__main__":
    L = []
    def pr(s): print(s, flush=True); L.append(s)
    res = {}
    for nm in ("PROD", "M4"):
        y = Z[f"{nm}__hit"]
        X1 = matriz(nm, onehot=True); X2 = matriz(nm, onehot=False)
        pLR, p0, mLR = walk(X1, y, lr_fit)
        pGB, _, mGB = walk(X2, y, gbm_fit)
        masa = Z[f"{nm}__masa15"]
        # solo hora+día (control: ¿todo viene del calendario?) y solo masa+RD
        pHD, _, _ = walk(matriz(nm, ["hora", "dow"]), y, lr_fit)
        pMR, _, _ = walk(matriz(nm, ["masa15", "rd_disp", "rd_in15"]), y, lr_fit)
        _, p0c, _ = walk(matriz(nm, ["hora"])[:, :1] * 0, y, lambda X, yy, w: (lambda Xn: np.zeros(len(Xn)), None), hl=30.0)
        preds = {"C0": p0, "C0_vm30d": p0c, "C1_masa": masa, "LR": pLR, "GBM": pGB, "LR_horadia": pHD, "LR_masa+RD": pMR}
        res[nm] = preds
        pr(f"== Parte 1 · motor {nm}: Δ log-loss contra C0 (milésimas de nat por sorteo; negativo = mejor), AUC")
        informe(nm, y, preds, "C0", lineas=L)
        for tr in ("AJUSTE", "ELECCION"):
            m = A.TRAMOS[tr] & ~np.isnan(pLR)
            pr(f"  calibración LR {tr}: " + calibracion(pLR, y, m))
            pr(f"  calibración GBM {tr}: " + calibracion(pGB, y, m))
        coef = mLR.coef_[0]; nomb = [f for f in NOM if f not in ("hora", "dow")] + [f"h{h}" for h in range(1, 12)] + [f"d{d}" for d in range(1, 7)]
        top = np.argsort(-np.abs(coef))[:12]
        pr("  LR último ajuste, coeficientes estandarizados mayores: " + ", ".join(f"{nomb[k]} {coef[k]:+.3f}" for k in top))
        imp = mGB.booster_.feature_importance("gain"); nomg = [f for f in NOM if f not in ("hora", "dow")] + ["hora", "dow"]
        imp = imp / imp.sum(); top = np.argsort(-imp)[:10]
        pr("  GBM último ajuste, ganancia: " + ", ".join(f"{nomg[k]} {100*imp[k]:.0f}%" for k in top))
        # ---------------- parte 3: rachas de la mañana
        hit = y; oe = hit - masa
        dkey = A.F
        u, inv = np.unique(dkey, return_inverse=True)
        man = np.bincount(inv, oe * (A.H <= 4), len(u))[inv]; manh = np.bincount(inv, hit * (A.H <= 4), len(u))[inv]
        nman = np.bincount(inv, (A.H <= 4).astype(float), len(u))[inv]
        tarde = (A.H >= 5) & (nman == 5)
        pr(f"== Parte 3 · motor {nm}: tarde (13-19 h) según aciertos Top-15 de la mañana (8-12 h, 5 sorteos)")
        for tr in ("ANTIGUO", "AJUSTE", "ELECCION"):
            m = A.TRAMOS[tr] & tarde; s = f"  {tr:8}"
            for nmb, (a, b) in (("0-1", (0, 1)), ("2", (2, 2)), ("3", (3, 3)), ("4-5", (4, 5))):
                mm = m & (manh >= a) & (manh <= b)
                if mm.sum(): s += f" | mañana {nmb}: n={mm.sum():4d} tarde {hit[mm].mean()*100:.1f}% (esp {masa[mm].mean()*100:.1f}) O−E {100*oe[mm].mean():+.1f}pp"
            r = np.corrcoef(man[m], oe[m])[0, 1]
            s += f" | corr(O−E mañana, O−E tarde) {r:+.3f}"
            pr(s)
        cols_b = ["hora", "dow", "masa15"]
        Xb = matriz(nm, cols_b)
        Xm = np.column_stack([Xb, man]); Xq = np.column_stack([Xb, Z[f"{nm}__q"], Z[f"{nm}__pri"]]); Xqm = np.column_stack([Xq, man])
        pb, _, _ = walk(Xb, y, lr_fit, filas=tarde); pm, _, _ = walk(Xm, y, lr_fit, filas=tarde)
        pq, _, _ = walk(Xq, y, lr_fit, filas=tarde); pqm, _, _ = walk(Xqm, y, lr_fit, filas=tarde)
        pr(f"  logística walk-forward en la tarde (base = hora, día, masa):")
        informe(nm + " tarde", y, {"base": pb, "+mañana": pm, "+q,π": pq, "+q,π+mañana": pqm}, "base", filas=tarde, lineas=L)
        informe(nm + " tarde (vs base+q)", y, {"+q,π": pq, "+q,π+mañana": pqm}, "+q,π", filas=tarde, lineas=L)
        res[nm].update({"tarde_base": pb, "tarde_man": pm, "tarde_q": pq, "tarde_qman": pqm})
    np.savez_compressed(SP + "/S1_pred.npz", **{f"{nm}__{k}": v for nm in res for k, v in res[nm].items()})
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "salida_modelo.txt"), "w").write("\n".join(L) + "\n")
