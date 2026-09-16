# Consejero B "Secuencialista": Markov orden 1/2 con backoff Dirichlet.
# Walk-forward ESTRICTO: para predecir el sorteo t solo se usan sorteos < t.
# NOTA ANTI-FUGA: historial.txt contiene sorteos posteriores al objetivo
# (2026-09-14 hora 8 y 9). Se truncan: todo indice >= idx_target queda excluido
# de entrenamiento y de evaluacion.
import numpy as np
from math import log
from scipy.stats import binom

RUTA = r"C:\Users\edics\Downloads\lotto-activo\lotto-activo\historial.txt"
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
K = 38
TARGET_FECHA, TARGET_HORA = "2026-09-14", 8

fechas, horas, nums = [], [], []
with open(RUTA, encoding="utf-8") as f:
    for linea in f:
        linea = linea.strip()
        if not linea:
            continue
        d, h, n = linea.split()
        fechas.append(d); horas.append(int(h)); nums.append(POS.index(n))

A = np.array(nums, dtype=np.int64)
H = np.array(horas, dtype=np.int64)
N = len(A)

idx_target = next(i for i in range(N) if fechas[i] == TARGET_FECHA and H[i] == TARGET_HORA)
print(f"Sorteos totales en archivo: {N}; indice objetivo ({TARGET_FECHA} h{TARGET_HORA}): {idx_target}")
print(f"ANTI-FUGA: se ignoran {N - idx_target} sorteos del archivo (indices >= {idx_target}).")
print(f"Contexto real usado: hora6={POS[A[idx_target-3]]}, hora7(prev)={POS[A[idx_target-2]]} -> predecir hora8")

# Claves de transicion (target indexado en j):
# keys1[j-1] = transicion (A[j-1] -> A[j]); keys2[j-2] = ((A[j-2],A[j-1]) -> A[j])
keys1 = A[:-1] * K + A[1:]
keys2 = (A[:-2] * K + A[1:-1]) * K + A[2:]

def conteos_para(t):
    """Devuelve (g, h, m1, m2, prev1, prev2) usando solo sorteos < t."""
    g = np.bincount(A[:t], minlength=K).astype(np.float64)
    mask_h = H[:t] == H[t]
    h = np.bincount(A[:t][mask_h], minlength=K).astype(np.float64)
    c1 = np.bincount(keys1[:t - 1], minlength=K * K)
    prev1 = A[t - 1]
    m1 = c1[prev1 * K:(prev1 + 1) * K].astype(np.float64)
    prev2 = A[t - 2]
    ctx = prev2 * K + prev1
    c2 = np.bincount(keys2[:t - 2], minlength=K * K * K)
    m2 = c2[ctx * K:(ctx + 1) * K].astype(np.float64)
    return g, h, m1, m2, prev1, prev2

def p_global(g):
    return g / g.sum()

def p_hour(g, h, a0):
    pg = p_global(g)
    return (h + a0 * pg) / (h.sum() + a0)

def p_m1(m1, p_back, a1):
    return (m1 + a1 * p_back) / (m1.sum() + a1)

def p_m2(m2, p_back1, a2):
    return (m2 + a2 * p_back1) / (m2.sum() + a2)

# ---------------- Seleccion de hiperparametros (ventana [-2000,-1000)) ----------------
SEL = range(idx_target - 2000, idx_target - 1000)
TEST = range(idx_target - 1000, idx_target)          # ultimos 1000 sorteos estrictos
ULT24 = range(idx_target - 24, idx_target)

cache = {}
def datos(t):
    if t not in cache:
        cache[t] = conteos_para(t)
    return cache[t]

def loglike_sel(fn):
    s, n = 0.0, 0
    for t in SEL:
        p = fn(datos(t))
        s += log(max(p[A[t]], 1e-12)); n += 1
    return s / n

# 1) suavizado de la distribucion por hora
mejor_a0, mejor_ll = None, -1e18
for a0 in [5, 10, 25, 50, 100, 200, 500]:
    ll = loglike_sel(lambda d, a0=a0: p_hour(d[0], d[1], a0))
    print(f"  hora a0={a0:<5} loglik_sel={ll:.4f}")
    if ll > mejor_ll: mejor_ll, mejor_a0 = ll, a0
print(f"mejor a0 = {mejor_a0}")

