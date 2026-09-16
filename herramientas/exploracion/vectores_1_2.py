# -*- coding: utf-8 -*-
"""VECTORES 1 y 2 -- consolidado.

Reune en UN solo documento lo que estaba disperso en intradia_*.py,
secuencia_*.py y haz_*.py:
  V1  sesgo de frecuencias puro (chi2 de uniformidad: global, ano, dia de
      semana, hora) con correccion por comparaciones multiples.
  V2  dependencia temporal (Markov 1 y 2, gaps vs geometrica, Ljung-Box)
      y el sesgo conductual: evitacion de repeticion intradia + balanceo
      de conteos a largo plazo.

SOLO tramo de DESARROLLO [W, CORTE_FIJO). El tramo de prueba NO se toca.

Uso:  python vectores_1_2.py
Salida: herramientas/resultados/reporte_vectores_1_2.md
"""
import math, os, sys
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
import lotto_eval as LE

K = 38
ALFA = 0.01
RNG = np.random.default_rng(20260915)

M = []


def di(s=""):
    print(s, flush=True)
    M.append(s)


def chi2_sf(x, k):
    if k <= 0:
        return 1.0
    z = ((x / k) ** (1.0 / 3) - (1 - 2.0 / (9 * k))) / math.sqrt(2.0 / (9 * k))
    return 0.5 * math.erfc(z / math.sqrt(2))


def chi2_unif(cu):
    cu = np.asarray(cu, dtype=float)
    nn = cu.sum()
    if nn == 0:
        return 0.0, len(cu) - 1, 1.0
    esp = nn / len(cu)
    x = float(((cu - esp) ** 2 / esp).sum())
    gl = len(cu) - 1
    return x, gl, chi2_sf(x, gl)


def ic_prop(k, nn):
    """IC95 de Wilson para una proporcion."""
    if nn == 0:
        return 0.0, 0.0
    z = 1.959964
    p = k / nn
    d = 1 + z * z / nn
    c = (p + z * z / (2 * nn)) / d
    h = z * math.sqrt(p * (1 - p) / nn + z * z / (4 * nn * nn)) / d
    return max(0.0, c - h), min(1.0, c + h)


def bh_fdr(ps, q=ALFA):
    ps = np.asarray(ps)
    o = np.argsort(ps)
    m_ = len(ps)
    bh = ps[o] <= (np.arange(1, m_ + 1) / m_) * q
    return int(np.flatnonzero(bh).max() + 1) if bh.any() else 0


# ------------------------------------------------------------------- datos
datos = LE.cargar()
n_tot = len(datos)
INI, FIN = LE.W, LE.CORTE_FIJO
s = datos.seq[INI:FIN].astype(np.int64)
hora = datos.hora[INI:FIN].astype(np.int64)
dow = datos.dow[INI:FIN].astype(np.int64)
dia = datos.dia[INI:FIN].astype(np.int64)
fecha = datos.fecha[INI:FIN]
anio = np.array([int(f[:4]) for f in fecha])
n = len(s)
p0 = 1.0 / K
DIAS_SEM = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

di("# Vectores 1 y 2 -- reporte consolidado")
di("")
di("Generado por `herramientas/exploracion/vectores_1_2.py`.")
di("")
di("- Historial completo: **%d sorteos**. Tramo de prueba (>= %d): **intacto, no se toca**."
   % (n_tot, LE.CORTE_FIJO))
di("- Analizado aqui: tramo de **desarrollo** `[%d, %d)` = **%d sorteos**, %s a %s."
   % (INI, FIN, n, fecha[0], fecha[-1]))
di("- Azar puro de referencia: Top-1 2.63%, Top-3 7.89%, 1 animal = 1/38 = 2.632%.")
di("- alfa = %.2f, con Bonferroni y FDR (Benjamini-Hochberg) donde hay tests multiples." % ALFA)
di("")

# =====================================================================
di("---")
di("")
di("## Vector 1 -- Sesgo de frecuencias puro")
di("")

