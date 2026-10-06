"""A5 extra 2 (NO pre-registrado, adversarial): corrección por selección. Bajo la nula (el día de la semana no importa),
se barajan las etiquetas de día de la semana entre jornadas de 2026, se elige la PEOR terna en 2026 entero (como se
hizo en la exploración) y se mira cuán a menudo sale tan mala como la observada, y si además 'replica' en ambas mitades."""
import sys, itertools, numpy as np
sys.argv = sys.argv[:2]
exec(open(__file__.replace("a5_perm.py", "a5.py")).read().split("RES = {}")[0])
from scipy.stats import norm
M26 = AJ | PR; g0 = ganancia(RK0) / 8
o = np.argsort(-P, 1, kind="stable"); in15 = RK0 < 15; m15 = np.take_along_axis(P, o[:, :15], 1).sum(1)
ds, inv = np.unique(f[M26], return_inverse=True)
G = np.bincount(inv, g0[M26]); C = np.bincount(inv); O15 = np.bincount(inv, in15[M26]); E15 = np.bincount(inv, m15[M26])
dw = np.array([date.fromisoformat(d).weekday() for d in ds]); half = np.array([d <= "2026-05-31" for d in ds])
TR = list(itertools.combinations(range(7), 3)); W = np.array([[d in tr for d in range(7)] for tr in TR])  # 35x7
def stats(lbl):
    I = W[:, lbl]  # 35 x días
    def dif(v, c, sel):
        a = (I & sel); b = (~I & sel)
        return (a @ v) / (a @ c) - (b @ v) / (b @ c)
    def oe(sel): a = I & sel; return (a @ O15) / (a @ E15)
    allm = np.ones(len(ds), bool)
    return dif(G, C, allm), dif(G, C, half), dif(G, C, ~half), oe(allm), oe(half), oe(~half)
obs = stats(dw); k = TR.index((2, 3, 4))
print(f"Observado mié-jue-vie: plata Δ 2026 {100*obs[0][k]:+.1f} pp (AJ {100*obs[1][k]:+.1f}, PR {100*obs[2][k]:+.1f}); Top-15 O/E 2026 {obs[3][k]:.3f} (AJ {obs[4][k]:.3f}, PR {obs[5][k]:.3f})")
rng = np.random.default_rng(1); N = 5000; c_g = c_gh = c_o = c_oh = 0
for _ in range(N):
    s = stats(rng.permutation(dw))
    j = int(np.argmin(s[0]))
    if s[0][j] <= obs[0][k]: c_g += 1
    if s[0][j] <= obs[0][k] and s[1][j] <= obs[1][k] and s[2][j] <= obs[2][k]: c_gh += 1
    j = int(np.argmin(s[3]))
    if s[3][j] <= obs[3][k]: c_o += 1
    if s[3][j] <= obs[3][k] and s[4][j] <= obs[4][k] and s[5][j] <= obs[5][k]: c_oh += 1
print(f"Permutación ({N}), peor terna de 35 elegida en 2026 entero:")
print(f"  plata: P(peor terna ≤ observado) = {c_g/N:.4f}; y además ambas mitades ≤ observadas = {c_gh/N:.4f}")
print(f"  Top-15 O/E: P(peor terna ≤ observado) = {c_o/N:.4f}; y además ambas mitades ≤ observadas = {c_oh/N:.4f}")
