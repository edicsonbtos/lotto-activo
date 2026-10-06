from comun import *
import importlib.util
spec = importlib.util.spec_from_file_location("iv2", "/home/user/lotto-activo/herramientas/modelos/intradia_v2.py")
iv2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(iv2)
tabs, Dn = iv2.construir(D, {})
nom = ["ema40", "ema160", "emaz640", "emaz2560", "semana_actual", "semana_anterior", "mes_actual", "mes_anterior"]
# matriz completa como en predecir()
d = sum(sz - 1 for _, sz in tabs) + Dn.shape[2]; a0 = 100
X = np.zeros((n - a0, K, d), np.float32); o_ = 0
for ix, sz in tabs:
    ix = ix[a0:]; r, c = np.nonzero(ix); X[r, c, o_ + ix[r, c] - 1] = 1.0; o_ += sz - 1
X[:, :, o_:] = Dn[a0:]
T26 = int(np.searchsorted(np.array(D.fecha), "2026-01-01"))
print("Coeficientes de intradia_v2 (ventana 4500, tau 1500, como en producción) en distintos cortes:")
for lab, T in (("fin 2024", int(np.searchsorted(np.array(D.fecha), "2025-01-01"))), ("corte dev 9357", 9357), ("1-ene-2026", T26), ("final", n)):
    a1 = max(a0, T - 4500); w = np.exp(-(T - 1 - np.arange(a1, T)) / 1500)
    b = iv2.ajustar_newton(X[a1 - a0:T - a0], SEQ[a1:T], w, 1.0)
    print(f"  {lab:15} " + "  ".join(f"{nm} {v:+.3f}" for nm, v in zip(nom, b[o_:])))
# residuo de cada rasgo continuo: valor en el ganador − Σ P·rasgo, por grupo y era (z por días)
F = Dn[t]
print("\nResiduo (ganador − esperado por el motor) de los rasgos de calendario, por grupo. z por bootstrap de días")
rng = np.random.default_rng(3)
for j, nm in enumerate(nom):
    if j < 4: continue
    res = F[rows, y, j] - (P * F[:, :, j]).sum(1); s = f"  {nm:16}"
    for era, me in (("dev", DEV), ("2026", A26)):
        for g, gm in (("MVF", MVF), ("SM", ~MVF)):
            m = me & gm; u, inv = np.unique(dayid[m], return_inverse=True); sd = np.bincount(inv, res[m]); cn = np.bincount(inv)
            bs = [sd[i].sum() / cn[i].sum() for i in (rng.integers(0, len(sd), len(sd)) for _ in range(500))]
            s += f" | {era} {g} {res[m].mean():+.3f} (z {res[m].mean()/np.std(bs):+.1f})"
    print(s)
# rasgo semana_actual por día de semana: media del valor en el ganador y su dispersión entre animales
print("\nsemana_actual: desviación típica entre animales (cuánto pesa el rasgo) por día de semana, 2026")
for k in range(7):
    m = A26 & (dow == k); print(f"   {['lun','mar','mié','jue','vie','sáb','dom'][k]}: sd {F[m][:, :, 4].std(1).mean():.2f}")
