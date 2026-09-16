# -*- coding: utf-8 -*-
"""
CONSEJERO E - Explorador Libre / Abogado del Diablo
Explora multiples senales sobre historial.txt, valida walk-forward estricto
y entrega Top-3/Top-5 para 2026-09-14 hora 8.
"""
import math
from collections import defaultdict
from datetime import date

POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {a: i for i, a in enumerate(POS)}
N = len(POS)  # 38
UNIF = 1.0 / N

HIST = r"C:\Users\edics\Downloads\lotto-activo\lotto-activo\historial.txt"

# ---------- carga ----------
draws = []  # (fecha, hora, idx)
with open(HIST, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        d, h, a = line.split()
        draws.append((date.fromisoformat(d), int(h), IDX[a]))

T_TOTAL = len(draws)
# objetivo: predecir el sorteo 2026-09-14 hora 8 usando SOLO sorteos anteriores
TARGET = (date(2026, 9, 14), 8)
t_target = next(i for i, (d, h, _) in enumerate(draws) if (d, h) == TARGET)

weekdays = [d.weekday() for d, _, _ in draws]  # 0=lunes
hours = [h for _, h, _ in draws]
ys = [a for _, _, a in draws]

def chi2(counts, expected):
    return sum((c - e) ** 2 / e for c, e in zip(counts, expected))

print("=" * 70)
print("FASE 1: EXPLORACION (sobre todo el historial, solo diagnostico)")
print("=" * 70)

# 1) frecuencia global
g = [0] * N
for a in ys:
    g[a] += 1
exp = [T_TOTAL / N] * N
print(f"\n[Global] chi2 vs uniforme = {chi2(g, exp):.1f} (gl={N-1}, crit 95% ~ 52.2)")

# 2) por hora (12 x 38)
print("\n[Por hora] chi2 por hora (crit 95% ~ 52.2, gl=37):")
sig_horas = 0
for h in range(12):
    cnt = [0] * N
    nh = 0
    for i in range(T_TOTAL):
        if hours[i] == h:
            cnt[ys[i]] += 1
            nh += 1
    c2 = chi2(cnt, [nh / N] * N)
    if c2 > 52.2:
        sig_horas += 1
    print(f"  hora {h:2d}: n={nh:5d} chi2={c2:6.1f}{'  *' if c2 > 52.2 else ''}")
print(f"  -> horas 'significativas': {sig_horas}/12 (con 12 pruebas, esperas ~0.6 por azar)")

# 3) por dia de semana (7 x 38)
print("\n[Por dia de semana] chi2 (crit 95% ~ 52.2):")
sig_dias = 0
for w in range(7):
    cnt = [0] * N
    nw = 0
    for i in range(T_TOTAL):
        if weekdays[i] == w:
            cnt[ys[i]] += 1
            nw += 1
    c2 = chi2(cnt, [nw / N] * N)
    if c2 > 52.2:
        sig_dias += 1
    print(f"  dia {w}: n={nw:5d} chi2={c2:6.1f}{'  *' if c2 > 52.2 else ''}")
print(f"  -> dias 'significativos': {sig_dias}/7")

# 4) autocorrelacion: repeticion mismo animal lag-1 y mismo animal a la misma hora del dia anterior
rep1 = sum(1 for i in range(1, T_TOTAL) if ys[i] == ys[i - 1])
same_h_prev_day = 0
n_same_h = 0
for i in range(T_TOTAL):
    d, h, a = draws[i]
    for j in range(i - 1, max(0, i - 15), -1):
        if draws[j][0] != d or True:
            pass
    # buscar (d-1, h)
    pass
# mas simple: mapa (fecha,hora)->animal
m = {(d, h): a for (d, h, a) in draws}
from datetime import timedelta
sh = 0
sh_n = 0
for (d, h), a in m.items():
    k = (d - timedelta(days=1), h)
    if k in m:
        sh_n += 1
        if m[k] == a:
            sh += 1
print(f"\n[Repeticion lag-1] {rep1}/{T_TOTAL-1} = {rep1/(T_TOTAL-1)*100:.2f}% (azar {UNIF*100:.2f}%)")
print(f"[Mismo animal misma hora dia anterior] {sh}/{sh_n} = {sh/sh_n*100:.2f}% (azar {UNIF*100:.2f}%)")

# 5) calientes recientes: ultimos 24/48/84 sorteos vs historico
for W, nombre in [(24, "ultimos 24"), (48, "ultimos 48"), (84, "ultimos 7 dias")]:
    cnt = [0] * N
    for a in ys[-W:]:
        cnt[a] += 1
    c2 = chi2(cnt, [W / N] * N)
    print(f"[{nombre}] chi2={c2:.1f} (crit 95% 52.2)")

# 6) Markov: transicion desde el animal previo (38x38), chi2 por fila solo para filas frecuentes
print("\n[Markov lag-1] chi2 promedio por fila (diag, solo 5 filas mas frecuentes):")
trans = [[0] * N for _ in range(N)]
row_n = [0] * N
for i in range(1, T_TOTAL):
    trans[ys[i - 1]][ys[i]] += 1
    row_n[ys[i - 1]] += 1
sig_rows = 0
for r in range(N):
    if row_n[r] < 50:
        continue
    c2 = chi2(trans[r], [row_n[r] / N] * N)
    if c2 > 52.2:
        sig_rows += 1
print(f"  filas significativas: {sig_rows}/{N} (con 38 pruebas esperas ~1.9 por azar)")

print()
print("=" * 70)
print("FASE 2: VALIDACION WALK-FORWARD ESTRICTA (ultimos 1000 sorteos pre-target)")
print("=" * 70)

# extremos de validacion: predecir sorteos en [t_val_start, t_target) usando solo < t
VAL_N = 1000
t_val_start = t_target - VAL_N

def eval_signal(rank_fn, t0, t1):
    """rank_fn(t) -> lista de indices ordenada por prob desc, usando solo datos < t."""
    top1 = top3 = top5 = top10 = 0
    n = 0
    for t in range(t0, t1):
        ranking = rank_fn(t)
        y = ys[t]
        top1 += y in ranking[:1]
        top3 += y in ranking[:3]
        top5 += y in ranking[:5]
        top10 += y in ranking[:10]
        n += 1
    return top1, top3, top5, top10, n

def counts_before(t, cond=None, window=None):
    cnt = [0] * N
    lo = 0 if window is None else max(0, t - window)
    for i in range(lo, t):
        if cond is None or cond(i):
            cnt[ys[i]] += 1
    return cnt

def rank_from_probs(probs):
    return sorted(range(N), key=lambda a: -probs[a])

ALPHA = 1.0  # suavizado Dirichlet hacia uniforme

def mk_global(t):
    cnt = counts_before(t)
    tot = sum(cnt) + ALPHA * N
    return rank_from_probs([(c + ALPHA) / tot for c in cnt])

def mk_recent(W):
    def f(t):
        c_rec = counts_before(t, window=W)
        c_glob = counts_before(t)
        # mezcla: frecuencia reciente con pseudo-conteo global como prior
        probs = [(c_rec[a] + 0.05 * (c_glob[a] + ALPHA)) for a in range(N)]
        return rank_from_probs(probs)
    return f

def mk_hour(t):
    h = hours[t]
    cnt = counts_before(t, cond=lambda i: hours[i] == h)
    tot = sum(cnt) + ALPHA * N
    return rank_from_probs([(c + ALPHA) / tot for c in cnt])

def mk_weekday(t):
    w = weekdays[t]
    cnt = counts_before(t, cond=lambda i: weekdays[i] == w)
    tot = sum(cnt) + ALPHA * N
    return rank_from_probs([(c + ALPHA) / tot for c in cnt])

def mk_hour_weekday(t):
    h, w = hours[t], weekdays[t]
    cnt = counts_before(t, cond=lambda i: hours[i] == h and weekdays[i] == w)
    c_h = counts_before(t, cond=lambda i: hours[i] == h)
    # suavizado fuerte hacia la distribucion de la hora
    probs = [(cnt[a] + 0.5 * (c_h[a] + ALPHA)) for a in range(N)]
    return rank_from_probs(probs)

def mk_markov(t):
    prev = ys[t - 1]
    # transiciones observadas desde 'prev' en datos < t
    cnt = [0] * N
    for i in range(1, t):
        if ys[i - 1] == prev:
            cnt[ys[i]] += 1
    c_glob = counts_before(t)
    probs = [(cnt[a] + 0.2 * (c_glob[a] + ALPHA)) for a in range(N)]
    return rank_from_probs(probs)

def p_binom(k, n, p):
    # p-valor unilateral (>=k aciertos) bajo Binomial(n,p)
    from math import comb
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))

