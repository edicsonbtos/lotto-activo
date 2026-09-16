# -*- coding: utf-8 -*-
"""TAREA 2 (CORREGIDA) + TAREA 4 -- que mira f: el hueco o el DIA?

Por que se rehace la Tarea 2:

  1. `hora` y `posicion en la jornada` son practicamente la misma variable;
     reportarlas como dos interacciones era doble conteo.
  2. Peor: `ya salio hoy` es una FUNCION DETERMINISTA de (hueco, posicion):
       salio_hoy  <=>  hueco <= posicion_en_la_jornada
     Asi que "f(hueco) con interaccion de hora" y "f(hueco, salio_hoy)" son la
     MISMA familia de modelos escrita de dos formas. La tabla de la v1 ademas
     normalizaba contra celdas ESTRUCTURALMENTE IMPOSIBLES (hueco>=28 y salio
     hoy no puede pasar en una jornada de 12), y por eso escupia
     multiplicadores de 8.8x que no significaban nada.

Experimento decisivo: comparar por AIC dos parametrizaciones rivales de f
sobre los mismos datos. La que gane describe lo que el script mira de verdad.

  A) f(hueco)      -- 61 parametros, hueco 1..60 + 61+
  B) f(DIA)        -- 11 parametros para "salio hoy, hace d sorteos" +
                      bins de hueco para "no salio hoy". La politica tendria
                      estado POR JORNADA.
  C) f(hueco) x momento del dia -- el modelo saturado de la v1.

TAREA 4: oraculo de la politica evaluado WALK-FORWARD en desarrollo
(f se reajusta cada 250 sorteos solo con el pasado) contra el ensamble.

SOLO desarrollo. El tramo de prueba no se toca.

Uso:  python politica_f2.py
Salida: herramientas/resultados/politica_f2.md
"""
import json, math, os, sys, time
import numpy as np
from scipy.optimize import minimize

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

K = 38
P0 = 1.0 / K
GMAX = 60
R_REAJ = 250

M = []


def di(s=""):
    print(s, flush=True)
    M.append(s)


def wilson(k, n, z=1.959964):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


# ------------------------------------------------------------------ datos
datos = LE.cargar()
n_tot = len(datos)
INI, FIN = LE.W, LE.CORTE_FIJO
seq = datos.seq[:FIN].astype(np.int64)
hora = datos.hora[:FIN].astype(np.int64)
dia = datos.dia[:FIN].astype(np.int64)
nf = len(seq)

gap = np.zeros((nf, K), dtype=np.int64)
dintra = np.zeros((nf, K), dtype=np.int64)     # 0 = no salio hoy; d = hace d sorteos, hoy
vhoy = np.zeros((nf, K), dtype=np.int64)
posd = np.zeros(nf, dtype=np.int64)
last = np.full(K, -1)
ultimo_hoy = np.full(K, -1)
cur, cnt, pd = -1, np.zeros(K, dtype=np.int64), 0
for t in range(nf):
    if dia[t] != cur:
        cur = dia[t]
        cnt = np.zeros(K, dtype=np.int64)
        ultimo_hoy = np.full(K, -1)
        pd = 0
    posd[t] = pd
    vhoy[t] = cnt
    vis = last >= 0
    gap[t, vis] = t - last[vis]
    gap[t, ~vis] = 10 ** 6
    vh = ultimo_hoy >= 0
    dintra[t, vh] = t - ultimo_hoy[vh]
    last[seq[t]] = t
    ultimo_hoy[seq[t]] = t
    cnt[seq[t]] += 1
    pd += 1

dv = slice(INI, FIN)
G, DI_, VH, Y = gap[dv], dintra[dv], vhoy[dv], seq[dv]
HORA, POSD = hora[dv], posd[dv]
N = len(Y)
FIL = np.arange(N)

di("# Tarea 2 (corregida) y Tarea 4 - que mira la politica f")
di("")
di("Generado por `herramientas/exploracion/politica_f2.py`.")
di("")
di("- Desarrollo `[%d, %d)` = **%d sorteos**. Tramo de prueba **intacto**." % (INI, FIN, N))
di("")
di("## 2.0 Por que la Tarea 2 de la primera pasada estaba mal")
di("")
co = float((HORA == POSD).mean())
det = float(((G <= POSD[:, None]) == (DI_ > 0)).mean())
di("1. `hora` y `posicion en la jornada` coinciden en el **%.0f%%** de las filas y sus tablas "
   "de interaccion salieron casi identicas: son **la misma variable**, no dos hallazgos." % (100 * co))
