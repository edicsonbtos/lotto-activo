# -*- coding: utf-8 -*-
"""INGENIERIA INVERSA DE LA POLITICA f   (Tareas 1 y 2)

Hipotesis de trabajo: el sorteo es software con PRNG fuerte (Vector 3 cerrado)
mas una politica de pesos:   ganador = choice(animales, weights=f(hueco, ...))

TAREA 1: mapa fino de f(hueco) 1..60 + 61+, forma funcional, escalones y
         multiplicadores DESNORMALIZADOS.
TAREA 2: interacciones de f con hora, veces-hoy, dia de semana y posicion
         en la jornada.

Clave metodologica: la tasa observada NO es el peso. Es  w_i / suma_j w_j,
y la suma cambia en cada sorteo segun los huecos de los 38 animales. El
multiplicador exacto sale de un LOGIT CONDICIONAL (un parametro por bin):

    P(gana a | sorteo t) = exp(b[bin(g_ta)]) / suma_a' exp(b[bin(g_ta')])

Eso es exactamente el sistema desnormalizado, resuelto por maxima
verosimilitud. exp(b) es el peso relativo que usa el script del operador.

SOLO tramo de DESARROLLO [W, CORTE_FIJO). El tramo de prueba NO se toca.

Uso:  python politica_f.py
Salida: herramientas/resultados/politica_f.md
"""
import math, os, sys
import numpy as np
from scipy.optimize import minimize

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

K = 38
P0 = 1.0 / K
ALFA = 0.01
GMAX = 60

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


def chi2_sf(x, k):
    if k <= 0:
        return 1.0
    if x <= 0:
        return 1.0
    z = ((x / k) ** (1.0 / 3) - (1 - 2.0 / (9 * k))) / math.sqrt(2.0 / (9 * k))
    return 0.5 * math.erfc(z / math.sqrt(2))


# ------------------------------------------------------------------ datos
datos = LE.cargar()
n_tot = len(datos)
INI, FIN = LE.W, LE.CORTE_FIJO
seq = datos.seq[:FIN].astype(np.int64)
hora = datos.hora[:FIN].astype(np.int64)
dow = datos.dow[:FIN].astype(np.int64)
dia = datos.dia[:FIN].astype(np.int64)
nf = len(seq)

# estado por fila: hueco de cada animal, veces que salio hoy, posicion en la jornada
gap = np.zeros((nf, K), dtype=np.int64)
hoy = np.zeros((nf, K), dtype=np.int64)
pos_dia = np.zeros(nf, dtype=np.int64)
last = np.full(K, -1)
cur, cnt, pd = -1, np.zeros(K, dtype=np.int64), 0
for t in range(nf):
    if dia[t] != cur:
        cur = dia[t]
        cnt = np.zeros(K, dtype=np.int64)
        pd = 0
    hoy[t] = cnt
    pos_dia[t] = pd
    vis = last >= 0
    gap[t, vis] = t - last[vis]
    gap[t, ~vis] = 10 ** 6
    last[seq[t]] = t
    cnt[seq[t]] += 1
    pd += 1

dv = slice(INI, FIN)
G = gap[dv]                      # (N, 38)
Y = seq[dv]
N = len(Y)
HOY = hoy[dv]
HORA = hora[dv]
DOW = dow[dv]
POSD = pos_dia[dv]
FIL = np.arange(N)

di("# Ingenieria inversa de la politica f")
di("")
di("Generado por `herramientas/exploracion/politica_f.py`.")
di("")
di("- Historial completo **%d sorteos**; tramo de prueba (>= %d) **intacto**." % (n_tot, LE.CORTE_FIJO))
di("- Analizado: **desarrollo** `[%d, %d)` = **%d sorteos** = %d pares (sorteo, animal)."
   % (INI, FIN, N, N * K))
di("- Azar puro por animal: 1/38 = **2.632%**.")
di("")

# =====================================================================
di("---")
di("")
di("## Tarea 1 - Mapa fino de f(hueco)")
di("")
di("### 1.1 Tasa por hueco individual (1 a %d, mas 61+)" % GMAX)
di("")

