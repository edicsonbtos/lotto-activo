# -*- coding: utf-8 -*-
"""VECTOR 3 -- ATAQUE LCG / PRNG (descarte formal).

Trata la secuencia de animales como salida de un generador pseudoaleatorio y
busca estructura de PRNG debil. SOLO sobre el tramo de DESARROLLO [W, CORTE_FIJO).
El tramo de prueba (>=9357) NO se toca.

Expectativa declarada de antemano: BAJA. El sesgo ya documentado en este
proyecto es conductual (el operador evita repetir animales dentro del mismo
dia), no criptografico. Este script existe para descartarlo formalmente.

Dos hipotesis nulas, para no confundir "PRNG roto" con "sesgo ya conocido":
  NULO A  = iid uniforme sobre 38 animales (azar puro).
  NULO B  = permutacion DENTRO de cada jornada. Conserva que animales
            salieron cada dia (o sea, conserva el sesgo conductual) y destruye
            el ORDEN. Si un estadistico sigue siendo extremo contra el NULO B,
            hay estructura de orden mas alla de lo que ya sabemos.

Uso:  python prng_lcg.py
Salida: herramientas/resultados/vector3_prng.txt
"""
import math, os, sys, time
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

K = 38
ALFA = 0.01
N_PERM = 1000
RNG = np.random.default_rng(20260915)

L = []


def di(s=""):
    print(s, flush=True)
    L.append(s)


def norm_sf2(z):
    """Cola bilateral de la normal estandar."""
    return math.erfc(abs(z) / math.sqrt(2))


def chi2_sf(x, k):
    """Cola superior de chi2 con k gl (Wilson-Hilferty; suficiente para cribar)."""
    if k <= 0:
        return 1.0
    z = ((x / k) ** (1.0 / 3) - (1 - 2.0 / (9 * k))) / math.sqrt(2.0 / (9 * k))
    return 0.5 * math.erfc(z / math.sqrt(2))


def chi2_unif(cuentas):
    cuentas = np.asarray(cuentas, dtype=float)
    n = cuentas.sum()
    if n == 0:
        return 0.0, len(cuentas) - 1, 1.0
    esp = n / len(cuentas)
    x = ((cuentas - esp) ** 2 / esp).sum()
    gl = len(cuentas) - 1
    return x, gl, chi2_sf(x, gl)


# ------------------------------------------------------------------- datos
datos = LE.cargar()
n_tot = len(datos)
INI, FIN = LE.W, LE.CORTE_FIJO
s = datos.seq[INI:FIN].astype(np.int64)
hora = datos.hora[INI:FIN].astype(np.int64)
dia = datos.dia[INI:FIN].astype(np.int64)
fecha = datos.fecha[INI:FIN]
n = len(s)
p0 = 1.0 / K

di("=" * 78)
di(" VECTOR 3 -- ATAQUE LCG / PRNG      (solo tramo de DESARROLLO)")
di("=" * 78)
di(" historial completo: %d sorteos   |  tramo de prueba (>=%d): INTACTO" % (n_tot, LE.CORTE_FIJO))
di(" desarrollo analizado: [%d, %d) = %d sorteos, %s .. %s"
   % (INI, FIN, n, fecha[0], fecha[-1]))
di(" alfa = %.2f con correccion por comparaciones multiples donde aplica" % ALFA)
di(" permutaciones Monte Carlo por nulo: %d" % N_PERM)
di("")

dias_u = np.unique(dia)
idx_por_dia = [np.flatnonzero(dia == d) for d in dias_u]


def perm_dentro_dia(rng):
    t = s.copy()
    for ix in idx_por_dia:
        t[ix] = rng.permutation(s[ix])
    return t


def perm_iid(rng):
    return rng.integers(0, K, size=n)


