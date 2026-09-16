# -*- coding: utf-8 -*-
"""
CONSEJERO C - "Cazador de Atrasos"
Estrategia basada en ATRASOS (hazard): P(salir | sorteos sin salir).
1) Diagnostico de senal: tabla de hazard por tramo de atraso + regresion logistica
   (cruda y residual sobre frecuencia por animal).
2) Walk-forward ESTRICTO (para predecir t solo se usan sorteos < t), ultimos 1000.
   Modelos: M0 azar | M1 frecuencia | M2 hazard puro | M3 frecuencia x hazard.
3) Aciertos ultimos 24 sorteos.
4) Top-3/Top-5 para 2026-09-14 hora 8 (solo datos anteriores a ese sorteo).
"""
import numpy as np

K = 38
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {a: i for i, a in enumerate(POS)}
BASE = 1.0 / K
TARGET = ("2026-09-14", 8)


def load():
    seq, meta = [], []
    with open("historial.txt", encoding="utf-8") as f:
        for line in f:
            p = line.split()
            if len(p) < 3:
                continue
            seq.append(IDX[p[2]])
            meta.append((p[0], int(p[1])))
    return np.array(seq, dtype=np.int64), meta


seq, meta = load()
N = len(seq)
print(f"Sorteos totales: {N}  ({meta[0]} .. {meta[-1]})")

# --- Matrices gap e hit (una sola pasada) -----------------------------------
# gap[t,i] = nro de sorteos desde la ultima aparicion de i ANTES del sorteo t
#            (1 si salio en t-1). 999999 si nunca salio antes.
gap = np.zeros((N, K), dtype=np.int32)
HIT = np.zeros((N, K), dtype=bool)
HIT[np.arange(N), seq] = True
last = np.full(K, -1, dtype=np.int64)
for t in range(N):
    seen = last >= 0
    gap[t, seen] = (t - last[seen]).astype(np.int32)
    gap[t, ~seen] = 999999
    last[seq[t]] = t

# --- 1) DIAGNOSTICO DE SENAL (sobre todo el historial; quema 500) -----------
BURN = 500
EDGES = np.array([5, 10, 15, 20, 30, 40, 60, 80, 120, 200])  # bordes de tramo
g_all = gap[BURN:].ravel()
h_all = HIT[BURN:].ravel()
b_all = np.digitize(g_all, EDGES)
print("\n=== Tabla de hazard empirica por tramo de atraso (todo el historial) ===")
print(f"{'tramo':>10} {'n':>9} {'tasa%':>7} {'IC95%':>16}")
labels = ["1-4", "5-9", "10-14", "15-19", "20-29", "30-39",
          "40-59", "60-79", "80-119", "120-199", "200+"]
for b in range(len(EDGES) + 1):
    m = b_all == b
    n = m.sum()
    p = h_all[m].mean()
    se = np.sqrt(p * (1 - p) / n)
    print(f"{labels[b]:>10} {n:>9} {100*p:>7.2f} [{100*(p-1.96*se):.2f},{100*(p+1.96*se):.2f}]")
print(f"Base teorica: {100*BASE:.2f}%")

# Regresion logistica pooled: hit ~ atraso (atraso en unidades de 38 sorteos)
def fit_logit(x, y):
    X = np.column_stack([np.ones_like(x), x])
    beta = np.zeros(2)
    for _ in range(60):
        z = X @ beta
        p = 1 / (1 + np.exp(-z))
        W = p * (1 - p)
        grad = X.T @ (y - p)
        Hm = X.T @ (X * W[:, None])
        step = np.linalg.solve(Hm + 1e-9 * np.eye(2), grad)
        beta += step
        if np.max(np.abs(step)) < 1e-11:
            break
    cov = np.linalg.pinv(X.T @ (X * W[:, None]))
    return beta, np.sqrt(np.diag(cov))

x_gap = np.minimum(g_all, 300).astype(float) / K  # cap 300, en "esperas esperadas"
beta, se = fit_logit(x_gap, h_all.astype(float))
z = beta[1] / se[1]
from scipy import stats as st
pval = 2 * (1 - st.norm.cdf(abs(z)))
print(f"\nLogit pooled hit~atraso: pendiente={beta[1]:+.5f}  z={z:+.2f}  p={pval:.4f}")

# Version residual: restar la frecuencia propia de cada animal (efectos fijos)
cnt = HIT[BURN:].sum(axis=0)
f_i = cnt / (N - BURN)
resid = h_all.astype(float) - np.repeat(f_i[None, :], N - BURN, axis=0).ravel()
beta_r, se_r = fit_logit(x_gap, resid)  # OLS sobre residuo basta para el signo
z_r = beta_r[1] / se_r[1]
pval_r = 2 * (1 - st.norm.cdf(abs(z_r)))
print(f"Logit residual (menos frec. animal): pendiente={beta_r[1]:+.6f}  z={z_r:+.2f}  p={pval_r:.4f}")