signals = [
    ("S0 frecuencia global", mk_global),
    ("S1a calientes 24", mk_recent(24)),
    ("S1b calientes 48", mk_recent(48)),
    ("S1c calientes 84", mk_recent(84)),
    ("S1d calientes 168", mk_recent(168)),
    ("S2 por hora", mk_hour),
    ("S3 por dia semana", mk_weekday),
    ("S4 hora+dia", mk_hour_weekday),
    ("S5 Markov lag-1", mk_markov),
]

results = []
print(f"\nValidando {len(signals)} senales en sorteos [{t_val_start},{t_target})  (n={VAL_N})")
for name, fn in signals:
    t1, t3, t5, t10, n = eval_signal(fn, t_val_start, t_target)
    p3 = p_binom(t3, n, 3 / N)
    results.append((name, t1, t3, t5, t10, n, p3))
    print(f"  {name:22s} Top1={t1/n*100:5.2f}% Top3={t3/n*100:5.2f}% "
          f"Top5={t5/n*100:5.2f}% Top10={t10/n*100:5.2f}%  p(Top3)={p3:.3f}")

print("\nAzar: Top1=2.63% Top3=7.89% Top5=13.16% Top10=26.32%")
print(f"Correccion de seleccion: probe {len(signals)} senales -> umbral p ~ {0.05/len(signals):.4f}")

