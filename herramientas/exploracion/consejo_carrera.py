# -*- coding: utf-8 -*-
"""CARRERA A CIEGAS 1 ANO: 4 predictores compiten prediciendo CADA sorteo de
los ultimos 365 dias usando solo datos pasados (walk-forward estricto).
  A intradia (hora, decaimiento) | B Markov | C hazard M3 | D ENSAMBLE produccion
  + baseline uniforme.
El ensamble corre con pesos reajustados cada 250 sorteos DENTRO de la ventana
(arranque=inicio de la ventana) -> sin fuga de pesos del futuro.
Salida: herramientas/resultados/carrera_1ano.txt y .json
"""
import json, math, os, sys, time
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

DIAS = 365
SORTEOS = DIAS * 12
K, HORAS = 38, 12
BASE = 1.0 / K
POS = LE.POS

datos = LE.cargar()
n = len(datos)
A, H = datos.seq, datos.hora
INI = n - SORTEOS
print(f"n={n}  carrera: sorteos [{INI},{n}) = {datos.fecha[INI]} .. {datos.fecha[-1]}", flush=True)

KS = (1, 3, 5, 10)
class Bolsa:
    def __init__(self):
        self.ll = 0.0; self.m = 0
        self.hits = {k: 0 for k in KS}
        self.mes = {}   # "AAAA-MM" -> [hits3, m]
    def apuntar(self, p, y, fecha):
        self.ll += math.log(max(p[y], 1e-15)); self.m += 1
        orden = np.argsort(-p)
        for k in KS:
            self.hits[k] += int(y in orden[:k])
        mm = fecha[:7]
        e = self.mes.setdefault(mm, [0, 0])
        e[0] += int(y in orden[:3]); e[1] += 1

# ---------------- A: intradia ----------------
halfA, sA = 1440.0, 20.0
dA = 0.5 ** (1.0 / halfA)
CA = np.zeros((HORAS, K)); GA = np.zeros(K)
for t in range(INI):
    CA *= dA; GA *= dA
    CA[H[t], A[t]] += 1.0; GA[A[t]] += 1.0
# ---------------- B: markov ----------------
a0B, a1B = 50.0, 400.0
transB = np.zeros((K, K)); hcB = np.zeros((HORAS, K)); gcB = np.zeros(K)
for t in range(1, INI):
    gcB[A[t]] += 1.0; hcB[H[t], A[t]] += 1.0
    transB[A[t - 1], A[t]] += 1.0
if INI >= 1:
    gcB[A[0]] += 1.0; hcB[H[0], A[0]] += 1.0
# ---------------- C: hazard M3 ----------------
gap = np.zeros((n, K), dtype=np.int32)
HIT = np.zeros((n, K), dtype=bool)
HIT[np.arange(n), A] = True
last = np.full(K, -1, dtype=np.int64)
for t in range(n):
    seen = last >= 0
    gap[t, seen] = (t - last[seen]).astype(np.int32)
    gap[t, ~seen] = 10 ** 6
    last[A[t]] = t
EDGES = np.array([5, 10, 15, 20, 30, 40, 60, 80, 120, 200])
BURN, ALPHA_HZ, W_FREQ, REFIT = 500, 8000.0, 1500, 25
# ---------------- D: ensamble ----------------
print("ensamble: calculando submodelos walk-forward (largo)...", flush=True)
t0 = time.time()
ens = LE.cargar_modelo(os.path.join(RAIZ, "herramientas", "modelos", "ensamble_v2.py"),
                       arranque=INI)
P_ens = LE.normalizar(ens.predecir(datos, INI))
print(f"ensamble listo en {(time.time()-t0)/60:.1f} min", flush=True)