# =====================================================================
di("-" * 78)
di(" 3.1  LCG DIRECTO mod 38   (hipotesis: s[t+1] = (a*s[t] + c) mod 38)")
di("-" * 78)
a_g, c_g = np.meshgrid(np.arange(K), np.arange(K), indexing="ij")
pred = (a_g[:, :, None] * s[None, None, :-1] + c_g[:, :, None]) % K
aciertos = (pred == s[None, None, 1:]).sum(axis=2)
mejor = int(aciertos.max())
ai, ci = np.unravel_index(int(aciertos.argmax()), aciertos.shape)
m = n - 1
z = (mejor - m * p0) / math.sqrt(m * p0 * (1 - p0))
p_bruto = norm_sf2(z) / 2
p_bonf = min(1.0, p_bruto * K * K)
di(" mejor par: a=%d c=%d -> %d/%d aciertos = %.3f%%  (azar %.3f%%)"
   % (ai, ci, mejor, m, 100 * mejor / m, 100 * p0))
di(" z = %+.2f   p bruto = %.4f   p Bonferroni (x%d) = %.4f" % (z, p_bruto, K * K, p_bonf))
ver31 = p_bonf < ALFA
di(" VEREDICTO 3.1: %s" % ("SENAL" if ver31 else "RUIDO"))

di("")
di(" reconstruccion algebraica (a,c desde 3 salidas consecutivas, validada en 1000):")


def inv_mod(x, mod):
    try:
        return pow(int(x), -1, mod)
    except ValueError:
        return None


val, intentos, resueltas = [], 0, 0
for t in range(0, 300):
    d1 = int(s[t + 1] - s[t]) % K
    inv = inv_mod(d1, K)
    intentos += 1
    if inv is None:
        continue
    resueltas += 1
    a = (int(s[t + 2] - s[t + 1]) * inv) % K
    c = (int(s[t + 1]) - a * int(s[t])) % K
    j0 = t + 3
    pr = (a * s[j0:j0 + 1000] + c) % K
    val.append((pr == s[j0 + 1:j0 + 1001]).mean())
val = np.array(val) if val else np.array([0.0])
di("   %d tripletas probadas, %d invertibles mod 38 (38=2*19 no es primo)"
   % (intentos, resueltas))
di("   tasa de validacion: media %.3f%%  max %.3f%%   (azar %.3f%%)"
   % (100 * val.mean(), 100 * val.max(), 100 * p0))
di("   VEREDICTO: %s" % ("SENAL" if val.max() > 0.10 else
                         "RUIDO -- ninguna reconstruccion sobrevive la validacion"))

# =====================================================================
di("")
di("-" * 78)
di(" 3.2  ESTRUCTURA DE RETICULO (LCG truncado: salida = (estado>>k) mod 38)")
di("-" * 78)
di(" No se puede invertir el truncamiento, pero un LCG truncado deja los pares")
di(" (s_t, s_t+1) sobre pocas rectas: para cada (u,v) se mira si (u*s_t+v*s_t+1)")
di(" mod 38 es uniforme. Un reticulo lo rompe con fuerza.")
di("")
di(" CUIDADO (defecto corregido en v2): si gcd(u,v,38)>1 la combinacion solo")
di(" puede caer en 38/g residuos, asi que da chi2 gigante SIEMPRE, hasta con")
di(" datos perfectamente aleatorios. Esas %d combinaciones se EXCLUYEN."
   % sum(1 for u in range(1, K) for v in range(K) if math.gcd(math.gcd(u, v), K) > 1))
di(" Ademas el recuento de significativas se calibra contra los dos nulos: la")
di(" evitacion intradia ya conocida tambien deforma la tabla de pares.")
UV = [(u, v) for u in range(1, K) for v in range(K) if math.gcd(math.gcd(u, v), K) == 1]
n_uv = len(UV)
ii, jj = np.meshgrid(np.arange(K), np.arange(K), indexing="ij")
MAPAS = [((u * ii + v * jj) % K).ravel() for u, v in UV]
umbral_bonf = ALFA / n_uv