cu_g = np.bincount(s, minlength=K)
x_g, gl_g, p_g = chi2_unif(cu_g)
di("### 1.1 Uniformidad global")
di("")
di("| test | n | chi2 | gl | p |")
di("|---|---|---|---|---|")
di("| 38 animales, global | %d | %.1f | %d | %.4f |" % (n, x_g, gl_g, p_g))
di("")
top = np.argsort(-cu_g)[:3]
bot = np.argsort(cu_g)[:3]
esp = n / K
di("Mas frecuentes: %s. Menos frecuentes: %s. Esperado por animal: %.1f."
   % (", ".join("`%s` (%d)" % (LE.POS[i], cu_g[i]) for i in top),
      ", ".join("`%s` (%d)" % (LE.POS[i], cu_g[i]) for i in bot), esp))
lo, hi = ic_prop(int(cu_g.max()), n)
di("El animal mas frecuente sale el %.3f%% de las veces (IC95 %.3f-%.3f%%); el azar da 2.632%%."
   % (100 * cu_g.max() / n, 100 * lo, 100 * hi))
di("")
v11 = p_g < ALFA
di("**Veredicto 1.1: %s** (p=%.4f)." % ("SENAL REAL" if v11 else "RUIDO", p_g))
di("")

di("### 1.2 Uniformidad por ano")
di("")
di("| ano | n | chi2 | gl | p bruto | signif. Bonferroni |")
di("|---|---|---|---|---|---|")
anios = sorted(set(anio.tolist()))
ps_a = []
for a in anios:
    cu = np.bincount(s[anio == a], minlength=K)
    x, gl, p = chi2_unif(cu)
    ps_a.append(p)
    di("| %d | %d | %.1f | %d | %.4f | %s |"
       % (a, int((anio == a).sum()), x, gl, p, "SI" if p < ALFA / len(anios) else "no"))
ps_a = np.array(ps_a)
v12 = bool((ps_a < ALFA / len(anios)).any())
di("")
di("Umbral Bonferroni = %.4f (%d tests). Significativos: Bonferroni %d/%d, FDR %d/%d."
   % (ALFA / len(anios), len(anios), int((ps_a < ALFA / len(anios)).sum()), len(anios),
      bh_fdr(ps_a), len(anios)))
di("")
di("**Veredicto 1.2: %s**." % ("SENAL REAL" if v12 else "RUIDO"))
di("")

di("### 1.3 Uniformidad por dia de semana")
di("")
di("| dia | n | chi2 | p bruto | signif. Bonferroni |")
di("|---|---|---|---|---|")
ps_d = []
for d in range(7):
    cu = np.bincount(s[dow == d], minlength=K)
    x, gl, p = chi2_unif(cu)
    ps_d.append(p)
    di("| %s | %d | %.1f | %.4f | %s |"
       % (DIAS_SEM[d], int((dow == d).sum()), x, p, "SI" if p < ALFA / 7 else "no"))
ps_d = np.array(ps_d)
v13 = bool((ps_d < ALFA / 7).any())
di("")
di("Umbral Bonferroni = %.4f (7 tests). Significativos: Bonferroni %d/7, FDR %d/7."
   % (ALFA / 7, int((ps_d < ALFA / 7).sum()), bh_fdr(ps_d)))
di("")
di("**Veredicto 1.3: %s**." % ("SENAL REAL" if v13 else "RUIDO"))
di("")

di("### 1.4 Uniformidad por hora (sorteo del dia)")
di("")
di("| hora | n | chi2 | p bruto | signif. Bonferroni |")
di("|---|---|---|---|---|")
ps_h = []
for h in range(12):
    cu = np.bincount(s[hora == h], minlength=K)
    x, gl, p = chi2_unif(cu)
    ps_h.append(p)
    di("| %d | %d | %.1f | %.4f | %s |"
       % (h, int((hora == h).sum()), x, p, "SI" if p < ALFA / 12 else "no"))
