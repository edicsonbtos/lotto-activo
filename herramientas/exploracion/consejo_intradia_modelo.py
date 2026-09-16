# -*- coding: utf-8 -*-
"""
CONSEJERO A - "Cronista Intradia"
Estrategia: P(animal | hora) con decaimiento exponencial por recencia,
suavizado tipo Dirichlet hacia la frecuencia global (tambien con decaimiento).
Variante B: condicionado a (dia_semana x hora).
Hiperparametros (vida media, suavizado) elegidos por validacion walk-forward
en un tramo de validacion; metricas reportadas en un tramo de prueba posterior
(estrictamente: para predecir t solo se usan sorteos < t).
"""
import math
import numpy as np
from collections import defaultdict

RUTA = r"C:\Users\edics\Downloads\lotto-activo\lotto-activo\historial.txt"
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {a: i for i, a in enumerate(POS)}
K = 38

# ---------- Carga ----------
fechas, horas, nums = [], [], []
with open(RUTA, encoding="utf-8") as f:
    for linea in f:
        linea = linea.strip()
        if not linea:
            continue
        fch, h, n = linea.split()
        fechas.append(fch)
        horas.append(int(h))
        nums.append(IDX[n])
N = len(nums)
horas = np.array(horas)
nums = np.array(nums)
import datetime as _dt
dow = np.array([_dt.date.fromisoformat(f).weekday() for f in fechas])

# Objetivo: 2026-09-14 hora 8
t_obj = None
for i in range(N - 1, -1, -1):
    if fechas[i] == "2026-09-14" and horas[i] == 8:
        t_obj = i
        break
print(f"N={N}  ultimo={fechas[-1]} h{horas[-1]} '{POS[nums[-1]]}'")
print(f"Indice objetivo (2026-09-14 h8): {t_obj}  -> resultado real en archivo: '{POS[nums[t_obj]]}' (NO usado)")

# ---------- Conteos acumulados con decaimiento ----------
def cum_decay(d, claves):
    """claves: array (N,) de cluster (hora o (dow,hora)).
    Devuelve C dict cluster -> (N,K) con C[t] = suma_{i<t, clave_i=cluster} d^(t-i) onehot(num_i),
    y G (N,K) global = suma_{i<t} d^(t-i)."""
    clusters = sorted(set(claves.tolist()))
    pos = {c: k for k, c in enumerate(clusters)}
    M = len(clusters)
    C = np.zeros((M, N, K), dtype=np.float64)
    cur = np.zeros((M, K), dtype=np.float64)
    for t in range(N):
        cur *= d
        C[:, t, :] = cur
        cur[pos[claves[t]], nums[t]] += 1.0
    G = C.sum(axis=0)  # (N,K) global decayed counts antes de t
    return {c: C[pos[c]] for c in clusters}, G

def evaluar(Cdict, G, claves, half, s, rng):
    """Modelo: p_t = (C_h[t] + s * G[t]/sum G[t]) normalizado.
    half informativo solo (d ya aplicado). Devuelve loglik, top1, top3, top5 sobre indices rng."""
    ll = 0.0
    t1 = t3 = t5 = 0
    n = 0
    for t in rng:
        c = Cdict[claves[t]][t]
        g = G[t]
        gs = g.sum()
        prior = g / gs if gs > 0 else np.full(K, 1.0 / K)
        v = c + s * prior
        p = v / v.sum()
        y = nums[t]
        ll += math.log(max(p[y], 1e-15))
        order = np.argsort(-p)
        r = int(np.where(order == y)[0][0])
        t1 += r < 1
        t3 += r < 3
        t5 += r < 5
        n += 1
    return ll / n, t1, t3, t5, n

def predecir(Cdict, G, clave, t, s):
    c = Cdict[clave][t]
    g = G[t]
    gs = g.sum()
    prior = g / gs if gs > 0 else np.full(K, 1.0 / K)
    v = c + s * prior
    return v / v.sum()

# ---------- Rangos ----------
TEST = 1000
VAL = 1000
test_rng = range(t_obj - TEST, t_obj)          # ultimos 1000 sorteos ANTES del objetivo
val_rng = range(t_obj - TEST - VAL, t_obj - TEST)
print(f"Validacion: [{val_rng.start}..{val_rng.stop-1}]  {fechas[val_rng.start]} h{horas[val_rng.start]} .. {fechas[val_rng.stop-1]} h{horas[val_rng.stop-1]}")
print(f"Prueba:     [{test_rng.start}..{test_rng.stop-1}]  {fechas[test_rng.start]} h{horas[test_rng.start]} .. {fechas[test_rng.stop-1]} h{horas[test_rng.stop-1]}")

halves = [90, 180, 360, 720, 1440, 2880, 10**9]  # vida media en sorteos (12/dia); 1e9 ~ sin decaimiento
ss = [2, 5, 10, 20, 40, 80]

claves_h = horas.copy()
claves_wh = dow * 12 + horas  # 84 clusters

