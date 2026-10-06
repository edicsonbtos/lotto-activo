import numpy as np, time
from comb import *
wf = np.load(os.path.join(SP, "wf_0605.npz"))["P"]
E2, WG = ensamble_v2()
print("máx |E2-wf|", np.abs(E2 - wf).max(), " máx |ajustar(wf)-PROD|", np.abs(ajustar(wf) - A.PROD).max())
np.savez(os.path.join(SP, "M5_ens.npz"), E2=E2, WG=WG)
for b in range(M):
    Pb = np.exp(L[T0 - a0:, b]); A.evaluar(ajustar(Pb), "base_" + str(z["nombres"][b]))
A.evaluar(ajustar(E2), "ensamble_v2_reproducido")
print("pesos globales en 2025-07, 2026-03, 2026-06:", [WG[np.argmax(A.F >= d)].round(3) for d in ("2025-07-01", "2026-03-01", "2026-06-30")])
