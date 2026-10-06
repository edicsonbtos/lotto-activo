# M4 final congelado: V3 (todo el pasado, vida media 180 d, con RD), mezcla w = 1,25 con PROD (elegida en ELECCION).
import sys, json, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2")
import arnes as A
L = np.log(np.clip(A.PROD, 1e-9, None))
P3 = np.load(A.SP + "/m4_V3.npz", allow_pickle=True)["P"]
z = -0.25 * L + 1.25 * np.log(np.clip(P3, 1e-9, None)); z -= z.max(1, keepdims=True); P = np.exp(z); P /= P.sum(1, keepdims=True)
# ANTIGUO (< 2025-07) no se reentrenó: ahí P = PROD (Δ = 0 por construcción)
assert np.allclose(P[A.F < "2025-07-01"], A.PROD[A.F < "2025-07-01"], atol=1e-6)
np.savez_compressed(A.SP + "/motor2_M4.npz", P=P)
r = A.evaluar(P, "M4-final", tramos=("AJUSTE", "ELECCION"))
el = r[1]
if el["ic90"][0] > 0 and r[0]["dmbits_vs_prod"] > 0:
    r += A.evaluar(P, "M4-final", tramos=("PRUEBA26",), extra="M4 V3 vida180 +RD, w=1.25, congelado")
# informativo: Δ por bloque de días (mié-vie vs resto) en cada tramo
for tr in ("AJUSTE", "ELECCION", "PRUEBA26"):
    i = np.where(A.TRAMOS[tr])[0]; d = 1000 * np.log2(P[i, A.Y[i]] / A.PROD[i, A.Y[i]]); m = np.isin(A.DOW[i], [2, 3, 4])
    print(f"  {tr}: Δ mié-vie {d[m].mean():+.1f}  resto {d[~m].mean():+.1f}")
json.dump(r, open("resultados.json", "w"), ensure_ascii=False, indent=1)
