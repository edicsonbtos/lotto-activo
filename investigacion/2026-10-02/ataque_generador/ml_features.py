import sys, json
from pathlib import Path
import numpy as np
import torch, torch.nn as nn
from sklearn.cluster import KMeans
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "herramientas"))
import lotto_eval as LE
torch.set_num_threads(2); torch.manual_seed(20261002); rng = np.random.default_rng(20261002)
K = 38; A, B, CUT = 2000, 9357, 5678
D = LE.cargar()
seq, hora, dia = D.seq, D.hora, D.dia
z = np.load(RAIZ / "herramientas/exploracion/calor_cache.npz")
P = z["P"].astype(np.float64); y = z["y"].astype(int)
assert len(P) == B - A and (y == seq[A:B]).all()
P = P / P.sum(1, keepdims=True)
ll_ens = np.log(P[np.arange(len(y)), y] + 1e-12)
T = np.arange(A, B)                       # fila global de cada sorteo
trn = T < CUT; E1 = (T >= CUT) & (T < (CUT + B) // 2); E2 = T >= (CUT + B) // 2
dias_e = dia[A:B]
MB = 1000 / np.log(2)


def boot_mean(v, mask, nb=5000):
    d = dias_e[mask]; vv = v[mask]; u, inv = np.unique(d, return_inverse=True)
    s = np.bincount(inv, vv); c = np.bincount(inv).astype(float)
    idx = rng.integers(0, len(u), (nb, len(u)))
    m = s[idx].sum(1) / c[idx].sum(1)
    return float(vv.mean()), [float(np.quantile(m, .00625)), float(np.quantile(m, .99375))]


out = {}
# ---------------- F1 LSTM ----------------
H = 100
def ventana(t):
    x = np.zeros((H, K), np.float32); h = seq[t - H:t]; x[np.arange(H), h] = 1; return x
class Net(nn.Module):
    def __init__(s):
        super().__init__(); s.l = nn.LSTM(K, 64, batch_first=True); s.o = nn.Linear(64 + 12, K)
    def forward(s, x, hh):
        _, (h, _) = s.l(x); return s.o(torch.cat([h[-1], hh], 1))
def lote(ts):
    X = torch.tensor(np.stack([ventana(t) for t in ts])); hh = torch.zeros(len(ts), 12)
    hh[torch.arange(len(ts)), torch.tensor(hora[ts])] = 1; return X, hh
net = Net(); opt = torch.optim.Adam(net.parameters(), 2e-3)
tr_t = T[trn]; yt = torch.tensor(seq[tr_t])
for ep in range(12):
    perm = rng.permutation(len(tr_t)); tot = 0
    for i in range(0, len(perm), 128):
        b = perm[i:i + 128]; X, hh = lote(tr_t[b])
        loss = nn.functional.cross_entropy(net(X, hh), yt[b]); opt.zero_grad(); loss.backward(); opt.step(); tot += loss.item() * len(b)
ev_t = T[~trn]
with torch.no_grad():
    logit = torch.cat([net(*lote(ev_t[i:i + 256])) for i in range(0, len(ev_t), 256)])
PL = torch.softmax(logit, 1).numpy().astype(np.float64)
ye = y[~trn]; ll_l = np.log(PL[np.arange(len(ye)), ye] + 1e-12); ll_e = ll_ens[~trn]
out["F1_entropia_cruzada"] = {"lstm": float(-ll_l.mean()), "ensamble": float(-ll_e.mean()), "reduccion_pct": float(100 * (ll_l.mean() - ll_e.mean()) / -ll_e.mean())}
e1 = E1[~trn]; e2 = E2[~trn]
best = None
for w in np.linspace(0, 1, 21):
    lb = (1 - w) * np.log(P[~trn] + 1e-12) + w * np.log(PL + 1e-12); lb -= np.log(np.exp(lb).sum(1, keepdims=True))
    g = lb[np.arange(len(ye)), ye] - ll_e
    if best is None or g[e1].mean() > best[1]: best = (float(w), float(g[e1].mean()), g)
w, _, g = best
full = np.zeros(len(y)); full[~trn] = g * MB
out["F1_mezcla"] = {"w_elegido_en_E1": w, "E1_mbits": float(g[e1].mean() * MB), "E2": dict(zip(("mbits", "IC98.75"), boot_mean(full, E2)))}

# ---------------- ranking Top-5 y retorno ----------------
fich = np.array([2, 2, 2, 1, 1])
rank = np.argsort(-P, axis=1, kind="stable")[:, :5]
pos = (rank == y[:, None])
ret = (pos * fich).sum(1) * 30 / 8 - 1          # retorno por ficha por sorteo
hit = pos.any(1).astype(float)
mass5 = np.take_along_axis(P, rank, 1).sum(1)
out["top5_base"] = {"retorno_E1": float(ret[E1].mean()), "retorno_E2": float(ret[E2].mean())}

# ---------------- F2 autoencoder ----------------
def cuentas(t): return np.bincount(seq[t - 38:t], minlength=K).astype(np.float32) / 38
Xall = torch.tensor(np.stack([cuentas(t) for t in T]))
ae = nn.Sequential(nn.Linear(K, 16), nn.ReLU(), nn.Linear(16, K)); o2 = torch.optim.Adam(ae.parameters(), 3e-3)
Xt = Xall[torch.tensor(trn)]
for ep in range(300):
    l = ((ae(Xt) - Xt) ** 2).mean(); o2.zero_grad(); l.backward(); o2.step()
with torch.no_grad(): err = ((ae(Xall) - Xall) ** 2).mean(1).numpy()
thr = err[trn].mean() + 3 * err[trn].std()
an = err > thr
res = {"umbral": float(thr), "anomalos_E1": int(an[E1].sum()), "anomalos_E2": int(an[E2].sum())}
for nom, m in (("E1", E1), ("E2", E2)):
    a_, n_ = m & an, m & ~an
    if a_.sum() > 20:
        res[nom] = {"retorno_anomalos": float(ret[a_].mean()), "retorno_resto": float(ret[n_].mean()),
                    "OE_top5_anomalos": float(hit[a_].sum() / mass5[a_].sum()), "OE_top5_resto": float(hit[n_].sum() / mass5[n_].sum())}
        d = ret.copy(); d[~a_] = 0
        # diferencia por jornada: bootstrap de retorno de los anomalos
        res[nom]["retorno_anomalos_IC"] = boot_mean(ret, a_)[1]
out["F2"] = res

# ---------------- F4 clustering de firmas ----------------
WIN, STEP = 200, 50
def firma(t):
    ind = np.zeros((WIN, K)); ind[np.arange(WIN), seq[t - WIN:t]] = 1
    f = np.abs(np.fft.rfft(ind - ind.mean(0), axis=0)).mean(1); return f / f.sum()
bl = np.arange(A, B, STEP); Fb = np.stack([firma(t) for t in bl])
btr = bl < CUT
km = KMeans(3, n_init=10, random_state=20261002).fit(Fb[btr])
lab = km.predict(Fb); lab_t = lab[(T - A) // STEP]
def estad(l, m):
    r = [ret[m & (l == c)].mean() for c in range(3) if (m & (l == c)).sum() > 30]
    return float(np.var(r)) if len(r) > 1 else 0.0
res = {"tamano_clusters_E": [int(((~trn) & (lab_t == c)).sum()) for c in range(3)]}
ev = ~trn
obs = estad(lab_t, ev); ge = 0
for _ in range(5000):
    pl = rng.permutation(lab); ge += estad(pl[(T - A) // STEP], ev) >= obs
res["retorno_por_cluster_E1"] = [float(ret[E1 & (lab_t == c)].mean()) if (E1 & (lab_t == c)).any() else None for c in range(3)]
res["retorno_por_cluster_E2"] = [float(ret[E2 & (lab_t == c)].mean()) if (E2 & (lab_t == c)).any() else None for c in range(3)]
res["p_perm"] = (ge + 1) / 5001
out["F4"] = res
Path(__file__).with_name("SALIDA_features_ml.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
