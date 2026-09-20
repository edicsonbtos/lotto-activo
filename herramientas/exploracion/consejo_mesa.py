# -*- coding: utf-8 -*-
"""MESA DEL CONSEJO: 5 estrategias predicen el PROXIMO sorteo (2026-09-15 hora 0).
A=intradia con decaimiento, B=Markov orden 1 con backoff a hora,
C=frecuencia x hazard (atrasos), D=ensamble de produccion, E=frecuencia reciente.
Validacion walk-forward estricta: seleccion de hiperparametros en [N-2000,N-1000),
metricas reportadas en [N-1000,N). NO modifica ningun archivo.
"""
import json, math, os, sys
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))

POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {a: i for i, a in enumerate(POS)}
K = 38
BASE = 1.0 / K
FECHA_OBJ, HORA_OBJ = None, None   # se calculan tras cargar el historial

fechas, horas_l, nums_l = [], [], []
with open(os.path.join(RAIZ, "historial.txt"), encoding="utf-8") as f:
    for ln in f:
        p = ln.split()
        if len(p) == 3 and p[2] in IDX:
            fechas.append(p[0]); horas_l.append(int(p[1])); nums_l.append(IDX[p[2]])
A = np.array(nums_l); H = np.array(horas_l); N = len(A)
# proximo sorteo: dinamico (el siguiente al ultimo registrado)
from datetime import date as _date, timedelta as _td
_f = _date.fromisoformat(fechas[-1])
if H[-1] < 11:
    FECHA_OBJ, HORA_OBJ = fechas[-1], int(H[-1]) + 1
else:
    FECHA_OBJ, HORA_OBJ = str(_f + _td(days=1)), 0
print(f"N={N}  ultimo={fechas[-1]} h{H[-1]} '{POS[A[-1]]}'  -> objetivo {FECHA_OBJ} h{HORA_OBJ}")

SEL = (N - 2000, N - 1000)
TES = (N - 1000, N)
KS = (1, 3, 5, 10)

def nueva_bolsa():
    return {w: {"ll": 0.0, "n": 0, "hits": {k: 0 for k in KS}} for w in ("sel", "tes")}

def apuntar(bolsa, t, p, y):
    w = "sel" if SEL[0] <= t < SEL[1] else ("tes" if TES[0] <= t < TES[1] else None)
    if w is None:
        return
    b = bolsa[w]
    b["ll"] += math.log(max(p[y], 1e-15)); b["n"] += 1
    orden = np.argsort(-p)
    for k in KS:
        b["hits"][k] += int(y in orden[:k])

def reporte(nombre, bolsa):
    b = bolsa["tes"]; n = max(b["n"], 1)
    r = {k: b["hits"][k] / n for k in KS}
    print(f"  {nombre:<26} Top1 {r[1]*100:5.2f}%  Top3 {r[3]*100:5.2f}% ({b['hits'][3]:>3}/{n})  "
          f"Top5 {r[5]*100:5.2f}%  Top10 {r[10]*100:5.2f}%")
    return r

# ---------------------------------------------------------------- A: intradia
print("\n== A: intradia (hora, decaimiento exponencial + suavizado global) ==")
HALVES, SS = [360, 720, 1440], [5, 10, 20]
resA = {}
for half in HALVES:
    d = 0.5 ** (1.0 / half)
    C = np.zeros((12, K)); G = np.zeros(K)
    bolsas = {s: nueva_bolsa() for s in SS}
    for t in range(N):
        C *= d; G *= d
        gs = G.sum()
        if t >= SEL[0]:
            prior = G / gs if gs > 0 else np.full(K, BASE)
            for s in SS:
                v = C[H[t]] + s * prior
                apuntar(bolsas[s], t, v / v.sum(), A[t])
        C[H[t], A[t]] += 1.0; G[A[t]] += 1.0
    resA[half] = bolsas
mejorA = max(((b["sel"]["ll"], half, s) for half in HALVES for s, b in resA[half].items()))
_, halfA, sA = mejorA
print(f"  elegido por validacion: half={halfA} s={sA} (ll_sel={mejorA[0]/1000:.4f})")
reporte(f"A(half={halfA},s={sA})", resA[halfA][sA])
d = 0.5 ** (1.0 / halfA)
C = np.zeros((12, K)); G = np.zeros(K)
for t in range(N):
    C *= d; G *= d
    C[H[t], A[t]] += 1.0; G[A[t]] += 1.0
C *= d; G *= d
prior = G / G.sum()
v = C[HORA_OBJ] + sA * prior
pA = v / v.sum()