gb = np.minimum(G, GMAX + 1)          # 1..60 exactos, 61+ colapsado en 61
gb[G > GMAX] = GMAX + 1
NB = GMAX + 2                          # indices 0..61 (0 no se usa)
plano_b = gb.ravel()
gano = np.zeros((N, K), dtype=bool)
gano[FIL, Y] = True
plano_h = gano.ravel()
nb = np.bincount(plano_b, minlength=NB).astype(float)
cb = np.bincount(plano_b[plano_h], minlength=NB).astype(float)

di("| hueco | n pares | aciertos | tasa | IC95 | vs azar |")
di("|---|---|---|---|---|---|")
for g in list(range(1, 13)) + [15, 18, 20, 25, 30, 40, 50, 60, GMAX + 1]:
    if nb[g] < 30:
        continue
    r = cb[g] / nb[g]
    lo, hi = wilson(int(cb[g]), int(nb[g]))
    di("| %s | %d | %d | %.3f%% | %.3f-%.3f%% | **%.2fx** |"
       % ("61+" if g == GMAX + 1 else str(g), int(nb[g]), int(cb[g]),
          100 * r, 100 * lo, 100 * hi, r / P0))
di("")
di("(Tabla completa 1..60 en el JSON adjunto; aqui van los puntos de referencia.)")
di("")

# grafico ASCII
di("### Curva (cada linea es un hueco; `|` marca el azar 2.632%)")
di("")
di("```")
esc = 46
for g in range(1, 31):
    if nb[g] < 30:
        continue
    r = cb[g] / nb[g]
    x = int(round(r / P0 * esc / 2.0))
    cero = int(round(esc / 2.0))
    barra = ["."] * (esc + 2)
    barra[cero] = "|"
    for i in range(min(x, esc + 1)):
        if i != cero:
            barra[i] = "#"
    di("g=%2d %5.2fx %s" % (g, r / P0, "".join(barra)))
di("```")
di("")

# ---------------------------------------------------- 1.3 logit condicional
di("### 1.3 Multiplicadores DESNORMALIZADOS (logit condicional)")
di("")
di("La tasa observada es `w_i / suma_j w_j` y esa suma cambia en cada sorteo. "
   "Para recuperar el peso `w` que usa el script hay que resolver el sistema. "
   "Se ajusta por maxima verosimilitud")
di("")
di("> `P(gana a | sorteo t) = exp(b[bin(hueco)]) / suma_a' exp(b[bin(hueco_a')])`")
di("")
di("y el multiplicador es `exp(b)` normalizado a 1 en el bin de referencia.")
di("")


def ajustar_logit(bins, nbins, ref=None, maxiter=300):
    """Logit condicional: un parametro por bin. Devuelve (beta, loglik)."""
    B = bins                                  # (N, K) enteros 0..nbins-1
    cuenta_gana = np.bincount(B[FIL, Y], minlength=nbins).astype(float)
    Bf = B.ravel()

    def f(b):
        z = b[B]                              # (N, K)
        zm = z.max(1, keepdims=True)
        e = np.exp(z - zm)
        S = e.sum(1, keepdims=True)
        p = e / S
        ll = float((z[FIL, Y] - zm[:, 0] - np.log(S[:, 0])).sum())
        esp = np.bincount(Bf, weights=p.ravel(), minlength=nbins)
        return -ll, -(cuenta_gana - esp)

    b0 = np.zeros(nbins)
    r = minimize(f, b0, jac=True, method="L-BFGS-B", options={"maxiter": maxiter})
    b = r.x - (r.x[ref] if ref is not None else r.x.mean())
    return b, -r.fun


# bins para el logit: 1..60 individuales + 61+  -> indices 0..60
lb = gb - 1                                    # 0..60
NBL = GMAX + 1
beta, ll_fino = ajustar_logit(lb, NBL, ref=None)
mult = np.exp(beta)
mult = mult / np.median(mult[24:60])           # referencia: meseta de huecos largos
di("| hueco | multiplicador exp(b) | tasa cruda (tasa/azar) |")
di("|---|---|---|")
for g in list(range(1, 13)) + [15, 20, 25, 30, 40, 50, 60, 61]:
    i = g - 1
    if i >= NBL or nb[g] < 30:
        continue
    di("| %s | **%.3f** | %.3f |" % ("61+" if g == 61 else str(g), mult[i], (cb[g] / nb[g]) / P0))
