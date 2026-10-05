# -*- coding: utf-8 -*-
"""Sorteo de las 8:00 (PREREGISTRO.md): H1 ayer como hoy, H2 sombras, H3 primer sorteo de hace k días,
H4 retraso. Uso: python 1_analisis.py HIST WF.npz   (WF de 0_walkforward.py; ~10 s)"""
import math, os, sys
from datetime import date, timedelta
import numpy as np
from scipy.stats import chi2

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "herramientas")); sys.path.insert(0, os.path.join(RAIZ, "herramientas", "modelos"))
import lotto_eval as LE  # noqa: E402
import exposicion as EX  # noqa: E402

AJUSTE_PRIMER = {1: 0.272, 3: 1.736}          # = prediccion.AJUSTE_PRIMER (producción)
D = LE.cargar(sys.argv[1]); z = np.load(sys.argv[2]); A = z["P"]; T0 = int(z["desde"])
S = np.asarray(D.seq); H = np.asarray(D.hora); F = list(D.fecha); N = len(S)
K = 38

por_dia = {}
for t in range(N):
    por_dia.setdefault(F[t], []).append(t)
primero = {f: (int(H[ts[0]]), int(S[ts[0]])) for f, ts in por_dia.items()}


def ayer(f, k=1):
    return (date.fromisoformat(f) - timedelta(days=k)).isoformat()


def B(t):
    """Producción: ensamble walk-forward + ajuste del primer sorteo."""
    p = A[t - T0].copy()
    if t > 0 and F[t - 1] == F[t]:
        return p
    for k, m in AJUSTE_PRIMER.items():
        x = primero.get(ayer(F[t], k))
        if x is not None and x[0] == int(H[t]):
            p[x[1]] *= m
    return p / p.sum()


def tramo(t):
    return "dev" if t < LE.CORTE_FIJO else ("vivo" if F[t] >= "2026-09-15" else "prueba")


TR = ("dev", "prueba", "vivo")
ocho = [t for t in range(T0, N) if H[t] == 0 and F[t - 1] != F[t]]
PB = {t: B(t) for t in ocho}


def ic(O, E):
    lo = chi2.ppf(0.025, 2 * O) / 2 if O else 0.0
    hi = chi2.ppf(0.975, 2 * O + 2) / 2
    return lo / E, hi / E


def linea(nombre, filas):
    """filas: [(t, O 0/1, E, var)] -> O/E por tramo."""
    out = [f"{nombre:<38}"]
    for tr in TR:
        x = [r for r in filas if tramo(r[0]) == tr]
        if not x:
            out.append(f"{tr}: -"); continue
        O = sum(r[1] for r in x); E = sum(r[2] for r in x); V = sum(r[3] for r in x)
        lo, hi = ic(O, E); zz = (O - E) / math.sqrt(V) if V > 0 else 0
        out.append(f"{tr} n={len(x):4d} O={O:4d} E={E:6.1f} O/E={O / E:4.2f} [{lo:4.2f};{hi:4.2f}] z={zz:+5.1f}")
    print("  ".join(out))


def filas_conj(ts, conj, prob):
    """conj(t) -> lista de animales; prob(t) -> 38 probs. Devuelve filas para linea()."""
    r = []
    for t in ts:
        c = conj(t)
        if c is None or not len(c):
            continue
        c = sorted(set(c)); e = float(sum(prob(t)[i] for i in c))
        r.append((t, int(S[t] in c), e, e * (1 - e)))
    return r


crudo = lambda t: np.full(K, 1 / K)          # noqa: E731


def ayer_set(t, k=1):
    ts = por_dia.get(ayer(F[t], k))
    return [int(S[u]) for u in ts] if ts and len(ts) >= 10 else None


def hoy_antes(t):
    return [int(S[u]) for u in por_dia[F[t]] if u < t]


print("=" * 30, "Motor B a las 8:00", "=" * 30)
for tr in TR:
    x = [t for t in ocho if tramo(t) == tr]
    rk = [int((PB[t] > PB[t][S[t]]).sum()) for t in x]
    mb = np.mean([1000 * math.log2(PB[t][S[t]] * K) for t in x])
    print(f"{tr:6} n={len(x):4d}  Top-1 {np.mean([r < 1 for r in rk]):5.1%}  Top-3 {np.mean([r < 3 for r in rk]):5.1%}"
          f"  Top-5 {np.mean([r < 5 for r in rk]):5.1%}  Top-15 {np.mean([r < 15 for r in rk]):5.1%}  mbits {mb:+6.1f}")