# ---------------------------------------------------------------- B: Markov
print("\n== B: Markov orden 1 (backoff a distribucion de la hora) ==")
A0, A1S = 50.0, [50, 100, 200, 400]
trans = np.zeros((K, K)); hc = np.zeros((12, K)); gc = np.zeros(K)
bolsasB = {a1: nueva_bolsa() for a1 in A1S}
for t in range(N):
    if t >= SEL[0]:
        pg = gc / gc.sum()
        pb = (hc[H[t]] + A0 * pg) / (hc[H[t]].sum() + A0)
        m1 = trans[A[t - 1]]
        for a1 in A1S:
            v = m1 + a1 * pb
            apuntar(bolsasB[a1], t, v / v.sum(), A[t])
    gc[A[t]] += 1.0; hc[H[t], A[t]] += 1.0
    if t >= 1:
        trans[A[t - 1], A[t]] += 1.0
mejorB = max(((b["sel"]["ll"], a1) for a1, b in bolsasB.items()))
_, a1B = mejorB
print(f"  elegido por validacion: a1={a1B} (backoff hora a0={A0:.0f})  (ll_sel={mejorB[0]/1000:.4f})")
reporte(f"B(markov a1={a1B})", bolsasB[a1B])
pg = gc / gc.sum()
pb = (hc[HORA_OBJ] + A0 * pg) / (hc[HORA_OBJ].sum() + A0)
v = trans[A[N - 1]] + a1B * pb
pB = v / v.sum()

# ---------------------------------------------------------------- C: hazard
print("\n== C: atrasos (frecuencia ventana x multiplicador hazard) ==")
gap = np.zeros((N, K), dtype=np.int32)
HIT = np.zeros((N, K), dtype=bool)
HIT[np.arange(N), A] = True
last = np.full(K, -1, dtype=np.int64)
for t in range(N):
    seen = last >= 0
    gap[t, seen] = (t - last[seen]).astype(np.int32)
    gap[t, ~seen] = 10 ** 6
    last[A[t]] = t
EDGES = np.array([5, 10, 15, 20, 30, 40, 60, 80, 120, 200])
NBIN = len(EDGES) + 1
BURN, ALPHA_HZ, W_FREQ, REFIT = 500, 8000.0, 1500, 25
# Bins de atraso precalculados una sola vez (int8) y conteos acumulados por fila:
# en cada refit el hazard se arma restando dos filas de cum_*, en vez de volver a
# aplanar y digitalizar gap[BURN:t] (eso pedia varios MB por refit y reventaba
# con MemoryError en equipos con poca RAM libre). Los numeros son identicos.
BIN = np.empty((N, K), dtype=np.int8)
cum_nb = np.zeros((N + 1, NBIN), dtype=np.int32)
cum_cb = np.zeros((N + 1, NBIN), dtype=np.int32)
for t in range(N):
    b = np.digitize(gap[t], EDGES)
    BIN[t] = b
    cum_nb[t + 1] = cum_nb[t] + np.bincount(b, minlength=NBIN)
    cum_cb[t + 1] = cum_cb[t] + np.bincount(b[HIT[t]], minlength=NBIN)

def hazard(hasta):
    """Hazard por bin con las filas [BURN, hasta) del historial (solo pasado)."""
    nb = (cum_nb[hasta] - cum_nb[BURN]).astype(float)
    cb = (cum_cb[hasta] - cum_cb[BURN]).astype(float)
    return (cb + ALPHA_HZ * BASE) / (nb + ALPHA_HZ)

hz_tab, last_refit = None, -10 ** 9
bolsasC = {m: nueva_bolsa() for m in ("M1_freq", "M2_hazard", "M3_freq_x_hz")}
for t in range(SEL[0], N):
    if hz_tab is None or t - last_refit >= REFIT:
        hz_tab = hazard(t)
        last_refit = t
    a = max(0, t - W_FREQ)
    f = (HIT[a:t].sum(axis=0) + 1.0) / (t - a + K)
    mult = hz_tab[BIN[t]] / BASE
    apuntar(bolsasC["M1_freq"], t, f / f.sum(), A[t])
    p2 = BASE * mult; apuntar(bolsasC["M2_hazard"], t, p2 / p2.sum(), A[t])
    p3 = f * mult; apuntar(bolsasC["M3_freq_x_hz"], t, p3 / p3.sum(), A[t])
mejorC = max(bolsasC, key=lambda m: bolsasC[m]["sel"]["ll"])
for m in bolsasC:
    reporte(f"C-{m}" + ("  <- elegido" if m == mejorC else ""), bolsasC[m])
# prediccion para el objetivo (t = N)
last = np.full(K, -1, dtype=np.int64)
for t in range(N):
    last[A[t]] = t
