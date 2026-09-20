# -*- coding: utf-8 -*-
"""¿La racha del favorito informa? Validacion walk-forward en DESARROLLO.

Pre-registro: PREREGISTRO_racha_favorito.md (escrito ANTES de correr esto).
Lee ese archivo primero; aqui solo se ejecuta lo que alli quedo fijado.

NO toca produccion: no escribe en historial.txt ni predicciones.json, no
cambia pesos ni modelos. Solo lee el historial y escribe su reporte en
herramientas/resultados/racha_favorito.md.

SOLO DESARROLLO: se evalua sobre datos.prefijo(CORTE_FIJO=9357), asi que el
tramo de prueba ni siquiera se carga en memoria.

Uso:  python herramientas/exploracion/racha_favorito.py
Primera corrida ~1-3 min (matriz walk-forward). Se cachea en racha_wf.npy,
las siguientes son instantaneas.
"""
import math, os, sys
import numpy as np

RAIZ = os.environ.get("LOTTO_RAIZ") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERR = os.path.join(RAIZ, "herramientas")
sys.path.insert(0, HERR)
import lotto_eval as LE

# En Railway el historial vive en el volumen, no junto al codigo (igual que
# en prediccion.py). En local ambos coinciden.
DATOS_DIR = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or RAIZ
HISTORIAL = os.path.join(DATOS_DIR, "historial.txt")

UMBRAL_RACHA = 3          # fijado en el pre-registro. NO tocar tras ver el resultado.
B_BOOT = 2000
ALFA_BONF = 0.05 / 3
RNG = np.random.default_rng(20260920)
CACHE = os.environ.get("LOTTO_CACHE") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "racha_wf.npy")
SALIDA = os.environ.get("LOTTO_SALIDA") or os.path.join(
    HERR, "resultados", "racha_favorito.md")

M = []


def di(s=""):
    print(s, flush=True)
    M.append(s)


# ------------------------------------------------------------------ utilidades
def z_dos_prop(k1, n1, k0, n0):
    """z de contraste de dos proporciones (crudo, sin estratificar)."""
    if n1 == 0 or n0 == 0:
        return 0.0
    p = (k1 + k0) / (n1 + n0)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n0))
    return (k1 / n1 - k0 / n0) / se if se > 0 else 0.0


def p_dos_colas(z):
    return math.erfc(abs(z) / math.sqrt(2))


def mantel_haenszel(hit, exp, estrato):
    """MH para 2x2xH. Devuelve (z, OR_MH, tabla por estrato).

    a = aciertos entre expuestos (racha>=umbral) en el estrato.
    Bajo H0, E[a] y Var[a] son los de la hipergeometrica.
    """
    A = E = V = 0.0
    num_or = den_or = 0.0
    filas = []
    for h in sorted(set(estrato.tolist())):
        m = estrato == h
        n1 = int((m & exp).sum())            # expuestos
        n0 = int((m & ~exp).sum())           # no expuestos
        N = n1 + n0
        if n1 == 0 or n0 == 0 or N < 2:
            continue
        a = int((m & exp & hit).sum())
        b = n1 - a
        c = int((m & ~exp & hit).sum())
        d = n0 - c
        m1 = a + c
        m0 = N - m1
        A += a
        E += n1 * m1 / N
        V += n1 * n0 * m1 * m0 / (N * N * (N - 1))
        num_or += a * d / N
        den_or += b * c / N
        filas.append((h, n1, a, a / n1 * 100, n0, c, c / n0 * 100))
    z = (A - E) / math.sqrt(V) if V > 0 else 0.0
    orr = num_or / den_or if den_or > 0 else float("nan")
    return z, orr, filas


def boot_dif(hit, exp, dia, b=B_BOOT):
    """IC95 de la diferencia de tasas por bootstrap de BLOQUES DE DIA."""
    dias = np.unique(dia)
    pos = [np.flatnonzero(dia == d) for d in dias]
    out = np.empty(b)
    for i in range(b):
        pick = RNG.integers(0, len(dias), len(dias))
        idx = np.concatenate([pos[j] for j in pick])
        e = exp[idx]
        n1, n0 = int(e.sum()), int((~e).sum())
        if n1 == 0 or n0 == 0:
            out[i] = np.nan
            continue
        out[i] = hit[idx][e].mean() - hit[idx][~e].mean()
    out = out[~np.isnan(out)]
    return np.percentile(out, 2.5) * 100, np.percentile(out, 97.5) * 100


def rachas_de(top1, reset=None):
    """Longitud de racha del favorito terminando en cada indice."""
    n = len(top1)
    L = np.ones(n, np.int64)
    for t in range(1, n):
        corta = reset is not None and reset[t]
        if top1[t] == top1[t - 1] and not corta:
            L[t] = L[t - 1] + 1
    return L


