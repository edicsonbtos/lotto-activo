# -*- coding: utf-8 -*-
"""Desarrollo: O/E de cada rasgo contra el ensamble walk-forward (calor_cache), dev-A / dev-B."""
import sys, os, json
import numpy as np
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas")); sys.path.insert(0, os.path.dirname(__file__))
import lotto_eval as LE
from rasgos import mascaras, NOMBRES
D = LE.cargar(os.path.join(RAIZ, "verificacion/hilo9/datos/historial.txt"))
c = np.load(os.path.join(RAIZ, "verificacion/hilo9/datos/calor_cache.npz"))
P, y = c["P"], c["y"]; P = P / P.sum(1, keepdims=True)
T0 = 2000
assert (D.seq[T0:T0 + len(y)] == y).all()
filas = []   # (dia, nombre, obs, esp, var)
for i in range(len(y)):
    t = T0 + i
    prev = D.seq[t - 1] if D.dia[t - 1] == D.dia[t] else None
    mes = int(D.fecha[t][5:7])
    for k, m in mascaras(prev, mes, int(D.dow[t])).items():
        if m is None: continue
        e = P[i][m].sum()
        filas.append((int(D.dia[t]), k, float(m[y[i]]), e, e * (1 - e)))
dias = sorted({f[0] for f in filas}); corte = dias[len(dias) // 2]
rng = np.random.default_rng(20261022)
def resumen(sel):
    o = sum(f[2] for f in sel); e = sum(f[3] for f in sel); v = sum(f[4] for f in sel)
    return o, e, o / e, (o - e) / np.sqrt(v)
def boot(sel, B=2000):
    por = {}
    for f in sel: por.setdefault(f[0], [0.0, 0.0]); por[f[0]][0] += f[2]; por[f[0]][1] += f[3]
    a = np.array(list(por.values())); n = len(a); r = []
    for _ in range(B):
        s = a[rng.integers(0, n, n)].sum(0); r.append(s[0] / s[1])
    return np.percentile(r, [2.5, 97.5])
out = {}
print(f"{'rasgo':16s} {'dev-A O/E (z)':>18s} {'dev-B O/E (z)':>18s} {'total O/E [IC95] z':>30s}  veredicto")
for k in NOMBRES:
    s = [f for f in filas if f[1] == k]
    A = resumen([f for f in s if f[0] < corte]); B_ = resumen([f for f in s if f[0] >= corte]); T = resumen(s)
    ic = boot(s)
    pasa = (np.sign(A[3]) == np.sign(B_[3]) and abs(A[3]) >= 2 and abs(B_[3]) >= 2 and abs(T[3]) >= 2.73)
    out[k] = dict(A=A, B=B_, T=T, ic=list(ic), pasa=bool(pasa))
    print(f"{k:16s} {A[2]:7.3f} ({A[3]:+5.2f})    {B_[2]:7.3f} ({B_[3]:+5.2f})    {T[2]:6.3f} [{ic[0]:.2f};{ic[1]:.2f}] {T[3]:+5.2f}  {'PASA' if pasa else 'no'}  obs={T[0]:.0f} esp={T[1]:.1f}")
json.dump(out, open(os.path.join(os.path.dirname(__file__), "resultado_dev.json"), "w"), indent=1, default=float)
