#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lotto Activo — servidor local, todo en una sola página.

  * Próximo sorteo: Top-3 del ensamble (herramientas/modelos/ensamble_v2.py).
  * Tripleta: 2 tripletas para los 12 sorteos que empiezan en el siguiente
    (herramientas/tripleta_ventana.py). Paga 45x.
  * Registro de resultados, marcadores honestos (solo pronósticos hechos antes
    del resultado) y panel de herramientas de validación.

Sin numpy/scipy funciona con el modelo antiguo (solo librería estándar).
"""
import hashlib, os, sys, json, math, webbrowser, threading, subprocess, time, html
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from datetime import date, datetime, timedelta
from math import comb

# Jornada y etiquetas deben correr en hora de Caracas (UTC-4, sin DST),
# no en la hora del contenedor. FUERZA el valor: la imagen de Railway ya
# trae TZ (sfo -> America/Los_Angeles, UTC-8); setdefault quedaba corto.
# tzdata (requirements.txt) garantiza que la zona exista en imagenes slim.
os.environ["TZ"] = "America/Caracas"
try:
    time.tzset()
except AttributeError:
    pass

RUTA = os.path.dirname(os.path.abspath(__file__))
DATOS = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or RUTA
HIST = os.path.join(DATOS, "historial.txt")
LOG  = os.path.join(DATOS, "predicciones.json")
HERR = os.path.join(RUTA, "herramientas")
PUERTO = 8000  # local; en Railway se usa PORT
PAGO = 30
PAGO_TRIPLETA = 45
VENTANA = 12

POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}
K = len(POS); P0 = 1.0 / K
ANIM = {"0":"DELFÍN","00":"BALLENA","1":"CARNERO","2":"TORO","3":"CIEMPIÉS","4":"ALACRÁN",
 "5":"LEÓN","6":"RANA","7":"PERICO","8":"RATÓN","9":"ÁGUILA","10":"TIGRE","11":"GATO",
 "12":"CABALLO","13":"MONO","14":"PALOMA","15":"ZORRO","16":"OSO","17":"PAVO","18":"BURRO",
 "19":"CHIVO","20":"COCHINO","21":"GALLO","22":"CAMELLO","23":"CEBRA","24":"IGUANA",
 "25":"GALLINA","26":"VACA","27":"PERRO","28":"ZAMURO","29":"ELEFANTE","30":"CAIMÁN",
 "31":"LAPA","32":"ARDILLA","33":"PESCADO","34":"VENADO","35":"JIRAFA","36":"CULEBRA"}
HORAS = ["8:00 AM","9:00 AM","10:00 AM","11:00 AM","12:00 PM","1:00 PM",
         "2:00 PM","3:00 PM","4:00 PM","5:00 PM","6:00 PM","7:00 PM"]
DIAS_SEM = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
BINS = [0,1,2,3,4,5,6,8,10,13,17,22,28,36,46,60,80,10**9]
# Tasas medidas en prueba ciega (3.122 sorteos no vistos, herramientas/resultados/final.txt)
P_MOD_T3, P_AZAR_T3 = 0.1227, 3.0/K     # ensamble_v2 (el antiguo: 0,1060)
P_MOD_T1 = 0.0400

# Modelo nuevo. Necesita numpy y scipy; si faltan, se usa el antiguo.
try:
    import prediccion
    PRED = prediccion.Predictor(); PRED_ERR = None
except Exception as _ex:
    PRED = None; PRED_ERR = f"{type(_ex).__name__}: {_ex}"

AVISO = {"texto": "", "clase": ""}      # mensaje que se muestra una vez tras un POST

# ----------------------------------------------------------------- datos
def bidx(g):
    i = 0
    for j, b in enumerate(BINS):
        if g >= b: i = j
        else: break
    return i

def cargar():
    filas = []
    for ln in open(HIST, encoding="utf-8"):
        p = ln.split()
        if len(p) == 3 and p[2] in IDX:
            filas.append((p[0], int(p[1]), IDX[p[2]]))
    filas.sort(key=lambda r: (r[0], r[1]))
    return filas

def hazard(seq):
    nb = len(BINS); hit = [0.0]*nb; tot = [0.0]*nb; last = {}
    for t, v in enumerate(seq):
        if t > 0:
            b = [bidx((t - last[s]) if s in last else 10**6) for s in range(K)]
            for s in range(K): tot[b[s]] += 1
            hit[b[v]] += 1
        last[v] = t
    return [hit[i]/tot[i] if tot[i] >= 30 else P0 for i in range(nb)]

def siguiente(f, h):
    if h < 11: return f, h + 1
    return (date.fromisoformat(f) + timedelta(days=1)).isoformat(), 0

def estado(filas):
    """Modelo antiguo (tramos de retraso) + datos del próximo sorteo."""
    seq = [v for _, _, v in filas]
    n = len(seq); last = {}
    for t, v in enumerate(seq): last[v] = t
    g = [n - 1 - last[s] if s in last else 10**6 for s in range(K)]
    hz = hazard(seq)
    sc = [hz[bidx(x + 1)] for x in g]
    orden = sorted(range(K), key=lambda i: -sc[i])
    f, h, v = filas[-1]
    nf, nh = siguiente(f, h)
    return dict(sc=sc, gaps=g, orden=orden, n=n, ult=(f, h, v), pf=nf, ph=nh)

def log_cargar():
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            d = json.load(f)
    else:
        d = {"registros": []}
    d.setdefault("registros", []); d.setdefault("tripletas", []); d.setdefault("sorteos_conocidos", [])
    return d

def log_guardar(d):
    with open(LOG + ".tmp", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(LOG + ".tmp", LOG)

def ahora():
    return datetime.now().isoformat(timespec="seconds")

def vigente(r):
    return not r.get("anulado")

def suspendido(x):
    return bool(x.get("suspendido"))

def _lineas_bin():
    with open(HIST, "rb") as f:
        return [l for l in f.read().splitlines(keepends=True) if l.strip()]

def _huella(lineas_bin, k):
    return hashlib.sha1(b"".join(lineas_bin[:k])).hexdigest()

def suspender(x, lineas_bin, k):
    """Deja en espera algo calculado sobre las primeras k líneas del historial.

    Un «deshacer» encadenado quita líneas que ese cálculo usó. Si al volver a
    anotar el historial queda IDÉNTICO en esas k líneas, el cálculo vuelve a
    ser válido y se restaura; si cambió, se anula (ver reanudar_suspendidos).
    Anularlo de entrada dejaba borrar un fallo con dos deshacer seguidos."""
    if not suspendido(x):
        x["suspendido"] = {"cuando": ahora(), "requiere_n": k, "requiere_sha1": _huella(lineas_bin, k)}

def reanudar_suspendidos(d):
    """Tras anotar una línea: restaura o anula lo que esperaba este historial."""
    lb = _lineas_bin()
    for x in d["registros"] + d["tripletas"]:
        if not vigente(x) or not suspendido(x):
            continue
        req = x["suspendido"]
        if len(lb) < req["requiere_n"]:
            continue                      # aún faltan líneas por volver a anotar
        if _huella(lb, req["requiere_n"]) == req["requiere_sha1"]:
            x.setdefault("reanudado", []).append({"cuando": ahora(), "suspendido": req["cuando"]})
            del x["suspendido"]
        else:
            x["anulado"] = {"cuando": ahora(), "motivo": "el dato corregido cambió lo que usó el cálculo"}

def fecha_corta(f):
    d = date.fromisoformat(f)
    hoy = date.today()
    if d == hoy: return "hoy"
    if d == hoy + timedelta(days=1): return "mañana"
    if d == hoy - timedelta(days=1): return "ayer"
    return f"{DIAS_SEM[d.weekday()]} {d.day} {MESES[d.month-1]}"

def fin_ventana(f, h):
    for _ in range(VENTANA - 1):
        f, h = siguiente(f, h)
    return f, h

# ------------------------------------------------------ sello del pronóstico
def modelo_de(info):
    """Nombre con que se guarda el pronóstico según los pesos que usó (H1).

    Con pesos uniformes (volumen sin pesos, o pesos de un bloque posterior
    tras un «deshacer») el ensamble es OTRO modelo, no el que se midió en la
    prueba ciega: se guarda con otro nombre para que el marcador no lo mezcle.
    """
    if info.get("frontera_pesos") is None:
        return prediccion.MODELO_ENSAMBLE + "_sin_pesos"
    return prediccion.MODELO_ENSAMBLE

def sello(info):
    """Campos aditivos que dejan comprobar el pronóstico después (H1 y H2).

    hist_sha1/hist_n: huella del historial con que se calculó. El ensamble
    solo depende de ese contenido; si la huella coincide con las primeras
    hist_n líneas del historial, el resultado del sorteo NO estaba dentro.
    pesos_frontera/pesos_vigentes/pesos: qué pesos del ensamble se usaron
    (no están en el historial, así que se guardan tal cual).
    """
    return {k_dst: info.get(k_src) for k_dst, k_src in (
        ("hist_sha1", "hist_sha1"), ("hist_n", "hist_n"), ("calculado", "calculado"),
        ("pesos_frontera", "frontera_pesos"), ("pesos_vigentes", "pesos_vigentes"), ("pesos", "pesos"))
        if info.get(k_src) is not None}

# -------------------------------------------------------------- marcadores
MODELO_MARCADOR = "ensamble_v2"
TOP_N = 15
P_AZAR_T15 = TOP_N / K          # 39,47%: un Top-15 al azar ya acierta 2 de cada 5

def resueltas(d):
    """Pronósticos del modelo en uso, con resultado y sin anular."""
    return [r for r in d["registros"] if vigente(r) and r.get("salio") is not None
            and r.get("modelo") == MODELO_MARCADOR]

def puesto_ganador(r):
    """Puesto (1..38) en que quedó el ganador dentro del orden congelado.

    None cuando el pronóstico se guardó sin `orden_completo` (registros viejos):
    esos no se pueden puntuar por Top-15 sin inventar el orden, así que quedan
    fuera del conteo en vez de contarse como fallo.
    """
    orden = r.get("orden_completo")
    if not orden:
        return None
    try:
        return orden.index(r["salio"]) + 1
    except ValueError:
        return None

def cola_binomial(k, n, p):
    """P(X >= k) exacta: probabilidad de sacar k o más aciertos por pura suerte."""
    if n <= 0 or k <= 0:
        return 1.0
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))

def marcador(d):
    """Marcador del modelo EN USO. Las predicciones del modelo antiguo
    (hazard, sin campo «modelo») no se mezclan: el factor de Bayes y el SPRT
    tienen que medir el modelo que se está jugando, no una mezcla de dos."""
    res = resueltas(d)
    n = len(res)
    if n == 0: return dict(n=0, n15=0)
    t3 = sum(1 for r in res if r["salio"] in r["top3"])
    t1 = sum(1 for r in res if r["salio"] == r["top3"][0])
    lo = 0.0
    for r in res:
        lo += math.log(P_MOD_T3/P_AZAR_T3) if r["salio"] in r["top3"] else math.log((1-P_MOD_T3)/(1-P_AZAR_T3))
    puestos = [p for p in (puesto_ganador(r) for r in res) if p is not None]
    n15 = len(puestos)
    t15 = sum(1 for p in puestos if p <= TOP_N)
    t5 = sum(1 for p in puestos if p <= 5)
    m = dict(n=n, t3=t3, t1=t1, tasa3=t3/n*100, tasa1=t1/n*100, factor=math.exp(lo),
             n15=n15, t15=t15, t5=t5)
    if n15:
        m.update(tasa15=t15/n15*100, tasa5=t5/n15*100, puesto_medio=sum(puestos)/n15,
                 p15=cola_binomial(t15, n15, P_AZAR_T15))
    return m

# ------------------------------------------------------------ la jugada
# Cuántas fichas va a cada puesto del orden congelado. Por qué así
# (herramientas/resultados/estrategia_top5.md):
#   * Prueba ciega (3.154 sorteos no vistos): Top-3 12,27 % (equilibrio 10 %),
#     Top-5 19,50 % (16,7 %), Top-15 49,46 % (50 %). Del 6º al 15º cada puesto
#     acierta ~3,0 %, por DEBAJO del 3,33 % que pide el pago 30x: pierden plata.
#   * El 4º y 5º aciertan ~3,6 % cada uno: ganan, pero menos y con menos
#     seguridad que el 1º-3º (~4,1 %). Kelly para apuestas simultáneas les da
#     menos de la mitad del monto; 2:1 es la versión redonda.
# Se juega TODOS los sorteos: elegir sorteos por lo «caliente» que se ve la
# lista FALLÓ en prueba ciega (hilo 6).
JUGADA = [(1, 3, 2), (4, 5, 1)]          # (desde, hasta, fichas por animal)
# Alternativa para quien quiere cobrar la mitad de los sorteos: el mismo Top-15
# pero con más fichas donde el modelo acierta más. Cada acierto deja ganancia
# (+67 / +37 / +7 con 23 fichas). Prueba ciega: ≈ +6 % frente a −1 % del plano.
PONDERADO = [(1, 3, 3), (4, 5, 2), (6, 15, 1)]
P_MOD_T5 = 0.1950                         # Top-5 en prueba ciega

def fichas_por_puesto(plan=None):
    f = [0] * (K + 1)
    for a, b, n in (plan or JUGADA):
        for p in range(a, b + 1):
            f[p] = n
    return f

ESTRATEGIAS = [("Top-5 escalonado (2-2-2-1-1)", fichas_por_puesto()),
               ("Top-15 ponderado (3-2-1)", fichas_por_puesto(PONDERADO)),
               ("Top-3 plano", [0] + [1] * 3 + [0] * (K - 3)),
               ("Top-15 plano", [0] + [1] * 15 + [0] * (K - 15))]

def efecto_correcciones(d):
    """Pronósticos cuyo resultado se cambió con «deshacer», y cómo quedaría
    el Top-3 contando el PRIMER valor anotado en vez del corregido."""
    res = resueltas(d)
    corr = [r for r in res if r.get("correcciones")]
    if not corr:
        return None
    t3_hoy = sum(1 for r in res if r["salio"] in r["top3"])
    t3_orig = sum(1 for r in res if (r["correcciones"][0]["salio_anterior"] if r.get("correcciones")
                                     else r["salio"]) in r["top3"])
    cambiados = sum(1 for r in corr if r["correcciones"][0]["salio_anterior"] != r["salio"])
    return dict(n=len(corr), cambiados=cambiados, t3_hoy=t3_hoy, t3_orig=t3_orig, total=len(res))

def economia(d, res=None):
    """Qué habría dejado cada forma de jugar, con 1 ficha = 1 unidad, sobre
    los pronósticos puntuables del marcador real (los que tienen orden)."""
    res = resueltas(d) if res is None else res
    puestos = [p for p in (puesto_ganador(r) for r in res) if p is not None]
    n = len(puestos)
    out = []
    for nombre, f in ESTRATEGIAS:
        apostado = sum(f) * n
        cobrado = sum(PAGO * f[p] for p in puestos)
        aciertos = sum(1 for p in puestos if f[p] > 0)
        out.append(dict(nombre=nombre, n=n, aciertos=aciertos, fichas=sum(f),
                        neto=cobrado - apostado,
                        roi=(cobrado - apostado) / apostado * 100 if apostado else 0.0))
    return out

# Tramos del Top-15: dónde cae el ganador dentro del orden que el modelo
# congeló ANTES del sorteo. Si el orden tuviera valor, los tramos de arriba
# tienen que salir por encima de su cuota de azar (cada puesto vale 1/38).
TRAMOS = [(1, 1, "1º"), (2, 3, "2º y 3º"), (4, 5, "4º y 5º"), (6, 10, "6º a 10º"),
          (11, 15, "11º a 15º"), (16, K, "fuera del Top-15")]

def analisis_top15(d, res=None):
    """Reparto del puesto del ganador, contra lo que daría el azar."""
    res = resueltas(d) if res is None else res
    puestos = [p for p in (puesto_ganador(r) for r in res) if p is not None]
    n = len(puestos)
    if not n:
        return dict(n=0, tramos=[])
    tramos = []
    for lo, hi, etiqueta in TRAMOS:
        veces = sum(1 for p in puestos if lo <= p <= hi)
        azar = (hi - lo + 1) / K
        tramos.append(dict(etiqueta=etiqueta, veces=veces, tasa=veces/n*100,
                           azar=azar*100, ventaja=veces/n - azar))
    return dict(n=n, tramos=tramos, puesto_medio=sum(puestos)/n, puesto_azar=(K + 1) / 2)

P_MOD_T15 = 0.4946   # Top-15 del ensamble_v2 en la prueba ciega (estrategia_top5.md), como T3 y T5

def prob_racha(k, n, p=P_MOD_T15):
    """P(ver una racha de >= k fallos EN ALGÚN punto de n sorteos) si el modelo
    está sano.

    La corrección por «en algún punto» es el corazón del asunto. Una racha de
    3 fallos seguidos tiene por sí sola un 10 % de probabilidad, pero en 78
    sorteos hay decenas de sitios donde puede empezar una, así que verla es
    casi seguro. Avisar por la racha suelta sería gritar en falso una y otra
    vez; por eso el umbral sube con el número de sorteos jugados.

    Número esperado de rachas de longitud >= k: q^k * (1 + (n-k) * p), porque
    una racha o empieza en el primer sorteo o empieza justo después de un
    acierto. De ahí P ≈ 1 - exp(-esperadas) (aproximación de Poisson, verificada
    contra simulación: n=18, k=9 da 0,0064 por las dos vías).
    """
    if k <= 0 or n <= 0:
        return 1.0
    q = 1.0 - p
    esperadas = q ** k * (1 + max(0, n - k) * p)
    return 1.0 - math.exp(-esperadas)

def temperatura_top15(d):
    """Racha actual de fallos del Top-15, puesta en escala contra lo normal.

    Devuelve None si aún no hay pronósticos puntuables por Top-15.
    """
    puestos = [p for p in (puesto_ganador(r) for r in resueltas(d)) if p is not None]
    n = len(puestos)
    if not n:
        return None
    racha = 0
    for p in reversed(puestos):
        if p > TOP_N:
            racha += 1
        else:
            break
    prob = prob_racha(racha, n) if racha else 1.0
    # Umbrales dinámicos: la racha más corta que ya sería rara (<10 %) y la que
    # sería francamente improbable (<1 %) con los sorteos jugados hasta hoy.
    ojo = alerta = None
    for k in range(1, n + 2):
        pk = prob_racha(k, n)
        if ojo is None and pk < 0.10:
            ojo = k
        if pk < 0.01:
            alerta = k
            break
    if racha == 0:
        nivel, etiqueta = "ok", "NORMAL"
    elif alerta is not None and racha >= alerta:
        nivel, etiqueta = "alerta", "ALERTA"
    elif ojo is not None and racha >= ojo:
        nivel, etiqueta = "ojo", "INUSUAL"
    else:
        nivel, etiqueta = "ok", "NORMAL"
    # 5 puntos: cuanto más improbable la racha, más encendidos.
    for i, corte in enumerate((0.50, 0.10, 0.05, 0.01)):
        if prob >= corte:
            puntos = i + 1
            break
    else:
        puntos = 5
    return dict(racha=racha, n=n, prob=prob, ojo=ojo, alerta=alerta,
                nivel=nivel, etiqueta=etiqueta, puntos=puntos,
                sola=(1 - P_MOD_T15) ** racha if racha else 1.0)

def analisis_reciente(d, filas, cuantos=48):
    """Estado de acierto en los últimos `cuantos` sorteos ya resueltos.

    Ventana corta a propósito: sirve para ver si algo se rompió hace poco, no
    para concluir que el modelo funciona. Con 48 sorteos el ruido es enorme y
    el texto lo dice.
    """
    ultimos = {(f, h) for f, h, _ in filas[-cuantos:]}
    res = [r for r in resueltas(d) if (r["fecha"], r["hora"]) in ultimos]
    n = len(res)
    if n == 0:
        return dict(n=0, cuantos=cuantos)
    t1 = sum(1 for r in res if r["salio"] == r["top3"][0])
    t3 = sum(1 for r in res if r["salio"] in r["top3"])
    puestos = [p for p in (puesto_ganador(r) for r in res) if p is not None]
    n15 = len(puestos); t15 = sum(1 for p in puestos if p <= TOP_N)
    a = dict(cuantos=cuantos, n=n, t1=t1, t3=t3, n15=n15, t15=t15,
             tasa1=t1/n*100, tasa3=t3/n*100,
             esp1=n * P0, esp3=n * P_AZAR_T3,
             p3=cola_binomial(t3, n, P_AZAR_T3),
             roi=(PAGO * t3 - 3 * n) / (3 * n) * 100,
             desde=filas[-cuantos][0] if len(filas) >= cuantos else filas[0][0],
             analisis=analisis_top15(d, res), eco=economia(d, res)[0],
             t5=sum(1 for p in puestos if p <= 5))
    if n15:
        a.update(tasa15=t15/n15*100, esp15=n15 * P_AZAR_T15,
                 p15=cola_binomial(t15, n15, P_AZAR_T15))
    return a

def resolver_tripletas(d, filas):
    """Cierra las tripletas cuya ventana de 12 sorteos ya está completa."""
    cambio = False; cerradas = []
    for t in d["tripletas"]:
        if not vigente(t) or suspendido(t) or t.get("estado") != "pendiente":
            continue
        i = t["n_inicio"]
        if i < len(filas) and (filas[i][0], filas[i][1]) != (t["inicio_fecha"], t["inicio_hora"]):
            t["anulado"] = {"cuando": ahora(), "motivo": "el historial no coincide con el inicio"}; cambio = True
            continue
        if len(filas) >= i + VENTANA:
            salieron = [filas[j][2] for j in range(i, i + VENTANA)]
            s = set(salieron)
            t["salieron"] = salieron
            t["aciertos"] = [all(a in s for a in jug) for jug in t["jugadas"]]
            t["base"] = comb(len(s), 3) / comb(K, 3)
            t["estado"] = "resuelta"; t["resuelto"] = ahora()
            cambio = True; cerradas.append(t)
    return cambio, cerradas

# Cadencia de la tripleta automática: 2 tripletas (un par) cada 24 horas, en vez
# de un par por sorteo. Menos jugadas y mejores: el par se arma con los 6
# animales de mayor probabilidad en el momento en que toca generarlo.
TRIPLETA_CADA_H = 24

def tripletas_auto(d):
    return [t for t in d["tripletas"] if vigente(t)
            and str(t.get("modelo", "")).startswith("tripleta_ventana")]

def horas_desde(cuando):
    try:
        return (datetime.now() - datetime.fromisoformat(cuando)).total_seconds() / 3600
    except (TypeError, ValueError):
        return None

def toca_tripleta(d):
    """(sí/no, horas que faltan). La primera de todas se genera enseguida."""
    autos = tripletas_auto(d)
    if not autos:
        return True, 0.0
    ultima = max(autos, key=lambda t: t.get("creado") or "")
    h = horas_desde(ultima.get("creado"))
    if h is None:                      # fecha ilegible: no bloquear para siempre
        return True, 0.0
    return h >= TRIPLETA_CADA_H, max(0.0, TRIPLETA_CADA_H - h)

def tripleta_en_curso(d, filas):
    """La tripleta automática viva más reciente (la que se está jugando)."""
    abiertas = [t for t in tripletas_auto(d) if t.get("estado") == "pendiente" and not suspendido(t)]
    return max(abiertas, key=lambda t: t["n_inicio"]) if abiertas else None

def marcador_tripleta(d):
    res = [t for t in d["tripletas"] if vigente(t) and t.get("estado") == "resuelta"]
    if not res: return dict(n=0)
    jug = sum(len(t["jugadas"]) for t in res)
    ac = sum(sum(t["aciertos"]) for t in res)
    esp = sum(t["base"] * len(t["jugadas"]) for t in res)
    return dict(n=len(res), jugadas=jug, aciertos=ac, tasa=ac/jug*100, azar=esp/jug*100,
                ganancia=ac * PAGO_TRIPLETA - jug)

# ---------------------------------------------------------------- deshacer
def deshacer():
    """Quita la última línea del historial.

    El pronóstico de ese sorteo se REABRE, no se anula (H3). Se calculó con el
    historial ANTERIOR a esa línea, que no cambia, así que sigue siendo un
    pronóstico honesto; lo que estaba mal era el resultado anotado. Anularlo
    dejaría borrar un fallo del marcador con «deshacer» + volver a anotar el
    mismo número. El valor anterior queda en `correcciones`, a la vista.

    Sí se anulan los pendientes y las tripletas calculados DESPUÉS del dato
    erróneo (lo llevaban dentro). Las tripletas anteriores cuya ventana lo
    contenía se reabren y se vuelven a cerrar con el dato corregido."""
    if not os.path.exists(HIST):
        return "No hay historial.", False
    with open(HIST, encoding="utf-8") as f:
        lineas = [l for l in f.readlines() if l.strip()]
    if not lineas:
        return "El historial está vacío.", False
    p = lineas[-1].split()
    if len(p) != 3:
        return "La última línea no tiene formato válido, no se tocó nada.", False
    fecha, hora_txt, num = p
    try:
        hora_idx = int(hora_txt)
    except ValueError:
        return "La última línea no tiene formato válido, no se tocó nada.", False
    idx_quitado = len(cargar()) - 1
    lb = _lineas_bin()                     # historial ANTES de quitar la línea
    with open(HIST, "w", encoding="utf-8") as f:
        f.writelines(lineas[:-1])
    d = log_cargar()
    reabierto = False
    for r in d["registros"]:
        if not vigente(r):
            continue
        mismo = r.get("fecha") == fecha and r.get("hora") == hora_idx
        if mismo and r.get("salio") is not None:
            r.setdefault("correcciones", []).append(
                {"cuando": ahora(), "salio_anterior": r["salio"], "resuelto_anterior": r.get("resuelto")})
            r["salio"] = None
            r.pop("resuelto", None)
            reabierto = True
        elif r.get("salio") is None and not mismo:
            # Pendiente del sorteo siguiente: se calculó con el historial
            # completo de antes de este deshacer.
            suspender(r, lb, len(lb))
    for t in d["tripletas"]:
        if not vigente(t):
            continue
        if t["n_inicio"] > idx_quitado:
            # Se generó con esta línea ya en el historial: queda en espera.
            if t.get("estado") == "resuelta":
                t.setdefault("correcciones", []).append(
                    {"cuando": ahora(), "salieron_anterior": t.get("salieron"), "aciertos_anterior": t.get("aciertos")})
                for k in ("salieron", "aciertos", "base", "resuelto"):
                    t.pop(k, None)
                t["estado"] = "pendiente"
            suspender(t, lb, t["n_inicio"])
        elif idx_quitado < t["n_inicio"] + VENTANA and t.get("estado") == "resuelta":
            t.setdefault("correcciones", []).append(
                {"cuando": ahora(), "salieron_anterior": t.get("salieron"), "aciertos_anterior": t.get("aciertos")})
            for k in ("salieron", "aciertos", "base", "resuelto"):
                t.pop(k, None)
            t["estado"] = "pendiente"
    if [fecha, hora_idx] not in d["sorteos_conocidos"]:
        d["sorteos_conocidos"].append([fecha, hora_idx])
    log_guardar(d)
    hora_leg = HORAS[hora_idx] if 0 <= hora_idx < 12 else hora_txt
    extra = (" Su pronóstico sigue en el marcador y se puntuará con el número que anotes ahora."
             if reabierto else "")
    return (f"Se deshizo {fecha_corta(fecha)} {hora_leg}: {num} {ANIM.get(num, '?')}. "
            f"Escribe el número correcto.{extra}"), True

# ------------------------------------------------------------- herramientas
HERRAMIENTAS = {
    "tripleta": {
        "titulo": "Validar tripleta de 12 sorteos", "dura": "1 a 3 min",
        "cmd": ["tripleta_ventana.py"],
        "que": "Mide en el histórico cuántas veces habrían ganado las tripletas sugeridas.",
        "mirar": "En la línea A_123_456: el % de aciertos debe superar 2,22% (umbral de 45x) y al «azar». "
                 "Si el primer número del intervalo [a-b] supera 2,22% y z(bloques) es mayor que +2, hay evidencia "
                 "real. Si «EV 45x» tiene el límite inferior negativo, todavía puede haber pérdida.",
    },
    "simulacion": {
        "titulo": "Simular ganancias del Top-5 escalonado", "dura": "30 a 60 s",
        "cmd": ["simulacion_banca.py", "2000", "1"],
        "que": "Juega miles de meses imaginarios con banca 2.000 y ficha 1, en tres escenarios.",
        "mirar": "«mitad de las veces» es lo típico; «1 de cada 10 mal» es un mes malo pero normal. Compara "
                 "el escenario MEDIDO con el PRUDENTE: la verdad está probablemente entre los dos. El escenario "
                 "SIN VENTAJA es lo que pasa si el modelo deja de servir: por eso existe el freno del 25 %.",
    },
    "escenario": {
        "titulo": "Escenario: cada forma de jugar, mes a mes, con 300 $", "dura": "10 s (la 1ª vez, varios min)",
        "cmd": ["escenario_gestion.py"],
        "que": "Repite 21 meses REALES (sorteos y pronósticos de desarrollo) jugando desde 300 $ con 5 políticas.",
        "mirar": "«final típico» es lo que pasa la mitad de los meses; «mes malo», 1 de cada 10. Mira el DIARIO: "
                 "incluso el mes típico puede bajar mucho antes de subir. Es algo optimista: en prueba ciega el "
                 "modelo rindió unos 5 puntos menos, y el Top-15 plano ahí perdió.",
    },
    "estrategia": {
        "titulo": "Cuántos animales conviene jugar", "dura": "10 a 30 s",
        "cmd": ["exploracion/estrategia_top5.py"],
        "que": "Acierto de cada puesto del orden y calibración del modelo, en 7.357 sorteos de desarrollo.",
        "mirar": "En la tabla 1, cada puesto con «retorno/ficha» negativo pierde plata aunque acierte a veces. "
                 "En la tabla 3, compara la ganancia por sorteo del Top-5 2-2-2-1-1 con el Top-15 plano.",
    },
    "top_grande": {
        "titulo": "¿Rinde jugar Top-15 a Top-23 a 10 $ por animal?", "dura": "30 a 90 s (la 1ª vez, varios min)",
        "cmd": ["exploracion/top_n_grande.py"],
        "que": "Mide en 7.357 sorteos de desarrollo la ganancia por sorteo de cada Top-N y un mes con 300 $ al Top-23.",
        "mirar": "«acierta» tiene que superar a «necesita» (N/30) para ganar. «gana/sorteo» con el IC95 entero "
                 "bajo 0 = pierde plata seguro. Desarrollo es optimista: en prueba ciega rinde algo menos.",
    },
    "reciproca": {
        "titulo": "¿RD Internacional ayuda a Lotto Activo? (H4b)", "dura": "5 a 15 min",
        "cmd": ["rdint/reciproca_la.py"],
        "que": "Recalcula el ensamble de LA y mide si saber lo que salió en RD 30 min antes mejora el pronóstico.",
        "mirar": "La fila PRINCIPAL: pasa si Δ mbits ≥ +5 con el IC95 entero sobre 0. Para dinero, el Top-5 "
                 "escalonado «+RD» tiene que superar al del ensamble solo.",
    },
    "cambio_rd": {
        "titulo": "¿Sacar del Top-5 de LA el animal que salió en RD? (regla de cambio)", "dura": "10 a 15 min",
        "cmd": ["rdint/cambio_top5.py"],
        "que": "Si el animal de RD de las (h−1):30 está en el Top-5 de LA h:00, lo saca y sube al #6; mide la plata.",
        "mirar": "La fila PRINCIPAL: diferencia por ficha > 0 con IC95 sobre 0 = confirmada; > 0 = se adopta "
                 "sin confirmar; ≤ 0 = se descarta.",
    },
    "cambio_noche": {
        "titulo": "¿RD de las 7:30 PM afecta a LA de las 8:00 del día siguiente?", "dura": "10 a 15 min",
        "cmd": ["rdint/cambio_noche.py"],
        "que": "Extiende la regla de cambio a las 8:00 con el RD de las 19:30 de la víspera y mide señal y plata.",
        "mirar": "La fila PRINCIPAL (PREREGISTRO_cambio_rd_noche.md): diferencia > 0 con IC95 sobre 0 y p < 0,05 "
                 "= confirmada; > 0 aquí y en desarrollo = se adopta sin confirmar; si no, se descarta.",
    },
}
TAREAS = {}

def salida_tarea(clave):
    return os.path.join(HERR, "resultados", f"pagina_{clave}.txt")

def iniciar_tarea(clave):
    if clave not in HERRAMIENTAS: return
    t = TAREAS.get(clave)
    if t and t["proc"].poll() is None: return
    os.makedirs(os.path.join(HERR, "resultados"), exist_ok=True)
    out = open(salida_tarea(clave), "w", encoding="utf-8")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    proc = subprocess.Popen([sys.executable] + HERRAMIENTAS[clave]["cmd"], cwd=HERR, stdout=out,
                            stderr=subprocess.STDOUT, env=env)
    TAREAS[clave] = {"proc": proc, "inicio": time.time(), "out": out}

def detener_tarea(clave):
    t = TAREAS.get(clave)
    if t and t["proc"].poll() is None:
        t["proc"].terminate()

def estado_tareas():
    res = {}
    for clave in HERRAMIENTAS:
        t = TAREAS.get(clave); ruta = salida_tarea(clave)
        texto = ""
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8", errors="replace") as f:
                texto = f.read()[-12000:]
        if t is None:
            est = "lista" if not texto else "terminada (ejecución anterior)"
            seg = None
        else:
            rc = t["proc"].poll()
            seg = int(time.time() - t["inicio"]) if rc is None else t.get("seg")
            if rc is None:
                est = "corriendo"
            else:
                if "seg" not in t:
                    t["seg"] = int(time.time() - t["inicio"]); t["out"].close(); seg = t["seg"]
                est = "terminada" if rc == 0 else f"terminó con error ({rc})"
        res[clave] = {"estado": est, "segundos": seg, "salida": texto}
    return res

# ------------------------------------------------- auto-registro del resultado
# El resultado sale publicado ~10 min despues de cada sorteo. Un hilo daemon
# consulta la fuente y lo anota con el MISMO registrar() del boton manual, asi
# que el marcador sigue siendo honesto: el pronostico del slot ya estaba
# guardado como pendiente ANTES de que nadie mirara el resultado.
#
# Todo lo que escribe (historial y predicciones) pasa por CERROJO, que tambien
# toman las peticiones HTTP: el hilo nunca escribe a la vez que un render.
CERROJO = threading.RLock()
AUTO_INTERVALO = 5 * 60          # cada cuanto revisa, en horario de sorteo
AUTO_ACTIVO = os.environ.get("AUTO_RESULTADO", "1") not in ("0", "no", "off")
AUTO = {"activo": AUTO_ACTIVO, "revisado": None, "anotados": 0, "seq": 0,
        "mensaje": "aún no se ha revisado", "corriendo": False}

def _auto_hora_util(t=None):
    """True entre las 8:05 y las 20:30 de Caracas (jornada + margen)."""
    t = t or datetime.now()
    return (8, 5) <= (t.hour, t.minute) and t.hour < 21

def auto_pasada():
    """Una consulta a la fuente. Devuelve cuantos resultados se anotaron."""
    if AUTO["corriendo"]:
        return 0
    AUTO["corriendo"] = True
    try:
        from scraping import auto_resultado
        with CERROJO:
            n = auto_resultado.una_pasada()
        AUTO["anotados"] = n
        AUTO["mensaje"] = (f"{n} resultado{'s' if n != 1 else ''} anotado"
                           f"{'s' if n != 1 else ''}") if n else "sin novedad"
        if n:
            AUTO["seq"] += 1          # dispara la recarga de la página abierta
    except Exception as ex:  # noqa: BLE001
        AUTO["mensaje"] = f"no se pudo consultar la fuente ({type(ex).__name__})"
        print(f"[auto] {ahora()} fallo: {ex!r}", file=sys.stderr, flush=True)
        n = 0
    finally:
        AUTO["revisado"] = ahora()
        AUTO["corriendo"] = False
    return n

def auto_bucle():
    while True:
        try:
            if AUTO["activo"] and _auto_hora_util():
                auto_pasada()
        except Exception as ex:  # noqa: BLE001
            print(f"[auto] {ahora()} bucle: {ex!r}", file=sys.stderr, flush=True)
        time.sleep(AUTO_INTERVALO)

PRONOSTICO_INTERVALO = 60        # segundos

def pronostico_bucle():
    """Cada minuto deja congelado el pronóstico del próximo sorteo.

    El primer llamado lanza el cálculo (asíncrono, ~10 s a 2 min); el
    siguiente lo encuentra hecho y lo guarda. Tras cada resultado, el
    pronóstico del sorteo siguiente queda guardado en 1-3 min, mucho antes
    de que se juegue."""
    while True:
        try:
            if PRED is not None:
                with CERROJO:
                    preparar()
        except Exception as ex:  # noqa: BLE001
            print(f"[pronostico] {ahora()} bucle: {ex!r}", file=sys.stderr, flush=True)
        time.sleep(PRONOSTICO_INTERVALO)

def auto_estado():
    base = {"seq": AUTO["seq"], "corriendo": AUTO["corriendo"]}
    hora = AUTO["revisado"][11:16] if AUTO["revisado"] else ""
    if not AUTO["activo"]:
        return dict(base, txt="Anotado automático apagado", clase="off")
    if AUTO["corriendo"]:
        return dict(base, txt="buscando el resultado…", clase="on")
    if not hora:
        return dict(base, txt="automático · primera revisión en marcha", clase="on")
    return dict(base, txt=f"automático · revisado {hora} · {AUTO['mensaje']}", clase="on")

# ------------------------------------------------------------------ página
def esc(s):
    return html.escape(str(s))

def num(x, dec=1):
    """Número con coma decimal, como se escribe en español."""
    return f"{x:.{dec}f}".replace(".", ",")

def plural(n, singular, plural_):
    """«1 acierto» / «3 aciertos»: el marcador se lee, no se descifra."""
    return f"{n} {singular if n == 1 else plural_}"

def chip(i, extra=""):
    return f'<span class="chip {extra}"><b>{POS[i]}</b> {ANIM[POS[i]].title()}</span>'

CSS = """
/* Sistema visual: tokens -> componentes. Claro y oscuro con el MISMO
   contraste de lectura (texto secundario >= 4.5:1 sobre su fondo).
   Estructura: cabecera fija con 2 pestañas; en cada pestaña la jugada y el
   registro arriba, y lo demás en desplegables (details.sec). */