di("2. Mas grave: `ya salio hoy` es una **funcion determinista** de (hueco, posicion) -- "
   "se cumple `salio_hoy <=> hueco <= posicion` en el **%.2f%%** de las celdas. "
   "Asi que «f(hueco) con interaccion de hora» y «f(hueco, salio_hoy)` son **el mismo modelo**." % (100 * det))
imp = int(((G >= 28) & (DI_ > 0)).sum())
di("3. La tabla de `veces-hoy` de la v1 normalizaba contra celdas **estructuralmente "
   "imposibles** (hueco>=28 **y** salio hoy: %d casos en %d). De ahi salian los "
   "multiplicadores de 8.8x. **Eran un artefacto, como el `gcd` del Vector 3.**" % (imp, N * K))
di("")
di("Lo que sigue reemplaza esa seccion.")
di("")

# ---------------------------------------------------------------- logit
def ajustar(bins, nbins, maxiter=400, sub=None):
    B = bins
    fil = FIL if sub is None else sub
    yy = Y[fil]
    cg = np.bincount(B[fil, yy], minlength=nbins).astype(float)
    Bs = B[fil]
    Bf = Bs.ravel()
    nf_ = len(fil)
    f_ = np.arange(nf_)

    def f(b):
        z = b[Bs]
        zm = z.max(1, keepdims=True)
        e = np.exp(z - zm)
        S = e.sum(1, keepdims=True)
        p = e / S
        ll = float((z[f_, yy] - zm[:, 0] - np.log(S[:, 0])).sum())
        esp = np.bincount(Bf, weights=p.ravel(), minlength=nbins)
        return -ll, -(cg - esp)

    r = minimize(f, np.zeros(nbins), jac=True, method="L-BFGS-B", options={"maxiter": maxiter})
    return r.x - r.x.mean(), -r.fun


def aic(ll, k):
    return -2 * ll + 2 * k


di("---")
di("")
di("## 2.1 El experimento decisivo: f(hueco) contra f(DIA)")
di("")

# A) f(hueco)
gb = np.minimum(G, GMAX + 1)
gb[G > GMAX] = GMAX + 1
bA = gb - 1
NA = GMAX + 1
t0 = time.time()
_, llA = ajustar(bA, NA)

# B) f(dia): 0..11 para "salio hoy hace d" (0 = no salio hoy) + bins de hueco para los que no
BORDES = [1, 8, 13, 28, 45, 70, 110, 180, 10 ** 7]
gq = np.zeros_like(G)
for i in range(len(BORDES) - 1):
    gq[(G >= BORDES[i]) & (G < BORDES[i + 1])] = i
NQ = len(BORDES) - 1
bB = np.where(DI_ > 0, np.minimum(DI_, 11), 12 + gq)     # 1..11 intra ; 12..12+NQ-1 no-intra
bB = np.where(DI_ > 0, bB - 1, bB - 1)                    # 0..10 intra ; 11.. no-intra
NB = 11 + NQ
_, llB = ajustar(bB, NB)

# C) saturado: hueco grueso x momento
BORDES_C = [1, 3, 7, 13, 28, 10 ** 7]
rg = np.zeros_like(G)
for i in range(len(BORDES_C) - 1):
    rg[(G >= BORDES_C[i]) & (G < BORDES_C[i + 1])] = i
NRC = len(BORDES_C) - 1
bC = rg * 12 + np.repeat(POSD[:, None], K, axis=1)
_, llC = ajustar(bC, NRC * 12)

# D) f(dia) + hueco fino para los que NO salieron hoy  (mezcla)
bD = np.where(DI_ > 0, np.minimum(DI_, 11) - 1, 11 + np.minimum(gb - 1, GMAX))
ND = 11 + GMAX + 1
_, llD = ajustar(bD, ND)

di("Todas son logit condicional sobre los mismos %d sorteos. AIC menor gana." % N)
di("")
di("| parametrizacion | que asume | parametros | logver | AIC | delta AIC |")
di("|---|---|---|---|---|---|")
filas = [("A) f(hueco) 1..60 + 61+", "la politica mira el hueco global", NA, llA),
         ("B) f(DIA): salio hoy hace d, si no hueco grueso", "la politica tiene estado POR JORNADA", NB, llB),
         ("C) f(hueco grueso) x momento del dia", "modelo saturado de la v1", NRC * 12, llC),
         ("D) f(DIA) + hueco fino fuera del dia", "estado por jornada + recencia entre dias", ND, llD)]
