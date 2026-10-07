"""Evalúa la corrida sellada según PREREGISTRO.md (sin regla RD)."""
import numpy as np, json
SP = "/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad"
z = np.load(SP + "/sel_resultado.npz"); S2, B, y, F = z["S2"], z["base"], z["y"].astype(int), z["f"]
ok = np.isfinite(S2[:, 0]) & np.isfinite(B[:, 0]); print("filas T", len(y), "con S2", int(np.isfinite(S2[:, 0]).sum()), "con base", int(np.isfinite(B[:, 0]).sum()), "comunes", int(ok.sum()))
def norm(P): P = np.clip(P, 1e-9, None); return P / P.sum(1, keepdims=True)
S2, B = norm(S2[ok]), norm(B[ok]); y, F = y[ok], F[ok]
w = 0.75; M = norm(np.exp((1 - w) * np.log(B) + w * np.log(S2)))
def ic90(v, f):
    u, inv = np.unique(f, return_inverse=True); per = np.bincount(inv, v); cnt = np.bincount(inv)
    se = np.sqrt(((per - v.mean() * cnt) ** 2).sum() * len(u) / (len(u) - 1)) / len(v); return v.mean() - 1.645 * se, v.mean() + 1.645 * se
def rk(P, y): o = np.argsort(-P, 1, kind="stable"); return np.argmax(o == y[:, None], 1)
def gan(r, plan):
    f = {"T15": np.ones(15), "T5esc": np.array([2, 2, 2, 1, 1.])}[plan]; n = len(f)
    return np.where(r < n, 30 * f[np.minimum(r, n - 1)], 0.0) / f.sum() - 1
def informe(sel, tit):
    f = F[sel]; yy = y[sel]; print(f"\n== {tit}: n={sel.sum()} jornadas={len(np.unique(f))}")
    rb = rk(B[sel], yy)
    for nom, P in (("base ens_v2", B), ("S2 solo", S2), ("mezcla .75", M)):
        Q = P[sel]; r = rk(Q, yy); mb = 1000 * np.log2(Q[np.arange(len(yy)), yy] * 38)
        d = 1000 * np.log2(Q[np.arange(len(yy)), yy] / B[sel][np.arange(len(yy)), yy]); lo, hi = ic90(d, f)
        h = (r < 15).astype(float) - (rb < 15); l15, h15 = ic90(100 * h, f)
        g15 = gan(r, "T15"); g5 = gan(r, "T5esc"); d5 = g5 - gan(rb, "T5esc"); l5, h5 = ic90(100 * d5, f)
        print(f"{nom:12} mbits {mb.mean():+6.1f} | Δ vs base {d.mean():+6.2f} [{lo:+6.2f};{hi:+6.2f}] | Top15 {100*(r<15).mean():.1f} Δ {100*h.mean():+.2f} [{l15:+.2f};{h15:+.2f}] | Top5 {100*(r<5).mean():.1f} | T15 {100*g15.mean():+.1f}% | T5esc {100*g5.mean():+.1f}% Δ {100*d5.mean():+.1f} [{l5:+.1f};{h5:+.1f}]")
informe(np.ones(len(y), bool), "TODO 2020-2023")
for a in ("2020", "2021", "2022", "2023"): informe(np.char.startswith(F, a), a)