# ------------------------------------------------------------------ 1. datos
di("# Racha del favorito: ¿informa? — validación walk-forward")
di()
di("Pre-registro: `PREREGISTRO_racha_favorito.md` (fijado antes de esta corrida).")
di()

datos_full = LE.cargar(HISTORIAL)
di(f"Histórico completo en disco: {len(datos_full)} sorteos.")
datos = datos_full.prefijo(LE.CORTE_FIJO)
del datos_full
di(f"**Recortado a desarrollo: {len(datos)} sorteos (corte {LE.CORTE_FIJO}). "
   f"El tramo de prueba no se usa.**")

if os.path.exists(CACHE):
    P = np.load(CACHE)
    di(f"Matriz walk-forward leída de caché ({os.path.basename(CACHE)}).")
    if P.shape != (len(datos) - LE.W, LE.K):
        sys.exit(f"Caché con forma {P.shape}, esperaba {(len(datos)-LE.W, LE.K)}. Bórrala y repite.")
else:
    di("Calculando la matriz walk-forward con `ensamble_v2` (el de producción)…")
    modelo = LE.cargar_modelo(os.path.join(HERR, "modelos", "ensamble_v2.py"))
    P = LE.normalizar(modelo.predecir(datos, LE.W))
    np.save(CACHE, P)
    di(f"Listo y cacheado en `{os.path.basename(CACHE)}`.")

y = datos.seq[LE.W:]
hora = np.clip(datos.hora[LE.W:], 0, 11)
dia = datos.dia[LE.W:]
n = len(y)
assert P.shape == (n, LE.K)

orden = LE.rankings(P)                       # mismo desempate que usa el marcador
puesto = np.argmax(orden == y[:, None], axis=1)
hit3 = puesto < 3
hit1 = puesto < 1
top1 = orden[:, 0]
p3 = np.take_along_axis(P, orden[:, :3], axis=1).sum(axis=1)

di()
di(f"Base: **{n} sorteos** de desarrollo. Top-3 global "
   f"{hit3.mean()*100:.2f}% (azar 7,89%). Top-1 {hit1.mean()*100:.2f}%.")

# ------------------------------------------------------------------ 2. rachas
nuevo_dia = np.r_[True, dia[1:] != dia[:-1]]
L = rachas_de(top1)
L_reset = rachas_de(top1, reset=nuevo_dia)
exp = L >= UMBRAL_RACHA

di()
di("## Descriptivo: ¿qué tan seguido se enfrasca?")
di()
di(f"- Mismo #1 que el sorteo anterior: **{(L[1:] > 1).mean()*100:.1f}%** de los sorteos.")
di(f"- Sorteos con racha >= {UMBRAL_RACHA}: **{exp.sum()} de {n} ({exp.mean()*100:.1f}%)**.")
di()
di("| Racha | Sorteos | Top-3 | Top-1 |")
di("|---|---|---|---|")
for k in range(1, 7):
    m = (L == k) if k < 6 else (L >= 6)
    if m.sum() == 0:
        continue
    et = str(k) if k < 6 else "6+"
    di(f"| {et} | {m.sum()} | {hit3[m].mean()*100:.2f}% | {hit1[m].mean()*100:.2f}% |")
di()
di("*(La curva completa es descriptiva. El umbral de la prueba es "
   f"{UMBRAL_RACHA}, fijado en el pre-registro: elegir otro al ver esta tabla "
   "sería sobreajuste.)*")

# --- el confusor, a la vista
di()
di("## El confusor: la racha crece con la hora")
di()
di("| Hora | Racha media | % con racha >= 3 |")
di("|---|---|---|")
for h in range(12):
    m = hora == h
    if m.sum():
        di(f"| {h+1}º | {L[m].mean():.2f} | {exp[m].mean()*100:.1f}% |")
di()
di("Por eso la prueba primaria va **estratificada por hora**. Comparar crudo "
   "mezclaría el efecto de la racha con el de la hora, que es el artefacto "
   "que ya invalidó al HILO 1.")

# ------------------------------------------------------------------ 3. pruebas
di()
di("## Pruebas pre-especificadas (Bonferroni α = 0,0167)")

k1, n1 = int(hit3[exp].sum()), int(exp.sum())
k0, n0 = int(hit3[~exp].sum()), int((~exp).sum())
z_crudo = z_dos_prop(k1, n1, k0, n0)
lo, hi = boot_dif(hit3, exp, dia)

di()
di("### Crudo (referencia, NO decide)")
di()
di(f"- racha >= {UMBRAL_RACHA}: **{k1}/{n1} = {k1/n1*100:.2f}%**")
di(f"- racha <= {UMBRAL_RACHA-1}: **{k0}/{n0} = {k0/n0*100:.2f}%**")
di(f"- diferencia **{(k1/n1-k0/n0)*100:+.2f} pts**, IC95 bootstrap por día "
   f"[{lo:+.2f}, {hi:+.2f}], z = {z_crudo:+.2f} (p = {p_dos_colas(z_crudo):.4f})")