best = min(aic(ll, k) for _, _, k, ll in filas)
for nom, que, k, ll in sorted(filas, key=lambda r: aic(r[3], r[2])):
    di("| %s | %s | %d | %.1f | %.1f | %+.1f |" % (nom, que, k, ll, aic(ll, k), aic(ll, k) - best))
di("")
gana = min(filas, key=lambda r: aic(r[3], r[2]))
di("**Gana: %s** (%.1fs).  " % (gana[0], time.time() - t0))
di("")

# ------------------------------------------------- las dos curvas de f(dia)
di("### 2.2 Las dos curvas de la politica")
di("")
bD_, _ = ajustar(bD, ND)
mD = np.exp(bD_)
ref = np.median(mD[11 + 27:11 + 60])
mD = mD / ref
gano = np.zeros((N, K), dtype=bool)
gano[FIL, Y] = True

di("**(a) El animal YA salio hoy**, hace `d` sorteos:")
di("")
di("| d | n pares | tasa | IC95 | multiplicador |")
di("|---|---|---|---|---|")
for d in range(1, 12):
    m_ = DI_ == d
    nn = int(m_.sum())
    if nn < 30:
        continue
    kk = int((m_ & gano).sum())
    lo, hi = wilson(kk, nn)
    di("| %d | %d | %.3f%% | %.3f-%.3f%% | **%.2f** | " % (d, nn, 100 * kk / nn, 100 * lo, 100 * hi, mD[d - 1]))
m_ = DI_ > 0
nn = int(m_.sum())
kk = int((m_ & gano).sum())
lo, hi = wilson(kk, nn)
di("")
di("**Cualquier d**: %d de %d = **%.3f%%** (IC95 %.3f-%.3f%%) = **%.2fx** el azar."
   % (kk, nn, 100 * kk / nn, 100 * lo, 100 * hi, (kk / nn) / P0))
di("")

di("**(b) El animal NO salio hoy**, segun su hueco global:")
di("")
di("| hueco | n pares | tasa | IC95 | vs azar |")
di("|---|---|---|---|---|")
for lo_, hi_ in [(1, 8), (8, 13), (13, 20), (20, 28), (28, 45), (45, 70), (70, 110), (110, 180), (180, 10 ** 7)]:
    m_ = (DI_ == 0) & (G >= lo_) & (G < hi_)
    nn = int(m_.sum())
    if nn < 50:
        continue
    kk = int((m_ & gano).sum())
    l2, h2 = wilson(kk, nn)
    di("| %d-%s | %d | %.3f%% | %.3f-%.3f%% | **%.2fx** |"
       % (lo_, "inf" if hi_ > 10 ** 6 else hi_ - 1, nn, 100 * kk / nn, 100 * l2, 100 * h2, (kk / nn) / P0))
di("")

# comparacion directa: mismo hueco, dentro vs fuera del dia
di("### 2.3 La prueba que separa las dos hipotesis")
di("")
di("Para un **mismo hueco corto**, comparar los casos en que esa aparicion previa cae "
   "DENTRO de la jornada contra los que caen FUERA (el animal salio ayer al final). "
   "Si la politica mirara el hueco, las dos columnas serian iguales.")
di("")
di("| hueco | salio HOY: tasa (n) | NO salio hoy: tasa (n) | razon |")
di("|---|---|---|---|")
for g in range(1, 12):
    m1 = (G == g) & (DI_ > 0)
    m2 = (G == g) & (DI_ == 0)
    n1, n2 = int(m1.sum()), int(m2.sum())
    if n1 < 30 or n2 < 30:
        continue
    k1, k2 = int((m1 & gano).sum()), int((m2 & gano).sum())
    r1, r2 = k1 / n1, k2 / n2
    di("| %d | %.3f%% (%d) | %.3f%% (%d) | **%.2f** |" % (g, 100 * r1, n1, 100 * r2, n2,
                                                          r1 / r2 if r2 > 0 else float("nan")))