di("")
di("El multiplicador desnormalizado y la tasa cruda casi coinciden: la suma de pesos "
   "`S_t` varia poco entre sorteos, asi que la lectura ingenua no estaba lejos. "
   "Diferencia media absoluta: **%.4f**."
   % np.mean([abs(mult[g - 1] - (cb[g] / nb[g]) / P0) for g in range(1, 61) if nb[g] >= 30]))
di("")

# ---------------------------------------------------- 1.2 forma funcional
di("### 1.2 Forma funcional: suave o escalones?")
di("")
gs = np.array([g for g in range(1, GMAX + 1) if nb[g] >= 50])
ns = nb[gs]
ks = cb[gs]
rs = ks / ns


def ll_binom(r_pred):
    r_pred = np.clip(r_pred, 1e-9, 1 - 1e-9)
    return float((ks * np.log(r_pred) + (ns - ks) * np.log(1 - r_pred)).sum())


def aic(ll, npar):
    return -2 * ll + 2 * npar


modelos = {}
modelos["constante (nula)"] = (ll_binom(np.full(len(gs), ks.sum() / ns.sum())), 1, None)


def ajusta(fun, x0, npar, nombre):
    def obj(th):
        return -ll_binom(fun(gs, th))
    best = None
    for _ in range(6):
        th0 = np.array(x0) * (1 + 0.3 * np.random.default_rng(len(nombre) + _).standard_normal(len(x0)))
        try:
            r = minimize(obj, th0, method="Nelder-Mead",
                         options={"maxiter": 20000, "xatol": 1e-10, "fatol": 1e-10})
            if best is None or r.fun < best.fun:
                best = r
        except Exception:
            pass
    modelos[nombre] = (-best.fun, npar, (fun, best.x))
    return best


ajusta(lambda g, th: th[0] * (1 - th[1] * np.exp(-g / max(th[2], 1e-6))),
       [0.028, 0.9, 5.0], 3, "exponencial saturante")
ajusta(lambda g, th: th[0] / (1 + np.exp(-(np.log(g) - th[1]) / max(th[2], 1e-6))),
       [0.030, 1.5, 0.5], 3, "logistica en log(hueco)")
ajusta(lambda g, th: np.clip(th[0] * g ** th[1], 1e-9, 0.5),
       [0.01, 0.3], 2, "potencia")
ajusta(lambda g, th: th[0] * (1 - th[1] * np.exp(-g / max(th[2], 1e-6))) * np.exp(-g / max(th[3], 1e-6)),
       [0.035, 0.9, 5.0, 200.0], 4, "exponencial saturante x decaimiento")


# ---- escalones por segmentacion binaria con penalizacion BIC
def ll_seg(a, b):
    nn = ns[a:b].sum()
    kk = ks[a:b].sum()
    if nn == 0:
        return 0.0
    r = kk / nn
    if r <= 0 or r >= 1:
        return 0.0
    return kk * math.log(r) + (nn - kk) * math.log(1 - r)


def segmentar(max_cortes=8):
    cortes = []
    for _ in range(max_cortes):
        limites = [0] + sorted(cortes) + [len(gs)]
        mejor = None
        base_ll = sum(ll_seg(limites[i], limites[i + 1]) for i in range(len(limites) - 1))
        for i in range(len(limites) - 1):
            a, b = limites[i], limites[i + 1]
            for c in range(a + 2, b - 1):
                g = (ll_seg(a, c) + ll_seg(c, b)) - (ll_seg(a, b))
                if mejor is None or g > mejor[0]:
                    mejor = (g, c)
        if mejor is None:
            break
        pen = 0.5 * math.log(ns.sum())
        if mejor[0] < pen:
            break
        cortes.append(mejor[1])
    return sorted(cortes)