print("\n=== Modelo A: hora del dia (12 clusters) ===")
mejores_A = []
for half in halves:
    d = 0.5 ** (1.0 / half)
    Cdict, G = cum_decay(d, claves_h)
    for s in ss:
        ll, t1, t3, t5, n = evaluar(Cdict, G, claves_h, half, s, val_rng)
        mejores_A.append((ll, half, s, t1, t3, t5, n))
mejores_A.sort(reverse=True)
for ll, half, s, t1, t3, t5, n in mejores_A[:6]:
    print(f"  val ll={ll:.4f} half={half} s={s}  top1={t1/n:.3%} top3={t3/n:.3%} top5={t5/n:.3%} (n={n})")

print("\n=== Modelo B: dia_semana x hora (84 clusters) ===")
mejores_B = []
for half in halves:
    d = 0.5 ** (1.0 / half)
    Cdict, G = cum_decay(d, claves_wh)
    for s in ss:
        ll, t1, t3, t5, n = evaluar(Cdict, G, claves_wh, half, s, val_rng)
        mejores_B.append((ll, half, s, t1, t3, t5, n))
mejores_B.sort(reverse=True)
for ll, half, s, t1, t3, t5, n in mejores_B[:6]:
    print(f"  val ll={ll:.4f} half={half} s={s}  top1={t1/n:.3%} top3={t3/n:.3%} top5={t5/n:.3%} (n={n})")

# ---------- Baseline: solo global con decaimiento ----------
print("\n=== Baseline: frecuencia global con decaimiento (sin condicionar) ===")
for half in halves:
    d = 0.5 ** (1.0 / half)
    Cdict, G = cum_decay(d, claves_h)
    ll = t1 = t3 = t5 = n = 0
    for t in val_rng:
        g = G[t]; p = g / g.sum()
        y = nums[t]
        ll += math.log(max(p[y], 1e-15))
        order = np.argsort(-p); r = int(np.where(order == y)[0][0])
        t1 += r < 1; t3 += r < 3; t5 += r < 5; n += 1
    print(f"  half={half}: val ll={ll/n:.4f} top1={t1/n:.3%} top3={t3/n:.3%} top5={t5/n:.3%}")

# ---------- Evaluacion en PRUEBA con los mejores hiperparametros de validacion ----------
def en_prueba(claves, half, s, etiqueta):
    d = 0.5 ** (1.0 / half)
    Cdict, G = cum_decay(d, claves)
    ll, t1, t3, t5, n = evaluar(Cdict, G, claves, half, s, test_rng)
    print(f"\n--- PRUEBA {etiqueta}: half={half} s={s} (n={n}) ---")
    print(f"  loglik media={ll:.4f}  (azar={-math.log(38):.4f})")
    print(f"  Top-1: {t1}/{n} = {t1/n:.3%}  (azar 2.63%)")
    print(f"  Top-3: {t3}/{n} = {t3/n:.3%}  (azar 7.89%)")
    print(f"  Top-5: {t5}/{n} = {t5/n:.3%}  (azar 13.16%)")
    # p-valor binomial vs azar (Top-3)
    from scipy.stats import binomtest
    pv = binomtest(t3, n, 3/38, alternative="greater").pvalue
    print(f"  p-valor Top-3 vs azar: {pv:.4f}")
    # ultimos 24 sorteos antes del objetivo
    r24 = range(t_obj - 24, t_obj)
    a3 = a5 = 0
    det = []
    for t in r24:
        c = Cdict[claves[t]][t]; g = G[t]; gs = g.sum()
        prior = g / gs if gs > 0 else np.full(K, 1.0 / K)
        v = c + s * prior; p = v / v.sum()
        order = np.argsort(-p); r = int(np.where(order == nums[t])[0][0])
        a3 += r < 3; a5 += r < 5
        det.append((fechas[t], horas[t], POS[nums[t]], r + 1))
    print(f"  Ultimos 24 sorteos: Top-3={a3}/24 (azar esperado ~1.9), Top-5={a5}/24 (azar esperado ~3.2)")
    for fch, h, an, r in det:
        print(f"    {fch} h{h:2d} -> '{an}'  rank={r}")
    # Prediccion para el objetivo
    p_obj = predecir(Cdict, G, claves[t_obj], t_obj, s)
    order = np.argsort(-p_obj)
    print(f"\n  PREDICCION 2026-09-14 h8 (cluster clave={claves[t_obj]}, dow={dow[t_obj]}):")
    for j in order[:8]:
        print(f"    '{POS[j]}'  p={p_obj[j]:.4f}")
    return order, p_obj

llA, halfA, sA = mejores_A[0][0], mejores_A[0][1], mejores_A[0][2]
llB, halfB, sB = mejores_B[0][0], mejores_B[0][1], mejores_B[0][2]
print(f"\nMejor validacion: A ll={llA:.4f} (half={halfA},s={sA}) | B ll={llB:.4f} (half={halfB},s={sB})")
en_prueba(claves_h, halfA, sA, "Modelo A (hora)")
en_prueba(claves_wh, halfB, sB, "Modelo B (dow x hora)")