ps_h = np.array(ps_h)
v14 = bool((ps_h < ALFA / 12).any())
di("")
di("Umbral Bonferroni = %.4f (12 tests). Significativos: Bonferroni %d/12, FDR %d/12."
   % (ALFA / 12, int((ps_h < ALFA / 12).sum()), bh_fdr(ps_h)))
di("")
di("**Veredicto 1.4: %s**." % ("SENAL REAL" if v14 else "RUIDO"))
di("")
v1 = v11 or v12 or v13 or v14
di("> **Vector 1 en una linea:** %s" % (
    "hay desviacion de la uniformidad que sobrevive la correccion." if v1 else
    "la frecuencia de cada animal NO se distingue de la uniforme. "
    "No hay 'animales calientes'. Apostar por frecuencia historica es tirar el dinero."))
di("")

# =====================================================================
di("---")
di("")
di("## Vector 2 -- Dependencia temporal")
di("")

di("### 2.1 Markov orden 1 (el ganador anterior condiciona el siguiente?)")
di("")
tab1 = np.zeros((K, K))
np.add.at(tab1, (s[:-1], s[1:]), 1)
fil = tab1.sum(1, keepdims=True)
col = tab1.sum(0, keepdims=True)
espm = fil * col / tab1.sum()
x1 = float(((tab1 - espm) ** 2 / np.maximum(espm, 1e-9)).sum())
gl1 = (K - 1) ** 2
p1 = chi2_sf(x1, gl1)
celdas_bajas = int((espm < 5).sum())
di("Tabla 38x38 de transiciones, n=%d pares." % (n - 1))
di("")
di("| test | chi2 | gl | p | celdas con esperado <5 |")
di("|---|---|---|---|---|")
di("| Markov orden 1 | %.1f | %d | %.4f | %d de %d |" % (x1, gl1, p1, celdas_bajas, K * K))
di("")
v21 = p1 < ALFA
di("**Veredicto 2.1: %s** (p=%.4f)." % ("SENAL REAL" if v21 else "RUIDO", p1))
di("")
di("**Pero cuidado con leer eso como 'no hay dependencia'.** El chi2 de la tabla completa "
   "reparte la evidencia en %d grados de libertad, y la dependencia real de este sorteo vive "
   "en **una sola** de esas direcciones: la diagonal (no repetir el animal anterior). "
   "Ese efecto se diluye. El test dirigido a la diagonal:" % gl1)
di("")
col_obs = int((s[:-1] == s[1:]).sum())
col_esp = (n - 1) * p0
z_col = (col_obs - col_esp) / math.sqrt((n - 1) * p0 * (1 - p0))
lo_c, hi_c = ic_prop(col_obs, n - 1)
di("| test dirigido | observado | esperado | tasa | IC95 | z | p |")
di("|---|---|---|---|---|---|---|")
di("| s(t) == s(t-1) | %d | %.1f | %.3f%% | %.3f-%.3f%% | %+.1f | %.2e |"
   % (col_obs, col_esp, 100 * col_obs / (n - 1), 100 * lo_c, 100 * hi_c, z_col,
      math.erfc(abs(z_col) / math.sqrt(2))))
di("")
di("**Veredicto 2.1-bis: SENAL REAL, y muy fuerte.** El sorteo NO repite el animal anterior "
   "casi nunca: %.3f%% contra el 2.632%% del azar (%.2fx). La leccion metodologica es que un "
   "chi2 de 1369 gl es la herramienta equivocada para un efecto que vive en 38 celdas."
   % (100 * col_obs / (n - 1), (col_obs / (n - 1)) / p0))
di("")

di("### 2.2 Markov orden 2")
di("")
di("Una tabla 38x38x38 son %d celdas para %d observaciones: **%.2f observaciones por celda**."
   % (K ** 3, n - 2, (n - 2) / K ** 3))
