"""C1: evaluación de S2 congelado (reentreno MENSUAL) en ANTIGUO, con la mezcla w = 0,75 contra PROD.
-> c1_salida.txt, c1.json"""
import sys, json, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
import eval_s2 as E
A = E.A; SP = E.SP
OUT = "/home/user/lotto-activo/investigacion/2026-10-06/ciego/T1/"
P = np.load(SP + "/T1_c1_C_90_2024-03_1_2025-06.npz", allow_pickle=True)["P"]
m = A.TRAMOS["ANTIGUO"]
assert np.isfinite(P[m]).all() and not np.isfinite(P[~m, 0]).any()
assert np.allclose(P[m].sum(1), 1)
S2 = np.where(m[:, None], P, A.PROD)           # filas fuera de ANTIGUO no se usan
MIX = E.mezcla(S2, 0.75)
Q = np.load(SP + "/motor0_S2.npz")["P"]       # orientación (reentreno trimestral) para cotejar
C = {"S2 solo (mensual)": S2, "S2+PROD w=0,75 (mensual)": MIX,
     "S2 solo (trimestral, orient.)": Q, "S2+PROD w=0,75 (trimestral, orient.)": E.mezcla(Q, 0.75)}
res = {}
print("== A.evaluar(..., tramos=('ANTIGUO',)) ==")
for k, X in C.items():
    res["evaluar|" + k] = A.evaluar(X, k, tramos=("ANTIGUO",))[0]

SEM = {"2024-S1 (mar-jun)": (A.F >= "2024-03-01") & (A.F <= "2024-06-30"),
       "2024-S2 (jul-dic)": (A.F >= "2024-07-01") & (A.F <= "2024-12-31"),
       "2025-S1 (ene-jun)": (A.F >= "2025-01-01") & (A.F <= "2025-06-30"), "ANTIGUO": m}


def fila(X, sel):
    X = E.norm(X); i = np.where(sel)[0]; y = A.Y[i]
    dmb = 1000 * np.log2(X[i, y] / A.PROD[i, y]); lo, hi = A._ic90(dmb, sel)
    rk = np.argmax(np.argsort(-X[i], 1, kind="stable") == y[:, None], 1)
    rkp = np.argmax(np.argsort(-A.PROD[i], 1, kind="stable") == y[:, None], 1)
    return dict(n=len(i), dmb=dmb.mean(), ic=(lo, hi), top5=100 * (rk < 5).mean(), top5p=100 * (rkp < 5).mean(),
                top15=100 * (rk < 15).mean(), top15p=100 * (rkp < 15).mean())


print("\n== por semestre (ranking directo, sin regla RD; Δ mbits contra PROD, IC 90 % por jornadas) ==")
for k in ("S2 solo (mensual)", "S2+PROD w=0,75 (mensual)"):
    for s, sel in SEM.items():
        o = fila(C[k], sel); res[f"sem|{k}|{s}"] = o
        print(f"  {k:26} {s:18} n={o['n']:5d} Δ {o['dmb']:+6.1f} [{o['ic'][0]:+6.1f};{o['ic'][1]:+6.1f}] "
              f"Top-5 {o['top5']:.1f} (PROD {o['top5p']:.1f}) Top-15 {o['top15']:.1f} (PROD {o['top15p']:.1f})")

print("\n== plata con la regla de cambio RD (h-1):30, pareado contra PROD con la misma regla, IC 90 % por jornadas ==")
for k in ("S2 solo (mensual)", "S2+PROD w=0,75 (mensual)", "S2+PROD w=0,75 (trimestral, orient.)"):
    for s, sel in SEM.items():
        o = E.resumen(C[k], k, "ANTIGUO", sel=sel); res[f"plata|{k}|{s}"] = o
        print(f"  {k:36} {s:18} n={o['n']:5d} T5esc {o['T5esc']:+6.1f}% (PROD {o['T5esc_ref']:+6.1f}%) "
              f"Δ {o['T5esc_d']:+5.1f} [{o['T5esc_dic'][0]:+5.1f};{o['T5esc_dic'][1]:+5.1f}] pp | "
              f"Top-5 {o['top5']:.1f} | Top-15 {o['top15']:.1f} (PROD {o['top15_ref']:.1f}) Δ {o['d15']:+.2f} "
              f"[{o['d15_ic'][0]:+.2f};{o['d15_ic'][1]:+.2f}] | T15pond Δ {o['T15pond_d']:+.1f} "
              f"[{o['T15pond_dic'][0]:+.1f};{o['T15pond_dic'][1]:+.1f}]")

oe = res["evaluar|S2+PROD w=0,75 (mensual)"]; op = res["plata|S2+PROD w=0,75 (mensual)|ANTIGUO"]
pasa = oe["ic90"][0] > 0 and op["T5esc_d"] >= 0
print(f"\nC1 (pre-registro): mezcla Δ mbits {oe['dmbits_vs_prod']:+.2f} IC90 [{oe['ic90'][0]:+.2f};{oe['ic90'][1]:+.2f}] "
      f"(¿>0? {oe['ic90'][0] > 0}) Y Δ T5esc RD pareado {op['T5esc_d']:+.1f} pp (¿≥0? {op['T5esc_d'] >= 0}) "
      f"=> {'PASA' if pasa else 'NO PASA'}")
res["C1_pasa"] = bool(pasa)
json.dump(res, open(OUT + "c1.json", "w"), default=float, indent=0, ensure_ascii=False)