:root{
  color-scheme:light dark;
  --bg:#f4f2ed; --bg-2:#ebe8e0; --card:#fff;
  --line:#e3dfd6; --line-soft:#efece5; --pista:#efece4;
  --ink:#17191d; --muted:#5b5e64; --soft:#6d7077;
  --brand:#b5621b; --brand-ink:#8a4a13; --brand-soft:#fbf0e3; --brand-line:#efd3b4;
  --ok:#1c6a49; --ok-soft:#e4f2ec; --bad:#96382a; --bad-soft:#f8e9e5;
  --r1:8px; --r2:14px; --pil:999px;
  --sh1:0 1px 2px rgba(23,25,29,.05);
  --sh2:0 1px 2px rgba(23,25,29,.04),0 6px 18px rgba(23,25,29,.06);
  --gap:14px; --cab:64px;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#131419; --bg-2:#1b1d23; --card:#1b1d23;
    --line:#2c2f38; --line-soft:#24272f; --pista:#262932;
    --ink:#ecebe7; --muted:#a8acb4; --soft:#959aa3;
    --brand:#e08b3f; --brand-ink:#f0a75f; --brand-soft:#2c2118; --brand-line:#5a3a1e;
    --ok:#5fc39a; --ok-soft:#16261f; --bad:#e78a76; --bad-soft:#2b1b17;
    --sh1:0 1px 2px rgba(0,0,0,.3);
    --sh2:0 1px 2px rgba(0,0,0,.3),0 6px 18px rgba(0,0,0,.35);
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-padding-top:calc(var(--cab) + 12px);accent-color:var(--brand);
  scrollbar-color:var(--line) transparent}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.5 "Segoe UI",-apple-system,BlinkMacSystemFont,Roboto,"Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;overflow-x:hidden}
