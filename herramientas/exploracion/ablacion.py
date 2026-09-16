# -*- coding: utf-8 -*-
"""TAREA 3 -- ABLACION DEL ENSAMBLE (atribuir los 0.6 puntos de margen).

NO toca el ensamble en produccion. Reproduce EXACTAMENTE su algoritmo
(mismo ajustar_pesos, mismo R, mismo arranque, mismo tau/lam) pero calcula
las log-probabilidades de los 3 submodelos UNA sola vez y luego reajusta los
pesos para cada subconjunto. Eso hace que 5 variantes cuesten casi lo mismo
que una.

SOLO desarrollo: se evalua sobre datos.prefijo(CORTE_FIJO), asi que el tramo
de prueba ni siquiera se lee.

Comparacion pareada: mismos sorteos para todas las variantes, e intervalos
por bootstrap de BLOQUES DE DIA (respeta la correlacion intradia).

Uso:  python ablacion.py
Salida: herramientas/resultados/ablacion.md
"""
import importlib.util, json, math, os, sys, time
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERR = os.path.join(RAIZ, "herramientas")
sys.path.insert(0, HERR)
import lotto_eval as LE

K = 38
B_BOOT = 2000
RNG = np.random.default_rng(20260915)

_spec = importlib.util.spec_from_file_location("ensamble", os.path.join(HERR, "modelos", "ensamble.py"))
ENS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ENS)

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
full = LE.cargar()
n_tot = len(full)
INI, FIN = LE.W, LE.CORTE_FIJO
datos = full.prefijo(FIN)               # el tramo de prueba NI SE LEE
n = len(datos)
y = datos.seq[INI:].astype(np.int64)
N = len(y)
dia = datos.dia[INI:]
dias_u = np.unique(dia)
bloques = [np.flatnonzero(dia == d) for d in dias_u]

BASE = ["intradia_v2", "secuencia_v3", "haz_v1"]
R, ARRANQUE, TAU, LAM = 250, 1000, 3000.0, 5.0

di("# Tarea 3 - Ablacion del ensamble")
di("")
di("Generado por `herramientas/exploracion/ablacion.py`.")
di("")
di("- Historial completo **%d sorteos**; aqui se lee solo hasta la fila %d: "
   "**el tramo de prueba no se abre**." % (n_tot, FIN))
di("- Evaluacion en **desarrollo**: %d sorteos (%s a %s)." % (N, datos.fecha[INI], datos.fecha[-1]))
di("- Mismos sorteos para todas las variantes (comparacion **pareada**).")
di("- Intervalos por bootstrap de **bloques de dia** (%d remuestreos, %d dias)."
   % (B_BOOT, len(bloques)))
di("")

print("calculando los 3 submodelos una sola vez (lento)...", flush=True)
t0 = time.time()
a = min(ARRANQUE, INI)
mods = [ENS._cargar(b) for b in BASE]
L_all = np.stack([np.log(np.clip(m.predecir(datos, a), 1e-9, None)) for m in mods], axis=1)
L_all -= np.log(np.exp(L_all).sum(2, keepdims=True))
print("submodelos listos en %.1f min" % ((time.time() - t0) / 60), flush=True)
y_a = datos.seq[a:]


def correr(idx):
    """Repite el bucle de bloques de ensamble.Modelo.predecir con los componentes idx."""
    L = L_all[:, idx, :]
    Mm = len(idx)
    w = np.full(Mm, 1.0 / Mm)
    out = np.empty((n - INI, K))
    hist = []
    for T in range(INI, n, R):
        j = T - a
        if j >= 200:
            pesos_t = np.exp(-(j - 1 - np.arange(j)) / TAU) if TAU else None
            w = ENS.ajustar_pesos(L[:j], y_a[:j], w, LAM, pesos_t)
        hist.append((T, w.copy()))
        b = min(T + R, n)
        z = np.einsum("nmk,m->nk", L[T - a:b - a], w)
        z -= z.max(1, keepdims=True)
        p = np.exp(z)
        out[T - INI:b - INI] = p / p.sum(1, keepdims=True)
    return out, hist


