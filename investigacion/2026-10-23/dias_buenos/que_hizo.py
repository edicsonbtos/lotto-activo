# -*- coding: utf-8 -*-
"""¿Qué hizo el motor (y el operador) en los días buenos vs malos del Top-15? Desarrollo LA."""
import sys, os
import numpy as np
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE
D = LE.cargar(os.path.join(RAIZ, "verificacion/hilo9/datos/historial.txt"))
c = np.load(os.path.join(RAIZ, "verificacion/hilo9/datos/calor_cache.npz"))
P, y = c["P"], c["y"]; P = P / P.sum(1, keepdims=True)
T0 = 2000; n = len(y); dia = D.dia[T0:T0 + n]
rank = (P > P[np.arange(n), y][:, None]).sum(1) + 1
hit = rank <= 15
# hueco (en días) desde la última salida del ganador, y si ya había salido hoy
ult = {}; gap = np.zeros(n); hoy = np.zeros(n, bool)
for t in range(T0 + n):
    a = D.seq[t]
    if t >= T0:
        i = t - T0
        gap[i] = D.dia[t] - ult[a] if a in ult else 99
        hoy[i] = a in ult and ult[a] == D.dia[t]
    ult[a] = D.dia[t]
H = {d: hit[dia == d].sum() for d in np.unique(dia)}
tipo = np.array(["bueno" if H[d] >= 8 else ("malo" if H[d] <= 4 else "normal") for d in dia])
ent = -(P * np.log2(P)).sum(1)
print("Días: bueno (≥8/12 en Top-15) =", len({d for d in H if H[d] >= 8}), " malo (≤4) =", len({d for d in H if H[d] <= 4}), " de", len(H))
print(f"\n{'':10s}{'gan.1-2 d':>10s}{'3-5 d':>8s}{'6-10 d':>8s}{'>10 d':>8s}{'ya salió hoy':>14s}{'puesto mediano':>16s}{'entropía modelo':>17s}{'masa Top15':>12s}")
mass = np.sort(P, 1)[:, -15:].sum(1)
for t in ["bueno", "normal", "malo"]:
    m = tipo == t; g = gap[m & ~hoy]
    print(f"{t:10s}{np.mean((gap[m]>=1)&(gap[m]<=2)):10.0%}{np.mean((gap[m]>=3)&(gap[m]<=5)):8.0%}{np.mean((gap[m]>=6)&(gap[m]<=10)):8.0%}{np.mean(gap[m]>10):8.0%}{np.mean(hoy[m]):14.1%}{np.median(rank[m]):16.0f}{ent[m].mean():17.3f}{mass[m].mean():12.3f}")
# Top-15 acierto según hueco del ganador
print("\nAcierto Top-15 según cuánto llevaba sin salir el ganador (todo desarrollo):")
for lo, hi, et in [(1,2,"1-2 días"),(3,5,"3-5 días"),(6,10,"6-10 días"),(11,99,">10 días")]:
    m = (gap >= lo) & (gap <= hi) & ~hoy
    print(f"  {et:10s} {m.mean():5.1%} de los sorteos  → Top-15 acierta {hit[m].mean():.0%}")
print(f"  ya salió hoy {hoy.mean():5.1%} de los sorteos → Top-15 acierta {hit[hoy].mean():.0%}")
# ¿se agrupan los ganadores 'fríos' (>5 días) dentro del mismo día? (sobredispersión)
frio = ((gap > 5) | hoy).astype(float); dd = np.unique(dia)
F = np.array([frio[dia == d].sum() for d in dd]); N = np.array([(dia == d).sum() for d in dd]); pf = frio.mean()
phi = ((F - N*pf)**2).sum() / (N*pf*(1-pf)).sum()
rng = np.random.default_rng(1); s = []
for _ in range(2000):
    fs = rng.random(n) < pf; Fs = np.array([fs[dia == d].sum() for d in dd]); s.append(((Fs - N*pf)**2).sum() / (N*pf*(1-pf)).sum())
print(f"\n¿Hay días 'fríos' (muchos ganadores con hueco >5 días o repetidos)? φ = {phi:.3f}, azar {np.mean(s):.3f} [{np.percentile(s,2.5):.3f}; {np.percentile(s,97.5):.3f}], P = {np.mean(np.array(s)>=phi):.3f}")
# ¿anticipa algo la mañana? frío en los 4 primeros sorteos vs acierto del resto del día
pm, rest = [], []
for d in dd:
    ii = np.where(dia == d)[0]
    if len(ii) >= 10: pm.append(frio[ii[:4]].mean()); rest.append(hit[ii[4:]].mean())
pm, rest = np.array(pm), np.array(rest)
print(f"Mañana fría (≥2 de 4 primeros fríos) → resto del día Top-15 {rest[pm>=0.5].mean():.1%} (n={int((pm>=0.5).sum())}) vs mañana normal {rest[pm<0.5].mean():.1%} (n={int((pm<0.5).sum())}); r = {np.corrcoef(pm,rest)[0,1]:+.3f}")
