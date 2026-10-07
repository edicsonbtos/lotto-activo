"""(f) Bootstrap por jornadas (10.000) del Δ mbits contra PROD, motor S2 congelado (matriz completa, sin submuestra).
También el Δ Top-15 con la regla RD y, como robustez frente a la autocorrelación, bloques de 7 días naturales."""
import sys, json, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
import eval_s2 as E
A = E.A
z = np.load(A.SP + "/motor0_S2.npz"); C = {"S2 solo": z["P"], "S2+PROD w=0,75": z["P_mezcla075"]}
B = 10000; res = {}
def boot(v, idx, clave, B=B, semilla=20261006):
    u, inv = np.unique(clave, return_inverse=True); s = np.bincount(inv, v); n = np.bincount(inv)
    rng = np.random.default_rng(semilla); k = rng.integers(0, len(u), (B, len(u)))
    m = s[k].sum(1) / n[k].sum(1)
    return dict(media=float(v.mean()), ic90=[float(np.percentile(m, 5)), float(np.percentile(m, 95))],
                ic95=[float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], p_le0=float((m <= 0).mean()), nbloques=len(u))
for tr in ("ELECCION", "AJUSTE"):
    idx = np.where(A.TRAMOS[tr])[0]; y = A.Y[idx]
    dia = A.F[idx]; sem = np.array([(np.datetime64(f) - np.datetime64("2025-06-30")).astype(int) // 7 for f in dia])
    for k, P in C.items():
        Pn = E.norm(P)
        dmb = 1000 * np.log2(Pn[idx, y] / A.PROD[idx, y])
        h = (E.rango_rd(Pn, idx) < 15).astype(float) - (E.rango_rd(E.norm(A.PROD), idx) < 15).astype(float)
        o = dict(dmb_dias=boot(dmb, idx, dia), dmb_semanas=boot(dmb, idx, sem), d15_dias=boot(100 * h, idx, dia),
                 ic90_normal=list(E.ic90_dias(dmb, idx)))
        res[f"{k}|{tr}"] = o
        print(f"{tr:8} {k:15} Δmbits {o['dmb_dias']['media']:+6.2f} | boot días IC90 [{o['dmb_dias']['ic90'][0]:+.2f};{o['dmb_dias']['ic90'][1]:+.2f}] "
              f"IC95 [{o['dmb_dias']['ic95'][0]:+.2f};{o['dmb_dias']['ic95'][1]:+.2f}] P(Δ≤0)={o['dmb_dias']['p_le0']:.4f} "
              f"| semanas IC90 [{o['dmb_semanas']['ic90'][0]:+.2f};{o['dmb_semanas']['ic90'][1]:+.2f}] P≤0={o['dmb_semanas']['p_le0']:.4f} "
              f"| normal IC90 [{o['ic90_normal'][0]:+.2f};{o['ic90_normal'][1]:+.2f}] "
              f"| ΔTop15 {o['d15_dias']['media']:+.2f} pp IC90 [{o['d15_dias']['ic90'][0]:+.2f};{o['d15_dias']['ic90'][1]:+.2f}] P≤0={o['d15_dias']['p_le0']:.4f}")
json.dump(res, open("/home/user/lotto-activo/investigacion/2026-10-06/ciego/T2/bootstrap.json", "w"), indent=1)