def sig_reticulo(x):
    """Nº de (u,v) coprimas cuyo chi2 de uniformidad pasa Bonferroni, + p minimo."""
    T = np.bincount(x[:-1] * K + x[1:], minlength=K * K).astype(float)
    peor, cuenta = 1.0, 0
    arg = None
    for idx, mp in enumerate(MAPAS):
        cu = np.bincount(mp, weights=T, minlength=K)
        _, _, p = chi2_unif(cu)
        if p < umbral_bonf:
            cuenta += 1
        if p < peor:
            peor, arg = p, UV[idx]
    return cuenta, peor, arg


cuenta_sig, peor_p, peor_uv = sig_reticulo(s)
N_CAL = 200
calA = np.array([sig_reticulo(perm_iid(RNG))[0] for _ in range(N_CAL)])
calB = np.array([sig_reticulo(perm_dentro_dia(RNG))[0] for _ in range(N_CAL)])
pA_ret = max((calA >= cuenta_sig).mean(), 1.0 / N_CAL)
pB_ret = max((calB >= cuenta_sig).mean(), 1.0 / N_CAL)
di("")
di(" %d combinaciones (u,v) coprimas probadas; umbral Bonferroni = %.2e" % (n_uv, umbral_bonf))
di(" p minimo observado = %.2e en (u=%d, v=%d)" % (peor_p, peor_uv[0], peor_uv[1]))
di(" significativas con Bonferroni: %d de %d" % (cuenta_sig, n_uv))
di(" calibracion (%d permutaciones):" % N_CAL)
di("   NULO A (azar puro)      : media %.1f  max %d  -> p = %.4f" % (calA.mean(), calA.max(), pA_ret))
di("   NULO B (mismo dia)      : media %.1f  max %d  -> p = %.4f" % (calB.mean(), calB.max(), pB_ret))
ver32 = pB_ret < ALFA
di(" VEREDICTO 3.2: %s" % ("SENAL -- reticulo mas alla del sesgo conductual" if ver32
                           else "RUIDO -- lo que se ve lo explica el sesgo intradia ya conocido"))

# =====================================================================
di("")
di("-" * 78)
di(" 3.3  COMPLEJIDAD LINEAL (Berlekamp-Massey) -- hay un LFSR escondido?")
di("-" * 78)


def bm_gf2(bits):
    nn = len(bits)
    c = np.zeros(nn + 1, dtype=np.int64)
    b = np.zeros(nn + 1, dtype=np.int64)
    c[0] = b[0] = 1
    ll, mm = 0, -1
    for i in range(nn):
        d = int(bits[i])
        if ll:
            d += int(np.dot(c[1:ll + 1], bits[i - ll:i][::-1]))
        if d % 2 == 1:
            tmp = c.copy()
            desp = i - mm
            if desp < nn + 1:
                c[desp:] = (c[desp:] + b[:nn + 1 - desp]) % 2
            if 2 * ll <= i:
                ll = i + 1 - ll
                mm = i
                b = tmp
    return ll


def bm_gfp(sec, p):
    nn = len(sec)
    c = np.zeros(nn + 1, dtype=np.int64)
    b = np.zeros(nn + 1, dtype=np.int64)
    c[0] = b[0] = 1
    ll, mm, bb = 0, -1, 1
    for i in range(nn):
        d = int(sec[i]) % p
        if ll:
            d = (d + int(np.dot(c[1:ll + 1], sec[i - ll:i][::-1]))) % p
        if d != 0:
            tmp = c.copy()
            coef = (d * pow(int(bb), -1, p)) % p
            desp = i - mm
            if desp < nn + 1:
                c[desp:] = (c[desp:] - coef * b[:nn + 1 - desp]) % p
            if 2 * ll <= i:
                ll = i + 1 - ll
                mm = i
                b = tmp
                bb = d
    return ll


