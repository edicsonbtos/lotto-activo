# -*- coding: utf-8 -*-
"""Verificación independiente de r2_a03 (no modifica su código)."""
import os, sys, csv, io
import numpy as np
V = os.path.dirname(os.path.abspath(__file__)); C = os.path.dirname(V); sys.path.insert(0, C)
import experimento as X
A, E2, LE = X.A, X.E2, X.LE
D = A.datos().prefijo(A.CORTE); _, y = A.base()
assert len(D.seq) == A.CORTE == 9357
assert np.array_equal(np.asarray(D.seq[A.W:A.CORTE]), y), "y no coincide con seq"
Pv1 = np.load(os.path.join(X.MN, "ag12_transiciones", "P_V1.npy")); Pv1 /= Pv1.sum(1, keepdims=True)
LV1 = np.log(np.clip(Pv1, 1e-12, None))
dia = np.asarray(D.dia[A.W:A.CORTE]); blo = E2.bloques_jornada(dia)
fecha = np.asarray(D.fecha[A.W:A.CORTE]); hora = np.asarray(D.hora[A.W:A.CORTE])
print("bloques:", np.bincount(blo), "fechas corte:", [fecha[blo == k][[0, -1]].tolist() for k in range(5)])
rd = X.cargar_rd(D.fecha[-1])
assert max(f for f, _ in rd) <= "2025-12-17"

# 1) reconstrucción independiente de L1 / L3 desde el CSV crudo
raw = {}
for r in csv.DictReader(io.open(X.RD_CSV, encoding="utf-8")):
    if r["hora"].endswith(":30"):
        raw[(r["fecha"], int(r["hora"][:2]))] = LE.IDX[X.ANIMALES[X.sin_acentos(r["animal"])]]
L1 = np.zeros((len(y), 38)); L3 = np.zeros((len(y), 38))
for j in range(len(y)):
    hr = 8 + int(hora[j])       # LA h:00 real
    a = raw.get((fecha[j], hr - 1)); b = raw.get((fecha[j], hr - 2))
    if a is not None and hr - 1 >= 8: L1[j, a] = 1
    if b is not None and hr - 2 >= 8: L3[j, b] = 1
Xr = X.rasgos_rd(D, A.W, rd).astype(np.float64)
print("L1 idéntico:", np.array_equal(L1, Xr[:, :, 0]), " L3 idéntico:", np.array_equal(L3, Xr[:, :, 1]))
# tasa cruda (sin modelo): LA h:00 == RD (h-1):30
m = L1.sum(1) > 0
print(f"cruda L1: {int(L1[np.arange(len(y)), y][m].sum())} / {m.sum()} = {L1[np.arange(len(y)), y][m].mean():.4f} vs 1/38={1/38:.4f}")

def va(Xf):
    P, w = E2.cross_fit(lambda tr: E2.ajustar_lineal(Xf[tr], LV1[tr], y[tr], X.LAM),
                        lambda w, te: E2.predecir_lineal(w, Xf[te], LV1[te]), blo)
    return A.evaluar(P, P_ref=Pv1, y=y)["delta_mbits"], P

# 2) placebos propios
rng = np.random.default_rng(2026)
dias_u = sorted(set(f for f, _ in rd))
nulos = []
for p in range(20):
    perm = dict(zip(dias_u, rng.permutation(dias_u)))      # RD de otro día al azar, misma hora
    rdp = {(f, h): rd[(perm[f], h)] for (f, h) in rd if (perm[f], h) in rd}
    d, _ = va(X.rasgos_rd(D, A.W, rdp).astype(np.float64)); nulos.append(d[0])
nulos = np.array(nulos)
print(f"placebo permutación de días (20): media {nulos.mean():+.2f} sd {nulos.std():.2f} max {nulos.max():+.2f}")
# animal RD aleatorio uniforme
rdu = {k: int(rng.integers(38)) for k in rd}
print("placebo RD uniforme:", va(X.rasgos_rd(D, A.W, rdu).astype(np.float64))[0])
# 3) sensibilidad a bloques: cross-fit con 10 bloques (no el de ag12) -> sólo informativo
# 4) fuga por offset cross-fit: VA ajustado SOLO en otros bloques ya; comprobar forward estricto por fecha
#    (entrenar solo con bloques < k, offset P_V1 incluido) ya lo hace experimento; aquí L1+L3 sin offset aprendido:
#    peso fijo de la regla (w fijos -0.685,-0.289 del bloque 0 aplicados a bloques 1-4)
d_fix = []
w0 = None
P0, pars = E2.cross_fit(lambda tr: E2.ajustar_lineal(Xr[tr][:, :, :2], LV1[tr], y[tr], X.LAM),
                        lambda w, te: E2.predecir_lineal(w, Xr[te][:, :, :2], LV1[te]), blo)
w_b0 = E2.ajustar_lineal(Xr[blo == 0][:, :, :2], LV1[blo == 0], y[blo == 0], X.LAM)
Pf = E2.predecir_lineal(w_b0, Xr[:, :, :2], LV1); sel = blo > 0
dd = A.mbits_fila(Pf, y) - A.mbits_fila(Pv1, y)
print("pesos del bloque 0 solamente:", np.round(np.asarray(w_b0).ravel()[:2], 3),
      " Delta bloques 1-4:", A.ic_bloques(dd[sel], dia[sel]))
# 5) regla sin ajuste alguno: multiplicar P_V1 por 0.5 en RD(h-1) y 0.75 en RD(h-2)
Pr = Pv1 * np.where(L1 > 0, 0.5, 1) * np.where(L3 > 0, 0.75, 1)
print("regla fija 0.5/0.75 sin ajuste:", A.evaluar(Pr, P_ref=Pv1, y=y)["delta_mbits"])
# 6) Δ por año y por hora
dA = A.mbits_fila(va(Xr)[1], y) - A.mbits_fila(Pv1, y)
for yr in ["2024", "2025"]:
    s = np.array([f.startswith(yr) for f in fecha]); print(yr, A.ic_bloques(dA[s], dia[s]))
for k in range(5):
    s = blo == k; print("bloque", k, A.ic_bloques(dA[s], dia[s]))
