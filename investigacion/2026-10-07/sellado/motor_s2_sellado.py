# -*- coding: utf-8 -*-
"""S2: motor desde cero (sin PROD, sin RD) con LightGBM, walk-forward con reentreno mensual y pesos con olvido.

python motor_s2.py <obj> <vida> [desde] [paso_meses]   obj ∈ A, B1, B2, C
  -> SP/s2_<obj>_<vida>.npz con P (10744, 38) (filas no calculadas = NaN)
"""
import sys, time
from datetime import date, timedelta
import numpy as np
import lightgbm as lgb
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
import arnes as A

K = 38
PRM = dict(learning_rate=0.05, num_leaves=15, min_data_in_leaf=400, lambda_l2=10.0, feature_fraction=0.7,
           bagging_fraction=0.8, bagging_freq=1, max_bin=63, verbose=-1, num_threads=4, seed=7,
           deterministic=True, force_col_wise=True)
MAXR, PAC, VAL_DIAS, MIN_DIAS, INI_FILA, VENTANA = 500, 40, 60, 120, 300, 600


def softmax(z):
    z = z - z.max(1, keepdims=True); e = np.exp(z); return e / e.sum(1, keepdims=True)


def obj_softmax(w):
    def f(preds, ds):
        y = ds.get_label().reshape(-1, K); p = softmax(preds.reshape(-1, K))
        return ((p - y) * w[:, None]).reshape(-1), (np.maximum(p * (1 - p), 1e-6) * w[:, None]).reshape(-1)
    return f


def nll_eval(preds, ds):
    y = ds.get_label().reshape(-1, K); z = preds.reshape(-1, K); z = z - z.max(1, keepdims=True)
    return "nll", -((z * y).sum(1) - np.log(np.exp(z).sum(1))).mean(), False


# --- pérdida de cobertura del Top-15 (rango suave): L = softplus((r_y − 14.5)/TAU), r_y = Σ_j σ((s_j − s_y)/T)
T_R, TAU = 0.3, 1.0
def obj_cobertura(w):
    def f(preds, ds):
        y = ds.get_label().reshape(-1, K).astype(bool); s = preds.reshape(-1, K)
        sy = s[y][:, None]; u = (s - sy) / T_R; sg = 1 / (1 + np.exp(-u)); sg[y] = 0
        r = sg.sum(1); v = (r - 14.5) / TAU; dL = 1 / (1 + np.exp(-v)) / TAU          # dL/dr
        dr = sg * (1 - sg) / T_R                                                       # dr/ds_j (j≠y)
        g = dL[:, None] * dr; g[y] = -g.sum(1)
        h = np.abs(g) + 1e-3                                                           # hessiano aproximado (>0)
        return (g * w[:, None]).reshape(-1), (h * w[:, None]).reshape(-1)
    return f


def top15_eval(preds, ds):
    y = ds.get_label().reshape(-1, K); s = preds.reshape(-1, K)
    rk = (s > (s * y).sum(1, keepdims=True)).sum(1)
    return "top15", float((rk < 15).mean()), True


class Base:
    def __init__(self, X, nm, etq):
        self.X = X; self.nm = nm; self.F = X.shape[2]; self.etq = etq
        D = A.D; self.seq = np.asarray(D.seq)
        self.FD = np.array([date.fromisoformat(f) for f in D.fecha])
        self.Yoh = (np.arange(K)[None, :] == self.seq[:, None]).astype(np.float32)

    def ds(self, ii, w=None, init=None, ref=None, rank=False):
        kw = {}
        if init is not None: kw["init_score"] = init.reshape(-1)
        if rank: kw["group"] = np.full(len(ii), K)
        if w is not None and rank: kw["weight"] = np.repeat(w, K)
        return lgb.Dataset(self.X[ii].reshape(-1, self.F), self.Yoh[ii].reshape(-1), feature_name=self.nm,
                           free_raw_data=False, reference=ref, **kw)

    def softmax_fit(self, a, wa, v, tr, wtr, init_a=None, init_v=None, init_tr=None):
        prm = dict(PRM, objective=obj_softmax(wa), metric="None")
        dtr = self.ds(a, init=init_a); dva = self.ds(v, init=init_v, ref=dtr)
        m = lgb.train(prm, dtr, MAXR, valid_sets=[dva], feval=nll_eval, callbacks=[lgb.early_stopping(PAC, verbose=False)])
        b = max(m.best_iteration, 1)
        m2 = lgb.train(dict(PRM, objective=obj_softmax(wtr)), self.ds(tr, init=init_tr), b)
        return m2, b, m

    def raw(self, m, ii):
        return m.predict(self.X[ii].reshape(-1, self.F), raw_score=True).reshape(-1, K)


def ajustar_a(s, y):
    """a por MV: P = softmax(a·s)."""
    best = (1e18, 1.0)
    for a in np.exp(np.linspace(np.log(0.05), np.log(20), 60)):
        z = a * s; z = z - z.max(1, keepdims=True); ll = -(z[np.arange(len(y)), y] - np.log(np.exp(z).sum(1))).mean()
        best = min(best, (ll, a))
    return best[1]