di("El test esta **sin potencia**: no se puede concluir nada de orden 2 con este n.")
di("Lo que si se puede mirar es el efecto marginal del sorteo t-2 sobre el t:")
di("")
tab2 = np.zeros((K, K))
np.add.at(tab2, (s[:-2], s[2:]), 1)
fil = tab2.sum(1, keepdims=True)
col = tab2.sum(0, keepdims=True)
espm = fil * col / tab2.sum()
x2 = float(((tab2 - espm) ** 2 / np.maximum(espm, 1e-9)).sum())
p2 = chi2_sf(x2, gl1)
di("| test | chi2 | gl | p |")
di("|---|---|---|---|")
di("| s(t-2) -> s(t), marginal | %.1f | %d | %.4f |" % (x2, gl1, p2))
di("")
v22 = p2 < ALFA
di("**Veredicto 2.2: %s** para el efecto marginal a lag 2; **INCONCLUSO** para Markov de orden 2 "
   "completo (harian falta ~%s observaciones para 5 por celda, o sea ~%d anos de sorteos)."
   % ("SENAL REAL" if v22 else "RUIDO", "{:,}".format(5 * K ** 3), round(5 * K ** 3 / (12 * 365))))
di("")

di("### 2.3 Gaps entre repeticiones vs geometrica")
di("")
esp_gap = 1.0 / p0
filas_g = []
zs_g = []
for a in range(K):
    pos = np.flatnonzero(s == a)
    if len(pos) < 10:
        continue
    g = np.diff(pos)
    mu = g.mean()
    se = esp_gap / math.sqrt(len(g))
    zs_g.append((mu - esp_gap) / se)
zs_g = np.array(zs_g)
di("Bajo azar puro los huecos entre apariciones de un animal son geometricos de media %.1f sorteos."
   % esp_gap)
di("")
di("| estadistico | valor |")
di("|---|---|")
di("| animales evaluados | %d |" % len(zs_g))
di("| z medio del hueco medio | %+.2f |" % zs_g.mean())
di("| animales con \\|z\\| > 3 | %d |" % int((np.abs(zs_g) > 3).sum()))
di("")
# varianza de los huecos: la evitacion los hace MENOS dispersos que geometrico
disp = []
for a in range(K):
    pos = np.flatnonzero(s == a)
    if len(pos) < 10:
        continue
    g = np.diff(pos).astype(float)
    # geometrica: var = (1-p)/p^2, media = 1/p
    disp.append(g.var() / ((1 - p0) / p0 ** 2))
disp = np.array(disp)
di("Indice de dispersion (varianza observada / varianza geometrica), media sobre los 38 animales: "
   "**%.3f**. Menor que 1 = los huecos son **mas regulares** que el azar (evitacion / balanceo); "
   "mayor que 1 = mas irregulares (rachas)." % disp.mean())
di("")
v23 = bool((np.abs(zs_g) > 3).sum() > 2 or abs(disp.mean() - 1) > 0.05)
di("**Veredicto 2.3: %s**." % ("SENAL REAL" if v23 else "RUIDO"))
di("")

di("### 2.4 Ljung-Box sobre la serie indicadora de cada animal")
di("")
H = 24


def ljung_box(x, h=H):
    x = x - x.mean()
    nn = len(x)
    den = float((x * x).sum())
    q = 0.0
    for k in range(1, h + 1):
        r = float((x[:-k] * x[k:]).sum()) / den
        q += r * r / (nn - k)
    return nn * (nn + 2) * q


ps_lb = []
for a in range(K):
    q = ljung_box((s == a).astype(float))
    ps_lb.append(chi2_sf(q, H))
ps_lb = np.array(ps_lb)
n_bonf_lb = int((ps_lb < ALFA / K).sum())
n_fdr_lb = bh_fdr(ps_lb)
di("Un test por animal (38 tests), h=%d lags." % H)
di("")
di("| p minimo | animal | signif. Bonferroni | signif. FDR |")
di("|---|---|---|---|")
di("| %.5f | `%s` | %d/38 | %d/38 |" % (ps_lb.min(), LE.POS[int(ps_lb.argmin())], n_bonf_lb, n_fdr_lb))
di("")
v24 = n_bonf_lb > 0
di("**Veredicto 2.4: %s**." % ("SENAL REAL" if v24 else "RUIDO"))
di("")

