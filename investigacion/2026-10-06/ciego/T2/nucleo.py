# -*- coding: utf-8 -*-
"""T2 (C3, batería Turing): reimplementación PARAMETRIZADA del reentreno mensual del motor S2 congelado
(objetivo C, vida 90, mismos hiperparámetros que ../../motor0/S2/motor_s2.py). Con los parámetros por omisión
reproduce la matriz congelada (se comprueba en validar.py).

correr_mes(mes, seed=7, gap=0, perm=None, ruido=False) -> dict(P (filas del mes, 38), filas, imp, nm, bs)
  seed  : semilla de LightGBM (bagging 0,8 y feature_fraction 0,7 ya están en los hiperparámetros congelados)
  gap   : meses de hueco entre el fin del entrenamiento y el mes que se predice (0 = configuración congelada)
  perm  : semilla del placebo: las etiquetas (y la etiqueta blanda de régimen) de las jornadas de entrenamiento se
          barajan ENTRE jornadas, día entero contra día entero de la misma longitud y con el orden de las horas
  ruido : añade un rasgo N(0,1) iid por (sorteo, animal) como control
"""
import sys
from datetime import date, timedelta
import numpy as np
import lightgbm as lgb
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
import arnes as A
import motor_s2 as M

K = 38
SP = A.SP
_z = np.load(SP + "/s2_rasgos.npz")
X0 = _z["X"]; NM0 = [str(x) for x in _z["nm"]]; ETQ0 = _z["etq"]
SEQ = np.asarray(A.D.seq); DIA = np.asarray(A.D.dia)
FD = np.array([date.fromisoformat(f) for f in A.D.fecha])
_XR = None
HILOS = 2   # T1 corre a la vez en la misma máquina; con 2 hilos hay menos espera activa (validar.py compara con la matriz congelada)


def X_con_ruido():
    global _XR
    if _XR is None:
        r = np.random.default_rng(20261006).standard_normal((X0.shape[0], K, 1)).astype(np.float32)
        _XR = np.concatenate([X0, r], 2)
    return _XR


def menos_meses(d, k):
    y, m = d.year, d.month - k
    while m <= 0:
        m += 12; y -= 1
    return date(y, m, 1)


def filas_mes(mes):
    y, m = int(mes[:4]), int(mes[5:]); sig = date(y + (m == 12), m % 12 + 1, 1).isoformat()
    return A.T[(A.F >= mes + "-01") & (A.F < sig)]


def permutar_dias(tr, semilla):
    """Mapa fila -> fila origen de la etiqueta: cada jornada recibe la secuencia entera de otra jornada (misma longitud)."""
    rng = np.random.default_rng(semilla)
    src = np.arange(len(SEQ))
    dias = np.unique(DIA[tr])
    por_len = {}
    for d in dias:
        ii = tr[DIA[tr] == d]
        por_len.setdefault(len(ii), []).append(ii)
    for L, grupos in por_len.items():
        o = rng.permutation(len(grupos))
        for g, j in zip(grupos, o):
            src[g] = grupos[j]
    return src


def correr_mes(mes, seed=7, gap=0, perm=None, ruido=False):
    X = X_con_ruido() if ruido else X0
    nm = NM0 + (["ruido_gauss"] if ruido else [])
    M.PRM = dict(M.PRM, seed=seed, num_threads=HILOS)
    B = M.Base(X, nm, ETQ0)          # B.Yoh = one-hot de la secuencia REAL
    ini = date.fromisoformat(mes + "-01"); fin_tr = menos_meses(ini, gap)
    filas = filas_mes(mes)
    tr = np.where((FD < fin_tr) & (FD >= fin_tr - timedelta(days=M.VENTANA)))[0]; tr = tr[tr >= M.INI_FILA]
    etq = ETQ0.copy()
    if perm is not None:
        src = permutar_dias(tr, perm)
        Yoh = B.Yoh.copy(); Yoh[tr] = B.Yoh[src[tr]]; B.Yoh = Yoh
        etq[tr] = ETQ0[src[tr]]
        assert (FD[src[tr]] < fin_tr).all()
    edad = np.array([(fin_tr - d).days for d in FD[tr]], float)
    w = 0.5 ** (edad / 90.0); w = w / w.mean()
    corte = fin_tr - timedelta(days=M.VAL_DIAS)
    ma = FD[tr] < corte; a, v = tr[ma], tr[~ma]
    out, bs, imp = [], [], np.zeros(len(nm))
    for modo in ("N", "R"):
        e = etq[tr] if modo == "R" else 1 - etq[tr]
        ww = w * e; ww = ww / ww.mean(); wwa = ww[ma] / ww[ma].mean()
        m, b, _ = B.softmax_fit(a, wwa, v, tr, ww)
        out.append(M.softmax(B.raw(m, filas))); bs.append(b)
        imp += m.feature_importance("gain")
    q = X[filas, 0, nm.index("q_post")][:, None]
    P = (1 - q) * out[0] + q * out[1]
    # referencia "sin información": frecuencia (con olvido, vida 90) de las etiquetas del entrenamiento
    Yt = B.Yoh[tr]
    fr = (w[:, None] * Yt).sum(0) + 0.5; fr = fr / fr.sum()
    return dict(P=P, filas=filas, imp=imp, nm=nm, bs=bs, freq=fr)
