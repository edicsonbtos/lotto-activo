"""C2: S2-RD contra el motor de RD walk-forward (B1; también B0) en 2025-07-01..2026-09-22.
Δ mbits con IC 90 % por jornadas, Top-5, Top-15, Top-5 escalonado en plata (pareado), por semestre. -> c2.json"""
import sys, os, json, numpy as np
SP = "/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad"
OUT = "/home/user/lotto-activo/investigacion/2026-10-06/ciego/T1/"
d = np.load(SP + "/T1_rd_datos.npz"); F = np.array([str(x) for x in d["fecha"]]); Y = d["seq"]
mo = np.load(SP + "/T1_rd_motor.npz"); D0 = int(mo["desde"])
n = len(F); B0 = np.full((n, 38), np.nan); B1 = np.full((n, 38), np.nan); B0[D0:] = mo["P0"]; B1[D0:] = mo["P1"]
C = {"B0 (secuencia_v3, solo RD)": B0}
for var in ("todos", "solo_lah"):
    f = SP + f"/T1_c2_s2rd_{var}.npz"
    if os.path.exists(f):
        z = np.load(f, allow_pickle=True); P = np.full((n, 38), np.nan); P[z["t"]] = z["P"]
        C[f"S2-RD ({'3 rasgos LA' if var == 'todos' else 'solo LA h:00'})"] = P
TR = F >= "2025-07-01"
for k in list(C):
    if k.startswith("S2-RD"):
        assert np.isfinite(C[k][TR]).all(), k
        z = 0.25 * np.log(B1) + 0.75 * np.log(np.clip(C[k], 1e-9, None)); z -= np.nanmax(z, 1, keepdims=True)
        e = np.exp(z); C[k + " ⊗ B1 w=0,75"] = e / e.sum(1, keepdims=True)
SEM = {"2025-S2 (jul-dic)": TR & (F <= "2025-12-31"), "2026 (ene-sep)": F >= "2026-01-01", "2025-07..2026-09": TR}
FI = np.array([2, 2, 2, 1, 1.])


def norm(P):
    P = np.clip(P, 1e-9, None); return P / P.sum(1, keepdims=True)


def ic90(v, sel):
    ds = F[sel]; u, inv = np.unique(ds, return_inverse=True); per = np.bincount(inv, v); cnt = np.bincount(inv)
    se = np.sqrt(((per - v.mean() * cnt) ** 2).sum() * len(u) / (len(u) - 1)) / len(v)
    return v.mean() - 1.645 * se, v.mean() + 1.645 * se


def rk(P, i):
    return np.argmax(np.argsort(-P[i], 1, kind="stable") == Y[i][:, None], 1)


def fila(P, sel, ref=B1):
    i = np.where(sel)[0]; P = norm(P[i]); R = norm(ref[i]); y = Y[i]; a = np.arange(len(i))
    dmb = 1000 * np.log2(P[a, y] / R[a, y])
    r = np.argmax(np.argsort(-P, 1, kind="stable") == y[:, None], 1)
    rr = np.argmax(np.argsort(-R, 1, kind="stable") == y[:, None], 1)
    g = np.where(r < 5, 30 * FI[np.minimum(r, 4)], 0) / 8 - 1; gr = np.where(rr < 5, 30 * FI[np.minimum(rr, 4)], 0) / 8 - 1
    h5 = (r < 5) * 1.0 - (rr < 5); h15 = (r < 15) * 1.0 - (rr < 15)
    return dict(n=len(i), dias=len(np.unique(F[i])), mbits=float(1000 * np.log2(P[a, y] * 38).mean()),
                mbits_ref=float(1000 * np.log2(R[a, y] * 38).mean()), dmb=float(dmb.mean()), dmb_ic=ic90(dmb, sel),
                top5=100 * (r < 5).mean(), top5_ref=100 * (rr < 5).mean(), d5_ic=tuple(100 * x for x in ic90(h5, sel)),
                top15=100 * (r < 15).mean(), top15_ref=100 * (rr < 15).mean(), d15_ic=tuple(100 * x for x in ic90(h15, sel)),
                t5esc=100 * g.mean(), t5esc_ref=100 * gr.mean(), dt5=100 * (g - gr).mean(),
                dt5_ic=tuple(100 * x for x in ic90(g - gr, sel)))


res = {}
print("Referencia = B1 walk-forward (motor de RD: secuencia_v3 + LA h:00, (h-1):00 y antes-hoy). IC 90 % por jornadas.")
for k, P in C.items():
    for s, sel in SEM.items():
        o = fila(P, sel); res[f"{k}|{s}"] = o
        print(f"  {k:36} {s:17} n={o['n']:5d} mbits {o['mbits']:+6.1f} (B1 {o['mbits_ref']:+6.1f}) Δ {o['dmb']:+6.1f} "
              f"[{o['dmb_ic'][0]:+6.1f};{o['dmb_ic'][1]:+6.1f}] | Top-5 {o['top5']:.1f} (B1 {o['top5_ref']:.1f}) "
              f"[{o['d5_ic'][0]:+.1f};{o['d5_ic'][1]:+.1f}] | Top-15 {o['top15']:.1f} (B1 {o['top15_ref']:.1f}) "
              f"[{o['d15_ic'][0]:+.1f};{o['d15_ic'][1]:+.1f}] | T5esc {o['t5esc']:+.1f}% (B1 {o['t5esc_ref']:+.1f}%) "
              f"Δ {o['dt5']:+.1f} [{o['dt5_ic'][0]:+.1f};{o['dt5_ic'][1]:+.1f}]")
k = "S2-RD (3 rasgos LA)|2025-07..2026-09"
if k in res:
    o = res[k]; pasa = o["dmb_ic"][0] > 0
    print(f"\nC2 (pre-registro): S2-RD solo contra B1: Δ mbits {o['dmb']:+.2f} IC90 [{o['dmb_ic'][0]:+.2f};{o['dmb_ic'][1]:+.2f}] "
          f"=> {'PASA' if pasa else 'NO PASA'}")
    res["C2_pasa"] = bool(pasa)
json.dump(res, open(OUT + "c2.json", "w"), default=float, indent=0, ensure_ascii=False)
