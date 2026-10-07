"""C2: rasgos de S2 calculados con la secuencia RD (+3 rasgos LA del motor RD). Prueba de fuga a nivel de rasgos.
Guarda <SP>/T1_rd_rasgos.npz: X (n, 38, 40), nm, etq, rho."""
import sys, time, importlib.util, numpy as np
sys.path.insert(0, "/home/user/lotto-activo/investigacion/2026-10-06/motor0/S2")
sys.path.insert(0, "/home/user/lotto-activo/herramientas/rdint")
import rasgos_s2 as R, modelo as MB
spec = importlib.util.spec_from_file_location("r4", "/home/user/lotto-activo/investigacion/2026-10-06/motor2/M4/rasgos.py")
R4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(R4)
SP = "/tmp/claude-0/-home-user-lotto-activo/fec08f7b-ea3b-52a9-bbc3-adca57bb3a51/scratchpad"
z = np.load(SP + "/T1_rd_datos.npz")
seq, hora, dia = z["seq"], z["hora"], z["dia"]; fecha = [str(x) for x in z["fecha"]]
la_h, la_h1, la_hoy = z["la_h"], z["la_h1"], z["la_hoy"]


def construir(seq, la_h, la_h1, la_hoy, rho):
    X4, nm4 = R4.construir(seq, hora, dia, fecha, None)
    keep = [j for j, n in enumerate(nm4) if n not in ("rd1", "rd2", "hay_rd")]
    Xn, nmn, info = R.nuevos(seq, hora, dia, fecha, rho=rho)
    XL = MB.features(la_h, la_h1, la_hoy)
    X = np.concatenate([X4[:, :, keep], Xn, XL], 2).astype(np.float32)
    return X, [nm4[j] for j in keep] + nmn + ["la_h", "la_h1", "la_antes_hoy"], info


t0 = time.time()
rho, mreps = R.calibrar_rho(seq, dia, fecha, desde="2025-01-01", hasta="2025-06-30")
print("rho RD", round(rho, 3), "reps medias 2025-01..06", round(mreps, 3), "(LA: rho 0,240)")
X, nm, info = construir(seq, la_h, la_h1, la_hoy, rho)
print(X.shape, f"{time.time() - t0:.0f}s")
# fuga: alterar RD desde c y LA desde c+1 (la fila c usa legítimamente LA de su propio h:00)
rng = np.random.default_rng(1)
for c in (9500, 12000):
    s2 = seq.copy(); s2[c:] = (s2[c:] + 7) % 38
    h2 = la_h.copy(); h2[c + 1:] = rng.integers(0, 38, len(h2) - c - 1)
    g2 = la_h1.copy(); g2[c + 1:] = rng.integers(0, 38, len(g2) - c - 1)
    y2 = la_hoy.copy(); y2[c + 1:] = rng.integers(0, 2, y2[c + 1:].shape)
    Xb, _, _ = construir(s2, h2, g2, y2, rho)
    assert np.allclose(X[:c + 1], Xb[:c + 1], equal_nan=True), c
    assert not np.allclose(X[c + 1:], Xb[c + 1:], equal_nan=True)
    print("fuga rasgos corte", c, fecha[c], "OK")
np.savez_compressed(SP + "/T1_rd_rasgos.npz", X=X, nm=np.array(nm), etq=info["etq"], rho=rho)
F = np.array(fecha); q = X[:, 0, nm.index("q_prior")]; dow = z["dow"]
m = F >= "2025-07-01"
print("q_prior medio por dow (2025-07..)", [round(float(q[m & (dow == k)].mean()), 3) for k in range(7)])
print("etq media por dow (2025-07..)", [round(float(info["etq"][m & (dow == k)].mean()), 3) for k in range(7)])
print(f"total {time.time() - t0:.0f}s")
