"""chequear_fuga con el pipeline completo de S2 (rasgos M4 sin RD + nuevos + reentreno del mes de la fila, objetivo C)."""
import sys, importlib.util, numpy as np, copy
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
import arnes as A, rasgos_s2 as R, motor_s2 as M
spec = importlib.util.spec_from_file_location("r4", "/home/user/lotto-activo/investigacion/2026-10-06/motor2/M4/rasgos.py")
R4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(R4)
SP = A.SP; z = np.load(SP + "/s2_rasgos.npz"); rho = float(z["rho"]); NM = [str(x) for x in z["nm"]]
D0 = A.D; Pfin = np.load(SP + "/motor0_S2.npz")["P"]

def fn(seq, hora, dow, fecha, i):
    X4, nm4 = R4.construir(seq, hora, D0.dia, fecha, None)
    keep = [j for j, n in enumerate(nm4) if n not in ("rd1", "rd2", "hay_rd")]
    Xn, nmn, info = R.nuevos(seq, hora, D0.dia, fecha, rho=rho)
    X = np.concatenate([X4[:, :, keep], Xn], 2).astype(np.float32); nm = [nm4[j] for j in keep] + nmn
    assert nm == NM
    D = copy.copy(D0); D.seq = np.asarray(seq); M.A.D = D
    mes = fecha[i][:7]
    P, _, _ = M.correr("C", 90, X, nm, info["etq"], desde=mes, paso=1, hasta=mes, log=lambda *a, **k: None)
    M.A.D = D0
    return P[i - A.T[0]]

cortes = (9100, 11350)   # una fila de AJUSTE (2026-01) y una de ELECCION (2026-06)
for c in cortes: print(c, A.D.fecha[c])
for c in cortes:
    p = fn(np.asarray(D0.seq), np.asarray(D0.hora), np.asarray(D0.dow), list(D0.fecha), c)
    assert np.allclose(p, Pfin[c - A.T[0]]), "la matriz guardada no coincide con el pipeline"
print("matriz guardada = pipeline: OK")
A.chequear_fuga(fn, cortes=cortes)
