# -*- coding: utf-8 -*-
"""
CONSEJERO A - "Cronista Intradia"
Estrategia: p(animal | hora del sorteo) con decaimiento exponencial por recencia,
suavizado tipo Dirichlet hacia la frecuencia global (tambien decaido).
Variante B: interaccion dia-de-semana x hora, suavizado anidado hacia la hora.
Validacion walk-forward ESTRICTA: predecir t solo con sorteos < t.
Hiperparametros (vida media, suavizado) elegidos por walk-forward en ventana de
SELECCION y evaluados en ventana de TEST disjunta (sin reutilizar datos).
"""
import math
from datetime import date

import numpy as np

POS = ["0", "00"] + [str(i) for i in range(1, 37)]
N_A = len(POS)          # 38
N_H = 12
IDX = {a: i for i, a in enumerate(POS)}

# ---------------- carga ----------------
fechas, horas, animales = [], [], []
with open("historial.txt", encoding="utf-8") as f:
    for linea in f:
        linea = linea.strip()
        if not linea:
            continue
        d, h, a = linea.split()
        fechas.append(date.fromisoformat(d))
        horas.append(int(h))
        animales.append(IDX[a])

horas = np.array(horas)
animales = np.array(animales)
wd = np.array([d.weekday() for d in fechas])  # 0=lunes
N = len(animales)
print(f"Sorteos cargados: {N}  |  ultimo: {fechas[-1]} hora {horas[-1]} -> {POS[animales[-1]]}")

# ---------------- modelo ----------------
def predecir_probs(counts_h, counts_g, alpha):
    """counts_h: (12,38) pesos decaidos por hora; counts_g: (38,) global decaido.
    Suavizado Dirichlet: p_h = (w_h + alpha * g) / (W_h + alpha)."""
    g = counts_g / counts_g.sum()
    W = counts_h.sum(axis=1, keepdims=True)
    return (counts_h + alpha * g[None, :]) / (W + alpha)

def predecir_probs_dwh(counts_dwh, p_h, beta):
    """counts_dwh: (7,12,38); suavizado anidado hacia la distribucion de la hora."""
    W = counts_dwh.sum(axis=2, keepdims=True)
    return (counts_dwh + beta * p_h[None, :, :]) / (W + beta)

def walk_forward(half_life, alpha, ini, fin, variante="hora", beta=None):
    """Devuelve aciertos top-k y log-verosimilitud para t en [ini, fin).
    Estado = pesos decaidos de TODOS los sorteos < ini, actualizado paso a paso."""
    dec = 0.5 ** (1.0 / half_life)
    counts_h = np.zeros((N_H, N_A))
    counts_g = np.zeros(N_A)
    counts_dwh = np.zeros((7, N_H, N_A)) if variante == "dwh" else None
    # estado inicial con sorteos [0, ini)
    for t in range(ini):
        counts_h *= dec; counts_g *= dec
        a, h = animales[t], horas[t]
        counts_h[h, a] += 1.0; counts_g[a] += 1.0
        if variante == "dwh":
            counts_dwh *= dec; counts_dwh[wd[t], h, a] += 1.0
    hits = {1: 0, 3: 0, 5: 0, 10: 0}
    ll = 0.0
    for t in range(ini, fin):
        counts_h *= dec; counts_g *= dec
        if variante == "dwh":
            counts_dwh *= dec
        p_h = predecir_probs(counts_h, counts_g, alpha)
        if variante == "dwh":
            p = predecir_probs_dwh(counts_dwh, p_h, beta)[wd[t], horas[t]]
        else:
            p = p_h[horas[t]]
        a = animales[t]
        orden = np.argsort(-p)
        for k in hits:
            if a in orden[:k]:
                hits[k] += 1
        ll += math.log(max(p[a], 1e-12))
        # revelar sorteo t
        counts_h[horas[t], a] += 1.0; counts_g[a] += 1.0
        if variante == "dwh":
            counts_dwh[wd[t], horas[t], a] += 1.0
    n = fin - ini
    return {k: v / n for k, v in hits.items()}, ll / n, n

# ---------------- prueba de senal: chi-cuadrado hora x animal ----------------
tabla = np.zeros((N_H, N_A))
for h, a in zip(horas, animales):
    tabla[h, a] += 1