::selection{background:var(--brand-soft);color:var(--ink)}
input{caret-color:var(--brand)}
:where(a,button,input,select,summary):focus-visible{outline:2px solid var(--brand);outline-offset:2px;border-radius:6px}
.sr{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
[hidden]{display:none !important}
.w{max-width:1040px;margin:0 auto;padding:16px 16px 40px}

/* ---------- cabecera fija con pestañas ---------- */
.cab{position:sticky;top:0;z-index:30;background:var(--bg);border-bottom:1px solid var(--line)}
.cab-in{max-width:1040px;margin:0 auto;padding:8px 16px;display:flex;align-items:center;gap:14px}
.marca{font-weight:700;font-size:15px;letter-spacing:-.01em;white-space:nowrap}
.marca small{display:block;font-weight:400;font-size:12px;color:var(--muted)}
.tabs{flex:1;display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:4px;background:var(--bg-2);
  border-radius:12px;max-width:460px;margin-left:auto}
.tabs a{display:flex;flex-direction:column;justify-content:center;min-height:44px;padding:5px 12px;border-radius:9px;
  text-decoration:none;color:var(--muted);line-height:1.2;transition:background .2s,color .2s,box-shadow .2s}
.tabs a b{font-size:14.5px;font-weight:650;letter-spacing:-.01em}
.tabs a small{font-size:11.5px;font-variant-numeric:tabular-nums}
.tabs a:hover{color:var(--ink)}
.tabs a[aria-selected=true]{background:var(--card);color:var(--ink);box-shadow:var(--sh2)}
.tabs a[aria-selected=true] small{color:var(--brand-ink)}
@media (max-width:640px){.marca{display:none}.tabs{max-width:none;margin:0}}

/* ---------- tarjetas ---------- */
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--r2);padding:18px;
  box-shadow:var(--sh1);min-width:0;overflow-wrap:break-word}
.duo{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(0,1fr);gap:var(--gap);align-items:start;
  margin-bottom:var(--gap)}
.duo>*{min-width:0}
.duo .reg{position:sticky;top:calc(var(--cab) + 14px)}
@media (max-width:820px){.duo{grid-template-columns:1fr}.duo .reg{position:static}}
.pila{display:grid;gap:10px}

/* ---------- la jugada ---------- */
.jh{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:4px}
.jh h2{margin:0;font-size:clamp(21px,1rem + 1.2vw,26px);line-height:1.15;letter-spacing:-.02em;font-weight:750}
.jh h2 span{color:var(--brand-ink);white-space:nowrap}
.ult{margin:0 0 14px;font-size:13.5px;color:var(--muted)}
.ult b{color:var(--ink);font-weight:600}
.pill{display:inline-flex;align-items:center;gap:6px;flex:none;font-size:12px;padding:5px 11px;border-radius:var(--pil);
  background:var(--ok-soft);color:var(--ok);font-weight:650;line-height:1.2;white-space:nowrap}
.pill::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor;flex:0 0 auto}
.pill.warn{background:var(--brand-soft);color:var(--brand-ink)}
.pill.warn::before{animation:late 1.4s ease-in-out infinite}
.pill.gris{background:var(--bg-2);color:var(--muted)}
@keyframes late{50%{opacity:.25}}
.jug{list-style:none;margin:0;padding:0}
.jug li{display:grid;grid-template-columns:18px 50px minmax(0,1fr) 38px 38px;align-items:center;gap:8px;
  padding:8px 0;border-top:1px solid var(--line-soft)}
@media (max-width:640px){.jug li{padding:6px 0}.jug .n{font-size:25px}.jh h2{font-size:20px}.card{padding:16px}
  .leyenda{margin-top:10px}}
.jug li.cols{border-top:none;padding:0 0 6px;font-size:11px;color:var(--muted);font-weight:600;letter-spacing:.02em}
.jug li.cols span:nth-child(n+4){text-align:center;line-height:1.15}
.jug .rk{font-size:12px;color:var(--soft);font-variant-numeric:tabular-nums;text-align:right}
.jug .n{font-size:28px;font-weight:800;color:var(--brand);font-variant-numeric:tabular-nums;letter-spacing:-.03em;line-height:1}
.jug .nm{font-size:16px;font-weight:600;letter-spacing:-.01em;min-width:0}
.jug .nm small{display:block;font-size:12px;font-weight:400;color:var(--muted);font-variant-numeric:tabular-nums}
.fx{justify-self:center;display:inline-grid;place-items:center;min-width:30px;height:30px;padding:0 6px;border-radius:8px;
  font-size:15px;font-weight:700;font-variant-numeric:tabular-nums}
.fx.a{background:var(--brand);color:#fff}
@media (prefers-color-scheme:dark){.fx.a{color:#1b1206}}
.fx.b{background:var(--bg-2);color:var(--ink)}
.fx.z{color:var(--soft);font-weight:400}
.jug.resto li{grid-template-columns:18px 50px minmax(0,1fr) 38px 38px}
.jug.resto .n{font-size:22px;color:var(--muted)}
.jug.resto .nm{font-size:15px;font-weight:500}
details.mas{margin-top:2px;border-top:1px solid var(--line-soft)}
details.mas>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:8px;min-height:44px;
  font-size:13.5px;font-weight:600;color:var(--brand-ink)}
details.mas>summary::-webkit-details-marker{display:none}
details.mas[open]>summary{border-bottom:1px solid var(--line-soft)}
.leyenda{margin:14px 0 0;display:grid;gap:6px;font-size:13px;color:var(--muted)}
.leyenda p{margin:0}
.leyenda b{color:var(--ink)}
.leyenda i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:0}
.leyenda i.a{background:var(--brand)}.leyenda i.b{background:var(--bg-2);box-shadow:inset 0 0 0 1px var(--line)}

.compartir{display:flex;gap:8px;margin-top:12px}
.compartir select{padding:0 10px;font:inherit;font-size:15px;color:var(--ink);background:var(--bg-2);
  border:1px solid var(--line);border-radius:var(--r1)}
.compartir input[type=text]{font-size:16px;padding:10px 12px}

/* ---------- chevron (dibujado, no un glifo) ---------- */
.chev{flex:none;width:9px;height:9px;border-right:2px solid currentColor;border-bottom:2px solid currentColor;
  transform:translateY(-2px) rotate(45deg);transition:transform .25s cubic-bezier(.22,1,.36,1)}
details[open]>summary .chev{transform:translateY(2px) rotate(-135deg)}

/* ---------- registrar ---------- */
.reg h2{margin:0;font-size:17px;letter-spacing:-.01em}
.reg .rh{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px}
.reg p{margin:0 0 12px;font-size:13px;color:var(--muted)}
form.anotar{display:flex;gap:8px}
input[type=text]{flex:1;min-width:0;padding:12px 14px;font-size:20px;font-weight:600;color:var(--ink);border:1px solid var(--line);
  border-radius:var(--r1);background:var(--bg-2);font-variant-numeric:tabular-nums;font-family:inherit}
input[type=text]::placeholder{color:var(--soft);font-weight:400;font-size:16px}
input[type=text]:focus{border-color:var(--brand);outline:none;box-shadow:0 0 0 3px var(--brand-soft)}
button{min-height:44px;padding:10px 18px;font:inherit;font-size:15px;font-weight:650;border:1px solid transparent;border-radius:var(--r1);
  background:var(--ink);color:var(--card);cursor:pointer;transition:opacity .15s,background .15s,border-color .15s}
button:hover{opacity:.88}
button:active{transform:translateY(1px)}
button.sec{background:var(--card);color:var(--ink);border-color:var(--line)}
button.sec:hover{border-color:var(--soft);opacity:1}
button.link{min-height:44px;background:none;color:var(--bad);padding:8px 2px;font-size:13.5px;font-weight:500;
  text-decoration:underline;text-underline-offset:3px;border:none}
.acciones{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px 14px;margin-top:12px}
.acciones form{margin:0}
.auto{display:inline-flex;align-items:center;gap:7px;font-size:12px;font-weight:600;color:var(--ok);
  background:var(--ok-soft);padding:5px 10px;border-radius:var(--pil);line-height:1.25}
.auto::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor;flex:0 0 auto}
.auto.off{color:var(--muted);background:var(--bg-2)}

/* ---------- avisos ---------- */
.msg{font-size:14px;padding:12px 15px;border-radius:var(--r1);margin:0 0 var(--gap);border:1px solid transparent}
.msg.ok{background:var(--ok-soft);color:var(--ok)}
.msg.no{background:var(--bg-2);color:var(--muted)}
.msg.bad{background:var(--bad-soft);color:var(--bad)}
.jugada .msg{margin:12px 0 0}
.tip{font-size:13.5px;color:var(--brand-ink);background:var(--brand-soft);padding:11px 13px;border-radius:var(--r1);margin:12px 0 0}
.note{font-size:12.5px;color:var(--muted);margin:10px 0 0}

/* ---------- desplegables ---------- */
details.sec{background:var(--card);border:1px solid var(--line);border-radius:var(--r2);box-shadow:var(--sh1);
  margin-bottom:10px;min-width:0}
details.sec>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:14px;padding:14px 18px;min-height:60px;
  border-radius:var(--r2)}
details.sec>summary::-webkit-details-marker{display:none}
details.sec>summary:hover .st{color:var(--ink)}
details.sec>summary .st{flex:1;min-width:0}
details.sec>summary h2{margin:0;font-size:16px;letter-spacing:-.01em;font-weight:650}
details.sec>summary .meta{display:block;font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums;margin-top:1px}
details.sec>summary .chev{color:var(--muted)}
details.sec[open]>summary{border-bottom:1px solid var(--line-soft);border-radius:var(--r2) var(--r2) 0 0}
.cuerpo{padding:16px 18px 18px}
details[open]>.cuerpo{animation:abre .28s cubic-bezier(.22,1,.36,1)}
@keyframes abre{from{opacity:0;transform:translateY(-4px)}}

/* ---------- resultados y puestos ---------- */
.lista{width:100%;border-collapse:collapse;font-size:14px}
.lista th,.lista td{padding:8px 6px;text-align:left;font-variant-numeric:tabular-nums}
.lista thead th{font-size:11.5px;color:var(--muted);font-weight:600;border-bottom:1px solid var(--line)}
.lista tbody th{font-size:12px;color:var(--brand-ink);font-weight:700;letter-spacing:.02em;padding-top:16px;
  border-bottom:1px solid var(--line)}
.lista tbody tr:first-child th{padding-top:8px}
.lista td{border-bottom:1px solid var(--line-soft)}
.lista td.h{color:var(--muted);white-space:nowrap;width:1%}
.lista td.s b{font-size:16px;margin-right:6px}
.lista td.p{text-align:right;width:1%;white-space:nowrap}
.lista .t3{color:var(--muted);font-size:12.5px}
.puesto{display:inline-grid;place-items:center;min-width:44px;height:28px;padding:0 8px;border-radius:var(--pil);
  font-weight:700;font-size:13.5px}
