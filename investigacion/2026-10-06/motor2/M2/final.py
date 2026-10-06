"""Conjunto CONGELADO: V1 (3 clases lun-mar / mié-vie / sáb-dom × {ya salió hoy, salió ayer o anteayer}), walk-forward
semanal, semivida 60 días, L2 prec. 5, mezcla w=0,75 con PROD. Chequeo de fuga + matriz final + UNA mirada a PRUEBA26."""
import numpy as np, comun as C, correccion as R, sys
A = C.A; W = 0.75
def motor():
    P, nom, th = R.walk_forward("V1", 60)
    M = np.exp((1 - W) * np.log(C.PROD) + W * np.log(P)); return M / M.sum(1, keepdims=True), dict(zip(nom, np.exp(th).round(3)))
P0, th = motor(); print("multiplicadores al final:", th)
# fuga: se altera el FUTURO (ganadores y categorías de regla de filas >= corte) y las filas < corte no deben cambiar
Y0, HOY0, AY0 = C.Y.copy(), C.HOY.copy(), C.AYAA.copy()
for corte in (3000, 7000, 9000):
    C.Y[corte:] = (Y0[corte:] + 7) % 38; C.HOY[corte:] = np.roll(HOY0[corte:], 7, 1); C.AYAA[corte:] = np.roll(AY0[corte:], 3, 1)
    R.C = C; P1, _ = motor()
    assert np.allclose(P0[:corte], P1[:corte]), f"FUGA {corte}"
    C.Y[:] = Y0; C.HOY[:] = HOY0; C.AYAA[:] = AY0
print("chequeo de fuga (futuro alterado en 3 cortes): OK")
assert P0.shape == (10744, 38)
np.savez_compressed(A.SP + "/motor2_M2.npz", P=P0, t=A.T)
A.evaluar(P0, "M2_final", tramos=("AJUSTE", "ELECCION"))
if "--prueba" in sys.argv:
    A.evaluar(P0, "M2_final", tramos=("PRUEBA26",), extra="M2: V1 3 clases hoy/ayaa, WF semanal H=60, w=0.75")