# --- 2) WALK-FORWARD ESTRICTO ------------------------------------------------
ALPHA_HZ = 8000.0     # pseudo-observaciones hacia la tasa base (suavizado hazard)
W_FREQ = 1500         # ventana movil para frecuencia por animal
REFIT = 25            # re-ajuste de la tabla hazard cada 25 sorteos

hz_tab = None
last_refit = -10**9

def fit_hz(t):
    """Tabla hazard ajustada SOLO con sorteos [BURN, t)."""
    gg = gap[BURN:t].ravel()
    hh = HIT[BURN:t].ravel()
    bb = np.digitize(gg, EDGES)
    nb = np.bincount(bb, minlength=len(EDGES) + 1).astype(float)
    cb = np.bincount(bb[hh], minlength=len(EDGES) + 1).astype(float)
    return (cb + ALPHA_HZ * BASE) / (nb + ALPHA_HZ)

def scores(t, model):
    """Vector de probabilidades (suma 1) para el sorteo t usando datos < t."""
    global hz_tab, last_refit
    if model in ("M2", "M3") and (hz_tab is None or t - last_refit >= REFIT):
        hz_tab = fit_hz(t)
        last_refit = t
    if model == "M0":
        return np.full(K, BASE)
    if model == "M2":
        mult = hz_tab[np.digitize(gap[t], EDGES)] / BASE
        p = BASE * mult
        return p / p.sum()
    # frecuencia en ventana movil [t-W_FREQ, t) con Laplace
    a = max(0, t - W_FREQ)
    f = (HIT[a:t].sum(axis=0) + 1.0) / (t - a + K)
    if model == "M1":
        return f / f.sum()
    # M3: frecuencia x multiplicador de hazard
    mult = hz_tab[np.digitize(gap[t], EDGES)] / BASE
    p = f * mult
    return p / p.sum()

def eval_wf(t0, t1, model):
    """Evalua sorteos [t0,t1). Retorna hits top-k y log-loss."""
    hits = {1: 0, 3: 0, 5: 0, 10: 0}
    ll = 0.0
    for t in range(t0, t1):
        p = scores(t, model)
        order = np.argsort(-p)
        y = seq[t]
        ll += -np.log(max(p[y], 1e-12))
        for k in hits:
            if y in order[:k]:
                hits[k] += 1
    return hits, ll / (t1 - t0)

# Seleccion de modelo en ventana INTERIOR (previa a la evaluacion, sin tocarla)
IN0, IN1 = N - 1500, N - 1000
print(f"\n=== Seleccion de modelo (ventana interior {IN0}..{IN1}, 500 sorteos) ===")
for m in ["M1", "M2", "M3"]:
    h, ll = eval_wf(IN0, IN1, m)
    print(f"{m}: Top-1={100*h[1]/500:.2f}% Top-3={100*h[3]/500:.2f}% "
          f"Top-5={100*h[5]/500:.2f}% LL={ll:.4f}")

EV0, EV1 = N - 1000, N
print(f"\n=== Walk-forward estricto, ULTIMOS 1000 sorteos ({meta[EV0]} .. {meta[EV1-1]}) ===")
res = {}
for m in ["M0", "M1", "M2", "M3"]:
    h, ll = eval_wf(EV0, EV1, m)
    res[m] = h
    print(f"{m}: Top-1={100*h[1]/1000:5.2f}% ({h[1]:>3}/1000) "
          f"Top-3={100*h[3]/1000:5.2f}% ({h[3]:>3}/1000) "
          f"Top-5={100*h[5]/1000:5.2f}% ({h[5]:>3}/1000) "
          f"Top-10={100*h[10]/1000:5.2f}% ({h[10]:>3}/1000) LL={ll:.4f}")

# --- 3) Ultimos 24 sorteos con el mejor modelo ------------------------------
best = max(["M1", "M2", "M3"], key=lambda m: res[m][3])
print(f"\nMejor modelo por Top-3 en WF: {best}")
h24, _ = eval_wf(N - 24, N, best)
print(f"Ultimos 24 sorteos ({best}): Top-3 aciertos={h24[3]}/24  Top-5={h24[5]}/24")

# --- 4) Prediccion para 2026-09-14 hora 8 ------------------------------------
t_target = next(i for i, m in enumerate(meta) if m == TARGET)
print(f"\nObjetivo {TARGET} = indice {t_target}. Entrenando SOLO con sorteos < {t_target}.")
hz_tab, last_refit = None, -10**9  # forzar re-ajuste sin fuga
p = scores(t_target, best)
order = np.argsort(-p)
print(f"\n=== TOP-5 para 2026-09-14 hora 8 (modelo {best}) ===")
for r, i in enumerate(order[:5], 1):
    g = int(gap[t_target, i])
    print(f"#{r}: animal {POS[i]:>3}  p={100*p[i]:.2f}%  atraso={g} sorteos")
print("\nTOP-3:", [POS[i] for i in order[:3]])
print("TOP-5:", [POS[i] for i in order[:5]])