.puesto.p5{background:var(--brand);color:#fff}
@media (prefers-color-scheme:dark){.puesto.p5{color:#1b1206}}
.puesto.p15{background:var(--brand-soft);color:var(--brand-ink);box-shadow:inset 0 0 0 1px var(--brand-line)}
.puesto.fuera{background:var(--bg-2);color:var(--muted)}
.clave{display:flex;flex-wrap:wrap;gap:6px 14px;margin:0 0 10px;font-size:12.5px;color:var(--muted)}
.clave .puesto{min-width:0;height:22px;font-size:11.5px;margin-right:4px}

/* ---------- piezas compartidas (RD) ---------- */
.chip{display:inline-flex;align-items:baseline;gap:6px;padding:6px 11px;border-radius:var(--pil);background:var(--bg-2);
  font-size:14px;color:var(--ink)}
.chip b{color:var(--brand-ink);font-size:15.5px;font-variant-numeric:tabular-nums}
.chip small{color:var(--muted);font-size:11.5px}
.tira{display:flex;flex-wrap:wrap;gap:6px}
.cuerpo h3{margin:0 0 8px;font-size:13px;color:var(--muted);font-weight:650}
.cuerpo h3~h3{margin-top:16px}
.cifras{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin:0 0 14px}
.cifras div{background:var(--bg-2);border-radius:var(--r1);padding:9px 12px}
.cifras small{display:block;font-size:11.5px;color:var(--muted)}
.cifras b{font-size:20px;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.tabla{width:100%;border-collapse:collapse;font-size:13.5px;font-variant-numeric:tabular-nums}
.tabla th{text-align:left;color:var(--muted);font-weight:600;font-size:12px;padding:6px 6px;border-bottom:1px solid var(--line)}
.tabla td{padding:7px 6px;border-bottom:1px solid var(--line-soft)}
.tabla td.ok{color:var(--ok);font-weight:650}.tabla td.bad{color:var(--bad);font-weight:650}
.desliza{overflow-x:auto;max-width:100%}
.cuerpo p{font-size:14px;margin:0 0 10px;max-width:70ch}

footer{font-size:12.5px;color:var(--muted);margin-top:18px;text-align:center}

@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms !important;animation-iteration-count:1 !important;
    transition-duration:.01ms !important;scroll-behavior:auto !important}
}
"""

JS = """
<script>
(function(){
  var calc = %CALC%;
  function tareas(){
    fetch('/tareas.json').then(r=>r.json()).then(function(t){
      var alguna=false;
      var a=t._auto;
      if(a){
        var el=document.getElementById('auto-est');
        if(el){ el.textContent=a.txt; el.className='auto '+a.clase; }
        // Si el resultado acaba de anotarse solo, la página que estás viendo ya
        // es vieja (hay sorteo nuevo y otra predicción): se recarga sola.
        if(window.__autoSeq===undefined) window.__autoSeq=a.seq;
        else if(a.seq>window.__autoSeq){ location.replace(location.pathname + location.search); return; }
        if(a.corriendo) alguna=true;
      }
      Object.keys(t).forEach(function(k){
        var s=document.getElementById('st-'+k), o=document.getElementById('out-'+k), b=document.getElementById('bt-'+k);
        if(!s) return;
        var e=t[k];
        s.textContent=e.estado+(e.segundos!=null?' · '+e.segundos+' s':'');
        s.className='st '+(e.estado==='corriendo'?'corriendo':'');
        if(o && e.salida){o.textContent=e.salida; o.parentNode.open = o.parentNode.open || e.estado==='corriendo';}
        if(b){b.textContent = e.estado==='corriendo' ? 'Detener' : 'Ejecutar';
              b.form.action = e.estado==='corriendo' ? '/herramienta/'+k+'/detener' : '/herramienta/'+k;}
        if(e.estado==='corriendo') alguna=true;
      });
      setTimeout(tareas, alguna?2000:8000);
    }).catch(function(){setTimeout(tareas,8000);});
  }
  tareas();
  // Pestañas: ?tab=la|rd manda; si no viene, la última que abriste.
  var tabs = [].slice.call(document.querySelectorAll('.tabs [role=tab]'));
  function ver(t, guardar){
    if(t !== 'la' && t !== 'rd') return;
    tabs.forEach(function(a){
      var on = a.getAttribute('data-tab') === t;
      a.setAttribute('aria-selected', on ? 'true' : 'false');
      a.tabIndex = on ? 0 : -1;
      var p = document.getElementById(a.getAttribute('aria-controls'));
      if(p) p.hidden = !on;
    });
    if(guardar){
      try{ localStorage.setItem('lotto.tab', t); }catch(e){}
      try{ var u = new URL(location.href); u.searchParams.set('tab', t);
           history.replaceState(null, '', u.pathname + u.search + u.hash); }catch(e){}
    }
  }
  tabs.forEach(function(a, i){
    a.addEventListener('click', function(ev){ ev.preventDefault(); ver(a.getAttribute('data-tab'), true); });
    a.addEventListener('keydown', function(ev){
      if(ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
      ev.preventDefault();
      var n = tabs[(i + (ev.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      n.focus(); ver(n.getAttribute('data-tab'), true);
    });
  });
  var qtab = null;
  try{ qtab = new URLSearchParams(location.search).get('tab'); }catch(e){}
  if(qtab){ try{ localStorage.setItem('lotto.tab', qtab); }catch(e){} }
  else { var s = null; try{ s = localStorage.getItem('lotto.tab'); }catch(e){} if(s) ver(s, false); }
  // Desplegables: recuerda cuáles dejaste abiertos.
  [].forEach.call(document.querySelectorAll('details[data-rec]'), function(d){
    var k = 'lotto.sec.' + d.id;
    try{ var v = localStorage.getItem(k); if(v === '1') d.open = true; else if(v === '0') d.open = false; }catch(e){}
    d.addEventListener('toggle', function(){ try{ localStorage.setItem(k, d.open ? '1' : '0'); }catch(e){} });
  });
  if(calc){
    (function listo(){
      fetch('/listo.json').then(r=>r.json()).then(function(j){
        var inp=document.getElementById('num');
        if(j.listo && !(inp && inp.value)) location.replace(location.pathname + location.search);
        else setTimeout(listo, 2500);
      }).catch(function(){setTimeout(listo,4000);});
    })();
  }
})();
</script>
"""

def html_prediccion(e, calculando, pend, aviso_modelo):
    fecha, hora = fecha_corta(e["pf"]), HORAS[e["ph"]]
    cab = f'<div class="hh"><h2>Próximo sorteo</h2><span>{esc(fecha)} · {hora}</span></div>'
    if calculando:
        cuerpo = ('<div class="tip">Calculando la predicción con el ensamble (unos 10 segundos). '
                  'La página se actualiza sola.</div>')
        if PRED is not None and PRED.error:
            cuerpo += f'<div class="msg bad">Error: {esc(PRED.error[-400:])}</div>'
        return f'<section class="card" id="sorteo">{cab}{cuerpo}</section>'
    # El orden que se muestra es el congelado del pronóstico, el que se puntúa.
    orden = e["orden"]
    if pend is not None:
        orden = pend.get("orden_completo") or pend["top3"]
    fichas = fichas_por_puesto()
    maxp = 0.07
    filas = ""
    for r, i in enumerate(orden[:5], 1):
        p = e["sc"][i]
        fx = fichas[r]
        filas += (f'<div class="pick"><span class="rk">{r}</span><span class="num">{POS[i]}</span>'
                  f'<div><div class="nm">{ANIM[POS[i]].title()} '
                  f'<small>· {fx} ficha{"s" if fx != 1 else ""}</small></div>'
                  f'<div class="bar"><i style="width:{min(100, p/maxp*100):.0f}%"></i>'
                  f'<em style="left:{P0/maxp*100:.0f}%" title="azar"></em></div></div>'
                  f'<span class="pc">{p*100:.2f}%<small>salió hace {e["gaps"][i] + 1} sorteos</small></span></div>')
    nota = ('<p class="note">La jugada: <b>2 fichas</b> a cada uno de los 3 primeros (la base, ventaja probada) y '
            '<b>1 ficha</b> al 4º y al 5º (refuerzo: gana en los datos pero sin certeza estadística). 8 fichas; cobra '
            '~1 de cada 5 sorteos: 60 si sale uno de los 3 primeros, 30 si sale el 4º o el 5º. '
            'La raya gris marca el azar (2,63%).</p>')
    top15 = html_top15(e, pend)
    return f'<section class="card" id="sorteo">{cab}{filas}{nota}{aviso_modelo}{top15}</section>'

def html_top15(e, pend=None):
    # El orden que se muestra tiene que ser EL MISMO que se puntúa: si ya hay
    # un pronóstico guardado para este sorteo, se usa su orden congelado.
    orden = e["orden"]
    if pend is not None and pend.get("orden_completo"):
        orden = pend["orden_completo"]
    filas = ""
    pond = fichas_por_puesto(PONDERADO)
    for r, i in enumerate(orden[:15], 1):
        p = e["sc"][i]
        if r == 6:
            filas += ('<p class="note"><b>Del 6º al 15º:</b> cada uno acierta ~3,0%, menos del 3,33% que pide el pago 30x. '
                      'Solo entran en el Top-15 ponderado, a 1 ficha, para que cobres la mitad de los sorteos.</p>')
        atenuado = ' style="opacity:.55"' if r > 5 else ""
        filas += (f'<div class="pick"{atenuado}><span class="rk">{r}</span><span class="num">{POS[i]}</span>'
                  f'<div><div class="nm">{ANIM[POS[i]].title()} <small>· ponderado: {pond[r]} ficha{"s" if pond[r] != 1 else ""}</small></div></div>'
                  f'<span class="pc">{p*100:.2f}%<small>salió hace {e["gaps"][i] + 1} sorteos</small></span></div>')
    nota = ('<p class="note"><b>Top-15 ponderado</b> (alternativa): 3 fichas del 1º al 3º, 2 al 4º y 5º, 1 del 6º '
            'al 15º = 23 fichas. Cobra ~1 de cada 2 sorteos y cada acierto deja ganancia: +67, +37 o +7. '
            'Prueba ciega ≈ +6% (el Top-15 plano, −1%).</p>')
    return (f'<details style="margin-top:12px"><summary>Ver Top-15 completo (y el ponderado)</summary>{nota}{filas}</details>')

def cambio_rd(orden, pf, ph):
    """Regla de cambio (PREREGISTRO_cambio_rd_top5.md, adoptada sin confirmar el 2026-09-23).

    Si el animal que salió en RD Internacional a las (h−1):30 está en el Top-5 de LA h:00, se
    intercambia con el 6º. Solo cambia lo que se MUESTRA para jugar: el congelado que se puntúa
    no se toca. Devuelve (orden, info); info es None en el sorteo de 8:00 o si falla RD."""
    if ph <= 0 or len(orden) < 6:
        return orden, None
    try:
        import rdint_vivo
        cod = next((c for f, h, c in rdint_vivo.cargar_rd() if f == pf and h == ph - 1), None)
        info = {"hora_rd": rdint_vivo.HORAS_RD[ph - 1], "rd": cod}
    except Exception:  # noqa: BLE001 — RD no debe tumbar la jugada de LA
        return orden, None
    nuevo = _cambiar(orden, cod) if cod is not None else orden
    if nuevo is orden:
        return orden, info
    info.update(sale=cod, entra=POS[orden[5]], puesto=orden.index(IDX[cod]) + 1)
    return nuevo, info

def _cambiar(orden, cod):
    """Igual que herramientas/rdint/cambio_top5.py (lo validado): se quita del
    Top-5 el animal `cod`, los de abajo suben un puesto y el 6º entra 5º; `cod`
    pasa al 6º. Devuelve el MISMO objeto `orden` si no hay cambio."""
    r = IDX[cod]
    if len(orden) < 6 or r not in orden[:5]:
        return orden
    return [x for x in orden[:5] if x != r] + [orden[5], r] + list(orden[6:])

# Marcador en vivo de la regla: cuenta desde el día en que se adoptó, que la
# prueba (hasta 2026-09-22) nunca vio. RD de las (h−1):30 siempre sale antes
# de LA h:00, así que aplicarla al congelado después no usa nada del futuro.
CAMBIO_RD_DESDE = "2026-09-23"

def marcador_cambio_rd(d):
    """Top-5 escalonado con y sin la regla de cambio, sobre el mismo congelado."""
    try:
        import rdint_vivo
        rd = {(f, h): c for f, h, c in rdint_vivo.cargar_rd()}
    except Exception:  # noqa: BLE001
        return None
    f = fichas_por_puesto()
    m = dict(desde=CAMBIO_RD_DESDE, n=0, cambios=0, gano_rd=0, gano_6=0, sin=0, con=0)
    for r in resueltas(d):
        orden = r.get("orden_completo")
        if not orden or r["fecha"] < CAMBIO_RD_DESDE or r["hora"] <= 0 or r["salio"] not in orden:
            continue
        cod = rd.get((r["fecha"], r["hora"] - 1))
        if cod is None:
            continue
        m["n"] += 1
        p = orden.index(r["salio"]) + 1
        m["sin"] += PAGO * f[p] - sum(f)
        nuevo = _cambiar(orden, cod)
        if nuevo is not orden:
            m["cambios"] += 1
            m["gano_rd"] += r["salio"] == IDX[cod]
            m["gano_6"] += r["salio"] == orden[5]
        m["con"] += PAGO * f[nuevo.index(r["salio"]) + 1] - sum(f)
    m["dif"] = m["con"] - m["sin"]
    return m

# ------------------------------------------------ pronósticos en sombra (motor_nuevo)
# ag12 (pares consecutivos recientes) y ag12 + RD se guardan junto al congelado
# del ensamble, pero NO se muestran ni se puntúan en el marcador principal: solo
# sirven para medirlos con sorteos futuros (motor_nuevo/RETOMAR.md).
SOMBRA_DESDE = "2026-09-26"
SOMBRA_MODELOS = ("ag12", "ag12_rd")

def sombra_de(filas, pf, ph, sc):
    """{modelo: 38 probabilidades} o None. Nunca tumba el pronóstico principal."""
    try:
        sys.path.insert(0, os.path.join(HERR, "modelos", "ag12"))
        import sombra
        try:
            import rdint_vivo
            rd = {(f, h): IDX[c] for f, h, c in rdint_vivo.cargar_rd() if c in IDX}
        except Exception:  # noqa: BLE001
            rd = None
        out = sombra.corregir(filas, pf, ph, sc, rd)
        return {k: v for k, v in out.items() if v is not None}
    except Exception as ex:  # noqa: BLE001
        print(f"[sombra] {ahora()} fallo: {ex!r}", file=sys.stderr, flush=True)
        return None

def marcador_sombra(d):
    """Ensamble contra los modelos en sombra, sobre los MISMOS sorteos resueltos."""
    fichas = fichas_por_puesto()
    nombres = ("ensamble",) + SOMBRA_MODELOS
    m = {k: dict(n=0, top3=0, top5=0, top15=0, mbits=0.0, t5_neto=0.0) for k in nombres}
    for r in resueltas(d):
        s = r.get("sombra")
        if not s or r["fecha"] < SOMBRA_DESDE or not r.get("scores") or not all(k in s for k in SOMBRA_MODELOS):
            continue
        for k in nombres:
            p = r["scores"] if k == "ensamble" else s[k]
            tot = sum(p)
            orden = sorted(range(K), key=lambda i: (-p[i], i))
            pos = orden.index(r["salio"]) + 1
            x = m[k]; x["n"] += 1
            x["top3"] += pos <= 3; x["top5"] += pos <= 5; x["top15"] += pos <= 15
            x["mbits"] += 1000 * math.log2(max(p[r["salio"]] / tot, 1e-12) * K)
            x["t5_neto"] += PAGO * fichas[pos] - sum(fichas)
    for x in m.values():
        if x["n"]:
            for c in ("top3", "top5", "top15"):
                x[c + "_pct"] = round(100 * x[c] / x["n"], 2)
            x["mbits"] = round(x["mbits"] / x["n"], 1)
    return {"desde": SOMBRA_DESDE, "marcador": m}

def nota_cambio_rd(info):
    if info is None:
        return ""
    if info["rd"] is None:
        return (f'<p class="note">RD de las {info["hora_rd"]} aún no está anotado: si el animal que salga ahí '
                'está en este Top-5, se cambia por el 6º al recargar.</p>')
    if "sale" not in info:
        return (f'<p class="note">RD de las {info["hora_rd"]}: '
                f'<b>{esc(info["rd"])} {esc(ANIM[info["rd"]].title())}</b> — no está en el Top-5, sin cambio.</p>')
    return (f'<div class="tip"><b>Cambio por RD:</b> {esc(info["sale"])} {esc(ANIM[info["sale"]].title())} '
            f'salió en RD a las {info["hora_rd"]} → sale del {info["puesto"]}º, los de abajo suben un puesto y entra '
            f'<b>{esc(info["entra"])} {esc(ANIM[info["entra"]].title())}</b> de 5º. Lotto Activo casi nunca repite lo '
            'que RD sacó media hora antes (prueba 2026-09-23: +1,4 puntos por ficha, sin confirmar aún).</div>')

def html_banca(e, banca=None):
    """Cuánto poner en cada animal según la banca (misma regla que gestion_banca.py)."""
    form = ('<form class="reg" method="get" action="/#banca">'
            '<label class="sr" for="banca">Tu banca</label>'
            f'<input type="text" id="banca" name="banca" inputmode="decimal" placeholder="Tu banca, p. ej. 2000" '
            f'value="{esc(f"{banca:g}") if banca else ""}" autocomplete="off"><button type="submit">Calcular</button></form>')
    cuerpo = ('<p class="note top">Escribe cuánta plata tienes separada para jugar y te digo cuánto poner en cada '
              'animal. Apuesta ~0,4 % de la banca por sorteo: poco a propósito, para aguantar las rachas.</p>')
    if banca:
        import gestion_banca as GB
        p = GB.plan_sorteo(banca)
        orden = e.get("orden") or []
        orden, _ = cambio_rd(orden, e["pf"], e["ph"])
        if p.get("solo_top3") or p["apostar"]:
            montos = ([p["solo_top3"]] * 3 + [0, 0]) if p.get("solo_top3") else \
                     [f * p["ficha"] for f in GB.FICHAS]
            filas = "".join(
                f'<div class="pick"><span class="rk">{r}</span><span class="num">{POS[i]}</span>'
                f'<div><div class="nm">{ANIM[POS[i]].title()}</div></div>'
                f'<span class="pc">{montos[r-1]:g}<small>{"no se juega" if not montos[r-1] else "a este animal"}</small></span></div>'
                for r, i in enumerate(orden[:5], 1)) if len(orden) >= 5 else ""
            total = p["total"]
            cuerpo += (f'<div class="msg ok">{esc(p["motivo"])}</div>{filas}'
                       f'<p class="note">Total por sorteo: <b>{total:g}</b>. Si sale uno de los 3 primeros ganas '
                       f'<b>{p["gana_top3"]:+g}</b> neto'
                       + (f'; si sale el 4º o 5º, <b>{p["gana_45"]:+g}</b>' if p["gana_45"] else "")
                       + f'; si no sale ninguno pierdes {total:g}. Recalcula con tu banca cada día.</p>')
        else:
            cuerpo += f'<div class="msg bad">{esc(p["motivo"])}</div>'
    return ('<section class="card" id="banca"><div class="hh"><h2>¿Cuánto apuesto?</h2></div>'
            f'{cuerpo}{form}</section>')

def html_registro(e=None):
    a = auto_estado()
    cuando = f' de las {HORAS[e["ph"]]}' if e else ""
    return ('<section class="card reg" id="registrar" aria-labelledby="reg-t">'
            f'<div class="rh"><h2 id="reg-t">¿Qué salió{cuando}?</h2>'
            f'<span class="auto {a["clase"]}" id="auto-est">{esc(a["txt"])}</span></div>'
            '<p>Se anota solo unos 10 min después del sorteo. Escríbelo aquí solo para adelantarlo.</p>'
            '<form class="anotar" method="post" action="/registrar">'
            '<label class="sr" for="num">Número del animal que salió</label>'
            '<input type="text" id="num" name="num" placeholder="0, 00 o 1-36" autocomplete="off" '
            'inputmode="numeric" enterkeyhint="send"><button type="submit">Anotar</button></form>'
            '<div class="acciones">'
            '<form method="post" action="/auto"><button class="sec" type="submit">Buscar ahora</button></form>'
            '<form method="post" action="/deshacer" onsubmit="return confirm(\'¿Deshacer el último resultado anotado?\')">'
            '<button class="link" type="submit">Deshacer el último</button></form></div></section>')

def _fx(n, clase):
    """Casilla de fichas: número relleno si se juega, raya tenue si no."""
    if not n:
        return '<span class="fx z" aria-label="sin fichas">–</span>'
    return f'<span class="fx {clase}" aria-label="{n} ficha{"s" if n != 1 else ""}">{n}</span>'

def fila_jugada(r, num_, nombre, sub, f5, fp):
    return (f'<li><span class="rk">{r}</span><span class="n">{esc(num_)}</span>'
            f'<span class="nm">{esc(nombre)}<small>{sub}</small></span>'
            f'{_fx(f5, "a")}{_fx(fp, "b")}</li>')

COLS_JUGADA = ('<li class="cols" aria-hidden="true"><span></span><span></span><span>Animal</span>'
               '<span>Top-5</span><span>Ponde&shy;rado</span></li>')

def html_compartir(titulo, animales):
    """Compartir la jugada como texto: Top 5 o Top 15, monto fijo por animal."""
    return (f'<div class="compartir" data-t="{esc(titulo)}" data-a="{esc("|".join(animales[:15]))}">'
            '<select aria-label="Cuántos animales"><option value="5">Top 5</option><option value="15">Top 15</option></select>'
            '<input type="text" inputmode="decimal" placeholder="$ por animal" aria-label="Monto por animal">'
            '<button type="button" class="sec">Compartir</button></div>')

def html_jugada(e, calculando, pend, aviso_modelo, modelo):
    """La jugada del próximo sorteo: Top-5 a la vista y del 6º al 15º plegado.

    El orden es SIEMPRE el congelado que se puntúa (pend), como antes."""
    fecha, hora = fecha_corta(e["pf"]), HORAS[e["ph"]]
    f, h, v = e["ult"]
    if calculando:
        pill = '<span class="pill warn">calculando…</span>'
    elif modelo == "hazard_actual":
        pill = '<span class="pill warn">modelo antiguo</span>'
    elif pend is not None:
        pill = '<span class="pill" title="guardado antes del sorteo: es el que se puntúa">congelado</span>'
    else:
        pill = '<span class="pill gris">listo</span>'
    cab = (f'<div class="jh"><h2 id="jug-t">Próximo sorteo · <span>{hora}</span></h2>{pill}</div>'
           f'<p class="ult">{esc(fecha.capitalize())} · último: '
           f'{"" if f == e["pf"] else esc(fecha_corta(f)) + " "}{HORAS[h]} → '
           f'<b>{POS[v]} {ANIM[POS[v]].title()}</b></p>')
    if calculando:
        cuerpo = ('<div class="tip">Calculando el pronóstico con el ensamble (de 10 segundos a 2 minutos). '
                  'La página se actualiza sola.</div>')
        if PRED is not None and PRED.error:
            cuerpo += f'<div class="msg bad">Error: {esc(PRED.error[-400:])}</div>'
        return f'<section class="card jugada" id="sorteo" aria-labelledby="jug-t">{cab}{cuerpo}</section>'
    orden = e["orden"]
    if pend is not None:
        orden = pend.get("orden_completo") or pend["top3"]
    orden, info_rd = cambio_rd(orden, e["pf"], e["ph"])
    esc5, pond = fichas_por_puesto(), fichas_por_puesto(PONDERADO)
    def fila(r, i):
        return fila_jugada(r, POS[i], ANIM[POS[i]].title(),
                           f'{num(e["sc"][i] * 100, 2)} % · hace {e["gaps"][i] + 1} sorteos',
                           esc5[r], pond[r])
    top5 = "".join(fila(r, i) for r, i in enumerate(orden[:5], 1))
    resto = "".join(fila(r, i) for r, i in enumerate(orden[5:15], 6))
    mas = (f'<details class="mas" id="la-resto" data-rec><summary><span class="chev" aria-hidden="true"></span>'
           f'Del 6º al 15º · solo para el ponderado</summary>'
           f'<ol class="jug resto" start="6">{resto}</ol>'
           '<p class="note">Del 6º al 15º cada uno acierta ~3,0 %, menos del 3,33 % que pide el pago 30x: '
           'solo entran a 1 ficha en el ponderado, para cobrar más seguido.</p></details>') if resto else ""
    leyenda = ('<div class="leyenda">'
               '<p><i class="a"></i><b>Top-5 escalonado</b> (recomendada): 8 fichas, cobra ~1 de cada 5 '
               '(60 si sale del 1º al 3º, 30 si sale 4º o 5º).</p>'
               '<p><i class="b"></i><b>Top-15 ponderado</b> (alternativa): 23 fichas, cobra ~1 de cada 2 '
               '(+67, +37 o +7).</p></div>')
    return (f'<section class="card jugada" id="sorteo" aria-labelledby="jug-t">{cab}'
            f'<ol class="jug">{COLS_JUGADA}{top5}</ol>{nota_cambio_rd(info_rd)}{mas}'
            f'{html_compartir(f"Lotto Activo {fecha} {hora}", [f"{POS[i]} {ANIM[POS[i]].title()}" for i in orden[:15]])}'
            f'{leyenda}{aviso_modelo}</section>')

def _clase_puesto(p):
    if p is None: return "fuera"
    return "p5" if p <= 5 else "p15" if p <= TOP_N else "fuera"

def resumen_resultados(d, ultimos=48):
    """Línea corta para el desplegable: último puesto y Top-15 reciente."""
    vistos = [r for r in d["registros"] if vigente(r) and r.get("salio") is not None]
    if not vistos:
        return "aún no hay resultados con pronóstico"
    p = puesto_ganador(vistos[-1])
    partes = [f"último: {p}º" if p else "último: sin puesto"]
    puestos = [x for x in (puesto_ganador(r) for r in vistos[-ultimos:]) if x is not None]
    if puestos:
        partes.append(f"Top-5 en {sum(1 for x in puestos if x <= 5)} y Top-15 en "
                      f"{sum(1 for x in puestos if x <= TOP_N)} de los últimos {len(puestos)}")
    return " · ".join(partes)

def html_resultados(d, limite=100):
    """Una sola lista: cada resultado y en qué puesto del Top quedó el ganador.

    Sustituye en la página al histórico en tabla y a «Últimas 48» (que era
    un resumen del mismo dato); el resumen corto va en la línea del desplegable."""
    vistos = [r for r in d["registros"] if vigente(r) and r.get("salio") is not None]
    if not vistos:
        return '<p class="note">Todavía no hay resultados con pronóstico guardado antes del sorteo.</p>'
    cuerpo = ""; dia = None
    for r in reversed(vistos[-limite:]):
        if r["fecha"] != dia:
            dia = r["fecha"]
            cuerpo += f'<tr><th colspan="3" scope="rowgroup">{esc(fecha_corta(dia).capitalize())}</th></tr>'
        s = POS[r["salio"]]
        p = puesto_ganador(r)
        if p:
            tramo = "del Top-5" if p <= 5 else "del Top-15" if p <= TOP_N else "fuera del Top-15"
            badge = f'<span class="puesto {_clase_puesto(p)}" title="{tramo}">{p}º<span class="sr"> {tramo}</span></span>'
        else:
            marca = "Top-3" if r["salio"] in r["top3"] else "fuera del Top-3"
            badge = f'<span class="puesto {"p5" if r["salio"] in r["top3"] else "fuera"}" title="{marca}">{marca}</span>'
        cuerpo += (f'<tr><td class="h">{HORAS[r["hora"]]}</td>'
                   f'<td class="s"><b>{esc(s)}</b>{esc(ANIM[s].title())}</td>'
                   f'<td class="p">{badge}</td></tr>')
    nota = (f'<p class="note">Se muestran los últimos {limite} de {len(vistos)}.</p>'
            if len(vistos) > limite else "")
    clave = ('<p class="clave"><span><span class="puesto p5">1º-5º</span>dentro de la jugada</span>'
             '<span><span class="puesto p15">6º-15º</span>solo ponderado</span>'
             '<span><span class="puesto fuera">16º+</span>fuera del Top-15</span></p>')
    return (f'{clave}<table class="lista"><thead><tr><th scope="col">Hora</th><th scope="col">Salió</th>'
            f'<th scope="col" style="text-align:right">Puesto</th></tr></thead><tbody>{cuerpo}</tbody></table>{nota}'
            '<p class="note">Solo cuentan pronósticos guardados antes de conocer el resultado.</p>')

def sec(id_, titulo, meta, cuerpo, abierto=False):
    """Desplegable de la página (se recuerda abierto/cerrado en el navegador)."""
    return (f'<details class="sec" id="{id_}" data-rec{" open" if abierto else ""}>'
            f'<summary><span class="st"><h2>{titulo}</h2><span class="meta">{meta}</span></span>'
            f'<span class="chev" aria-hidden="true"></span></summary>'
            f'<div class="cuerpo">{cuerpo}</div></details>')

def html_tripleta(e, tri_actual, d, filas, calculando=False, sin_modelo=False, faltan_h=0.0):
    # La ventana que se rotula es la de la tripleta que se muestra, que ya no
    # tiene por qué empezar en el próximo sorteo.
    if tri_actual is not None:
        vf, vh = tri_actual["inicio_fecha"], tri_actual["inicio_hora"]
    else:
        vf, vh = e["pf"], e["ph"]
    ff, fh = fin_ventana(vf, vh)
    cab = (f'<div class="hh"><h2>Tripleta · paga {PAGO_TRIPLETA}x</h2>'
           f'<span>{esc(fecha_corta(vf))} {HORAS[vh]} → {esc(fecha_corta(ff))} {HORAS[fh]}</span></div>')
    # Formulario manual: FALLBACK documentado. Solo se ofrece cuando la vía
    # automática no puede producir la tripleta (modelo caído o cálculo fallido).
    opciones = "".join(f'<option value="{POS[i]}">{POS[i]} · {ANIM[POS[i]].title()}</option>' for i in range(K))
    campos = "".join(
        f'<select name="{nom}" required><option value="">Animal {j}</option>{opciones}</select>'
        for j, nom in enumerate(["a1", "a2", "a3", "b1", "b2", "b3"], 1))
    form_manual = (
        f'<form class="reg" method="post" action="/tripleta/registrar" style="flex-wrap:wrap;gap:6px">'
        f'<input type="hidden" name="pf" value="{esc(e["pf"])}"><input type="hidden" name="ph" value="{e["ph"]}">'
        f'<input type="hidden" name="n" value="{len(filas)}">{campos}'
        '<button type="submit">Guardar tripleta</button></form>')
    # Orden de los casos: si hay una pareja en curso, se muestra SIEMPRE, aunque
    # el modelo esté calculando el próximo sorteo. Esa pareja ya está decidida y
    # jugándose; taparla con un «calculando…» es esconder lo único accionable.
    if sin_modelo and tri_actual is None:
        cuerpo = ('<div class="tip">La tripleta automática necesita el modelo nuevo (numpy/scipy), que ahora no '
                  'está disponible. <b>Fallback manual</b> (la vía normal es la generación automática):</div>'
                  + form_manual)
    elif calculando and tri_actual is None:
        cuerpo = '<div class="tip">Calculando las tripletas para esta ventana…</div>'
    elif tri_actual is None and faltan_h > 0:
        cuando = f"{faltan_h:.0f} h" if faltan_h >= 1 else f"{faltan_h*60:.0f} min"
        cuerpo = (f'<div class="tip">Las 2 tripletas de este ciclo ya cerraron su ventana. La próxima pareja se '
                  f'genera en <b>{cuando}</b>: se emiten 2 cada {TRIPLETA_CADA_H} horas.</div>')
    elif tri_actual is None:
        cuerpo = ('<div class="tip">No se pudo calcular la tripleta automática para esta ventana '
                  '(error del modelo). <b>Fallback manual</b>:</div>' + form_manual)
    else:
        cuerpo = ""
        for k, jug in enumerate(tri_actual["jugadas"], 1):
            cuerpo += (f'<div class="tri"><h3>Tripleta {k}</h3><div class="chips">'
                       + "".join(chip(i) for i in jug) + '</div></div>')
        probs = tri_actual.get("prob")
        if probs:
            cuerpo += ('<p class="note">Probabilidad de que cada uno salga en esos 12 sorteos: '
                       + ", ".join(f"{POS[i]} {p*100:.0f}%" for i, p in zip(sum(tri_actual['jugadas'], []), probs))
                       + ' (un animal cualquiera: ~30%).</p>')
        if faltan_h > 0:
            cuando = f"{faltan_h:.0f} h" if faltan_h >= 1 else f"{faltan_h*60:.0f} min"
            cuerpo += (f'<p class="note">Estas 2 son las de hoy. La próxima pareja se genera en <b>{cuando}</b>: '
                       f'se emiten 2 tripletas cada {TRIPLETA_CADA_H} horas, no una por sorteo.</p>')
    cuerpo += (f'<p class="note">Cada pareja vale para los 12 sorteos que arrancan cuando se generó. Una tripleta al '
               'azar gana ~2,2% de las veces y el umbral de 45x es 2,22%. Aún no está demostrada: juégala en papel y '
               'mira su marcador.</p>')
    # ventanas en curso
    curso = [t for t in d["tripletas"] if vigente(t) and t.get("estado") == "pendiente"
             and t["n_inicio"] < len(filas)][-4:]
    if curso:
        cuerpo += '<div style="margin-top:10px"><div class="hh"><h2>En curso</h2></div>'
        for t in reversed(curso):
            vistos = {filas[j][2] for j in range(t["n_inicio"], len(filas))}
            jugados = len(filas) - t["n_inicio"]
            cuerpo += (f'<div class="pend"><b>{esc(fecha_corta(t["inicio_fecha"]))} {HORAS[t["inicio_hora"]]}</b> · '
                       f'{jugados}/12 sorteos<div class="chips" style="margin-top:5px">'
                       + " ".join('<span style="margin-right:8px">' + "".join(chip(i, "si" if i in vistos else "") for i in jug) + '</span>'
                                  for jug in t["jugadas"]) + '</div></div>')
        cuerpo += '</div>'
    return f'<section class="card" id="tripleta">{cab}{cuerpo}</section>'

def html_marcadores(d):
    m = marcador(d)
    if m["n"] == 0:
        s1 = '<p class="note">Sin predicciones resueltas todavía.</p>'
    else:
        lect = ("evidencia fuerte a favor" if m["factor"] >= 20 else "evidencia moderada a favor" if m["factor"] >= 3
                else "todavía no distingue" if m["factor"] > 1/3 else "evidencia en contra")
        s1 = (f'<div class="kpis"><div class="kpi"><small>Predicciones</small><b>{m["n"]}</b></div>'
              f'<div class="kpi"><small>Top-3</small><b>{num(m["tasa3"])}%</b>'
              f'<span>{plural(m["t3"], "acierto", "aciertos")} · azar 7,9% · modelo 12,3%</span></div>')
        if m.get("n15"):
            s1 += (f'<div class="kpi"><small>Top-5</small><b>{num(m["tasa5"])}%</b>'
                   f'<span>{m["t5"]} de {m["n15"]} · azar 13,2% · modelo 19,5%</span></div>'
                   f'<div class="kpi"><small>Top-15</small><b>{num(m["tasa15"])}%</b>'
                   f'<span>{m["t15"]} de {m["n15"]} · azar 39,5% · equilibrio 50%</span></div>')
        s1 += (f'<div class="kpi"><small>Lectura</small><b style="font-size:14px">{lect}</b>'
               f'<span>factor {num(m["factor"], 2)} : 1</span></div></div>')
        ce = efecto_correcciones(d)
        if ce:
            s1 += (f'<p class="note"><b>Correcciones:</b> {ce["n"]} resultado{"s" if ce["n"] != 1 else ""} se '
                   f'deshizo y se volvió a anotar ({ce["cambiados"]} con un número distinto). Con los números '
                   f'anotados la primera vez el Top-3 sería {ce["t3_orig"]} de {ce["total"]}; ahora es '
                   f'{ce["t3_hoy"]} de {ce["total"]}.</p>')
        if m["n"] < 1000:
            s1 += f'<p class="note">Con {m["n"]} predicciones aún no se puede concluir: hacen falta 1.000 o más.</p>'
    mt = marcador_tripleta(d)
    if mt["n"] == 0:
        s2 = '<p class="note">Ninguna ventana de 12 sorteos cerrada todavía.</p>'
    else:
        s2 = (f'<div class="kpis"><div class="kpi"><small>Ventanas cerradas</small><b>{mt["n"]}</b><span>{mt["jugadas"]} tripletas</span></div>'
              f'<div class="kpi"><small>Aciertos</small><b>{num(mt["tasa"])}%</b>'
              f'<span>{mt["aciertos"]} · azar {num(mt["azar"])}% · umbral 2,22%</span></div>'
              f'<div class="kpi"><small>Resultado a 45x</small><b>{mt["ganancia"]:+d}</b><span>unidades si apostaras 1 por tripleta</span></div></div>')
        if mt["n"] < 300:
            s2 += f'<p class="note">Con {mt["n"]} ventanas es pura suerte: hacen falta varios cientos.</p>'
    return (f'<section class="card" id="marcadores"><div class="grid" style="gap:18px">'
            f'<div><div class="hh"><h2>Marcador sorteo</h2></div>{s1}</div>'
            f'<div><div class="hh"><h2>Marcador tripleta</h2></div>{s2}</div></div>'
            f'{html_economia(d)}'
            f'{html_temperatura(d)}'
            f'<p class="note">Solo cuentan pronósticos guardados antes de conocer el resultado.</p></section>')

def html_economia(d):
    """Plata real: qué habría dejado cada forma de jugar en TU marcador."""
    ec = economia(d)
    if not ec or not ec[0]["n"]:
        return ""
    filas = "".join(
        f'<div class="dist"><span class="dl">{esc(x["nombre"])}</span>'
        f'<span class="dv"><b>{x["neto"]:+,} fichas</b> ({x["roi"]:+.1f}%)'
        f'<small>{x["fichas"]} fichas por sorteo · cobró en {x["aciertos"]} de {x["n"]}</small></span></div>'
        for x in ec)
    c = marcador_cambio_rd(d)
    if c and c["n"]:
        filas += (f'<div class="dist"><span class="dl">Regla de cambio RD (Top-5 escalonado)</span>'
                  f'<span class="dv"><b>{c["dif"]:+,} fichas</b> frente a no cambiar'
                  f'<small>desde {esc(fecha_corta(c["desde"]))}: {c["n"]} sorteos, cambió en {c["cambios"]} · '
                  f'ganó el de RD {c["gano_rd"]}, el 6º que entró {c["gano_6"]}</small></span></div>')
    return ('<div style="margin-top:18px"><div class="hh"><h2>Cada forma de jugar, con plata</h2>'
            f'<span>{ec[0]["n"]} sorteos con orden guardado</span></div>{filas}'
            '<p class="note">Regla de cambio RD: en la prueba (377 cambios) ganó el de RD 6 veces y el 6º 14. '
            'Hacen falta cientos de cambios en vivo para confirmarla.</p>'
            '<p class="note">Lo esperado a largo plazo (prueba ciega, 3.154 sorteos): Top-5 escalonado ≈ +19 % (+10 a +28), '
            'Top-15 ponderado ≈ +6 %, Top-3 ≈ +23 %, Top-15 plano ≈ −1 %. Con menos de ~1.000 sorteos estas cifras bailan mucho por pura suerte.</p></div>')

def html_temperatura(d):
    """Temperatura del Top-15: la racha de fallos en curso, contra lo normal.

    El texto dice siempre las dos cifras: lo que vale la racha por sí sola (que
    es lo que uno siente) y si es normal con los sorteos que llevas (que es lo
    que decide). Sin la segunda, tres fallos seguidos parecen una avería.
    """
    t = temperatura_top15(d)
    if not t:
        return ""
    pts = "".join(f'<span class="pt{" on" if i < t["puntos"] else ""}"></span>'
                  for i in range(5))
    if t["racha"] == 0:
        txt = "El último sorteo puntuable entró en el Top-15. Sin racha de fallos en curso."
    else:
        veces = max(2, round(1 / t["sola"]))
        lectura = {"ok": "es lo normal", "ojo": "empieza a ser raro",
                   "alerta": "ya no cuadra con el modelo"}[t["nivel"]]
        txt = (f'{plural(t["racha"], "fallo seguido", "fallos seguidos")} del Top-15. '
               f'Una racha así, por sí sola, pasa 1 de cada {veces} veces; '
               f'con {t["n"]} sorteos puntuados {lectura}.')
        if t["alerta"] and t["nivel"] != "alerta":
            txt += f' Saltaría la alerta a partir de {t["alerta"]} seguidos.'
    return (f'<div class="temp {t["nivel"]}"><span class="pts">{pts}</span>'
            f'<b>{t["etiqueta"]}</b><span class="txt">{txt}</span></div>')

def html_ultimas(d, filas, cuantos=48):
    """Estado de acierto reciente: sirve para detectar roturas, no para concluir."""
    a = analisis_reciente(d, filas, cuantos)
    cab = (f'<div class="hh"><h2>Últimas {cuantos} · estado de acierto</h2>'
           f'<span>{a["n"]} con pronóstico previo</span></div>')
    if not a["n"]:
        return (f'<section class="card" id="ultimas">{cab}'
                f'<p class="note">Ninguno de los últimos {cuantos} sorteos tenía pronóstico guardado antes '
                'del resultado, así que no hay nada honesto que medir aquí todavía.</p></section>')
    kpis = (f'<div class="kpis"><div class="kpi"><small>Top-3</small><b>{num(a["tasa3"])}%</b>'
            f'<span>{plural(a["t3"], "acierto", "aciertos")} · por azar tocarían {num(a["esp3"])}</span></div>')
    if a.get("n15"):
        kpis += (f'<div class="kpi"><small>Top-5</small><b>{num(a["t5"] / a["n15"] * 100)}%</b>'
                 f'<span>{a["t5"]} de {a["n15"]} · por azar {num(a["n15"] * 5 / K)}</span></div>')
        kpis += (f'<div class="kpi"><small>Top-15</small><b>{num(a["tasa15"])}%</b>'
                 f'<span>{a["t15"]} de {a["n15"]} · por azar {num(a["esp15"])}</span></div>')
    ec = a["eco"]
    kpis += (f'<div class="kpi"><small>Top-5 escalonado</small><b>{ec["neto"]:+,}</b>'
             f'<span>fichas ({ec["roi"]:+.0f}%) con 8 fichas por sorteo</span></div></div>')
    # p-valor: qué tan fácil sería este resultado por pura suerte.
    prob = a["p3"] * 100
    if a["t3"] <= a["esp3"]:
        veredicto = (f'Por debajo de lo que daría el azar ({plural(a["t3"], "acierto", "aciertos")} '
                     f'contra {num(a["esp3"])} esperados). '
                     'Una racha así entra dentro de lo normal, pero si se repite varias ventanas seguidas, '
                     'es señal de que algo cambió.')
    elif prob > 20:
        veredicto = (f'Por encima del azar, pero flojo: una racha así o mejor sale por pura suerte el '
                     f'<b>{prob:.0f}%</b> de las veces. No prueba nada.')
    elif prob > 5:
        veredicto = (f'Por encima del azar: por suerte sola pasaría el <b>{prob:.0f}%</b> de las veces. '
                     'Es una pista, no una prueba.')
    else:
        veredicto = (f'Claramente por encima del azar en esta ventana: por suerte sola pasaría solo el '
                     f'<b>{prob:.1f}%</b> de las veces. Aun así son {a["n"]} sorteos; el marcador largo manda.')
    return (f'<section class="card" id="ultimas">{cab}{kpis}'
            f'<p class="note">Desde {esc(fecha_corta(a["desde"]))}. {veredicto}</p>'
            f'<p class="note">Esta ventana corta existe para <b>ver si algo se rompió</b>, no para decidir. '
            f'Con {a["n"]} sorteos, acertar uno más o uno menos mueve el porcentaje varios puntos.</p></section>')

def html_resumen(e, d, modelo, calculando):
    """Panel 'En palabras claras': qué jugar, cómo vas y qué hacer, sin tecnicismos."""
    partes = []
    if calculando:
        partes.append("<p>⏳ Calculando la jugada del próximo sorteo; aparece en unos segundos.</p>")
    elif modelo != "hazard_actual":
        partes.append("<p>🎯 <b>La jugada</b> está abajo, en «Próximo sorteo»: 5 animales con sus fichas. "
                      "Cuánto vale cada ficha te lo dice «¿Cuánto apuesto?».</p>")
    ec = economia(d)
    if not ec or not ec[0]["n"]:
        partes.append("<p>📊 <b>Cómo vas:</b> todavía no hay pronósticos resueltos.</p>")
    else:
        x = ec[0]
        cara = ("🟢 en positivo, pero con tan pocos sorteos todavía puede ser suerte" if x["neto"] >= 0
                else "🔴 en negativo; con tan pocos sorteos todavía puede ser mala racha")
        partes.append(
            f"<p>📊 <b>Cómo vas:</b> jugando el Top-5 escalonado a 1 ficha llevarías <b>{x['neto']:+,} fichas</b> "
            f"({x['roi']:+.0f}%) en {x['n']} sorteos: {cara}. Lo esperado a largo plazo es ≈ +19%; "
            f"hacen falta ~1.000 sorteos para saberlo.</p>")
    mt = marcador_tripleta(d)
    pend = sum(1 for t in d["tripletas"] if vigente(t) and t.get("estado") == "pendiente")
    if mt["n"] == 0:
        partes.append(f"<p>🎲 <b>Tripleta:</b> ninguna ventana cerrada todavía ({pend} en curso). Sin evidencia de que gane: juégala en papel y mira su marcador.</p>")
    else:
        partes.append(
            f"<p>🎲 <b>Tripleta:</b> {mt['aciertos']} de {mt['jugadas']} ganadoras ({mt['tasa']:.1f}%; necesitas más de 2,22%). "
            f"A 45x habrías sacado <b>{mt['ganancia']:+d}</b> unidades. Con {mt['n']} ventanas cerradas aún es pura suerte.</p>")
    partes.append('<p class="note">Reglas: juega el Top-5 escalonado en TODOS los sorteos · no pases del 5º (del 6º al 15º '
                  "cada animal pierde plata) · no subas el monto cuando el porcentaje se vea alto ni saltes sorteos que se "
                  "ven «fríos» (probado en prueba ciega: no acierta más) · las rachas de fallos no se pueden predecir: se aguantan "
                  "con una ficha pequeña (≤ 3 % de la banca por sorteo).</p>")
    return ('<section class="card" id="resumen"><div class="hh"><h2>En palabras claras</h2>'
            f"<span>{esc(fecha_corta(e['pf']))} · {HORAS[e['ph']]}</span></div>{''.join(partes)}</section>")

def html_historico(d, limite=100):
    vistos = [r for r in d["registros"] if vigente(r) and r.get("salio") is not None]
    filas_h = ""
    for r in reversed(vistos[-limite:]):
        top3 = " ".join(POS[i] for i in r["top3"])
        salio = POS[r["salio"]]
        if r["salio"] == r["top3"][0]: marca, clase = "Top-1", "ok"
        elif r["salio"] in r["top3"]: marca, clase = "Top-3", "ok"
        else: marca, clase = "fallo", "no"
        p = puesto_ganador(r)
        # El puesto solo existe si el orden completo se guardó ANTES del sorteo.
        puesto = (f'<td class="{"ok" if p <= TOP_N else "no"}">{p}º</td>' if p
                  else '<td class="no">—</td>')
        filas_h += (f'<tr><td>{esc(fecha_corta(r["fecha"]))} {HORAS[r["hora"]]}</td><td>{esc(top3)}</td>'
                    f'<td>{esc(salio)}</td>{puesto}<td class="{clase}">{marca}</td></tr>')
    if not filas_h:
        cuerpo = '<p class="note">Sin predicciones resueltas todavía.</p>'
    else:
        nota = (f'<p class="note">Mostrando las últimas {min(limite, len(vistos))} de {len(vistos)}.</p>'
                if len(vistos) > limite else "")
        cuerpo = (f'{nota}<table class="hist"><thead><tr><th>Sorteo</th><th>Top-3</th>'
                  f'<th>Salió</th><th>Puesto</th><th>Resultado</th></tr></thead>'
                  f'<tbody>{filas_h}</tbody></table>')
    return f'<section class="card" id="historico"><div class="hh"><h2>Histórico de predicciones</h2></div>{cuerpo}</section>'

def html_herramientas():
    est = estado_tareas()
    cuerpo = ""
    for k, h in HERRAMIENTAS.items():
        e = est[k]
        corriendo = e["estado"] == "corriendo"
        accion = f"/herramienta/{k}/detener" if corriendo else f"/herramienta/{k}"
        cuerpo += (f'<div class="tool"><div class="tool-h"><div><h3>{esc(h["titulo"])}</h3>'
                   f'<p>{esc(h["que"])} Tarda {esc(h["dura"])}.</p></div>'
                   f'<form method="post" action="{accion}"><span class="st" id="st-{k}">{esc(e["estado"])}</span> '
                   f'<button class="sec" id="bt-{k}" type="submit">{"Detener" if corriendo else "Ejecutar"}</button></form></div>'
                   f'<p class="mirar"><b>Qué mirar:</b> {esc(h["mirar"])}</p>'
                   f'<details{" open" if corriendo else ""}><summary>Ver resultado</summary>'
                   f'<pre id="out-{k}">{esc(e["salida"] or "Todavía no se ha ejecutado.")}</pre></details></div>')
    return (f'<section class="card" id="herramientas"><div class="hh"><h2>Herramientas de validación</h2>'
            f'<span>corren en el servidor (en Railway no gastan tu PC), sin tocar tus datos</span></div>'
            f'{cuerpo}</section>')

def preparar():
    """Congela el pronóstico del próximo sorteo (y la tripleta si toca).

    Lo llaman render() y el hilo pronostico_bucle: así el pronóstico queda
    guardado ANTES del sorteo aunque nadie abra la página. Antes solo se
    guardaba al visitar la web, y los sorteos sin visita quedaban sin puntuar.
    """
    filas = cargar(); e = estado(filas)
    d = log_cargar()
    cambio, _ = resolver_tripletas(d, filas)
    calculando = False; info = {}; aviso_modelo = ""; modelo = "hazard_actual"
    if PRED is not None:
        res = PRED.obtener(HIST, e["pf"], e["ph"])
        if res is None:
            calculando = True
        else:
            p, info = res
            e["sc"] = [float(x) for x in p]
            e["orden"] = sorted(range(K), key=lambda i: (-e["sc"][i], i))
            modelo = modelo_de(info)
            if info.get("frontera_pesos") is not None and not info.get("pesos_vigentes"):
                aviso_modelo = ('<div class="tip">Recalculando en segundo plano los pesos del ensamble '
                                '(1 a 3 min); mientras, se usan los del bloque anterior.</div>')
        if PRED is not None and PRED.error:
            aviso_modelo += f'<div class="msg bad">Último error del modelo: {esc(PRED.error[-300:])}</div>'
    elif PRED_ERR:
        aviso_modelo = f'<div class="tip">Modelo antiguo: no se pudo cargar el ensamble ({esc(PRED_ERR)}).</div>'

    conocido = [e["pf"], e["ph"]] in d["sorteos_conocidos"]
    pend = None
    if not calculando:
        for r in d["registros"]:
            if vigente(r) and not suspendido(r) and r.get("salio") is None:
                if (r["fecha"], r["hora"]) == (e["pf"], e["ph"]) and pend is None:
                    pend = r
                else:
                    r["anulado"] = {"cuando": ahora(), "motivo": "pendiente obsoleto"}; cambio = True
        if pend is None and not conocido:
            pend = {"fecha": e["pf"], "hora": e["ph"], "top3": e["orden"][:3],
                    "orden_completo": list(e["orden"]), "salio": None,
                    "scores": [round(float(x), 6) for x in e["sc"]],
                    "creado": ahora(), "modelo": modelo, **sello(info)}
            if modelo == MODELO_MARCADOR:
                sombra = sombra_de(filas, e["pf"], e["ph"], e["sc"])
                if sombra:
                    pend["sombra"] = sombra
            d["registros"].append(pend); cambio = True
    # Lo que se muestra es SIEMPRE el pronóstico congelado que se puntúa: tras
    # un deshacer o un reinicio el cálculo del momento puede no coincidir.
    if pend is not None:
        if pend.get("scores"):
            e["sc"] = [float(x) for x in pend["scores"]]
        if pend.get("orden_completo"):
            e["orden"] = list(pend["orden_completo"])
        if str(pend.get("modelo", "")).endswith("_sin_pesos"):
            aviso_modelo = ('<div class="msg bad">Este pronóstico se hizo con el ensamble SIN pesos (uniformes): '
                            'no es el modelo medido y NO cuenta en el marcador.</div>' + aviso_modelo)

    tri_actual = None
    for t in d["tripletas"]:
        if vigente(t) and (t["inicio_fecha"], t["inicio_hora"]) == (e["pf"], e["ph"]) and t["n_inicio"] == len(filas):
            tri_actual = t
    # Generación automática: 2 tripletas (un par) cada 24 h, no una por sorteo.
    # El par sale de los 6 animales con mayor probabilidad de aparecer en la
    # ventana, en el momento en que toca generarlo. El ingreso manual queda como
    # fallback (ver html_tripleta), no como sustituto.
    toca, faltan_h = toca_tripleta(d)
    if tri_actual is None and toca and not calculando and not conocido and "tripleta" in info:
        pt = info["tripleta"]
        o = sorted(range(K), key=lambda i: (-pt[i], i))
        tri_actual = {"inicio_fecha": e["pf"], "inicio_hora": e["ph"], "n_inicio": len(filas),
                      "jugadas": [o[0:3], o[3:6]], "prob": [round(float(pt[i]), 4) for i in o[:6]],
                      "estado": "pendiente", "creado": ahora(), "modelo": "tripleta_ventana_A"}
        d["tripletas"].append(tri_actual); cambio = True
        faltan_h = float(TRIPLETA_CADA_H)
        print(f"[tripleta] {ahora()} slot={e['pf']} h{e['ph']} n={len(filas)} "
              f"auto 2 tripletas: {[ [POS[i] for i in jug] for jug in tri_actual['jugadas'] ]}",
              file=sys.stderr, flush=True)
    # Fuera del momento de generar, la tarjeta muestra el par que se está
    # jugando (no un hueco ni el formulario manual).
    tri_mostrada = tri_actual or tripleta_en_curso(d, filas)
    if cambio:
        log_guardar(d)
    return dict(filas=filas, e=e, d=d, calculando=calculando, aviso_modelo=aviso_modelo,
                modelo=modelo, pend=pend, tri_mostrada=tri_mostrada, faltan_h=faltan_h)


def html_rd():
    """Fragmento de la pestaña RD Internacional. Si el módulo falla, la
    pestaña lo dice y Lotto Activo sigue funcionando."""
    try:
        import rdint_vivo
        return rdint_vivo.html()
    except Exception as ex:  # noqa: BLE001
        print(f"[rdint] {ahora()} html: {ex!r}", file=sys.stderr, flush=True)
        return '<div class="card"><p>RD Internacional se está preparando…</p></div>'


def render(banca=None, tab="la"):
    x = preparar()
    filas, e, d = x["filas"], x["e"], x["d"]
    calculando, aviso_modelo, modelo = x["calculando"], x["aviso_modelo"], x["modelo"]
    pend = x["pend"]
    tab = "rd" if tab == "rd" else "la"

    aviso = ""
    if AVISO["texto"]:
        aviso = f'<div class="msg {AVISO["clase"]}" role="status">{AVISO["texto"]}</div>'
        AVISO["texto"] = ""

    n_mesa = sum(1 for r in d["registros"] if vigente(r))
    panel_la = (
        f'{aviso}<div class="duo">{html_jugada(e, calculando, pend, aviso_modelo, modelo)}'
        f'{html_registro(e)}</div>'
        + sec("sec-mesa", "Historial de cuadrantes",
              f"los 38 animales por cuadrante, puesto o días sin salir · "
              f"{format(n_mesa, ',').replace(',', '.')} sorteos guardados",
              html_mesa())
        + sec("historico", "Resultados y puestos en el Top", esc(resumen_resultados(d)), html_resultados(d)))

    def pestana(clave, nombre, sub):
        on = clave == tab
        return (f'<a role="tab" id="t-{clave}" data-tab="{clave}" href="/?tab={clave}" aria-controls="p-{clave}" '
                f'aria-selected="{"true" if on else "false"}" tabindex="{0 if on else -1}">'
                f'<b>{nombre}</b><small>{sub}</small></a>')
    cab = ('<header class="cab"><div class="cab-in"><div class="marca">Lotto Activo<small>pronóstico y registro</small></div>'
           '<nav class="tabs" role="tablist" aria-label="Lotería">'
           + pestana("la", "Lotto Activo", f"próximo {HORAS[e['ph']]}")
           + pestana("rd", "RD Internacional", "sorteos a las y media")
           + '</nav></div></header>')
    cuerpo = (
        f'{cab}<main class="w"><h1 class="sr">Lotto Activo</h1>'
        f'<section class="panel" id="p-la" role="tabpanel" aria-labelledby="t-la"{"" if tab == "la" else " hidden"}>'
        f'{panel_la}</section>'
        f'<section class="panel" id="p-rd" role="tabpanel" aria-labelledby="t-rd"{"" if tab == "rd" else " hidden"}>'
        f'{html_rd()}</section>'
        '<footer>Es un juego de azar: ningún modelo garantiza ganar. Juega solo lo que puedas perder.</footer></main>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="theme-color" content="#f4f2ed" media="(prefers-color-scheme: light)">'
            '<meta name="theme-color" content="#131419" media="(prefers-color-scheme: dark)">'
            '<link rel="icon" href="data:,">'
            f'<title>Lotto Activo</title><style>{CSS}</style></head><body>{cuerpo}'
            f'{JS.replace("%CALC%", "true" if calculando else "false")}</body></html>')

# ------------------------------------------------------------------ servidor
def registrar(num):
    filas = cargar(); e = estado(filas)
    d = log_cargar(); estado_txt = "sin pronóstico previo, no cuenta"; clase = "no"
    # Cerrar el hueco del sorteo sin pronóstico: si aún no hay «pend» para este
    # slot pero la predicción ya estaba en caché (calculada en un render previo
    # a que saliera el resultado), se registra ahora: el pronóstico es anterior
    # al resultado, sigue siendo honesto. Si no hay caché, no hubo pronóstico.
    pend = None
    for r in d["registros"]:
        if (vigente(r) and not suspendido(r) and r.get("salio") is None
                and r["fecha"] == e["pf"] and r["hora"] == e["ph"]):
            pend = r
            break
    if pend is None and PRED is not None and [e["pf"], e["ph"]] not in d["sorteos_conocidos"]:
        res = PRED.obtener(HIST, e["pf"], e["ph"])
        if res is not None:
            p, info = res
            sc = [float(x) for x in p]
            orden = sorted(range(K), key=lambda i: (-sc[i], i))
            pend = {"fecha": e["pf"], "hora": e["ph"], "top3": orden[:3],
                    "orden_completo": orden, "salio": None,
                    "scores": [round(float(x), 6) for x in sc],
                    "creado": ahora(), "modelo": modelo_de(info), **sello(info)}
            d["registros"].append(pend)
    if pend is not None:
        pend["salio"] = IDX[num]; pend["resuelto"] = ahora()
        if IDX[num] == pend["top3"][0]: estado_txt, clase = "¡ACIERTO Top-1!", "ok"
        elif IDX[num] in pend["top3"]: estado_txt, clase = "acierto Top-3", "ok"
        else: estado_txt = "fallo"
    try:
        with open(HIST, "a", encoding="utf-8") as fh:
            fh.write(f"{e['pf']} {e['ph']} {num}\n")
    except OSError as ex:
        log_guardar(d)
        return (f"ERROR al guardar en el volumen: {ex}. NO se registró el resultado; "
                f"reintenta. Si persiste, el contenedor está sin escritura.", "bad")
    reanudar_suspendidos(d)
    _, cerradas = resolver_tripletas(d, cargar())
    log_guardar(d)
    texto = f'{HORAS[e["ph"]]} → <b>{num} {ANIM[num].title()}</b> · {estado_txt}'
    for t in cerradas:
        gan = sum(t["aciertos"])
        texto += (f'<br>Tripleta de {esc(fecha_corta(t["inicio_fecha"]))} {HORAS[t["inicio_hora"]]} cerrada: '
                  + (f"<b>¡{gan} ganadora{'s' if gan > 1 else ''}!</b>" if gan else "sin acierto"))
        if gan: clase = "ok"
    return texto, clase

def registrar_tripleta(pf, ph, n, codigos):
    filas = cargar(); e = estado(filas)
    if (pf, ph) != (e["pf"], e["ph"]) or n != len(filas):
        return "La ventana cambió, actualiza la página e inténtalo de nuevo.", "bad"
    for c in codigos:
        if c not in IDX:
            return f'«{c or "vacío"}» no es un animal válido.', "bad"
    if len(set(codigos)) != 6:
        return "Los 6 animales deben ser distintos.", "bad"
    d = log_cargar()
    for t in d["tripletas"]:
        if vigente(t) and (t["inicio_fecha"], t["inicio_hora"]) == (pf, ph) and t["n_inicio"] == n:
            return "Ya hay una tripleta guardada para esta ventana.", "bad"
    o = [IDX[c] for c in codigos]
    d["tripletas"].append({"inicio_fecha": pf, "inicio_hora": ph, "n_inicio": n,
                            "jugadas": [o[0:3], o[3:6]], "estado": "pendiente",
                            "creado": ahora(), "modelo": "manual"})
    log_guardar(d)
    return "Tripleta guardada.", "ok"


# ============================================================ mesa de probabilidades
# Bloque ADITIVO (solo lectura sobre la lógica existente). No toca predicción,
# scoring, registro, tripletas ni marcador: lee lo que el pipeline ya calculó y
# lo muestra completo (38 animales) en vez de solo el top-3/top-15.

# Cuadrantes de membresía FIJA (no dependen de la probabilidad).
# El "00" no tiene decena propia: se agrupa con Q4 (30-36) por convención
# documentada, para que los 4 cuadrantes cubran los 38 códigos sin solapes.
MESA_CUADRANTES = [
    ("Q1", "0-9", [IDX[c] for c in ["0"] + [str(i) for i in range(1, 10)]]),
    ("Q2", "10-19", [IDX[str(i)] for i in range(10, 20)]),
    ("Q3", "20-29", [IDX[str(i)] for i in range(20, 30)]),
    ("Q4", "30-36 + 00", [IDX[str(i)] for i in range(30, 37)] + [IDX["00"]]),
]
# Segmentos de rank (de 8 en 8; el último queda de 6 porque K=38).
MESA_SEG_RANK = [(1, 8), (9, 16), (17, 24), (25, 32), (33, 38)]
# Bins de hueco en DÍAS sin salir. "hoy" = ya salió en esta misma jornada.
MESA_BINS_HUECO = [(0, 0, "hoy"), (1, 1, "1 día"), (2, 2, "2 días"), (3, 5, "3-5 días"),
                   (6, 10, "6-10 días"), (11, 20, "11-20 días"), (21, 40, "21-40 días"),
                   (41, 10**9, "más de 40 días")]

def mesa_seg_rank(rk):
    for j, (a, b) in enumerate(MESA_SEG_RANK):
        if a <= rk <= b: return j
    return len(MESA_SEG_RANK) - 1

def mesa_bin_hueco(g):
    """g = días sin salir; None (nunca salió) cae en el último bin."""
    if g is None: return len(MESA_BINS_HUECO) - 1
    for j, (a, b, _) in enumerate(MESA_BINS_HUECO):
        if a <= g <= b: return j
    return len(MESA_BINS_HUECO) - 1

def mesa_huecos(filas, fecha, hora):
    """Días sin salir por animal ANTES del slot (fecha,hora). None = nunca salió.
    Usa solo sorteos estrictamente anteriores: no mira el resultado del slot."""
    ult = {}
    for f, h, v in filas:
        if (f, h) >= (fecha, hora): break
        ult[v] = f
    base = date.fromisoformat(fecha)
    return [(base - date.fromisoformat(ult[i])).days if i in ult else None for i in range(K)]

def mesa_slots_hist(d, actual):
    """Registros navegables (sin el slot actual), del más reciente al más antiguo."""
    h = [r for r in d["registros"] if vigente(r) and (r["fecha"], r["hora"]) != actual]
    h.sort(key=lambda r: (r["fecha"], r["hora"]), reverse=True)
    return h

def mesa_datos(offset=0):
    """Distribución completa del slot en offset (0 = actual). Solo lectura."""
    filas = cargar(); e = estado(filas); d = log_cargar()
    actual = (e["pf"], e["ph"])
    hist = mesa_slots_hist(d, actual)
    total = 1 + len(hist)
    try: offset = int(offset)
    except (TypeError, ValueError): offset = 0
    offset = max(0, min(offset, total - 1))

    if offset == 0:
        fecha, hora = actual
        winner = None
        pend = next((r for r in d["registros"]
                     if vigente(r) and (r["fecha"], r["hora"]) == actual), None)
        modelo = (pend or {}).get("modelo", "—")
        scores = (pend or {}).get("scores")
        orden = (pend or {}).get("orden_completo")
        top3 = (pend or {}).get("top3") or []
        if scores is None and PRED is not None:
            res = PRED.obtener(HIST, fecha, hora)   # mismo cálculo (cacheado) que render()
            if res is not None:
                p, _i = res
                scores = [float(x) for x in p]
                if modelo == "—": modelo = prediccion.MODELO_ENSAMBLE
        if scores is None and orden is None:
            scores = list(e["sc"])
            if modelo == "—": modelo = "hazard_actual"
    else:
        r = hist[offset - 1]
        fecha, hora = r["fecha"], r["hora"]
        winner = r.get("salio")
        modelo = r.get("modelo", "—")
        scores = r.get("scores")
        orden = r.get("orden_completo")
        top3 = r.get("top3") or []

    if orden is None and scores is not None:
        orden = sorted(range(K), key=lambda i: (-scores[i], i))
    rank = {}
    if orden:
        for pos, i in enumerate(orden, 1): rank[i] = pos

    gaps = mesa_huecos(filas, fecha, hora)
    probs = None
    if scores is not None:
        tot = sum(scores) or 1.0
        probs = [s / tot for s in scores]

    animales = []
    for i in range(K):
        rk = rank.get(i)
        animales.append({
            "idx": i, "num": POS[i], "nombre": ANIM[POS[i]].title(),
            "prob": (probs[i] if probs else None),
            "rank": rk,
            "gap_dias": gaps[i],
            "salio_hoy": gaps[i] == 0,
            "en_top15": (rk <= 15) if rk is not None else (i in top3),
            "es_top3": i in top3,
        })
    if scores is None and not orden:
        vista = "top3"       # registro viejo: solo se guardó el top-3
    elif probs is None:
        vista = "rank"       # registro viejo: orden completo, sin puntajes
    else:
        vista = "prob"
    return {
        "offset": offset, "total": total, "fecha": fecha, "hora": hora,
        "hora_txt": HORAS[hora], "fecha_txt": fecha_corta(fecha),
        "modelo": modelo, "vista": vista,
        "winner": winner,
        "winner_num": (POS[winner] if winner is not None else None),
        "winner_nombre": (ANIM[POS[winner]].title() if winner is not None else None),
        "winner_rank": (rank.get(winner) if winner is not None else None),
        "animales": animales,
        "cuadrantes": [{"clave": c, "etiqueta": et, "idx": ix} for c, et, ix in MESA_CUADRANTES],
        "seg_rank": [{"desde": a, "hasta": b} for a, b in MESA_SEG_RANK],
        "bins_hueco": [{"desde": a, "hasta": b, "etiqueta": t} for a, b, t in MESA_BINS_HUECO],
    }

def mesa_stats():
    """Dónde cayó el ganador, sobre TODOS los registros resueltos. Solo lectura.
    Muestra en vivo y pequeña: NO es validación (para eso, walk-forward en desarrollo)."""
    filas = cargar(); d = log_cargar()
    res = [r for r in d["registros"] if vigente(r) and r.get("salio") is not None]
    quiero = {(r["fecha"], r["hora"]) for r in res}
    snap = {}; ult = {}
    for f, h, v in filas:
        if (f, h) in quiero and (f, h) not in snap:
            base = date.fromisoformat(f)
            snap[(f, h)] = [(base - date.fromisoformat(ult[i])).days if i in ult else None
                            for i in range(K)]
        ult[v] = f

    nr = len(MESA_SEG_RANK); nh = len(MESA_BINS_HUECO)
    rank_n = 0; rank_seg = [0] * nr
    hue_n = 0; hue_seg = [0] * nh; hue_ocup = [0.0] * nh
    sin_orden = 0; sin_hist = 0
    for r in res:
        o = r.get("orden_completo")
        if o and r["salio"] in o:
            rank_seg[mesa_seg_rank(o.index(r["salio"]) + 1)] += 1; rank_n += 1
        else:
            sin_orden += 1
        g = snap.get((r["fecha"], r["hora"]))
        if g is None:
            sin_hist += 1; continue
        hue_seg[mesa_bin_hueco(g[r["salio"]])] += 1; hue_n += 1
        for i in range(K): hue_ocup[mesa_bin_hueco(g[i])] += 1

    return {
        "resueltos": len(res), "sin_orden_completo": sin_orden, "sin_historial": sin_hist,
        "rank": {"n": rank_n,
                 "segmentos": [{"etiqueta": "%d-%d" % (a, b), "n": rank_seg[j],
                                "pct": (rank_seg[j] / rank_n * 100 if rank_n else None),
                                "esperado": (b - a + 1) / K * 100}
                               for j, (a, b) in enumerate(MESA_SEG_RANK)]},
        "hueco": {"n": hue_n,
                  "segmentos": [{"etiqueta": MESA_BINS_HUECO[j][2], "n": hue_seg[j],
                                 "pct": (hue_seg[j] / hue_n * 100 if hue_n else None),
                                 "esperado": (hue_ocup[j] / (hue_n * K) * 100 if hue_n else None)}
                                for j in range(nh)]},
    }

def _api(fn, *args):
    """Envoltorio de las rutas /api/: nunca deja que un fallo de la mesa
    (funcion puramente de lectura) tumbe el servidor ni la pagina."""
    try:
        return fn(*args)
    except Exception as ex:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {"error": "%s: %s" % (type(ex).__name__, ex)}

def html_mesa():
    return (
        '<div id="mesa">'
        '<p class="mesa-slot" id="mesa-slot" aria-live="polite">cargando…</p>'
        '<div class="mesa-bar">'
        '<div class="mesa-nav"><button type="button" class="sec" id="mesa-prev" aria-label="Sorteo anterior">'
        '<span class="flecha izq" aria-hidden="true"></span></button>'
        '<span id="mesa-pos" class="mesa-pos"></span>'
        '<button type="button" class="sec" id="mesa-next" aria-label="Sorteo siguiente">'
        '<span class="flecha der" aria-hidden="true"></span></button></div>'
        '<div class="mesa-modos" role="group" aria-label="Agrupar por">'
        '<button type="button" class="sec on" aria-pressed="true" data-modo="rango">Cuadrantes</button>'
        '<button type="button" class="sec" aria-pressed="false" data-modo="rank">Puesto</button>'
        '<button type="button" class="sec" aria-pressed="false" data-modo="hueco">Días sin salir</button>'
        '</div></div>'
        '<div id="mesa-aviso"></div>'
        '<div id="mesa-cuerpo" class="mesa-cuerpo"></div>'
        '<details class="mas" id="mesa-dist" data-rec><summary><span class="chev" aria-hidden="true"></span>'
        'Dónde cayó el ganador (muestra en vivo)</summary>'
        '<div id="mesa-stats" class="mesa-stats">cargando…</div>'
        '<p class="tip"><b>Muestra en vivo, n pequeño: esto NO es validación.</b> Es un termómetro '
        'de lo que pasa ahora, no evidencia. Cualquier cambio de apuesta necesita validación '
        'walk-forward en desarrollo.</p>'
        '</details>'
        '<p class="note">La mesa no mejora la predicción: muestra completa la distribución que el '
        'modelo ya calculaba. Solo lectura.</p>'
        '</div>')

CSS_MESA = """
.mesa-slot{margin:0 0 12px;font-size:14px;color:var(--muted)}
.mesa-slot b{color:var(--ink)}
.mesa-bar{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px;margin-bottom:12px}
.mesa-nav{display:flex;align-items:center;gap:8px}
.mesa-nav button{width:44px;padding:0;display:inline-grid;place-items:center}
.mesa-nav button[disabled]{opacity:.35;cursor:default}
.mesa-pos{font-size:12.5px;color:var(--muted);font-variant-numeric:tabular-nums;min-width:9ch;text-align:center}
.flecha{width:9px;height:9px;border-left:2px solid currentColor;border-bottom:2px solid currentColor}
.flecha.izq{transform:translateX(2px) rotate(45deg)}.flecha.der{transform:translateX(-2px) rotate(-135deg)}
.mesa-modos{display:flex;gap:4px;flex-wrap:wrap;padding:3px;background:var(--bg-2);border-radius:10px}
.mesa-modos button{flex:1 1 auto;min-height:38px;padding:6px 10px;font-size:13px;font-weight:600;background:transparent;border-color:transparent;color:var(--muted)}
.mesa-modos button.on{background:var(--card);color:var(--ink);border-color:var(--line);box-shadow:var(--sh1)}
#mesa details.mas{margin-top:14px}
.mesa-cuerpo{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media (max-width:820px){.mesa-cuerpo{grid-template-columns:1fr}}
.mseg{border:1px solid var(--line);border-radius:9px;padding:10px 12px}
.mseg h4{margin:0 0 3px;font-size:13px;font-weight:600}
.mseg .masa{font-size:12px;color:var(--muted);margin:0 0 8px;font-variant-numeric:tabular-nums}
.mrow{display:grid;grid-template-columns:38px 1fr 46px;align-items:center;gap:8px;padding:3px 0;font-size:13px}
.mrow .mn{font-weight:700;color:var(--brand);font-variant-numeric:tabular-nums;font-size:15px}
.mrow .mb{height:15px;background:var(--pista);border-radius:4px;position:relative;overflow:hidden}
.mrow .mb i{display:block;height:100%;border-radius:4px;min-width:1px;background:var(--soft)}
.mrow .mb span{position:absolute;left:6px;top:0;line-height:15px;font-size:11px;color:var(--ink);white-space:nowrap}
.mrow .mp{text-align:right;font-variant-numeric:tabular-nums;color:var(--soft);font-size:11px}
.mrow.t15 .mb i{background:var(--brand)}
.mrow.gana{background:var(--ok-soft);border-radius:5px}
.mrow.gana .mn{color:var(--ok)}
.mrow.gana .mb i{background:var(--ok)}
.mrow .tag{font-style:normal;color:var(--soft);font-size:10px;margin-left:4px}
.mesa-stats table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
.mesa-stats th{text-align:left;color:var(--muted);font-weight:600;padding:5px 7px;border-bottom:1px solid var(--line)}
.mesa-stats td{padding:5px 7px;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}
.mesa-stats h4{margin:14px 0 0;font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
"""

JS_MESA = """
<script>
(function(){
  var off = 0, modo = 'rango', datos = null;
  var cuerpo = document.getElementById('mesa-cuerpo');
  if(!cuerpo) return;
  var slotEl = document.getElementById('mesa-slot'), posEl = document.getElementById('mesa-pos');
  var avisoEl = document.getElementById('mesa-aviso');
  var prev = document.getElementById('mesa-prev'), next = document.getElementById('mesa-next');

  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function pct(x){ return (x*100).toFixed(2)+'%'; }

  function fila(a, maxp){
    var cls = 'mrow' + (a.en_top15 ? ' t15' : '') +
              (datos.winner !== null && a.idx === datos.winner ? ' gana' : '');
    var ancho = (a.prob !== null && maxp > 0) ? Math.max(1, a.prob/maxp*100) : 0;
    var dentro = a.prob !== null ? pct(a.prob) : (a.rank !== null ? 'rank ' + a.rank : '\\u2014');
    var gap = a.gap_dias === null ? 'nunca' : (a.gap_dias === 0 ? 'hoy' : a.gap_dias + 'd');
    return '<div class="' + cls + '"><span class="mn">' + esc(a.num) + '</span>' +
      '<span class="mb"><i style="width:' + ancho.toFixed(1) + '%"></i><span>' + dentro +
      ' <em class="tag">' + esc(a.nombre) + '</em></span></span>' +
      '<span class="mp">' + gap + '</span></div>';
  }

  function bloque(titulo, sub, lista, maxp){
    var masa = 0, hay = false;
    lista.forEach(function(a){ if(a.prob !== null){ masa += a.prob; hay = true; } });
    var orden = lista.slice().sort(function(x, y){
      if(x.prob !== null && y.prob !== null) return y.prob - x.prob;
      if(x.rank !== null && y.rank !== null) return x.rank - y.rank;
      return x.idx - y.idx;
    });
    var cab = hay ? ('masa ' + pct(masa) + ' \\u00b7 ' + orden.length + ' animales')
                  : (orden.length + ' animales');
    return '<div class="mseg"><h4>' + esc(titulo) + (sub ? ' <em class="tag">' + esc(sub) +
      '</em>' : '') + '</h4><p class="masa">' + cab + '</p>' +
      orden.map(function(a){ return fila(a, maxp); }).join('') + '</div>';
  }

  function pinta(){
    if(!datos) return;
    var A = datos.animales, maxp = 0;
    A.forEach(function(a){ if(a.prob !== null && a.prob > maxp) maxp = a.prob; });
    var out = '';
    if(modo === 'rango'){
      datos.cuadrantes.forEach(function(q){
        out += bloque(q.clave, q.etiqueta, q.idx.map(function(i){ return A[i]; }), maxp);
      });
    } else if(modo === 'rank'){
      datos.seg_rank.forEach(function(s){
        var l = A.filter(function(a){ return a.rank !== null && a.rank >= s.desde && a.rank <= s.hasta; });
        if(l.length) out += bloque('Ranks ' + s.desde + '-' + s.hasta, '', l, maxp);
      });
      var sinr = A.filter(function(a){ return a.rank === null; });
      if(sinr.length) out += bloque('Sin rank guardado', '', sinr, maxp);
    } else {
      datos.bins_hueco.forEach(function(b){
        var l = A.filter(function(a){
          var g = a.gap_dias === null ? 99999 : a.gap_dias;
          return g >= b.desde && g <= b.hasta;
        });
        if(l.length) out += bloque(b.etiqueta, '', l, maxp);
      });
    }
    cuerpo.innerHTML = out || '<p class="note">Sin datos para este modo.</p>';
  }

  function carga(){
    fetch('/api/mesa?offset=' + off).then(function(r){ return r.json(); }).then(function(j){
      if(j.error){ cuerpo.innerHTML = '<p class="note">' + esc(j.error) + '</p>'; return; }
      datos = j; off = j.offset;
      var gan = j.winner !== null
        ? ' \\u00b7 sali\\u00f3 <b>' + esc(j.winner_num) + ' ' + esc(j.winner_nombre) + '</b>' +
          (j.winner_rank ? ' (rank ' + j.winner_rank + ')' : '')
        : ' \\u00b7 pendiente';
      slotEl.innerHTML = esc(j.fecha_txt) + ' ' + esc(j.hora_txt) + gan;
      posEl.textContent = (j.offset === 0 ? 'slot actual' : 'hace ' + j.offset) +
                          ' \\u00b7 ' + (j.offset + 1) + '/' + j.total;
      prev.disabled = (j.offset >= j.total - 1);
      next.disabled = (j.offset <= 0);
      avisoEl.innerHTML = j.vista === 'prob' ? '' :
        '<div class="tip">' + (j.vista === 'rank'
          ? 'Registro antiguo: se guard\\u00f3 el orden completo pero no los puntajes. Vista <b>solo rank</b>, sin barras de probabilidad.'
          : 'Registro antiguo: solo se guard\\u00f3 el Top-3. No hay ranks ni puntajes para los 38.') +
        '</div>';
      pinta();
    }).catch(function(){ cuerpo.innerHTML = '<p class="note">No se pudo cargar la mesa.</p>'; });
  }

  prev.onclick = function(){ off += 1; carga(); };
  next.onclick = function(){ if(off > 0){ off -= 1; carga(); } };
  Array.prototype.forEach.call(document.querySelectorAll('.mesa-modos button'), function(b){
    b.onclick = function(){
      Array.prototype.forEach.call(document.querySelectorAll('.mesa-modos button'), function(x){
        x.classList.remove('on'); x.setAttribute('aria-pressed', 'false'); });
      b.classList.add('on'); b.setAttribute('aria-pressed', 'true'); modo = b.getAttribute('data-modo'); pinta();
    };
  });

  function tabla(t, titulo, nota){
    var h = '<h4>' + titulo + '</h4><p class="note">' + nota + ' \\u00b7 n = ' + t.n + '</p>' +
      '<table><tr><th>segmento</th><th>ganadores</th><th>%</th><th>esperado</th></tr>';
    t.segmentos.forEach(function(s){
      h += '<tr><td>' + esc(s.etiqueta) + '</td><td>' + s.n + '</td><td>' +
           (s.pct === null ? '\\u2014' : s.pct.toFixed(1) + '%') + '</td><td>' +
           (s.esperado === null ? '\\u2014' : s.esperado.toFixed(1) + '%') + '</td></tr>';
    });
    return h + '</table>';
  }
  fetch('/api/mesa_stats').then(function(r){ return r.json(); }).then(function(j){
    var el = document.getElementById('mesa-stats');
    el.innerHTML =
      tabla(j.rank, 'Por segmento de rank', 'solo registros con orden completo guardado') +
      tabla(j.hueco, 'Por bin de hueco', 'esperado = ocupaci\\u00f3n media del bin bajo azar') +
      '<p class="note">' + j.resueltos + ' sorteos resueltos \\u00b7 ' + j.sin_orden_completo +
      ' sin orden completo \\u00b7 ' + j.sin_historial + ' sin fila en el historial.</p>';
  }).catch(function(){});

  carga();
})();
</script>
"""

CSS = CSS + CSS_MESA
JS_COMPARTIR = r"""
<script>
document.addEventListener('click', function(ev){
  var b = ev.target.closest('.compartir button'); if(!b) return;
  var c = b.parentNode, n = +c.querySelector('select').value;
  var m = parseFloat(c.querySelector('input').value.replace(',', '.')) || 0;
  var a = c.dataset.a.split('|').slice(0, n);
  var t = c.dataset.t + ' - Top ' + n + (m ? ' - $' + m + ' por animal' : '') + '\n'
        + a.map(function(x, k){ return (k + 1) + '. ' + x + (m ? ' - $' + m : ''); }).join('\n')
        + (m ? '\nTotal: $' + (m * a.length) : '');
  if(navigator.share) navigator.share({text: t}).catch(function(){});
  else navigator.clipboard.writeText(t).then(function(){ b.textContent = 'Copiado'; setTimeout(function(){ b.textContent = 'Compartir'; }, 1500); });
});
</script>
"""

JS = JS + JS_MESA + JS_COMPARTIR

class H(BaseHTTPRequestHandler):
    def _send(self, cuerpo, tipo="text/html; charset=utf-8", codigo=200):
        b = cuerpo.encode("utf-8")
        try:
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers(); self.wfile.write(b)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, OSError):
            pass

    def _volver(self, ancla=""):
        try:
            self.send_response(303); self.send_header("Location", "/" + ancla); self.end_headers()
        except OSError:
            pass

    # CERROJO: el hilo del anotado automático puede estar escribiendo justo
    # ahora. Serializar aquí evita que un render y una anotación se pisen.
    def do_GET(self):
        with CERROJO:
            self._get()

    def do_POST(self):
        with CERROJO:
            self._post()

    def _get(self):
        ruta = self.path.split("?")[0]
        if ruta in ("/", "/index.html"):
            q = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            try:
                banca = float(q.get("banca", [""])[0].replace(",", "."))
                banca = banca if 0 < banca < 1e9 else None
            except ValueError:
                banca = None
            tab = (q.get("tab", ["la"])[0] or "la").strip().lower()
            self._send(render(banca, tab))
        elif ruta == "/tareas.json":
            est = estado_tareas()
            est["_auto"] = auto_estado()
            self._send(json.dumps(est, ensure_ascii=False), "application/json; charset=utf-8")
        elif ruta == "/listo.json":
            listo = True
            if PRED is not None:
                filas = cargar(); e = estado(filas)
                listo = PRED.obtener(HIST, e["pf"], e["ph"]) is not None
            self._send(json.dumps({"listo": listo}), "application/json")
        elif ruta == "/api/mesa":
            q = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            self._send(json.dumps(_api(mesa_datos, q.get("offset", ["0"])[0]),
                                  ensure_ascii=False), "application/json; charset=utf-8")
        elif ruta == "/api/rdint":
            try:
                import rdint_vivo
                cuerpo = rdint_vivo.api()
            except Exception as ex:  # noqa: BLE001
                cuerpo = {"error": f"{type(ex).__name__}: {ex}"}
            self._send(json.dumps(cuerpo, ensure_ascii=False), "application/json; charset=utf-8")
        elif ruta == "/api/cambio_rd":
            self._send(json.dumps(_api(lambda: marcador_cambio_rd(log_cargar())), ensure_ascii=False),
                       "application/json; charset=utf-8")
        elif ruta == "/api/sombra":
            self._send(json.dumps(_api(lambda: marcador_sombra(log_cargar())), ensure_ascii=False),
                       "application/json; charset=utf-8")
        elif ruta == "/api/mesa_stats":
            self._send(json.dumps(_api(mesa_stats), ensure_ascii=False),
                       "application/json; charset=utf-8")
        else:
            self._send("No encontrado", "text/plain; charset=utf-8", 404)

    def _post(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        datos = self.rfile.read(n).decode("utf-8") if n else ""
        ruta = self.path.split("?")[0]
        if ruta == "/auto":
            # En segundo plano: consultar la fuente puede tardar varios segundos
            # y la página debe volver enseguida.
            if AUTO["corriendo"]:
                AVISO.update(texto="Ya se está buscando el resultado.", clase="no")
            else:
                threading.Thread(target=auto_pasada, daemon=True).start()
                AVISO.update(texto="Buscando el resultado en la fuente…", clase="no")
            return self._volver("#registrar")
        if ruta == "/deshacer":
            texto, ok = deshacer()
            AVISO.update(texto=esc(texto), clase="ok" if ok else "no")
            return self._volver("#registrar")
        if ruta in ("/registrar", "/"):
            num = (parse_qs(datos).get("num", [""])[0]).strip()
            if num not in IDX:
                AVISO.update(texto=f'«{esc(num) or "vacío"}» no es válido. Usa 0, 00 o 1–36.', clase="bad")
            else:
                texto, clase = registrar(num)
                AVISO.update(texto=texto, clase=clase)
            return self._volver()
        if ruta == "/tripleta/registrar":
            q = parse_qs(datos)
            pf = (q.get("pf", [""])[0]).strip()
            try: ph = int(q.get("ph", [""])[0])
            except ValueError: ph = -1
            try: n = int(q.get("n", [""])[0])
            except ValueError: n = -1
            codigos = [(q.get(k, [""])[0]).strip() for k in ("a1", "a2", "a3", "b1", "b2", "b3")]
            texto, clase = registrar_tripleta(pf, ph, n, codigos)
            AVISO.update(texto=esc(texto), clase=clase)
            return self._volver("#tripleta")
        if ruta.startswith("/herramienta/"):
            partes = ruta.strip("/").split("/")
            if len(partes) == 3 and partes[2] == "detener":
                detener_tarea(partes[1])
            elif len(partes) == 2:
                iniciar_tarea(partes[1])
            return self._volver("#herramientas")
        self._send("No encontrado", "text/plain; charset=utf-8", 404)

    def log_message(self, fmt, *a):
        # Silenciado antes: el servidor corría sordo y un traceback en
        # /registrar o en el recálculo de pesos dejaba rastro solo en la
        # consola. Railway captura stderr: ahora queda en los logs.
        sys.stderr.write("%s %s\n" % (datetime.now().isoformat(timespec="seconds"),
                                       fmt % a if a else fmt))

if __name__ == "__main__":
    if DATOS != RUTA and not os.path.exists(HIST):
        # Volumen recién creado (vacío): lo sembramos una vez con los datos del repo.
        import shutil
        for nombre in ("historial.txt", "predicciones.json", "pesos_ensamble.json"):
            origen = os.path.join(RUTA, nombre)
            if os.path.exists(origen):
                shutil.copy2(origen, os.path.join(DATOS, nombre))
    if not os.path.exists(HIST):
        sys.exit("Falta historial.txt en esta carpeta.")
    PUERTO = int(os.environ.get("PORT", PUERTO))
    EN_NUBE = bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT"))
    HOST = "0.0.0.0" if EN_NUBE else "127.0.0.1"
    url = f"http://localhost:{PUERTO}"
    print(f"\n  Lotto Activo corriendo en  {url}")
    print("  Modelo:", "ensamble (numpy/scipy OK)" if PRED else f"antiguo ({PRED_ERR})")
    threading.Thread(target=pronostico_bucle, daemon=True).start()
    try:                                  # RD Internacional (h:30): anotado + congelado propios
        import rdint_vivo
        rdint_vivo.iniciar()
        print("  RD Internacional: anotado y pronóstico automáticos activos")
    except Exception as ex:  # noqa: BLE001
        print(f"  RD Internacional desactivado: {ex!r}", file=sys.stderr)
    if AUTO["activo"]:
        threading.Thread(target=auto_bucle, daemon=True).start()
        print(f"  Resultado: se anota solo (revisa cada {AUTO_INTERVALO // 60} min, "
              "unos 10 min después de cada sorteo)")
    else:
        print("  Resultado: anotado automático APAGADO (AUTO_RESULTADO=0)")
    print("  Hora local:", datetime.now().isoformat(timespec="seconds"),
          f"({time.tzname[0]}, UTC{time.timezone/-3600:+.0f})")
    if time.timezone != 4 * 3600:
        print("  AVISO: la zona horaria no quedo en UTC-4 (Caracas); "
              "las etiquetas hoy/ayer saldran desplazadas.", file=sys.stderr)
    print("  Para detenerlo: Ctrl + C\n")
    if not EN_NUBE:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        HTTPServer((HOST, PUERTO), H).serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.\n")