z1, or1, filas = mantel_haenszel(hit3, exp, hora)
di()
di("### T1 (PRIMARIA) — Mantel-Haenszel estratificado por hora")
di()
di("| Hora | n racha>=3 | Top-3 | n racha<=2 | Top-3 |")
di("|---|---|---|---|---|")
for h, a_n, a_k, a_p, b_n, b_k, b_p in filas:
    di(f"| {h+1}º | {a_n} | {a_k} ({a_p:.1f}%) | {b_n} | {b_k} ({b_p:.1f}%) |")
di()
di(f"**z_MH = {z1:+.3f}**, p = {p_dos_colas(z1):.4f}, OR_MH = {or1:.3f}")

quint = np.searchsorted(np.percentile(p3, [20, 40, 60, 80]), p3)
z2, or2, _ = mantel_haenszel(hit3, exp, quint)
di()
di("### T2 — estratificado por quintil de la probabilidad que el modelo se da a sí mismo")
di()
di(f"**z_MH = {z2:+.3f}**, p = {p_dos_colas(z2):.4f}, OR_MH = {or2:.3f}")
di()
di("Si T1 sobrevive pero T2 no, el efecto es redundante: sólo marca sorteos "
   "que el modelo ya señalaba como buenos.")

acierta_el_rachoso = (y == top1)
z3, or3, _ = mantel_haenszel(acierta_el_rachoso, exp, hora)
k1b = int(acierta_el_rachoso[exp].sum())
k0b = int(acierta_el_rachoso[~exp].sum())
di()
di("### T3 — ¿acierta el propio animal en racha? (Top-1, estratificado por hora)")
di()
di(f"- racha >= {UMBRAL_RACHA}: {k1b}/{n1} = {k1b/n1*100:.2f}%")
di(f"- racha <= {UMBRAL_RACHA-1}: {k0b}/{n0} = {k0b/n0*100:.2f}%")
di(f"**z_MH = {z3:+.3f}**, p = {p_dos_colas(z3):.4f}, OR_MH = {or3:.3f}")

# --- variante con reset de día (descriptivo declarado en el pre-registro)
exp_r = L_reset >= UMBRAL_RACHA
zr, _, _ = mantel_haenszel(hit3, exp_r, hora)
di()
di(f"*Variante con reset en frontera de día (descriptivo): z_MH = {zr:+.3f}.*")

# ------------------------------------------------------------------ 4. veredicto
di()
di("## Veredicto según el criterio pre-comprometido")
di()
p1 = p_dos_colas(z1)
if abs(z1) < 2.0:
    di(f"**HIPÓTESIS DESCARTADA.** |z_MH| = {abs(z1):.3f} < 2,0 en la prueba "
       "primaria. Según el pre-registro esto se archiva aquí: no se prueban "
       "otros umbrales de racha ni otros cortes, y no se cambia nada del "
       "modelo ni de la apuesta.")
    di()
    di("Lo que se vio en el marcador en vivo (16,7% vs 4,4% en 87 registros) "
       "era ruido de muestra pequeña con un corte elegido a posteriori.")
elif p1 >= ALFA_BONF:
    di(f"**NO SOBREVIVE BONFERRONI.** z_MH = {z1:+.3f} (p = {p1:.4f}) no baja "
       f"de α = {ALFA_BONF:.4f}. Insuficiente. No se cambia nada.")
elif p_dos_colas(z2) >= ALFA_BONF:
    di(f"**REDUNDANTE.** T1 sobrevive (z = {z1:+.3f}) pero T2 no "
       f"(z = {z2:+.3f}, p = {p_dos_colas(z2):.4f}): el efecto ya está "
       "contenido en la probabilidad que el propio ensamble calcula. "
       "No hay información nueva. No se cambia nada.")
else:
    di(f"**CANDIDATA.** T1 z = {z1:+.3f} y T2 z = {z2:+.3f}, ambas bajo "
       f"α = {ALFA_BONF:.4f}. Pasa a la cola de validación en el tramo de "
       "prueba, que sólo puede mirarse UNA vez más.")
    di()
    di("**Aun así NO se cambia ninguna apuesta todavía.** El equilibrio a 30x "
       "sigue siendo 10% de Top-3.")

di()
di("---")
di()
di("Generado por `herramientas/exploracion/racha_favorito.py`. "
   "Sólo desarrollo; el tramo de prueba no se leyó.")

os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
with open(SALIDA, "w", encoding="utf-8") as f:
    f.write("\n".join(M) + "\n")
print(f"\n--> reporte escrito en {SALIDA}")