print("\n" + "=" * 30, "H1: ¿las 8:00 tratan lo de ayer como de hoy?", "=" * 30)
print("-- crudo (contra azar |Y|/38) --")
linea("8:00 ganador en Y=salidos ayer", filas_conj(ocho, ayer_set, crudo))
resto = [t for t in range(T0, N) if F[t - 1] == F[t]]
linea("REF 9am-7pm: ganador ya salió hoy", filas_conj(resto, hoy_antes, crudo))
for h in (1, 2, 6, 11):
    ts = [t for t in range(T0, N) if H[t] == h]
    linea(f"hora {h}: ganador en salidos ayer", filas_conj(ts, ayer_set, crudo))
linea("8:00 ganador en salidos anteayer", filas_conj(ocho, lambda t: ayer_set(t, 2), crudo))
print("-- contra el motor B --")
linea("8:00 ganador en Y=salidos ayer", filas_conj(ocho, ayer_set, lambda t: PB[t]))
linea("8:00 ganador en salidos anteayer", filas_conj(ocho, lambda t: ayer_set(t, 2), lambda t: PB[t]))
linea("8:00 en ayer Y anteayer", filas_conj(
    ocho, lambda t: (sorted(set(ayer_set(t) or []) & set(ayer_set(t, 2) or [])) or None), lambda t: PB[t]))
linea("8:00 en ni ayer ni anteayer", filas_conj(
    ocho, lambda t: [i for i in range(K) if i not in set(ayer_set(t) or []) | set(ayer_set(t, 2) or [])]
    if ayer_set(t) and ayer_set(t, 2) else None, lambda t: PB[t]))
print("-- por posición de ayer (hora j de ayer), crudo y contra B --")


def pos_ayer(j):
    def f(t):
        ts = por_dia.get(ayer(F[t]))
        x = [int(S[u]) for u in (ts or []) if H[u] == j]
        return x or None
    return f


for j in range(12):
    linea(f"crudo  ayer hora {j} ({(j + 7) % 12 + 1}h)", filas_conj(ocho, pos_ayer(j), crudo))
for j in range(12):
    linea(f"motor  ayer hora {j} ({(j + 7) % 12 + 1}h)", filas_conj(ocho, pos_ayer(j), lambda t: PB[t]))

print("\n" + "=" * 30, "H3: primer sorteo de hace k días (contra B)", "=" * 30)
for k in range(1, 11):
    def fk(t, k=k):
        x = primero.get(ayer(F[t], k))
        return [x[1]] if x is not None and x[0] == 0 else None
    linea(f"8:00 = 8:00 de hace {k} días", filas_conj(ocho, fk, lambda t: PB[t]))

print("\n" + "=" * 30, "H4: retraso (sorteos desde su última salida), contra B", "=" * 30)
ultimo = np.full(K, -10 ** 6); ret = {}
for t in range(N):
    if t in PB:
        ret[t] = t - ultimo
    ultimo[S[t]] = t
for lo, hi in ((1, 12), (13, 24), (25, 36), (37, 60), (61, 120), (121, 10 ** 7)):
    linea(f"retraso {lo}-{hi if hi < 10 ** 6 else '...'}",
          filas_conj(ocho, lambda t, lo=lo, hi=hi: [i for i in range(K) if lo <= ret[t][i] <= hi] or None,
                     lambda t: PB[t]))

print("\n" + "=" * 30, "H2: sombras a las 8:00 (mbits por sorteo, IC 90 % por jornada)", "=" * 30)


def rk(p, w):
    return int(sum(1 for i in range(K) if (-p[i], i) < (-p[w], w)))


for tr in TR:
    x = [t for t in ocho if tramo(t) == tr]
    res = {"B": [], "C": [], "C8": []}; dCB = []; dC8C = []; ven = [0, 0.0]
    for t in x:
        b = PB[t]; c = np.array(EX.aplicar(b, F[t], 0)); c8 = np.array(EX.aplicar_8am(b, F[t], 0)); w = S[t]
        for nm, p in (("B", b), ("C", c), ("C8", c8)):
            res[nm].append(rk(p, w))
        dCB.append(1000 * math.log2(c[w] / b[w])); dC8C.append(1000 * math.log2(c8[w] / c[w]))
        d = int(F[t][8:10]); vv = [EX.IDX[str(n)] for n in (d - 1, d, d + 1) if 1 <= n <= 36]
        ven[0] += w in vv; ven[1] += float(sum(c[i] for i in vv))

    def m90(v):
        v = np.array(v); se = v.std(ddof=1) / math.sqrt(len(v))
        return f"{v.mean():+6.1f} [{v.mean() - 1.645 * se:+6.1f};{v.mean() + 1.645 * se:+6.1f}]"
    t5 = "  ".join(f"{nm} T5 {np.mean([r < 5 for r in v]):5.1%} T15 {np.mean([r < 15 for r in v]):5.1%}"
                   for nm, v in res.items())
    print(f"{tr:6} n={len(x):4d}  C−B {m90(dCB)}  C8−C {m90(dC8C)}  ventana O={ven[0]} E(C)={ven[1]:.1f}  {t5}")
