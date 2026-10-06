"""Construye los rasgos de S2 (M4 sin RD + nuevos) y prueba la fuga de los rasgos nuevos."""
import sys, time, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor2"); sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
import arnes as A, rasgos_s2 as R
SP = A.SP; D = A.D
t0 = time.time()
z = np.load(SP + "/m4_rasgos.npz"); X4 = z["X"]; nm4 = [str(x) for x in z["nm"]]
keep = [j for j, n in enumerate(nm4) if n not in ("rd1", "rd2", "hay_rd")]
rho, mreps = R.calibrar_rho(np.asarray(D.seq), np.asarray(D.dia), list(D.fecha))
print("rho", round(rho, 3), "reps medias 2025-07..12", round(mreps, 3))
Xn, nmn, info = R.nuevos(D.seq, D.hora, D.dia, list(D.fecha), rho=rho)
print("nuevos", Xn.shape, round(time.time() - t0, 1), "s")
for c in (6000, 9000, 12000):
    S2 = np.asarray(D.seq).copy(); S2[c:] = (S2[c:] + 7) % 38
    Xb, _, _ = R.nuevos(S2, D.hora, D.dia, list(D.fecha), rho=rho)
    assert np.allclose(Xn[:c + 1], Xb[:c + 1]), c
print("fuga rasgos nuevos: OK", round(time.time() - t0, 1), "s")
X = np.concatenate([X4[:, :, keep], Xn], 2).astype(np.float32)
nm = [nm4[j] for j in keep] + nmn
np.savez_compressed(SP + "/s2_rasgos.npz", X=X, nm=np.array(nm), etq=info["etq"], rho=rho)
print(X.shape, nm)
q = Xn[:, 0, 3]; qp = Xn[:, 0, 4]
dow = np.asarray(D.dow); F = np.array(D.fecha)
for per in (("2025-07", "2026-02"), ("2026-03", "2026-06")):
    m = (F >= per[0]) & (F <= per[1] + "-31")
    print(per, "q_prior por dow", [round(q[m & (dow == k)].mean(), 3) for k in range(7)], "etq", [round(info["etq"][m & (dow == k)].mean(), 3) for k in range(7)])
