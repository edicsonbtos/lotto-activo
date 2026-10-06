# -*- coding: utf-8 -*-
"""M4: LightGBM con softmax por sorteo, apilado sobre log PROD, reentrenado cada mes (walk-forward).

python motor.py V1 V2 ...   -> guarda SP/m4_<V>.npz (P (10744,38), importancias)
"""
import sys, time, json
from datetime import date, timedelta
import numpy as np
import lightgbm as lgb
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
import arnes as A

K = 38
PRM = dict(learning_rate=0.05, num_leaves=7, min_data_in_leaf=400, lambda_l2=10.0, feature_fraction=0.7,
           bagging_fraction=0.8, bagging_freq=1, max_bin=63, verbose=-1, num_threads=4, seed=7,
           deterministic=True, force_col_wise=True)
MAXR, PAC, VAL_DIAS, MIN_DIAS = 300, 30, 60, 90
VARIANTES = {"V1": dict(ventana=None, vida=None, rd=True), "V2": dict(ventana=365, vida=None, rd=True),
             "V3": dict(ventana=None, vida=180, rd=True), "V4": dict(ventana=None, vida=90, rd=True)}
RD_NOMBRES = ("rd1", "rd2", "hay_rd")


def softmax(z):
    z = z - z.max(1, keepdims=True); e = np.exp(z); return e / e.sum(1, keepdims=True)


def hacer_obj(w_fila):
    def fobj(preds, ds):
        y = ds.get_label().reshape(-1, K); p = softmax(preds.reshape(-1, K))
        g = (p - y) * w_fila[:, None]; h = np.maximum(p * (1 - p), 1e-6) * w_fila[:, None]
        return g.reshape(-1), h.reshape(-1)
    return fobj


def feval(preds, ds):
    y = ds.get_label().reshape(-1, K); z = preds.reshape(-1, K); z = z - z.max(1, keepdims=True)
    ll = (z * y).sum(1) - np.log(np.exp(z).sum(1))
    return "nll", -ll.mean(), False


def preparar(X, nm, usar_rd):
    """X de arnés (12744,38,F) -> filas de A.T con log PROD y su puesto añadidos."""
    cols = [j for j, n in enumerate(nm) if usar_rd or n not in RD_NOMBRES]
    XT = X[A.T][:, :, cols]
    LP = np.log(np.clip(A.PROD, 1e-9, None)).astype(np.float32)
    rk = np.argsort(np.argsort(-A.PROD, 1), 1).astype(np.float32)
    XT = np.concatenate([XT, LP[:, :, None], rk[:, :, None]], 2)
    return XT, [nm[j] for j in cols] + ["logPROD", "puestoPROD"], LP


def entrenar(XT, LP, Yoh, idx, w, nombres, rondas=None, idx_val=None):
    """Entrena con las filas-sorteo idx (pesos w). Si idx_val, parada temprana y devuelve best_iter."""
    F = XT.shape[2]
    def ds(ii, ww, ref=None):
        return lgb.Dataset(XT[ii].reshape(-1, F), Yoh[ii].reshape(-1), init_score=LP[ii].reshape(-1),
                           feature_name=nombres, free_raw_data=False, reference=ref)
    prm = dict(PRM, objective=hacer_obj(w))
    dtr = ds(idx, w)
    if idx_val is not None:
        dva = ds(idx_val, None, dtr)
        m = lgb.train(dict(prm, metric="None"), dtr, MAXR, valid_sets=[dva], feval=feval,
                      callbacks=[lgb.early_stopping(PAC, verbose=False)])
        return m.best_iteration
    return lgb.train(prm, dtr, rondas)


def correr(nombre, X, nm, ventana=None, vida=None, rd=True, solo_desde=None, log=print):
    XT, nombres, LP = preparar(X, nm, rd)
    Yoh = (np.arange(K)[None, :] == A.Y[:, None]).astype(np.float32)
    FD = np.array([date.fromisoformat(f) for f in A.F])
    P = A.PROD.copy(); meses = sorted(set(f[:7] for f in A.F)); info = []
    imp = None
    for mes in meses:
        if solo_desde and mes < solo_desde:
            continue
        ini = date.fromisoformat(mes + "-01"); ip = np.where(np.char.startswith(A.F.astype(str), mes))[0]
        tr = np.where(FD < ini)[0]
        if ventana:
            tr = tr[FD[tr] >= ini - timedelta(days=ventana)]
        if len(tr) == 0 or (ini - FD[tr[0]]).days < MIN_DIAS:
            info.append((mes, "PROD")); continue
        edad = np.array([(ini - d).days for d in FD[tr]], float)
        w = 0.5 ** (edad / vida) if vida else np.ones(len(tr))
        w = (w / w.mean()).astype(np.float64)
        corte = ini - timedelta(days=VAL_DIAS)
        a = tr[FD[tr] < corte]; v = tr[FD[tr] >= corte]
        b = entrenar(XT, LP, Yoh, a, w[:len(a)] / w[:len(a)].mean(), nombres, idx_val=v) if len(a) > 0 else 0
        if b <= 0:
            info.append((mes, 0)); continue
        m = entrenar(XT, LP, Yoh, tr, w, nombres, rondas=b)
        raw = m.predict(XT[ip].reshape(-1, XT.shape[2]), raw_score=True).reshape(-1, K)
        P[ip] = softmax(raw + LP[ip])
        imp = (m.feature_importance("gain"), nombres)
        info.append((mes, b))
    log(f"[{nombre}] árboles por mes: " + " ".join(f"{m_[2:]}:{b}" for m_, b in info))
    return P, info, imp


if __name__ == "__main__":
    z = np.load(A.SP + "/m4_rasgos.npz"); X = z["X"]; nm = list(z["nm"])
    for v in sys.argv[1:]:
        t0 = time.time()
        cfg = dict(VARIANTES[v[:2]]) if v[:2] in VARIANTES else {}
        if v.endswith("noRD"):
            cfg["rd"] = False
        P, info, imp = correr(v, X, nm, solo_desde="2025-07", **cfg)
        np.savez(A.SP + f"/m4_{v}.npz", P=P, info=np.array(info, dtype=object), imp=imp[0], imp_nm=np.array(imp[1]))
        A.evaluar(P, "M4-" + v)
        print(f"   ({time.time() - t0:.0f} s)", flush=True)