# 2) Markov orden 1: backoff global vs hora
cand_m1 = []
for back in ["global", "hora"]:
    for a1 in [5, 10, 20, 50, 100, 200, 500, 1000]:
        if back == "global":
            fn = lambda d, a1=a1: p_m1(d[2], p_global(d[0]), a1)
        else:
            fn = lambda d, a1=a1: p_m1(d[2], p_hour(d[0], d[1], mejor_a0), a1)
        ll = loglike_sel(fn)
        cand_m1.append((ll, back, a1))
        print(f"  m1 back={back:<6} a1={a1:<5} loglik_sel={ll:.4f}")
cand_m1.sort(reverse=True)
ll_m1, back_m1, a1_m1 = cand_m1[0]
print(f"mejor M1: back={back_m1} a1={a1_m1} loglik={ll_m1:.4f}")

def fn_m1(d):
    pb = p_global(d[0]) if back_m1 == "global" else p_hour(d[0], d[1], mejor_a0)
    return p_m1(d[2], pb, a1_m1)

# 3) Markov orden 2 con backoff al mejor M1
mejor_a2, ll_m2 = None, -1e18
for a2 in [20, 50, 100, 200, 500, 1000, 2000]:
    ll = loglike_sel(lambda d, a2=a2: p_m2(d[3], fn_m1(d), a2))
    print(f"  m2 a2={a2:<5} loglik_sel={ll:.4f}")
    if ll > ll_m2: ll_m2, mejor_a2 = ll, a2
print(f"mejor a2 = {mejor_a2} (loglik={ll_m2:.4f} vs M1 {ll_m1:.4f})")

usar_m2 = ll_m2 > ll_m1 + 1e-4  # exigir mejora real, no ruido
def fn_final(d):
    p1 = fn_m1(d)
    return p_m2(d[3], p1, mejor_a2) if usar_m2 else p1

print(f"\nModelo elegido: {'M2(a2=%s) sobre ' % mejor_a2 if usar_m2 else ''}M1(back={back_m1}, a1={a1_m1}), hora a0={mejor_a0}")

# ---------------- Evaluacion walk-forward en ventana de TEST (ultimos 1000) ----------------
def evaluar(fn, ventana):
    tops = {1: 0, 3: 0, 5: 0, 10: 0}
    n = 0
    for t in ventana:
        p = fn(datos(t))
        orden = np.argsort(-p)
        real = A[t]
        for k in tops:
            if real in orden[:k]:
                tops[k] += 1
        n += 1
    return tops, n

modelos = {
    "global": lambda d: p_global(d[0]),
    "hora": lambda d: p_hour(d[0], d[1], mejor_a0),
    "M1": fn_m1,
    "FINAL": fn_final,
}
print(f"\n=== Walk-forward TEST (ultimos {len(list(TEST))} sorteos, estricto) ===")
for nombre, fn in modelos.items():
    tops, n = evaluar(fn, TEST)
    r = {k: tops[k] / n for k in tops}
    pval3 = binom.sf(tops[3] - 1, n, 3 / K)
    print(f"{nombre:<7} Top-1 {r[1]*100:5.2f}% ({tops[1]:>3}/{n})  "
          f"Top-3 {r[3]*100:5.2f}% ({tops[3]:>3}/{n})  "
          f"Top-5 {r[5]*100:5.2f}% ({tops[5]:>3}/{n})  "
          f"Top-10 {r[10]*100:5.2f}%  | p-val Top3 vs azar: {pval3:.3f}")

print("\nAzar teorico: Top-1 2.63% | Top-3 7.89% | Top-5 13.16% | Top-10 26.32%")

# ---------------- Ultimos 24 sorteos ----------------
tops24, n24 = evaluar(fn_final, ULT24)
print(f"\nUltimos 24 sorteos (modelo FINAL): Top-3 {tops24[3]}/24, Top-5 {tops24[5]}/24")

# ---------------- Prediccion para 2026-09-14 hora 8 ----------------
d = datos(idx_target)
p = fn_final(d)
orden = np.argsort(-p)
print(f"\n=== PREDICCION {TARGET_FECHA} hora {TARGET_HORA} (prev={POS[A[idx_target-1]]}, prev2={POS[A[idx_target-2]]}) ===")
for i in orden[:5]:
    print(f"  {POS[i]:>3}: {p[i]*100:5.2f}%")
