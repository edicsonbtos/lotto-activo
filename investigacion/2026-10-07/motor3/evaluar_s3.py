"""Evaluación pre-registrada (AJUSTE, ELECCION; PRUEBA26 solo con --reciente y versión elegida)."""
import sys, json, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
import arnes as A, eval_s2 as E
SP = A.SP
R = {"S2_90": np.load(SP + "/motor0_S2.npz")["P"]}
for k in ("S2_45", "S3_90", "S3_45"): R[k] = np.load(f"{SP}/s3run_{k}.npz")["P"]
tr = sys.argv[1:] or ["AJUSTE", "ELECCION"]
def fila(nm, P, t, cambio=True):
    o = E.resumen(P, nm, t, cambio=cambio); return o
print("== sin regla RD afuera (cambio=False) y con ella (True). Δ = pareado contra PROD con regla RD")
res = {}
for k, P in R.items():
    for w in (0.5, 0.75, 1.0):
        Q = P if w == 1.0 else E.mezcla(P, w)
        for t in tr:
            for cb in (True, False):
                o = E.resumen(Q, f"{k} w={w}", t, cambio=cb)
                res[f"{k}|{w}|{t}|{cb}"] = o
                print(f"{k:6} w={w:4} {t:8} cambio={str(cb):5} mbits Δ {o['dmb']:+6.1f} [{o['dmb_ic'][0]:+5.1f};{o['dmb_ic'][1]:+5.1f}] Top15 {o['top15']:.1f} (PROD {o['top15_ref']:.1f}) Δ {o['d15']:+.2f} [{o['d15_ic'][0]:+.2f};{o['d15_ic'][1]:+.2f}] T5esc {o['T5esc']:+.1f}% (PROD {o['T5esc_ref']:+.1f}) T15pond {o['T15pond']:+.1f}% ({o['T15pond_ref']:+.1f})")
json.dump(res, open("resultados_s3.json", "w"), default=float)
print("\n== ¿RD mejora? ¿recencia ayuda? Δ mbits pareado (AJUSTE+ELECCION juntos), IC 90 % por jornadas, w=1")
idx = np.where(A.TRAMOS["AJUSTE"] | A.TRAMOS["ELECCION"])[0]; y = A.Y[idx]
def lp(P): return np.log(E.norm(P)[idx, y])
for a, b, txt in (("S3_90", "S2_90", "RD dentro (vida 90)"), ("S3_45", "S2_45", "RD dentro (vida 45)"), ("S2_45", "S2_90", "vida 45 vs 90 (sin RD)"), ("S3_45", "S3_90", "vida 45 vs 90 (con RD)")):
    d = 1000 * (lp(R[a]) - lp(R[b]))/np.log(2); lo, hi = E.ic90_dias(d, idx)
    print(f"{txt:28} {d.mean():+6.2f} [{lo:+6.2f};{hi:+6.2f}]")
