import sys, json, math
from pathlib import Path
import numpy as np
from scipy import stats
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "herramientas"))
import lotto_eval as LE
rng = np.random.default_rng(20261002)
D = LE.cargar()
a, b = 2000, 9357
seq, dia, fecha = D.seq[a:b], D.dia[a:b], D.fecha[a:b]
n = len(seq); K = 38
out = {"n": n, "desde": fecha[0], "hasta": fecha[-1]}


def chi_unif(s):
    c = np.bincount(s, minlength=K); e = len(s) / K
    x = ((c - e) ** 2 / e).sum()
    return float(x), float(stats.chi2.sf(x, K - 1))


out["H1"] = dict(zip(("chi2", "p"), chi_unif(seq)))
out["H1_mitades_p"] = [chi_unif(seq[:n // 2])[1], chi_unif(seq[n // 2:])[1]]
c = np.bincount(seq, minlength=K)
out["H1_prop_primeros16"] = float(c[:16].sum() / n)
out["H1_esperado"] = 16 / 38


def bits(s):
    s = s[s < 32]  # rechazo: 0..31 son 5 bits uniformes bajo H0 (0..37 en 6 bits no lo son)
    return np.unpackbits(s.astype(np.uint8)[:, None], axis=1)[:, 3:].ravel()


def monobit(x):
    s = (2 * x.astype(int) - 1).sum()
    return float(math.erfc(abs(s) / math.sqrt(len(x)) / math.sqrt(2)))


def runs(x):
    N = len(x); pi = x.mean()
    if abs(pi - .5) >= 2 / math.sqrt(N):
        return 0.0
    v = 1 + (x[1:] != x[:-1]).sum()
    return float(math.erfc(abs(v - 2 * N * pi * (1 - pi)) / (2 * math.sqrt(2 * N) * pi * (1 - pi))))


def espectral(x):
    N = len(x); X = np.abs(np.fft.fft(2 * x.astype(float) - 1))[:N // 2]
    T = math.sqrt(math.log(1 / .05) * N); N0 = .95 * N / 2; N1 = (X < T).sum()
    d = (N1 - N0) / math.sqrt(N * .95 * .05 / 4)
    return float(math.erfc(abs(d) / math.sqrt(2)))


def serial2(x):
    N = len(x)

    def psi(m):
        y = np.concatenate([x, x[:m - 1]]) if m > 1 else x
        w = np.zeros(N, int)
        for i in range(m):
            w = (w << 1) | y[i:i + N]
        cc = np.bincount(w, minlength=2 ** m)
        return (2 ** m / N) * (cc.astype(float) ** 2).sum() - N
    return float(stats.chi2.sf(psi(2) - psi(1), 2))


def bm(s):
    n_ = len(s); c = np.zeros(n_ + 1, int); bb = np.zeros(n_ + 1, int)
    c[0] = bb[0] = 1; L = 0; m = -1
    for i in range(n_):
        d = int(s[i])
        for j in range(1, L + 1):
            d ^= int(c[j]) & int(s[i - j])
        if d:
            t = c.copy(); sh = i - m
            c[sh:] ^= bb[:n_ + 1 - sh]
            if L <= i // 2:
                L = i + 1 - L; m = i; bb = t
    return L


def lin_complex(x, M=500):
    N = len(x) // M
    Ls = np.array([bm(x[i * M:(i + 1) * M]) for i in range(N)])
    mu = M / 2 + (9 + (-1) ** (M + 1)) / 36 - (M / 3 + 2 / 9) / 2 ** M
    T = (-1) ** M * (Ls - mu) + 2 / 9
    cnt = np.histogram(T, [-1e9, -2.5, -1.5, -.5, .5, 1.5, 2.5, 1e9])[0]
    pi = np.array([.010417, .03125, .125, .5, .25, .0625, .020833])
    return float(stats.chi2.sf(((cnt - N * pi) ** 2 / (N * pi)).sum(), 6))


def bateria(s):
    x = bits(s)
    return dict(monobit=monobit(x), runs=runs(x), espectral=espectral(x), serial2=serial2(x),
                complejidad_lineal=lin_complex(x[:60000]))


out["H2"] = bateria(seq)
out["H2_mitades"] = [bateria(seq[:n // 2]), bateria(seq[n // 2:])]

esp = {"12-24", "12-25", "12-31", "01-01", "04-19", "06-24", "07-05", "07-24", "10-12"}
dias_u, inv = np.unique(dia, return_inverse=True)
primera = np.array([fecha[int(np.argmax(dia == d))][5:] for d in dias_u])
es_esp = np.array([f in esp for f in primera])


def chi_hom(m):
    t = np.vstack([np.bincount(seq[m], minlength=K), np.bincount(seq[~m], minlength=K)]) + 1e-9
    return float(stats.chi2_contingency(t, correction=False)[0])


mask = es_esp[inv]; obs = chi_hom(mask); ge = 0; k = int(es_esp.sum())
for _ in range(5000):
    pm = np.zeros(len(dias_u), bool); pm[rng.choice(len(dias_u), k, replace=False)] = True
    ge += chi_hom(pm[inv]) >= obs
out["H3"] = {"dias_especiales": k, "sorteos": int(mask.sum()), "chi2": obs, "p_perm": (ge + 1) / 5001}

x0, x1 = seq[:-1], seq[1:]; mis = dia[1:] == dia[:-1]


def trans(m):
    T = np.zeros((K, K)); np.add.at(T, (x0[m], x1[m]), 1)
    e = T.sum(1, keepdims=True) * T.sum(0, keepdims=True) / T.sum()
    ee = np.maximum(e, 1e-9); z = (T - e) / np.sqrt(ee)
    p = 2 * stats.norm.sf(np.abs(z))
    return int((p < .05 / (K * K)).sum()), float(stats.chi2.sf(((T - e) ** 2 / ee).sum(), (K - 1) ** 2)), int(T.sum())


for nom, m in (("todos", np.ones(len(x0), bool)), ("mismo_dia", mis), ("entre_dias", ~mis)):
    out["H4_" + nom] = dict(zip(("celdas_bonf", "p_global", "pares"), trans(m)))


def apen(s, m=2):
    def phi(m):
        w = np.lib.stride_tricks.sliding_window_view(s, m)
        kk = (w * (K ** np.arange(m))).sum(1)
        cc = np.unique(kk, return_counts=True)[1] / len(kk)
        return (cc * np.log(cc)).sum()
    return phi(m) - phi(m + 1)


s = seq[:6000]; o = apen(s); sims = np.array([apen(rng.permutation(s)) for _ in range(1000)])
out["H5"] = {"apen": float(o), "media_perm": float(sims.mean()), "p": float(((sims <= o).sum() + 1) / 1001)}
Path(__file__).with_name("SALIDA_ataque_generador.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