m1 = (G <= 11) & (DI_ > 0)
m2 = (G <= 11) & (DI_ == 0)
n1, n2 = int(m1.sum()), int(m2.sum())
k1, k2 = int((m1 & gano).sum()), int((m2 & gano).sum())
r1, r2 = k1 / n1, k2 / n2
z = (r1 - r2) / math.sqrt(r1 * (1 - r1) / n1 + r2 * (1 - r2) / n2)
di("")
di("**Agregado (huecos 1-11)**: salio hoy **%.3f%%** (n=%d) contra no salio hoy **%.3f%%** "
   "(n=%d). Razon **%.2f**, z = **%+.1f**, p = %.2e."
   % (100 * r1, n1, 100 * r2, n2, r1 / r2, z, math.erfc(abs(z) / math.sqrt(2))))
di("")

# =====================================================================
di("---")
di("")
di("## Tarea 4 - Oraculo de la politica, walk-forward")
di("")
di("f se reajusta cada %d sorteos **solo con el pasado** y se evalua en el bloque "
   "siguiente. Nada de ajustar y evaluar en los mismos datos." % R_REAJ)
di("")


def oraculo(bins, nbins, nombre):
    P = np.empty((N, K))
    for T in range(INI, FIN, R_REAJ):
        fin = min(T + R_REAJ, FIN)
        pasado = np.arange(0, T - INI)
        if len(pasado) < 500:
            b = np.zeros(nbins)
        else:
            b, _ = ajustar(bins, nbins, sub=pasado)
        z = b[bins[T - INI:fin - INI]]
        z = z - z.max(1, keepdims=True)
        e = np.exp(z)
        P[T - INI:fin - INI] = e / e.sum(1, keepdims=True)
    rng = np.random.default_rng(12345)
    o = np.argsort(-(P + rng.random(P.shape) * 1e-12), axis=1)
    pos = np.argmax(o == Y[:, None], axis=1)
    ev = np.arange(len(pos)) >= 500      # descarta el arranque sin datos
    t1 = float((pos[ev] < 1).mean())
    t3 = float((pos[ev] < 3).mean())
    bits = float(np.mean(np.log(P[ev, Y[ev]] * K) / math.log(2)))
    nn = int(ev.sum())
    lo, hi = wilson(int((pos[ev] < 3).sum()), nn)
    di("| %s | %d | %.2f%% | %.2f%% | %.2f-%.2f%% | %+.1f |"
       % (nombre, nn, 100 * t1, 100 * t3, 100 * lo, 100 * hi, 1000 * bits))
    return t1, t3, bits


di("| oraculo (walk-forward) | n | Top-1 | Top-3 | IC95 Top-3 | mbits |")
di("|---|---|---|---|---|---|")
r_gap = oraculo(bA, NA, "A) f(hueco)")
r_dia = oraculo(bD, ND, "D) f(DIA) + hueco fuera del dia")
bE = np.where(DI_ > 0, np.minimum(DI_, 11) - 1,
              11 + np.minimum(gb - 1, GMAX) * 1)
bE = bE * 4 + np.clip(np.repeat(POSD[:, None], K, axis=1) // 3, 0, 3)
r_pos = oraculo(bE, (11 + GMAX + 1) * 4, "E) f(DIA) x cuarto de jornada")
di("")
di("Referencias sobre los mismos sorteos de desarrollo:")
di("")
di("| modelo | Top-1 | Top-3 | mbits |")
di("|---|---|---|---|")
di("| azar puro | 2.63% | 7.89% | 0.0 |")
di("| oraculo tabular de la fase anterior (ajustado en los mismos datos) | 4.13% | 11.66% | - |")
di("| `hazard_actual` (produccion) | 3.41% | 10.74% | +47.6 |")
di("| **`ensamble_v2` (produccion)** | **4.53%** | **12.89%** | **+120.1** |")
di("")

mejor = max(r_gap[1], r_dia[1], r_pos[1])
di("**Techo del oraculo de politica: %.2f%% de Top-3.**" % (100 * mejor))
di("")
if mejor > 0.1289:
    di("El oraculo de f **SUPERA** al ensamble por %.2f puntos: hay estructura de la politica "
       "que el ensamble no esta usando." % (100 * mejor - 12.89))
else:
    di("El oraculo de f **NO supera** al ensamble (%.2f%% contra 12.89%%). El ensamble ya "
       "capturo la politica medible: no queda jugo por este lado." % (100 * mejor))
di("")

ruta = os.path.join(RAIZ, "herramientas", "resultados", "politica_f2.md")
with open(ruta, "w", encoding="utf-8") as f:
    f.write("\n".join(M) + "\n")
print("\nguardado en", ruta)