esp = tabla.sum(axis=1, keepdims=True) * tabla.sum(axis=0, keepdims=True) / tabla.sum()
chi2 = ((tabla - esp) ** 2 / esp).sum()
gl = (N_H - 1) * (N_A - 1)
print(f"\nChi2 hora x animal = {chi2:.1f} (gl={gl}, media esperada bajo nula={gl})")
print(f"Exceso sobre la nula: {chi2 - gl:+.1f}  (~z={(chi2-gl)/math.sqrt(2*gl):+.2f} sigma)")

# ---------------- seleccion de hiperparametros ----------------
# Ventana de SELECCION: sorteos [N-3500, N-1500) ; Ventana de TEST: [N-1000, N)
# (hueco de 500 entre ambas para no solapar seleccion con evaluacion)
SEL_INI, SEL_FIN = N - 3500, N - 1500
TST_INI, TST_FIN = N - 1000, N
half_lives = [30, 60, 120, 250, 500, 1000, 2000, 5000]
alphas = [1, 3, 10, 30, 100, 300, 1000]
betas = [3, 10, 30, 100, 300]

print(f"\nVentana SELECCION: [{SEL_INI},{SEL_FIN}) n={SEL_FIN-SEL_INI}  ({fechas[SEL_INI]} .. {fechas[SEL_FIN-1]})")
print(f"Ventana TEST:      [{TST_INI},{TST_FIN}) n={TST_FIN-TST_INI}  ({fechas[TST_INI]} .. {fechas[TST_FIN-1]})")

# Baseline: frecuencia global pura con decaimiento (sin condicionar por hora)
def walk_forward_global(half_life, alpha, ini, fin):
    dec = 0.5 ** (1.0 / half_life)
    counts_g = np.zeros(N_A)
    for t in range(ini):
        counts_g *= dec; counts_g[animales[t]] += 1.0
    hits = {1: 0, 3: 0, 5: 0, 10: 0}; ll = 0.0
    for t in range(ini, fin):
        counts_g *= dec
        p = (counts_g + alpha / N_A) / (counts_g.sum() + alpha)
        a = animales[t]; orden = np.argsort(-p)
        for k in hits:
            if a in orden[:k]: hits[k] += 1
        ll += math.log(max(p[a], 1e-12))
        counts_g[a] += 1.0
    n = fin - ini
    return {k: v / n for k, v in hits.items()}, ll / n

# grid variante hora
mejor_h = None
resultados_grid = []
for hl in half_lives:
    for al in alphas:
        tasas, ll, _ = walk_forward(hl, al, SEL_INI, SEL_FIN, "hora")
        resultados_grid.append((ll, tasas[3], hl, al))
        if mejor_h is None or ll > mejor_h[0]:
            mejor_h = (ll, hl, al, tasas)
resultados_grid.sort(reverse=True)
print("\nTop-5 configs (variante HORA) por log-verosimilitud en SELECCION:")
for ll, t3, hl, al in resultados_grid[:5]:
    print(f"  HL={hl:>5} alpha={al:>5}  LL={ll:.4f}  Top3={t3*100:.2f}%")
ll_h, HL_H, AL_H, tasas_sel_h = mejor_h
print(f"Elegida HORA: half-life={HL_H}, alpha={AL_H}  (LL={ll_h:.4f})")

# grid variante dia-semana x hora (fijando HL y alpha de la hora, barriendo beta)
mejor_d = None
for beta in betas:
    tasas, ll, _ = walk_forward(HL_H, AL_H, SEL_INI, SEL_FIN, "dwh", beta)
    print(f"  DWH beta={beta:>4}: LL={ll:.4f} Top3={tasas[3]*100:.2f}%")
    if mejor_d is None or ll > mejor_d[0]:
        mejor_d = (ll, beta, tasas)
ll_d, BETA_D, tasas_sel_d = mejor_d
usa_dwh = ll_d > ll_h
print(f"Mejor DWH: beta={BETA_D} LL={ll_d:.4f}  -> {'SE USA DWH' if usa_dwh else 'NO mejora: se usa variante HORA simple'}")

# baseline global en seleccion
bg_ll_mejor = -1e9; bg_conf = None
for hl in half_lives:
    for al in alphas:
        tasas, ll = walk_forward_global(hl, al, SEL_INI, SEL_FIN)
        if ll > bg_ll_mejor:
            bg_ll_mejor, bg_conf = ll, (hl, al, tasas)
