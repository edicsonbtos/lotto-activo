"""Prueba de fuga de la capa de combinación (las bases son los submodelos de producción, auditados por lotto_eval.prueba_fuga):
se cambia el futuro (y y L desde el corte c) y se exige que las filas < c+12 del día del corte no cambien."""
import numpy as np, comb as C
WG = np.load(C.os.path.join(C.SP, "M5_ens.npz"))["WG"]; DOWd = np.asarray(C.A.D.dow)
rng = np.random.default_rng(1)
for c in (9001, 11003, 12500):
    s = C.INI[C.INI <= c].max(); e = C.INI[C.INI > c].min(); i = np.searchsorted(C.INI, s)
    C_INI = C.INI.copy(); C.INI = C_INI[max(0, i - 1):i + 2]
    a = C.exp_diaria(2, 20, WG, grupo=DOWd, kappa=20)[s - C.T0:c - C.T0 + 1].copy()
    L0, y0 = C.L.copy(), C.y.copy()
    C.y[c - C.a0:] = rng.integers(0, 38, len(C.y) - (c - C.a0)); C.L[c - C.a0 + 1:] = C.L[c - C.a0 + 1:][::-1]
    b = C.exp_diaria(2, 20, WG, grupo=DOWd, kappa=20)[s - C.T0:c - C.T0 + 1]
    C.L, C.y, C.INI = L0, y0, C_INI
    assert np.allclose(a, b), c; print("corte", c, "sin fuga (filas", s, "a", c, ")")