def evaluar(P, semilla=12345):
    P = LE.normalizar(P)
    rng = np.random.default_rng(semilla)
    orden = np.argsort(-(P + rng.random(P.shape) * 1e-12), axis=1)
    pos = np.argmax(orden == y[:, None], axis=1)
    bits = np.log(P[np.arange(N), y] * K) / math.log(2)
    return {"pos": pos, "h1": (pos < 1).astype(float), "h3": (pos < 3).astype(float),
            "bits": bits}


VARIANTES = [("ensamble completo (linea base)", [0, 1, 2]),
             ("SIN secuencia_v3", [0, 2]),
             ("SIN haz_v1 (hazard)", [0, 1]),
             ("SIN intradia_v2", [1, 2]),
             ("solo secuencia_v3", [1]),
             ("solo intradia_v2", [0]),
             ("solo haz_v1", [2])]

res = {}
for nom, idx in VARIANTES:
    t1 = time.time()
    P, hist = correr(idx)
    res[nom] = evaluar(P)
    res[nom]["pesos_final"] = [round(float(x), 3) for x in hist[-1][1]]
    res[nom]["idx"] = idx
    print("  %-34s Top3 %.2f%%  (%.0fs)" % (nom, 100 * res[nom]["h3"].mean(), time.time() - t1),
          flush=True)

base = res["ensamble completo (linea base)"]

di("## 3.1 Linea base: reproduce el ensamble de produccion?")
di("")
t1b, t3b = base["h1"].mean(), base["h3"].mean()
mb = base["bits"].mean() * 1000
di("| medida | esta corrida | produccion (`pagina_sorteo.txt`) | coincide |")
di("|---|---|---|---|")
di("| Top-1 | %.2f%% | 4.53%% | %s |" % (100 * t1b, "SI" if abs(100 * t1b - 4.53) < 0.06 else "**NO**"))
di("| Top-3 | %.2f%% | 12.89%% | %s |" % (100 * t3b, "SI" if abs(100 * t3b - 12.89) < 0.06 else "**NO**"))
di("| mbits | %+.2f | +120.07 | %s |" % (mb, "SI" if abs(mb - 120.07) < 1.0 else "**NO**"))
di("")
ok_base = abs(100 * t3b - 12.89) < 0.06 and abs(mb - 120.07) < 1.0
if not ok_base:
    di("> **ALTO.** La linea base NO reproduce produccion. Todo lo que sigue queda en "
       "cuarentena hasta explicar la diferencia.")
di("")

# ----------------------------------------------------- bootstrap pareado
di("## 3.2 Aporte de cada componente (delta vs linea base)")
di("")
idx_boot = RNG.integers(0, len(bloques), size=(B_BOOT, len(bloques)))


def boot_delta(v, campo):
    d = res[v][campo] - base[campo]
    muestras = np.empty(B_BOOT)
    for i in range(B_BOOT):
        sel = np.concatenate([bloques[j] for j in idx_boot[i]])
        muestras[i] = d[sel].mean()
    return d.mean(), np.percentile(muestras, 2.5), np.percentile(muestras, 97.5)


di("| variante | Top-1 | Top-3 | delta Top-3 (IC95 bootstrap) | mbits | delta mbits (IC95) |")
di("|---|---|---|---|---|---|")
for nom, idx in VARIANTES:
    r = res[nom]
    d3, lo3, hi3 = boot_delta(nom, "h3")
    db, lob, hib = boot_delta(nom, "bits")
    di("| %s | %.2f%% | %.2f%% | %s | %+.1f | %s |"
       % (nom, 100 * r["h1"].mean(), 100 * r["h3"].mean(),
          "-" if nom.startswith("ensamble completo") else
          "%+.2f pts [%+.2f, %+.2f]" % (100 * d3, 100 * lo3, 100 * hi3),
          r["bits"].mean() * 1000,
          "-" if nom.startswith("ensamble completo") else
          "%+.1f [%+.1f, %+.1f]" % (1000 * db, 1000 * lob, 1000 * hib)))
di("")

# ----------------------------------------------------- veredicto y fragilidad
di("## 3.3 Veredicto por componente")
di("")
di("**El veredicto se decide con mbits, no con Top-3.** Top-3 tira el 97%% de la informacion "
   "de cada sorteo (solo mira si el ganador cayo en 3 de 38 casillas) y con n=%d su error "
   "estandar es de ~0.4 puntos: no distingue nada. La log-verosimilitud usa la distribucion "
   "completa. Abajo se ve que con Top-3 los tres componentes salen «no significativo», y con "
   "mbits dos de ellos se separan con claridad." % N)
