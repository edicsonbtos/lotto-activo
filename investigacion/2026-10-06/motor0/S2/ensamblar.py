"""Une las tres corridas de la versión congelada (C, vida 90) en motor0_S2.npz (P 10744×38)."""
import sys, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); import arnes as A
SP = A.SP; P = np.full((len(A.T), 38), np.nan)
for f in ("s2_C_90_2024-03_3_2025-06", "s2_C_90", "s2_C_90_2026-07_1_2026-10"):
    Q = np.load(f"{SP}/{f}.npz", allow_pickle=True)["P"]; ok = np.isfinite(Q[:, 0])
    assert not np.isfinite(P[ok, 0]).any(); P[ok] = Q[ok]
assert np.isfinite(P).all() and np.allclose(P.sum(1), 1)
w = 0.75; z = (1 - w) * np.log(A.PROD) + w * np.log(P); z -= z.max(1, keepdims=True); Pm = np.exp(z); Pm /= Pm.sum(1, keepdims=True)
np.savez_compressed(SP + "/motor0_S2.npz", P=P, P_mezcla075=Pm, t=A.T,
                    nombre="S2: LightGBM desde cero, mezcla de expertos por régimen (C), vida 90 d, sin PROD ni RD")
print("ok", P.shape)
