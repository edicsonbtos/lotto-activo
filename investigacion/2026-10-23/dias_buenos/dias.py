# -*- coding: utf-8 -*-
"""¿Se pueden reconocer los días buenos del Top-15 ANTES o DURANTE el día? Desarrollo LA [2000,9357), ensamble walk-forward."""
import sys, os
import numpy as np
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE
D = LE.cargar(os.path.join(RAIZ, "verificacion/hilo9/datos/historial.txt"))
c = np.load(os.path.join(RAIZ, "verificacion/hilo9/datos/calor_cache.npz"))
P, y = c["P"], c["y"]; P = P / P.sum(1, keepdims=True)
T0 = 2000; n = len(y)
assert (D.seq[T0:T0 + n] == y).all()
dia = D.dia[T0:T0 + n]; hora = D.hora[T0:T0 + n]; dow = D.dow[T0:T0 + n]
orden = np.argsort(-P, 1)
top15 = orden[:, :15]
hit = (top15 == y[:, None]).any(1).astype(float)
p = np.take_along_axis(P, top15, 1).sum(1)          # prob. del modelo de acertar el Top-15 en ese sorteo
rng = np.random.default_rng(20261023)
print(f"sorteos {n}, días {len(set(dia))}; Top-15 real {hit.mean():.3f}, esperado por el modelo {p.mean():.3f}")

# 1) ¿Existen días buenos como estado oculto? Sobredispersión de aciertos por día vs Poisson-binomial del modelo
dias = np.unique(dia)
H = np.array([hit[dia == d].sum() for d in dias]); E = np.array([p[dia == d].sum() for d in dias])
V = np.array([(p * (1 - p))[dia == d].sum() for d in dias])
phi = ((H - E) ** 2).sum() / V.sum()
sim = []
for _ in range(2000):
    hs = (rng.random(n) < p).astype(float)
    Hs = np.array([hs[dia == d].sum() for d in dias]); sim.append(((Hs - E) ** 2).sum() / V.sum())
sim = np.array(sim)
print(f"\n[1] Dispersión por día φ = {phi:.3f}  (azar puro: {np.mean(sim):.3f}, IC95 {np.percentile(sim,2.5):.3f}-{np.percentile(sim,97.5):.3f}; P(sim>=obs) = {np.mean(sim>=phi):.3f})")
print("    φ > 1 significaría días buenos/malos reales. φ ≈ 1 o < 1: el día bueno es suerte.")
dist = np.bincount(H.astype(int), minlength=13)
print("    aciertos/día:", " ".join(f"{k}:{v}" for k, v in enumerate(dist) if v))

# 2) Predictores ANTES del día y DURANTE el día, sobre el residuo (acierto - p)
r = hit - p
def corr_dia(x, z):
    m = np.isfinite(x) & np.isfinite(z); a, b = x[m], z[m]
    rr = np.corrcoef(a, b)[0, 1]; return rr, rr * np.sqrt(len(a)), len(a)
res = (H - E)
ayer = np.r_[np.nan, res[:-1]]
print("\n[2] ¿Qué anticipa un día bueno? (correlación con el residuo del día; z ≈ r·√n)")
for nombre, x in [("residuo de ayer", ayer), ("masa Top-15 prevista del día", E / np.array([(dia == d).sum() for d in dias]))]:
    rr, z, m = corr_dia(x, res); print(f"    {nombre:32s} r = {rr:+.3f}  z = {z:+.2f}  (n = {m})")
for k in range(7):
    m = np.array([dow[dia == d][0] for d in dias]) == k
    print(f"    {'lun mar mié jue vie sáb dom'.split()[k]}: real {H[m].sum()/len(m.nonzero()[0]):.2f}/día  esperado {E[m].sum()/m.sum():.2f}  (O/E {H[m].sum()/E[m].sum():.3f}, días {m.sum()})")

# 3) Durante el día: ¿lo que va pasando hoy predice el próximo sorteo?
prev_hits = np.zeros(n); prev_n = np.zeros(n); prev_last = np.full(n, np.nan)
for i in range(n):
    if i and dia[i - 1] == dia[i]:
        prev_hits[i] = prev_hits[i - 1] + hit[i - 1]; prev_n[i] = prev_n[i - 1] + 1; prev_last[i] = hit[i - 1]
    # resto 0
print("\n[3] Durante el día: acierto del siguiente sorteo según cómo va el día (O/E contra el modelo)")
def oe(mask, et):
    o = hit[mask].sum(); e = p[mask].sum(); v = (p * (1 - p))[mask].sum()
    print(f"    {et:42s} n={mask.sum():5d}  real {hit[mask].mean():.3f}  modelo {p[mask].mean():.3f}  O/E {o/e:.3f}  z {(o-e)/np.sqrt(v):+.2f}")
oe(prev_last == 1, "el sorteo anterior ACERTÓ")
oe(prev_last == 0, "el sorteo anterior FALLÓ")
tasa = np.where(prev_n > 0, prev_hits / np.maximum(prev_n, 1), np.nan)
oe((prev_n >= 4) & (tasa >= 0.6), "va ≥60 % en el día (≥4 sorteos)")
oe((prev_n >= 4) & (tasa <= 0.25), "va ≤25 % en el día (≥4 sorteos)")
racha0 = np.zeros(n)
for i in range(1, n):
    racha0[i] = racha0[i - 1] + 1 if (dia[i - 1] == dia[i] and hit[i - 1] == 0) else (0 if dia[i - 1] != dia[i] else 0)
oe(racha0 >= 3, "lleva ≥3 fallos seguidos hoy")

# 4) Reglas de juego: retorno por ficha del Top-15 plano (15 fichas, paga 30 => 2·acierto − 1)
print("\n[4] Reglas para 'evitar días malos' (Top-15 plano; retorno por ficha; IC95 bootstrap por día)")
ret = 2 * hit - 1
idx_dia = {d: np.where(dia == d)[0] for d in dias}
def regla(mask, et):
    sel = [idx_dia[d][mask[idx_dia[d]]] for d in dias]
    tot = np.array([[ret[s].sum(), len(s)] for s in sel])
    b = []
    for _ in range(2000):
        k = rng.integers(0, len(tot), len(tot)); s = tot[k].sum(0); b.append(s[0] / max(s[1], 1))
    print(f"    {et:46s} sorteos jugados {int(tot[:,1].sum()):5d}  retorno {tot[:,0].sum()/tot[:,1].sum():+.3%}  IC [{np.percentile(b,2.5):+.1%}; {np.percentile(b,97.5):+.1%}]")
regla(np.ones(n, bool), "jugar siempre")
parar = np.zeros(n, bool)   # parar el día tras 3 fallos seguidos
for d in dias:
    ii = idx_dia[d]; seguidos = 0; activo = True
    for i in ii:
        parar[i] = activo
        if activo:
            seguidos = 0 if hit[i] else seguidos + 1
            if seguidos >= 3: activo = False
regla(parar, "parar el día tras 3 fallos seguidos")
regla(prev_last == 1, "jugar solo si el anterior acertó")
regla((prev_n < 4) | (tasa >= 0.4), "seguir solo si el día va ≥40 %")
q = np.quantile(p, 0.66)
regla(p >= q, "solo sorteos con masa Top-15 alta (tercil sup.)")