MB = 4000
ver33 = False
for nom, bits in (("paridad (s mod 2)", (s[:MB] % 2).astype(np.int64)),
                  ("mitad alta (s>=19)", (s[:MB] >= 19).astype(np.int64))):
    t0 = time.time()
    cl = bm_gf2(bits)
    di(" %-24s complejidad lineal = %5d de %d bits (esperado ~%d)  [%.1fs]"
       % (nom, cl, len(bits), len(bits) // 2, time.time() - t0))
    if cl < 0.4 * len(bits):
        ver33 = True
t0 = time.time()
NB19 = 2000
cl19 = bm_gfp((s[:NB19] % 19).astype(np.int64), 19)
di(" %-24s complejidad lineal = %5d de %d simbolos (esperado ~%d)  [%.1fs]"
   % ("s mod 19 sobre GF(19)", cl19, NB19, NB19 // 2, time.time() - t0))
if cl19 < 0.4 * NB19:
    ver33 = True
di(" VEREDICTO 3.3: %s" % ("SENAL -- hay recurrencia lineal corta" if ver33 else
                           "RUIDO -- complejidad maxima, no hay LFSR detectable"))

# =====================================================================
di("")
di("-" * 78)
di(" 3.4  PERIODICIDAD (autocorrelacion de largo alcance + FFT)")
di("-" * 78)
LAGS = 2000
zs = np.zeros(LAGS + 1)
for lag in range(1, LAGS + 1):
    mm_ = n - lag
    coin = int((s[:-lag] == s[lag:]).sum())
    zs[lag] = (coin - mm_ * p0) / math.sqrt(mm_ * p0 * (1 - p0))
di(" OJO (defecto corregido en v2): PERIODICIDAD significa que la secuencia se")
di(" REPITE a cierto lag, o sea z POSITIVO. Un z muy negativo es lo contrario:")
di(" evitacion, que es el sesgo conductual ya conocido. La v1 los mezclaba")
di(" usando |z| y por eso marcaba SENAL de periodicidad donde no la hay.")
di("")
zpos = float(zs[1:].max())
lag_pos = int(zs[1:].argmax() + 1)
p_pos = norm_sf2(zpos) / 2
p_bonf_lag = min(1.0, p_pos * LAGS)
zneg = float(zs[1:].min())
lag_neg = int(zs[1:].argmin() + 1)
di(" coincidencias s[t]==s[t+lag] para lag=1..%d  (azar %.3f%%)" % (LAGS, 100 * p0))
di(" PERIODICIDAD (z positivo): z max = %+.2f en lag=%d  p bruto=%.4f  p Bonferroni(x%d)=%.4f"
   % (zpos, lag_pos, p_pos, LAGS, p_bonf_lag))
di(" EVITACION  (z negativo): z min = %+.2f en lag=%d  <- sesgo conductual conocido, NO es PRNG"
   % (zneg, lag_neg))
di(" lags con z>+3 (repeticion): %d  |  lags con z<-3 (evitacion): %d  (esperados ~%.1f cada uno)"
   % (int((zs[1:] > 3).sum()), int((zs[1:] < -3).sum()), LAGS * 0.00135))
di(" lag 12 (mismo sorteo, dia siguiente): z=%+.2f | lag 24: z=%+.2f | lag 84 (1 semana): z=%+.2f"
   % (zs[12], zs[24], zs[84]))
mas_neg = (np.argsort(zs[1:13]) + 1)[:3]
di(" lags 1-12 mas negativos (evitacion intradia): " +
   ", ".join("lag %d z=%+.1f" % (int(i), zs[int(i)]) for i in mas_neg))


def fisher_g(x):
    x = x - x.mean()
    P = np.abs(np.fft.rfft(x))[1:] ** 2
    if len(P) < 2 or P.sum() == 0:
        return 1.0
    g = float(P.max() / P.sum())
    mq = len(P)
    tot, j = 0.0, 1
    while j <= min(int(1 / g), 20):
        tot += ((-1) ** (j - 1)) * math.exp(
            math.lgamma(mq + 1) - math.lgamma(j + 1) - math.lgamma(mq - j + 1)
            + (mq - 1) * math.log(max(1e-300, 1 - j * g)))
        j += 1
    return max(0.0, min(1.0, tot))


ps_f = np.array([fisher_g((s == a).astype(float)) for a in range(K)])
n_bonf_f = int((ps_f < ALFA / K).sum())
bh_f = np.sort(ps_f) <= (np.arange(1, K + 1) / K) * ALFA
n_fdr_f = int(np.flatnonzero(bh_f).max() + 1) if bh_f.any() else 0
di(" Fisher g-test del periodograma, un test por animal (38 tests):")
di("   p minimo = %.4f (animal %s);  significativos: Bonferroni %d/38, FDR %d/38"
   % (ps_f.min(), LE.POS[int(ps_f.argmin())], n_bonf_f, n_fdr_f))
ver34 = (p_bonf_lag < ALFA) or (n_bonf_f > 0)
di(" VEREDICTO 3.4 (periodicidad): %s" % ("SENAL" if ver34 else
    "RUIDO -- ninguna periodicidad sobrevive la correccion"))
di(" (la evitacion a lag corto NO cuenta aqui: es el vector 2, no el 3)")

# =====================================================================
di("")
di("-" * 78)
di(" 3.5  SEMILLA POR TIMESTAMP  (re-siembra diaria? patron por hora?)")
di("-" * 78)
primero = np.array([ix[0] for ix in idx_por_dia if len(ix) > 0])
cu_p = np.bincount(s[primero], minlength=K)
x, gl, p_pri = chi2_unif(cu_p)
di(" primer sorteo del dia: n=%d  chi2=%.1f (gl=%d) p=%.4f" % (len(primero), x, gl, p_pri))
resto = np.setdiff1d(np.arange(n), primero)
cu_r = np.bincount(s[resto], minlength=K)
xr, glr, p_res = chi2_unif(cu_r)
di(" resto de sorteos      : n=%d  chi2=%.1f (gl=%d) p=%.4f" % (len(resto), xr, glr, p_res))
tab = np.vstack([cu_p, cu_r]).astype(float)
tot = tab.sum()
esp = np.outer(tab.sum(1), tab.sum(0)) / tot
x2 = float(((tab - esp) ** 2 / np.maximum(esp, 1e-9)).sum())
p_h = chi2_sf(x2, K - 1)
di(" primero vs resto (homogeneidad 2x38): chi2=%.1f (gl=%d) p=%.4f" % (x2, K - 1, p_h))
di("   -> si el operador re-sembrara cada dia, el primer sorteo del dia tendria")
di("      otra distribucion. p=%.4f: %s" % (p_h, "SUGIERE DIFERENCIA" if p_h < ALFA
                                            else "no la tiene"))
ps_h = []
for h in range(12):
    cu = np.bincount(s[hora == h], minlength=K)
    ps_h.append(chi2_unif(cu)[2])
ps_h = np.array(ps_h)
di(" uniformidad por hora (12 tests): p minimo=%.4f (hora %d); umbral Bonferroni=%.4f -> %d significativas"
   % (ps_h.min(), int(ps_h.argmin()), ALFA / 12, int((ps_h < ALFA / 12).sum())))
ver35 = (p_h < ALFA) or bool((ps_h < ALFA / 12).any()) or (p_pri < ALFA)
di(" VEREDICTO 3.5: %s" % ("SENAL" if ver35 else "RUIDO"))

# =====================================================================
di("")
di("-" * 78)
di(" 3.6  BATERIA DIEHARD SIMPLIFICADA  (contra NULO A y contra NULO B)")
di("-" * 78)


def est_monobit(x):
    return abs(float((x % 2).mean()) - 0.5)


def est_rachas(x):
    b = (x % 2).astype(np.int8)
    return float((b[1:] != b[:-1]).sum())


def est_serial(x):
    idx = x[:-1] * K + x[1:]
    cu = np.bincount(idx, minlength=K * K)
    return chi2_unif(cu)[0]


def est_colisiones(x):
    return float((x[1:] == x[:-1]).sum())


def est_distintos_jornada(x):
    return float(np.mean([len(np.unique(x[ix])) for ix in idx_por_dia]))


def est_gaps(x):
    tot = 0.0
    for a in range(K):
        pos = np.flatnonzero(x == a)
        if len(pos) < 3:
            continue
        g = np.diff(pos)
        espg = 1.0 / p0
        tot += ((g.mean() - espg) ** 2) / (espg ** 2 / len(g))
    return tot


ESTS = [("monobit (paridad)", est_monobit),
        ("rachas de paridad", est_rachas),
        ("serial 38x38 (pares)", est_serial),
        ("colisiones lag-1", est_colisiones),
        ("distintos por jornada", est_distintos_jornada),
        ("gaps vs geometrica", est_gaps)]
obs = {nom: f(s) for nom, f in ESTS}
di(" %d permutaciones por nulo, 2 nulos..." % N_PERM)
nulA = {nom: np.empty(N_PERM) for nom, _ in ESTS}
nulB = {nom: np.empty(N_PERM) for nom, _ in ESTS}
t0 = time.time()
for i in range(N_PERM):
    xa = perm_iid(RNG)
    xb = perm_dentro_dia(RNG)
    for nom, f in ESTS:
        nulA[nom][i] = f(xa)
        nulB[nom][i] = f(xb)
di(" (%.0f s)" % (time.time() - t0))
di("")
di(" %-24s %10s | %-21s | %-21s" % ("estadistico", "observado",
                                    "vs NULO A (azar puro)", "vs NULO B (mismo dia)"))
di(" " + "-" * 76)
ver36A = ver36B = False
umbral_bat = ALFA / len(ESTS)
for nom, _ in ESTS:
    o = obs[nom]
    pa = min(1.0, max(2 * min(float((nulA[nom] >= o).mean()), float((nulA[nom] <= o).mean())), 1.0 / N_PERM))
    pb = min(1.0, max(2 * min(float((nulB[nom] >= o).mean()), float((nulB[nom] <= o).mean())), 1.0 / N_PERM))
    if pa < umbral_bat:
        ver36A = True
    if pb < umbral_bat:
        ver36B = True
    di(" %-24s %10.4f | p=%.4f %-11s | p=%.4f %-11s"
       % (nom, o, pa, "SIGNIF" if pa < umbral_bat else "no",
          pb, "SIGNIF" if pb < umbral_bat else "no"))
di("")
di(" Bonferroni dentro de la bateria: umbral = %.4f" % umbral_bat)
di(" vs NULO A (azar puro)           : %s" % ("HAY ESTRUCTURA" if ver36A else "nada"))
di(" vs NULO B (orden dentro del dia): %s" % ("HAY ESTRUCTURA DE ORDEN" if ver36B else
    "nada -- lo que se ve se explica por QUE animales salen cada dia"))

# =====================================================================
di("")
di("=" * 78)
di(" VEREDICTO VECTOR 3")
di("=" * 78)
for nom, v in (("3.1 LCG directo mod 38", ver31),
               ("3.2 reticulo / LCG truncado", ver32),
               ("3.3 complejidad lineal (LFSR)", ver33),
               ("3.4 periodicidad FFT/autocorr", ver34),
               ("3.5 semilla por timestamp", ver35)):
    di("   %-32s %s" % (nom, "SENAL" if v else "RUIDO"))
prng = ver31 or ver32 or ver33 or ver34
di("")
if prng:
    di(" LCG/PRNG DEBIL: SENAL REAL -- hay estructura de generador. Revisar arriba.")
else:
    di(" LCG/PRNG DEBIL: RUIDO.")
    di(" Ni reconstruccion algebraica, ni reticulo, ni recurrencia lineal, ni")
    di(" periodicidad sobreviven la correccion por comparaciones multiples.")
    di(" El vector 3 queda ARCHIVADO.")
    if ver36A and not ver36B:
        di("")
        di(" CONFIRMADO ademas: la estructura que SI existe es conductual, no")
        di(" criptografica. Los estadisticos se desvian del azar puro (NULO A)")
        di(" pero NO del nulo que conserva la composicion de cada jornada")
        di(" (NULO B): la grieta esta en QUE animales salen cada dia, no en el")
        di(" orden en que los escupiria un generador.")
di("=" * 78)

ruta = os.path.join(RAIZ, "herramientas", "resultados", "vector3_prng.txt")
with open(ruta, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
print("\nguardado en", ruta)