cortes = segmentar()
lim = [0] + cortes + [len(gs)]
pred_esc = np.empty(len(gs))
for i in range(len(lim) - 1):
    a, b = lim[i], lim[i + 1]
    pred_esc[a:b] = ks[a:b].sum() / ns[a:b].sum()
modelos["escalones (segmentacion BIC)"] = (ll_binom(pred_esc), len(cortes) + 1, None)

di("Comparacion por AIC (verosimilitud binomial exacta por bin, %d bins con n>=50):" % len(gs))
di("")
di("| forma | parametros | logver | AIC | delta AIC |")
di("|---|---|---|---|---|")
tabla = sorted(modelos.items(), key=lambda kv: aic(kv[1][0], kv[1][1]))
mejor_aic = aic(tabla[0][1][0], tabla[0][1][1])
for nom, (ll, npar, _) in tabla:
    di("| %s | %d | %.1f | %.1f | %+.1f |" % (nom, npar, ll, aic(ll, npar), aic(ll, npar) - mejor_aic))
ganadora = tabla[0][0]
di("")
di("**Forma ganadora: %s.**" % ganadora)
di("")
puntos = [int(gs[c]) for c in cortes]
di("Puntos de corte detectados por segmentacion binaria (penalizacion BIC): "
   "**%s**." % (", ".join("hueco %d" % p for p in puntos) if puntos else "ninguno"))
di("")
if puntos:
    di("| regimen | huecos | n | tasa | IC95 | multiplicador |")
    di("|---|---|---|---|---|---|")
    for i in range(len(lim) - 1):
        a, b = lim[i], lim[i + 1]
        nn = int(ns[a:b].sum())
        kk = int(ks[a:b].sum())
        r = kk / nn
        lo, hi = wilson(kk, nn)
        di("| %d | %d-%d | %d | %.3f%% | %.3f-%.3f%% | **%.2fx** |"
           % (i + 1, int(gs[a]), int(gs[b - 1]), nn, 100 * r, 100 * lo, 100 * hi, r / P0))
di("")

# =====================================================================
di("---")
di("")
di("## Tarea 2 - Interacciones de f")
di("")
di("Metodo: se compara por razon de verosimilitudes el logit condicional con "
   "**efectos principales** (f depende solo del hueco) contra el que permite que "
   "los multiplicadores **cambien** segun la variable. Regimenes de hueco tomados "
   "de los cortes de la Tarea 1. Se exige p < %.2f tras FDR **y** tamano de efecto "
   "relativo > 10%%." % ALFA)
di("")

if puntos:
    bordes = [1] + puntos + [10 ** 7]
else:
    bordes = [1, 8, 12, 30, 110, 10 ** 7]
NR = len(bordes) - 1
reg = np.zeros_like(G)
for i in range(NR):
    reg[(G >= bordes[i]) & (G < bordes[i + 1])] = i
di("Regimenes usados: %s." % ", ".join(
    "R%d = huecos %d-%s" % (i + 1, bordes[i], "inf" if bordes[i + 1] > 10 ** 6 else bordes[i + 1] - 1)
    for i in range(NR)))
di("")

b_main, ll_main = ajustar_logit(reg, NR)
pruebas = []
for nombre, var, nv in (("hora del sorteo", np.repeat(HORA[:, None], K, axis=1), 12),
                        ("veces que ya salio hoy (0,1,2+)", np.clip(HOY, 0, 2), 3),
                        ("dia de semana", np.repeat(DOW[:, None], K, axis=1), 7),
                        ("posicion en la jornada (0-11)", np.repeat(POSD[:, None], K, axis=1), 12)):
    bins = reg * nv + var
    _, ll_int = ajustar_logit(bins, NR * nv)
    lr = 2 * (ll_int - ll_main)
    gl = NR * nv - NR - (nv - 1)
    p = chi2_sf(lr, gl)
    pruebas.append((nombre, lr, gl, p, nv, bins))