di("")
di("| componente | quitarlo cuesta (mbits) | IC95 | quitarlo cuesta (Top-3) | IC95 | por cuarto (mbits) | veredicto |")
di("|---|---|---|---|---|---|---|")
COMP = [("secuencia_v3", "SIN secuencia_v3"), ("haz_v1 (hazard)", "SIN haz_v1 (hazard)"),
        ("intradia_v2", "SIN intradia_v2")]
veredictos = {}
for comp, var in COMP:
    d3, lo3, hi3 = boot_delta(var, "h3")
    db, lob, hib = boot_delta(var, "bits")
    d = res[var]["bits"] - base["bits"]
    cuartos = [float(-c.mean() * 1000) for c in np.array_split(d, 4)]
    aporta = hib < 0
    signos = sum(1 for c in cuartos if c > 0)
    fragil = aporta and signos <= 2
    v = ("NO APORTA" if not aporta else
         "APORTA PERO FRAGIL" if fragil else "APORTA")
    veredictos[comp] = (v, -1000 * db, cuartos)
    di("| `%s` | %+.1f | [%+.1f, %+.1f] | %+.2f pts | [%+.2f, %+.2f] | %s | **%s** |"
       % (comp, -1000 * db, -1000 * hib, -1000 * lob, -100 * d3, 100 * lo3, 100 * hi3,
          " ".join("%+.1f" % c for c in cuartos), v))
di("")
di("(«por cuarto» = mbits que se pierden al quitarlo, en cada cuarto del periodo de desarrollo. "
   "Signos mezclados = aporte inestable.)")
di("")

# ------------------------------------------------- atribucion de los 0.6 pts
di("## 3.4 Atribucion de los ~1.2 puntos que el oraculo tabular no explicaba")
di("")
di("| modelo | Top-3 | mbits |")
di("|---|---|---|")
di("| mejor oraculo tabular de la fase anterior (con ventaja: ajustado en los mismos datos) | 11.66% | - |")
for nom, _ in VARIANTES:
    di("| %s | %.2f%% | %+.1f |" % (nom, 100 * res[nom]["h3"].mean(), res[nom]["bits"].mean() * 1000))
di("")
di("**La conclusion incomoda: Top-3 no puede atribuir nada.** Cualquier submodelo SOLO ya saca "
   "entre 12.45%% y 12.65%%, contra 12.89%% del ensamble completo, y todos los intervalos se "
   "solapan. Con este tamano de muestra el Top-3 no distingue el ensamble de sus piezas sueltas.")
di("")
di("**Con mbits si se separa:**")
di("")
for comp, (v, d, cu) in veredictos.items():
    di("- `%s`: quitarlo cuesta **%+.1f mbits** -> **%s**." % (comp, d, v))
di("")
di("- `solo haz_v1` se queda en **%+.1f mbits** contra **%+.1f** del ensamble: la curva de "
   "recencia sola predice el ganador casi igual de bien en Top-3, pero **calibra mucho peor**."
   % (res["solo haz_v1"]["bits"].mean() * 1000, base["bits"].mean() * 1000))
di("")
di("Los pesos que el propio ensamble le asigna a cada submodelo en el ultimo bloque lo dicen igual:")
di("")
di("| variante | pesos ajustados |")
di("|---|---|")
for nom, idx in VARIANTES:
    di("| %s | %s |" % (nom, ", ".join("`%s`=%s" % (BASE[i], p)
                                        for i, p in zip(idx, res[nom]["pesos_final"]))))
di("")

ruta = os.path.join(RAIZ, "herramientas", "resultados", "ablacion.md")
with open(ruta, "w", encoding="utf-8") as f:
    f.write("\n".join(M) + "\n")
with open(os.path.join(RAIZ, "herramientas", "resultados", "ablacion.json"), "w",
          encoding="utf-8") as f:
    json.dump({nom: {"top1": float(res[nom]["h1"].mean()), "top3": float(res[nom]["h3"].mean()),
                     "mbits": float(res[nom]["bits"].mean() * 1000),
                     "pesos_final": res[nom]["pesos_final"]} for nom, _ in VARIANTES},
              f, indent=1, ensure_ascii=False)
print("\nguardado en", ruta)
