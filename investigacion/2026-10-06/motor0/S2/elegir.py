"""S2: compara variantes en AJUSTE y ELECCION (sin tocar PRUEBA26)."""
import sys, json, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
import eval_s2 as E
SP = E.SP
cands = {}
for nm in sys.argv[1:]:
    z = np.load(f"{SP}/s2_{nm}.npz", allow_pickle=True)
    cands[nm] = z["P"]
    if nm.startswith("AB2"):
        cands["A" + nm[3:]] = z["P"]; cands["B2" + nm[3:]] = z["P2"]; del cands[nm]
cands["M4(final,RD)"] = np.load(f"{SP}/motor2_M4.npz")["P"]
cands["M4 V1 sinRD"] = np.load(f"{SP}/m4_V1noRD.npz")["P"]
res = []
for k, P in cands.items():
    for tr in ("AJUSTE", "ELECCION"):
        o = E.resumen(P, k, tr); res.append(o); print(E.linea(o))
json.dump(res, open("/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2/elegir_" + "_".join(sys.argv[1:]) + ".json", "w"),
          default=float, indent=0)