atrasoN = np.where(last >= 0, N - last, 10 ** 6)
hzN = hazard(N)
fN = (HIT[N - W_FREQ:N].sum(axis=0) + 1.0) / (W_FREQ + K)
multN = hzN[np.digitize(atrasoN, EDGES)] / BASE
if mejorC == "M1_freq":
    vC = fN
elif mejorC == "M2_hazard":
    vC = BASE * multN
else:
    vC = fN * multN
pC = vC / vC.sum()

# ---------------------------------------------------------------- E: reciente
print("\n== E: frecuencia reciente (ventana + prior global) ==")
WS = [24, 48, 84, 168]
bolsasE = {w: nueva_bolsa() for w in WS}
gcE = np.zeros(K)
from collections import deque
cola = deque()
for t in range(N):
    if t >= SEL[0]:
        for w in WS:
            pass  # se calcula abajo con ventanas mantenidas
    gcE[A[t]] += 1.0
# ventanas mantenidas por w
cw = {w: np.zeros(K) for w in WS}
qs = {w: deque() for w in WS}
gcE = np.zeros(K)
for t in range(N):
    if t >= SEL[0]:
        for w in WS:
            v = cw[w] + 0.05 * (gcE + 1.0)
            apuntar(bolsasE[w], t, v / v.sum(), A[t])
    y = A[t]
    gcE[y] += 1.0
    for w in WS:
        cw[w][y] += 1.0; qs[w].append(y)
        if len(qs[w]) > w:
            cw[w][qs[w].popleft()] -= 1.0
mejorE = max(((b["sel"]["ll"], w) for w, b in bolsasE.items()))
_, wE = mejorE
print(f"  elegido por validacion: ventana={wE}")
reporte(f"E(reciente w={wE})", bolsasE[wE])
vE = cw[wE] + 0.05 * (gcE + 1.0)
pE = vE / vE.sum()

# ---------------------------------------------------------------- D: ensamble
print("\n== D: ensamble de produccion (intradia_v2+secuencia_v3+haz_v1) ==")
print("  calculando submodelos (puede tardar varios minutos)...", flush=True)
import lotto_eval as LE
datos = LE.cargar()
n_d = len(datos)
from datetime import date
d0 = date.fromisoformat(datos.fecha[0])
fobj = date.fromisoformat(FECHA_OBJ)
ext = LE.Datos(np.r_[datos.seq, 0], np.r_[datos.hora, HORA_OBJ],
               np.r_[datos.dow, fobj.weekday()], np.r_[datos.dia, (fobj - d0).days],
               list(datos.fecha) + [FECHA_OBJ])
pj = json.load(open(os.path.join(RAIZ, "pesos_ensamble.json"), encoding="utf-8"))
w_ens = np.array(pj["pesos"])
ARRANQUE, R = 1000, 250
T = ARRANQUE + ((n_d - ARRANQUE) // R) * R
print(f"  bloque T={T}  pesos={np.round(w_ens, 3)}  vigente={pj['frontera'] == T}")
logs = []
for nombre in pj["base"]:
    sub = LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", nombre + ".py"))
    Pm = LE.normalizar(sub.predecir(ext, T))[-1]
    logs.append(np.log(np.clip(Pm, 1e-9, None)))
    print(f"  {nombre} ok", flush=True)
Lm = np.stack(logs)
Lm -= np.log(np.exp(Lm).sum(1, keepdims=True))
zz = w_ens @ Lm
zz -= zz.max()
pD = np.exp(zz); pD /= pD.sum()

# ---------------------------------------------------------------- verdicto
print("\n" + "=" * 78)
print(f"PREDICCIONES PARA {FECHA_OBJ} hora {HORA_OBJ} (proximo sorteo)")
print("=" * 78)
estrategias = {"A intradia": pA, "B markov": pB, f"C {mejorC}": pC, "D ensamble": pD, f"E reciente{wE}": pE}
votos = np.zeros(K, dtype=int)
pacum = np.zeros(K)
for nombre, p in estrategias.items():
    orden = np.argsort(-p)
    for i in orden[:3]:
        votos[i] += 1
    pacum += p / p.sum()
    top = "  ".join(f"{POS[i]}({p[i]*100:.1f})" for i in orden[:5])
    print(f"  {nombre:<16} top3: {[POS[i] for i in orden[:3]]}   top5: {top}")
pacum /= len(estrategias)
orden_c = np.argsort(-pacum)
print("\n-- CONSENSO (media de probabilidades de las 5 estrategias) --")
for r, i in enumerate(orden_c[:10], 1):
    print(f"  #{r:>2} {POS[i]:>3}  p_cons={pacum[i]*100:5.2f}%  votos_top3={votos[i]}/5")