# ---------------- carrera ----------------
bolsas = {k: Bolsa() for k in ("A intradia", "B markov", "C hazard", "D ensamble", "uniforme")}
hz_tab, last_refit = None, -10 ** 9
for j, t in enumerate(range(INI, n)):
    y = A[t]
    # A
    CA *= dA; GA *= dA
    v = CA[H[t]] + sA * GA / GA.sum()
    bolsas["A intradia"].apuntar(v / v.sum(), y, datos.fecha[t])
    CA[H[t], y] += 1.0; GA[y] += 1.0
    # B
    pg = gcB / gcB.sum()
    pb = (hcB[H[t]] + a0B * pg) / (hcB[H[t]].sum() + a0B)
    v = transB[A[t - 1]] + a1B * pb
    bolsas["B markov"].apuntar(v / v.sum(), y, datos.fecha[t])
    gcB[y] += 1.0; hcB[H[t], y] += 1.0
    transB[A[t - 1], y] += 1.0
    # C
    if hz_tab is None or t - last_refit >= REFIT:
        gg = gap[BURN:t].ravel(); hh = HIT[BURN:t].ravel()
        bb = np.digitize(gg, EDGES)
        nb = np.bincount(bb, minlength=len(EDGES) + 1).astype(float)
        cb = np.bincount(bb[hh], minlength=len(EDGES) + 1).astype(float)
        hz_tab = (cb + ALPHA_HZ * BASE) / (nb + ALPHA_HZ)
        last_refit = t
    a = max(0, t - W_FREQ)
    f = (HIT[a:t].sum(axis=0) + 1.0) / (t - a + K)
    mult = hz_tab[np.digitize(gap[t], EDGES)] / BASE
    v = f * mult
    bolsas["C hazard"].apuntar(v / v.sum(), y, datos.fecha[t])
    # D y uniforme
    bolsas["D ensamble"].apuntar(P_ens[j], y, datos.fecha[t])
    bolsas["uniforme"].apuntar(np.full(K, BASE), y, datos.fecha[t])
    if (j + 1) % 500 == 0:
        print(f"  {j+1}/{n-INI} sorteos...", flush=True)

# ---------------- reporte ----------------
out = {"inicio": datos.fecha[INI], "fin": datos.fecha[-1], "n": n - INI, "modelos": {}}
lineas = [f"CARRERA 1 ANO: {datos.fecha[INI]} .. {datos.fecha[-1]}  ({n-INI} sorteos, walk-forward estricto)", ""]
hdr = f"{'modelo':<12} {'Top1':>6} {'Top3':>7} {'Top5':>7} {'Top10':>7} {'mbits':>8}"
lineas.append(hdr + "   (azar: 2.63 / 7.89 / 13.16 / 26.32)")
for nombre, b in bolsas.items():
    m = b.m
    r = {k: b.hits[k] / m for k in KS}
    mbits = (b.ll - m * math.log(BASE)) / m / math.log(2) * 1000
    out["modelos"][nombre] = {"top1": r[1], "top3": r[3], "top5": r[5], "top10": r[10],
                              "mbits": mbits, "hits": b.hits, "meses": b.mes}
    lineas.append(f"{nombre:<12} {r[1]*100:5.2f}% {r[3]*100:6.2f}% {r[5]*100:6.2f}% {r[10]*100:6.2f}% {mbits:+8.2f}")
lineas.append("")
lineas.append("Top-3 por mes (estabilidad):")
meses = sorted(bolsas["D ensamble"].mes)
lineas.append(f"{'mes':<9}" + "".join(f"{nombre[:10]:>12}" for nombre in bolsas))
for mm in meses:
    lineas.append(f"{mm:<9}" + "".join(
        f"{(bolsas[x].mes[mm][0]/bolsas[x].mes[mm][1]*100):>11.1f}%" if mm in bolsas[x].mes else f"{'-':>12}"
        for x in bolsas))
texto = "\n".join(lineas)
print("\n" + texto)
with open(os.path.join(RAIZ, "herramientas", "resultados", "carrera_1ano.txt"), "w", encoding="utf-8") as f:
    f.write(texto + "\n")
with open(os.path.join(RAIZ, "herramientas", "resultados", "carrera_1ano.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\nguardado en herramientas/resultados/carrera_1ano.{txt,json}")