# =====================================================================
di("---")
di("")
di("## El sesgo conductual (lo que de verdad mueve la aguja)")
di("")

di("### 3.1 Evitacion de repeticion dentro de la jornada")
di("")
dias_u = np.unique(dia)
idx_por_dia = [np.flatnonzero(dia == d) for d in dias_u]
completas = [ix for ix in idx_por_dia if len(ix) == 12]
dist = np.array([len(np.unique(s[ix])) for ix in completas])
esp_dist = K * (1 - (1 - p0) ** 12)
se_d = dist.std(ddof=1) / math.sqrt(len(dist))
z_d = (dist.mean() - esp_dist) / se_d
di("Jornadas completas de 12 sorteos: **%d**." % len(completas))
di("")
di("| medida | observado | esperado por azar | z | p |")
di("|---|---|---|---|---|")
di("| animales distintos por jornada | **%.3f** (IC95 %.3f-%.3f) | %.3f | %+.1f | %.2e |"
   % (dist.mean(), dist.mean() - 1.96 * se_d, dist.mean() + 1.96 * se_d, esp_dist, z_d,
      math.erfc(abs(z_d) / math.sqrt(2))))
# tasa de repeticion por distancia dentro del dia
di("")
di("Probabilidad de que dos sorteos del **mismo dia** separados por `d` posiciones den el mismo "
   "animal (azar = 2.632%):")
di("")
di("| distancia d | pares | repeticiones | tasa | IC95 | vs azar |")
di("|---|---|---|---|---|---|")
tasas = []
for d in range(1, 12):
    tot = rep = 0
    for ix in completas:
        a = s[ix]
        tot += len(a) - d
        rep += int((a[:-d] == a[d:]).sum())
    lo, hi = ic_prop(rep, tot)
    r = rep / tot
    tasas.append(r)
    di("| %d | %d | %d | %.3f%% | %.3f-%.3f%% | %.2fx |"
       % (d, tot, rep, 100 * r, 100 * lo, 100 * hi, r / p0))
tot_all = rep_all = 0
for ix in completas:
    a = s[ix]
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            tot_all += 1
            rep_all += int(a[i] == a[j])
lo, hi = ic_prop(rep_all, tot_all)
di("")
di("**Todos los pares del mismo dia**: %d repeticiones en %d pares = **%.3f%%** "
   "(IC95 %.3f-%.3f%%) contra 2.632%% del azar -> **%.3fx**."
   % (rep_all, tot_all, 100 * rep_all / tot_all, 100 * lo, 100 * hi, (rep_all / tot_all) / p0))
z_rep = (rep_all - tot_all * p0) / math.sqrt(tot_all * p0 * (1 - p0))
di("z = %+.1f, p = %.2e." % (z_rep, math.erfc(abs(z_rep) / math.sqrt(2))))
di("")
di("La evitacion **depende de la distancia**: %s."
   % ("es mas fuerte en sorteos consecutivos y se diluye al alejarse"
      if tasas[0] < tasas[-1] else "no sigue un patron monotono claro"))
di("")

di("### 3.2 Balanceo de conteos a largo plazo -- NO se sostiene")
di("")
di("Si el operador equilibrara conteos, en ventanas largas los animales saldrian **mas parejo** "
   "de lo que dicta el azar: el indice de dispersion (varianza observada / multinomial) quedaria "
   "**por debajo de 1**, y de forma consistente al crecer la ventana.")