print(f"Baseline GLOBAL (sin hora): HL={bg_conf[0]}, alpha={bg_conf[1]}, LL={bg_ll_mejor:.4f}, Top3={bg_conf[2][3]*100:.2f}%")
print(f"Diferencia LL (mi modelo - global): {(ll_d if usa_dwh else ll_h) - bg_ll_mejor:+.5f} por sorteo")

# ---------------- evaluacion final en TEST (datos no usados para elegir) ----------------
variante = "dwh" if usa_dwh else "hora"
tasas_test, ll_test, n_test = walk_forward(HL_H, AL_H, TST_INI, TST_FIN, variante, BETA_D if usa_dwh else None)
tasas_test_g, _ = walk_forward_global(bg_conf[0], bg_conf[1], TST_INI, TST_FIN)
azar = {1: 1/38, 3: 3/38, 5: 5/38, 10: 10/38}
print("\n===== TEST walk-forward (ultimos 1000 sorteos, hiperparametros ya fijados) =====")
print(f"Variante: {'DIA-SEMANA x HORA' if usa_dwh else 'HORA'}  HL={HL_H} alpha={AL_H}" + (f" beta={BETA_D}" if usa_dwh else ""))
for k in (1, 3, 5, 10):
    n_hit = round(tasas_test[k] * n_test)
    z = (tasas_test[k] - azar[k]) / math.sqrt(azar[k] * (1 - azar[k]) / n_test)
    print(f"  Top-{k:<2}: {tasas_test[k]*100:6.2f}% ({n_hit}/{n_test})  azar={azar[k]*100:5.2f}%  z={z:+.2f}  | baseline global: {tasas_test_g[k]*100:6.2f}%")
print(f"  LL medio: {ll_test:.4f} (azar uniforme: {math.log(1/38):.4f})")

# ---------------- ultimos 24 sorteos ----------------
ini24 = N - 24
tasas24, _, _ = walk_forward(HL_H, AL_H, ini24, N, variante, BETA_D if usa_dwh else None)
print("\n===== Ultimos 24 sorteos =====")
print(f"  Top-3: {round(tasas24[3]*24)}/24   Top-5: {round(tasas24[5]*24)}/24   (azar: 1.9/24 y 3.2/24)")
print("  (NOTA: estos 24 incluyen sorteos ya usados en TEST; es solo un chequeo reciente)")

# ---------------- prediccion para 2026-09-14 hora 8 ----------------
# Objetivo estricto: solo sorteos ANTES de la linea '2026-09-14 8'.
t_obj = None
for t in range(N - 1, -1, -1):
    if str(fechas[t]) == "2026-09-14" and horas[t] == 8:
        t_obj = t
        break
print(f"\nPrediccion para el sorteo indice {t_obj} ({fechas[t_obj]} hora {horas[t_obj]}); "
      f"entrenando solo con sorteos [0,{t_obj})")

dec = 0.5 ** (1.0 / HL_H)
counts_h = np.zeros((N_H, N_A)); counts_g = np.zeros(N_A)
counts_dwh = np.zeros((7, N_H, N_A)) if usa_dwh else None
for t in range(t_obj):
    counts_h *= dec; counts_g *= dec
    a, h = animales[t], horas[t]
    counts_h[h, a] += 1.0; counts_g[a] += 1.0
    if usa_dwh:
        counts_dwh *= dec; counts_dwh[wd[t], h, a] += 1.0
p_h = predecir_probs(counts_h, counts_g, AL_H)
if usa_dwh:
    p = predecir_probs_dwh(counts_dwh, p_h, BETA_D)[wd[t_obj], 8]
else:
    p = p_h[8]
orden = np.argsort(-p)
print("\nTOP-5 para 2026-09-14 hora 8:")
for r, idx in enumerate(orden[:5], 1):
    print(f"  {r}. animal {POS[idx]:>3}  p={p[idx]*100:.2f}%")
print(f"\nDia de semana del objetivo: {wd[t_obj]} (0=lunes)")
print(f"Valor real registrado en el archivo para ese sorteo (NO usado): {POS[animales[t_obj]]}")