print()
print("=" * 70)
print("FASE 3: ULTIMOS 24 SORTEOS PRE-TARGET (Top-3 / Top-5)")
print("=" * 70)
# para la senal elegida (se decide tras ver resultados; aqui evaluamos todas en 24)
for name, fn in signals:
    t1, t3, t5, t10, n = eval_signal(fn, t_target - 24, t_target)
    print(f"  {name:22s} Top3={t3}/24 Top5={t5}/24")

print()
print("=" * 70)
print("FASE 4: PREDICCION PARA 2026-09-14 hora 8 (solo datos < t_target)")
print("=" * 70)

def probs_global(t):
    cnt = counts_before(t)
    tot = sum(cnt) + ALPHA * N
    return [(c + ALPHA) / tot for c in cnt]

pg = probs_global(t_target)
rank = rank_from_probs(pg)
print("\nTop-5 por frecuencia global suavizada (mal menor):")
for k, a in enumerate(rank[:5], 1):
    print(f"  {k}. animal {POS[a]:>2s}  p={pg[a]*100:.2f}%")

# tambien mostrar Top-5 de cada senal para el target, por transparencia
print("\nTop-3 del target segun cada senal:")
for name, fn in signals:
    r = fn(t_target)
    print(f"  {name:22s} -> {[POS[a] for a in r[:3]]}")

# NOTA de fuga: el archivo ya contiene el resultado del target
print(f"\n[FUGA DETECTADA] historial.txt YA contiene sorteos posteriores al target:")
for t in range(t_target, min(t_target + 3, T_TOTAL)):
    d, h, a = draws[t]
    print(f"  {d} hora {h} -> {POS[a]}")
print("  La prediccion de arriba NO uso esos datos (t_target excluido).")