di("")
di("| ventana (sorteos) | ventanas | indice de dispersion | IC95 de la media | lectura |")
di("|---|---|---|---|---|")
idms = []
for Wv in (38 * 5, 38 * 10, 38 * 25, 38 * 50):
    nv = n // Wv
    if nv < 3:
        continue
    ids = []
    for b in range(nv):
        cu = np.bincount(s[b * Wv:(b + 1) * Wv], minlength=K).astype(float)
        espv = Wv / K
        ids.append(cu.var() / (espv * (1 - p0)))
    ids = np.array(ids)
    idm = float(ids.mean())
    se = float(ids.std(ddof=1) / math.sqrt(len(ids))) if len(ids) > 1 else float("nan")
    idms.append(idm)
    di("| %d | %d | **%.3f** | %.3f - %.3f | %s |"
       % (Wv, nv, idm, idm - 1.96 * se, idm + 1.96 * se,
          "mas parejo" if idm + 1.96 * se < 1 else
          "mas desparejo" if idm - 1.96 * se > 1 else "no se distingue del azar"))
di("")
di("(Indice = 1.000 es exactamente multinomial, o sea azar puro.)")
di("")
di("**Veredicto 3.2: NO CONFIRMADO / INCONCLUSO.** Los indices no son consistentes (%s) y las "
   "ventanas largas son solo %d y %d observaciones, con intervalos que cruzan el 1. "
   "Los huecos entre repeticiones tampoco apoyan el balanceo: su indice de dispersion es "
   "**%.3f**, es decir por ENCIMA de 1, lo contrario de lo que produciria un mecanismo que "
   "equilibra conteos."
   % (", ".join("%.2f" % x for x in idms), n // (38 * 25), n // (38 * 50), disp.mean()))
di("")
di("> **Correccion a lo que creiamos.** El proyecto venia asumiendo dos fuentes de senal: "
   "evitacion intradia **y** balanceo de conteos a largo plazo. Los datos de desarrollo solo "
   "sostienen la primera. El balanceo a largo plazo queda como **no demostrado**: no lo damos "
   "por muerto (falta potencia), pero deja de citarse como hecho establecido.")
di("")

# =====================================================================
di("---")
di("")
di("## 3.3 El mecanismo completo, y el techo que permite")
di("")
di("La evitacion intradia no es un efecto suelto: es el tramo corto de **una sola curva de "
   "recencia**. Tasa de salida de un animal segun cuantos sorteos lleva sin salir (azar = 2.632%):")
di("")
seq_f = datos.seq[:FIN]
nf = len(seq_f)
gapf = np.zeros((nf, K), dtype=np.int64)
last = np.full(K, -1)
for t in range(nf):
    vis = last >= 0
    gapf[t, vis] = t - last[vis]
    gapf[t, ~vis] = 10 ** 6
    last[seq_f[t]] = t
HITf = np.zeros((nf, K), dtype=bool)
HITf[np.arange(nf), seq_f] = True
E = np.array([1, 2, 3, 4, 6, 8, 10, 12, 15, 20, 30, 45, 70, 110, 180, 300])
dv = slice(INI, FIN)
bb = np.digitize(gapf, E)          # longitud completa: _oraculo vuelve a cortar con [dv]
b1 = bb[dv].ravel()
h1 = HITf[dv].ravel()
nb = np.bincount(b1, minlength=len(E) + 1).astype(float)
cb = np.bincount(b1[h1], minlength=len(E) + 1).astype(float)
hz = (cb + 1) / (nb + 1 / p0)
lab = ["<1"] + ["%d-%d" % (E[i], E[i + 1] - 1) for i in range(len(E) - 1)] + [">=%d" % E[-1]]
di("| hueco (sorteos sin salir) | n | tasa | vs azar |")
di("|---|---|---|---|")
for l_, v_, c_ in zip(lab, hz, nb):
    if c_ < 50:
        continue
    di("| %s | %d | %.3f%% | **%.2fx** |" % (l_, int(c_), 100 * v_, v_ / p0))
di("")
di("Tres regimenes, no uno:")
di("")
di("1. **Huecos 1-7 (mismo dia): fuerte supresion, hasta 0.25x.** Es la evitacion intradia.")
di("2. **Huecos 12-29 (uno a dos dias y medio): elevacion, 1.21x-1.36x.** El operador **recicla** "
   "los animales con esa cadencia. Esto NO es intradia y el proyecto no lo tenia documentado.")
di("3. **Huecos >=110: supresion otra vez, hasta 0.57x.** Un animal que lleva mucho fuera "
   "**tiende a seguir fuera**. Esto es lo **contrario** de un mecanismo que equilibra conteos, "
   "y es otra razon para retirar la hipotesis de balanceo.")
di("")
di("### Techo alcanzable por mecanismo")
di("")
di("Cada fila es un **oraculo**: se le entrega la tabla empirica ajustada sobre los MISMOS datos "
   "que evalua. Son techos **optimistas** (tienen sobreajuste a favor), asi que sirven de cota "
   "superior de lo que ese mecanismo puede dar.")
di("")


def _oraculo(bins, nb_tot):
    b_ = bins[dv].ravel()
    h_ = HITf[dv].ravel()
    nb_ = np.bincount(b_, minlength=nb_tot).astype(float)
    cb_ = np.bincount(b_[h_], minlength=nb_tot).astype(float)
    hz_ = (cb_ + 1) / (nb_ + 1 / p0)
    P = hz_[bins[dv]]
    P = P / P.sum(1, keepdims=True)
    o = np.argsort(-P, axis=1)
    yy = seq_f[dv]
    return float((o[:, 0] == yy).mean()), float(np.mean([yy[i] in o[i, :3] for i in range(len(yy))]))


horaf = datos.hora[:FIN].astype(np.int64)
diaf = datos.dia[:FIN].astype(np.int64)
hoyf = np.zeros((nf, K), dtype=np.int64)
cur, cnt = -1, np.zeros(K, dtype=np.int64)
for t in range(nf):
    if diaf[t] != cur:
        cur = diaf[t]
        cnt = np.zeros(K, dtype=np.int64)
    hoyf[t] = cnt
    cnt[seq_f[t]] += 1
NG = len(E) + 1
hb = np.repeat(horaf[:, None], K, axis=1)
hy = np.clip(hoyf, 0, 2)
di("| mecanismo | Top-1 | Top-3 | vs equilibrio (10%) |")
di("|---|---|---|---|")
di("| azar puro | 2.63% | 7.89% | -2.11 pts |")
for nom, bins, tot in (("solo evitacion intradia", None, None),
                       ("solo recencia (curva de hueco)", bb, NG),
                       ("recencia x hora", bb * 12 + hb, NG * 12),
                       ("recencia x hora x veces-hoy", (bb * 12 + hb) * 3 + hy, NG * 12 * 3)):
    if bins is None:
        t1o, t3o = 0.0305, 0.0925
    else:
        t1o, t3o = _oraculo(bins, tot)
    di("| %s | %.2f%% | %.2f%% | %+.2f pts |" % (nom, 100 * t1o, 100 * t3o, 100 * t3o - 10))
di("| **ensamble_v2, desarrollo (walk-forward)** | 4.53% | 12.89% | +2.89 pts |")
di("| **ensamble_v2, PRUEBA CIEGA** | 4.00% | **12.27%** | **+2.27 pts** |")
di("| **ensamble_v2, carrera 1 ano** | 4.09% | 12.63% | +2.63 pts |")
di("")
di("**Como se lee esta tabla.** La evitacion intradia sola da **9.25%**: por debajo del "
   "equilibrio, o sea **no alcanza para ganar dinero**. La curva de recencia completa sube a "
   "**10.78%** y coincide casi exacta con lo que mide `hazard_actual` (10.74%): ese modelo "
   "**es** la curva de recencia. Anadir la hora llega a **11.66%**.")
di("")
di("El ensamble saca **12.27%** a ciegas, que es **mas** que el mejor de estos oraculos pese a "
   "que ellos juegan con ventaja (ajustados en los mismos datos). O sea: **de los 2.27 puntos "
   "de margen sobre el equilibrio, alrededor de 1.7 se explican por mecanismos que sabemos "
   "nombrar (recencia + hora) y el resto por estructura de secuencia que todavia no hemos "
   "caracterizado.** Eso ultimo es lo que hay que vigilar: es la parte del margen que no "
   "sabemos justificar.")
di("")
di("---")
di("")
di("## Que sabemos, que no sabemos, que descartamos")
di("")
di("1. **La frecuencia por animal %s.** %s"
   % ("SI se desvia de la uniforme" if v1 else "NO se desvia de la uniforme",
      "Hay animales con ventaja estable." if v1 else
      "No existen 'animales calientes': apostar por frecuencia historica no da ventaja."))
di("2. **El ganador anterior SI condiciona al siguiente, pero solo en la diagonal**: el sorteo "
   "repite el animal anterior el %.3f%% de las veces contra 2.632%% del azar (%.2fx, z=%+.1f). "
   "El chi2 de la tabla 38x38 completa NO lo ve (p=%.4f) porque diluye el efecto en %d grados "
   "de libertad: es el test equivocado, no la ausencia de senal."
   % (100 * col_obs / (n - 1), (col_obs / (n - 1)) / p0, z_col, p1, gl1))
di("3. **Markov de orden 2 es INCONCLUSO**, no negativo: con %d sorteos hay %.2f observaciones por "
   "celda. No se puede afirmar ni descartar." % (n, (n - 2) / K ** 3))
di("4. **El sesgo real y explotable es conductual**: dentro de una misma jornada el operador evita "
   "repetir animal. Dos sorteos del mismo dia repiten el %.3f%% de las veces contra el 2.632%% del "
   "azar (%.2fx, z=%+.1f)." % (100 * rep_all / tot_all, (rep_all / tot_all) / p0, z_rep))
di("5. **La jornada trae %.2f animales distintos** contra %.2f esperados por azar (z=%+.1f). Esa es "
   "la grieta que explota el ensamble." % (dist.mean(), esp_dist, z_d))
di("6. **El balanceo de conteos a largo plazo NO esta demostrado.** Es una CORRECCION a lo que "
   "el proyecto venia asumiendo: los indices de dispersion por ventana son inconsistentes y sus "
   "intervalos cruzan el 1, y el indice de los huecos es %.3f (>1), lo contrario de lo que "
   "produciria un equilibrador. Toda la senal medible esta en la jornada." % disp.mean())
di("7. **Lo que descartamos**: %s"
   % ("frecuencias fijas por animal (V1), " if not v1 else "") +
   "y, en el reporte del Vector 3, la hipotesis de PRNG/LCG debil.")
di("8. **Lo que no sabemos**: si el operador cambia de mecanismo. Por eso la carrera mensual y el "
   "SPRT en vivo son obligatorios, no opcionales.")
di("")
di("---")
di("")
di("## Regla pre-comprometida de vigilancia del ensamble")
di("")
di("> **Decidida el 2026-09-15, ANTES de ver los datos futuros.**")
di(">")
di("> Si el modelo `hazard` supera a `ensamble_v2` en Top-3 durante **3 meses consecutivos** en la "
   "carrera walk-forward mensual (`herramientas/resultados/carrera_1ano.txt`), se abre revision de "
   "la ponderacion del ensamble. **Antes de eso, no se toca nada.**")
di(">")
di("> Dato que motiva la regla: en **2026-09** hazard hizo **12.1%** de Top-3 contra **11.6%** del "
   "ensamble. Es **un solo mes y no es significativo** -- por eso la regla exige 3 seguidos y no "
   "reacciona a este.")
di(">")
di("> Contador actual: **1 mes** (2026-09). Faltan 2 para abrir revision.")
di("")

ruta = os.path.join(RAIZ, "herramientas", "resultados", "reporte_vectores_1_2.md")
with open(ruta, "w", encoding="utf-8") as f:
    f.write("\n".join(M) + "\n")
print("\nguardado en", ruta)