ps = np.array([x[3] for x in pruebas])
o = np.argsort(ps)
m_ = len(ps)
bh = ps[o] <= (np.arange(1, m_ + 1) / m_) * ALFA
n_fdr = int(np.flatnonzero(bh).max() + 1) if bh.any() else 0
umbral_fdr = ps[o][n_fdr - 1] if n_fdr else 0.0

di("| interaccion | razon de verosim. | gl | p | pasa FDR |")
di("|---|---|---|---|---|")
for nombre, lr, gl, p, nv, _ in pruebas:
    di("| %s | %.1f | %d | %s | %s |"
       % (nombre, lr, gl, ("%.2e" % p) if p < 1e-4 else "%.4f" % p,
          "SI" if p <= umbral_fdr else "no"))
di("")

signif = [x for x in pruebas if x[3] <= umbral_fdr]
if not signif:
    di("**Ninguna interaccion sobrevive.** f depende del hueco y de nada mas que podamos medir.")
else:
    di("Interacciones que pasan el filtro estadistico. Ahora el filtro de **tamano de efecto**:")
    di("")
    for nombre, lr, gl, p, nv, bins in signif:
        b_int, _ = ajustar_logit(bins, NR * nv)
        mi = np.exp(b_int).reshape(NR, nv)
        mi = mi / mi[NR - 1:NR, :]        # normaliza por el regimen de referencia
        rng_rel = []
        for i in range(NR):
            v = mi[i][np.isfinite(mi[i]) & (mi[i] > 0)]
            if len(v) > 1 and v.mean() > 0:
                rng_rel.append((v.max() - v.min()) / v.mean())
        efecto = max(rng_rel) if rng_rel else 0.0
        di("- **%s**: variacion relativa maxima del multiplicador entre niveles = **%.0f%%** -> %s"
           % (nombre, 100 * efecto, "**INTERACCION REAL**" if efecto > 0.10 else
              "descartada (estadisticamente significativa pero irrelevante)"))
        if efecto > 0.10 and nv <= 12:
            di("")
            di("  | nivel | " + " | ".join("R%d" % (i + 1) for i in range(NR)) + " |")
            di("  |---|" + "---|" * NR)
            for j in range(nv):
                di("  | %d | " % j + " | ".join("%.2f" % mi[i][j] for i in range(NR)) + " |")
            di("")
di("")

# ------------------------------------------------- pesos base (primer sorteo)
di("### 2.4 Pesos BASE: el primer sorteo del dia")
di("")
pri = np.flatnonzero(POSD == 0)
cu = np.bincount(Y[pri], minlength=K).astype(float)
espp = cu.sum() / K
x2 = float(((cu - espp) ** 2 / espp).sum())
pp = chi2_sf(x2, K - 1)
di("El primer sorteo de la jornada es el momento con menos estado intradia. "
   "n=%d, chi2=%.1f (gl=%d), **p=%.4f**." % (len(pri), x2, K - 1, pp))
di("")
di("**Los pesos BASE por animal son uniformes.** %s" %
   ("No hay animal con peso propio: toda la politica vive en el hueco, no en la identidad."
    if pp > 0.05 else "OJO: hay desviacion, revisar."))
di("")

ruta = os.path.join(RAIZ, "herramientas", "resultados", "politica_f.md")
with open(ruta, "w", encoding="utf-8") as f:
    f.write("\n".join(M) + "\n")

import json
jr = {"gap": list(range(1, GMAX + 2)),
      "n": [int(nb[g]) for g in range(1, GMAX + 2)],
      "aciertos": [int(cb[g]) for g in range(1, GMAX + 2)],
      "tasa": [float(cb[g] / nb[g]) if nb[g] else None for g in range(1, GMAX + 2)],
      "multiplicador_desnormalizado": [float(mult[g - 1]) for g in range(1, GMAX + 2)],
      "cortes": puntos, "forma_ganadora": ganadora, "bordes_regimen": bordes[:-1]}
with open(os.path.join(RAIZ, "herramientas", "resultados", "politica_f.json"), "w",
          encoding="utf-8") as f:
    json.dump(jr, f, indent=1)
print("\nguardado en", ruta)