def correr(obj, vida, X, nm, etq, desde="2025-07", paso=1, hasta="2026-06", log=print):
    B = Base(X, nm, etq); FD = B.FD; seq = B.seq; n = len(seq)
    P = np.full((len(A.T), K), np.nan); info = []; P2 = np.full((len(A.T), K), np.nan)
    meses = sorted(set(f[:7] for f in A.F)); meses = [m for m in meses if desde <= m <= hasta][::paso]
    todos = sorted(set(f[:7] for f in A.F))
    for k, mes in enumerate(meses):
        ini = date.fromisoformat(mes + "-01")
        sig = meses[k + 1] if k + 1 < len(meses) else None
        if sig is None:  # último mes de la tanda: hasta fin de 'hasta'
            filas = A.T[(A.F >= mes) & (np.char.ljust(A.F.astype(str), 7).astype('<U7') <= hasta)]
        else:
            filas = A.T[(A.F >= mes) & (A.F < sig + "-01")]
        ip = filas - A.T[0]
        tr = np.where((FD < ini) & (FD >= ini - timedelta(days=VENTANA)))[0]; tr = tr[tr >= INI_FILA]
        edad = np.array([(ini - d).days for d in FD[tr]], float)
        w = 0.5 ** (edad / vida); w = w / w.mean()
        corte = ini - timedelta(days=VAL_DIAS)
        ma = FD[tr] < corte; a, v = tr[ma], tr[~ma]; wa = w[ma] / w[ma].mean()
        t0 = time.time()
        if len(v) == 0 or len(a) < 500:   # SELLADO: cierre abr-ago 2020 sin 60 días previos: el mes se salta (queda NaN)
            log(f'  SALTADO {mes}'); info.append((mes, 'saltado')); continue
        if obj in ("A", "AB2"):
            m, b, m_a = B.softmax_fit(a, wa, v, tr, w)
            base_f = B.raw(m, filas); P[ip] = softmax(base_f); bc = -1
            if obj == "AB2":   # B2: ajuste fino con la pérdida de cobertura, parada temprana por Top-15 en validación
                ia, iv = B.raw(m_a, a), B.raw(m_a, v)
                prm = dict(PRM, objective=obj_cobertura(wa), metric="None", learning_rate=0.02)
                dtr = B.ds(a, init=ia); dva = B.ds(v, init=iv, ref=dtr)
                mc = lgb.train(prm, dtr, 200, valid_sets=[dva], feval=top15_eval,
                               callbacks=[lgb.early_stopping(PAC, verbose=False)])
                bc = mc.best_iteration
                if bc > 0:
                    mc2 = lgb.train(dict(PRM, objective=obj_cobertura(w), learning_rate=0.02),
                                    B.ds(tr, init=B.raw(m, tr)), bc)
                    P2[ip] = softmax(base_f + B.raw(mc2, filas))
                else:
                    P2[ip] = P[ip]
            info.append((mes, b, bc))
        elif obj == "C":
            out = []
            bs = []
            for modo in ("N", "R"):
                e = etq[tr] if modo == "R" else 1 - etq[tr]
                ww = w * e; ww = ww / ww.mean(); wwa = ww[ma] / ww[ma].mean()
                m, b, _ = B.softmax_fit(a, wwa, v, tr, ww); out.append(softmax(B.raw(m, filas))); bs.append(b)
            q = X[filas, 0, nm.index("q_post")][:, None]
            P[ip] = (1 - q) * out[0] + q * out[1]; info.append((mes, tuple(bs)))
        elif obj == "B1":
            prm = dict(PRM, objective="lambdarank", lambdarank_truncation_level=15, eval_at=[15], metric="ndcg",
                       label_gain=[0, 1])
            dtr = B.ds(a, wa, rank=True); dva = B.ds(v, rank=True, ref=dtr)
            m = lgb.train(prm, dtr, MAXR, valid_sets=[dva], callbacks=[lgb.early_stopping(PAC, verbose=False)])
            bb = max(m.best_iteration, 1)
            al = ajustar_a(B.raw(m, v), seq[v])           # calibración en la validación (fuera de muestra)
            m2 = lgb.train(dict(PRM, objective="lambdarank", lambdarank_truncation_level=15, label_gain=[0, 1]),
                           B.ds(tr, w, rank=True), bb)
            P[ip] = softmax(al * B.raw(m2, filas)); info.append((mes, bb, round(al, 2)))
        log(f"  [{obj} vida {vida}] {mes} {info[-1][1:]} {time.time() - t0:.0f}s", flush=True)
    return P, info, P2


if __name__ == "__main__":
    obj, vida = sys.argv[1], float(sys.argv[2])
    desde = sys.argv[3] if len(sys.argv) > 3 else "2025-07"; paso = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    z = np.load(A.SP + "/s2_rasgos.npz"); X = z["X"]; nm = [str(x) for x in z["nm"]]; etq = z["etq"]
    t0 = time.time()
    hasta = sys.argv[5] if len(sys.argv) > 5 else "2026-06"
    P, info, P2 = correr(obj, vida, X, nm, etq, desde, paso, hasta)
    tag = f"{obj}_{int(vida)}" + ("" if (desde, paso, hasta) == ("2025-07", 1, "2026-06") else f"_{desde}_{paso}_{hasta}")
    np.savez(A.SP + f"/s2_{tag}.npz", P=P, info=np.array(info, dtype=object), P2=P2)
    print(f"[{tag}] total {time.time() - t0:.0f}s")
