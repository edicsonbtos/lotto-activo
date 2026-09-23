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

P_MOD_T15 = 0.5307   # Top-15 del ensamble_v2 medido walk-forward en desarrollo

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
             analisis=analisis_top15(d, res))
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
    "diagnostico": {
        "titulo": "Diagnóstico de aleatoriedad", "dura": "segundos",
        "cmd": ["diagnostico.py"],
        "que": "Comprueba si el sorteo es azar puro o tiene patrones.",
        "mirar": "En «1-1» un valor muy por debajo de 1,00x y más de 11 animales distintos por jornada "
                 "significan que el operador evita repetir. Compara el primer y el último tercio: si cambian "
                 "mucho, el mecanismo del operador cambió.",
    },
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
    "sorteo": {
        "titulo": "Validar predicción por sorteo", "dura": "5 a 10 min",
        "cmd": ["lotto_eval.py", "modelos/hazard_actual.py", "modelos/ensamble_v2.py", "--sin-fuga"],
        "que": "Compara el modelo antiguo con el ensamble en 7.357 sorteos de desarrollo.",
        "mirar": "El ensamble debe superar al antiguo en Top1, Top3 y mbits, y en los 4 «cuartos». "
                 "Top1 por encima de 3,33% es el umbral con pago 30x; mira el primer número del intervalo [a-b].",
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
/* Sistema visual: tokens -> componentes. Un solo lugar donde cambiar color,
   radio, sombra o ritmo. Claro y oscuro con el MISMO contraste de lectura
   (texto secundario >= 4.5:1 sobre su fondo). */
:root{
  color-scheme:light dark;
  --bg:#f4f2ed; --bg-2:#ebe8e0; --card:#fff; --velo:rgba(244,242,237,.82);
  --line:#e3dfd6; --line-soft:#f0ede6; --pista:#efece4;
  --ink:#17191d; --muted:#5f6268; --soft:#73767d;
  --brand:#b5621b; --brand-ink:#8a4a13; --brand-soft:#fbf0e3;
  --ok:#1c6a49; --ok-soft:#e4f2ec; --bad:#96382a; --bad-soft:#f8e9e5;
  --r1:8px; --r2:12px; --r3:16px; --pil:999px;
  --sh1:0 1px 2px rgba(23,25,29,.05);
  --sh2:0 2px 4px rgba(23,25,29,.05),0 8px 24px rgba(23,25,29,.06);
  --gap:14px;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#131419; --bg-2:#1a1c22; --card:#1b1d23; --velo:rgba(19,20,25,.82);
    --line:#2c2f38; --line-soft:#24272f; --pista:#262932;
    --ink:#ecebe7; --muted:#a3a7af; --soft:#8b8f98;
    --brand:#e08b3f; --brand-ink:#f0a75f; --brand-soft:#2c2118;
    --ok:#5fc39a; --ok-soft:#16261f; --bad:#e78a76; --bad-soft:#2b1b17;
    --sh1:0 1px 2px rgba(0,0,0,.3);
    --sh2:0 2px 4px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.35);
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.55 "Segoe UI",-apple-system,BlinkMacSystemFont,Roboto,"Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.w{max-width:1100px;margin:0 auto;padding:20px 16px 48px}
:where(a,button,input,select,summary):focus-visible{outline:2px solid var(--brand);outline-offset:2px;border-radius:4px}
.sr{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}

/* ---------- cabecera y navegación ---------- */
header{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:10px;margin-bottom:14px}
h1{font-size:clamp(22px,1.1rem + 1.4vw,30px);margin:0;font-weight:700;letter-spacing:-.02em}
.sub{color:var(--muted);font-size:13.5px}
.sub b{color:var(--ink)}
.pill{display:inline-flex;align-items:center;gap:6px;font-size:12px;padding:5px 12px;border-radius:var(--pil);
  background:var(--ok-soft);color:var(--ok);font-weight:600;line-height:1.2}
.pill::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor;flex:0 0 auto}
.pill.warn{background:var(--brand-soft);color:var(--brand-ink)}
nav{position:sticky;top:0;z-index:20;display:flex;gap:6px;flex-wrap:wrap;margin:0 -16px var(--gap);padding:10px 16px;
  background:var(--velo);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid transparent}
nav a{display:inline-flex;align-items:center;min-height:36px;font-size:13.5px;color:var(--muted);text-decoration:none;
  padding:6px 13px;border:1px solid var(--line);border-radius:var(--pil);background:var(--card);transition:color .15s,border-color .15s}
nav a:hover{color:var(--ink);border-color:var(--soft)}
section[id],div[id]{scroll-margin-top:72px}
/* en el telefono la navegacion cabe en una sola tira deslizable en vez de
   comerse tres lineas de alto */
@media (max-width:560px){nav{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}
  nav::-webkit-scrollbar{display:none} nav a{flex:0 0 auto}}

/* ---------- últimos resultados ---------- */
.strip{display:flex;gap:8px;overflow-x:auto;padding:2px 2px 8px;margin-bottom:var(--gap);
  scroll-snap-type:x proximity;scrollbar-width:thin}
.res{flex:0 0 auto;background:var(--card);border:1px solid var(--line);border-radius:var(--r1);
  padding:7px 11px;text-align:center;min-width:84px;scroll-snap-align:start;box-shadow:var(--sh1)}
.res small{display:block;color:var(--soft);font-size:11px}
.res b{font-size:18px;font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.res span{display:block;font-size:11px;color:var(--muted)}
.res:first-child{border-color:var(--brand);box-shadow:0 0 0 1px var(--brand)}

/* ---------- rejilla y tarjetas ---------- */
.grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--gap);align-items:start}
@media (max-width:860px){.grid{grid-template-columns:1fr}}
/* sin esto, un hijo ancho (fichas, cabecera larga) estira la columna y saca
   barra horizontal en el telefono: los items de grid no encogen por defecto */
.grid>*,.grid .card{min-width:0}
.card{min-width:0;overflow-wrap:break-word}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--r2);padding:20px;margin-bottom:var(--gap);box-shadow:var(--sh1)}
.grid .card{margin-bottom:0}
.hh{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin:0 0 14px;flex-wrap:wrap}
.hh h2{font-size:12.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0;font-weight:700}
.hh span{font-size:13.5px;color:var(--ink);font-weight:600}

/* ---------- predicción ---------- */
.pick{display:grid;grid-template-columns:20px 68px 1fr auto;align-items:center;gap:12px;padding:11px 0;border-bottom:1px solid var(--line-soft)}
.pick:last-of-type{border-bottom:none}
.rk{font-size:12px;color:var(--soft);font-variant-numeric:tabular-nums}
.num{font-size:clamp(28px,1rem + 2vw,34px);font-weight:800;color:var(--brand);font-variant-numeric:tabular-nums;letter-spacing:-.03em;line-height:1}
.nm{font-size:16px;font-weight:600;letter-spacing:-.01em}
.bar{height:7px;background:var(--pista);border-radius:var(--pil);margin-top:6px;position:relative;overflow:hidden}
/* sin transición: el ancho viene ya calculado del servidor y animar `width`
   fuerza recálculo de layout en cada cuadro para un efecto que nadie ve */
.bar i{display:block;height:100%;background:var(--brand);border-radius:var(--pil)}
.bar em{position:absolute;top:-3px;width:2px;height:13px;background:var(--soft);border-radius:1px}
.pc{font-size:14.5px;font-weight:700;text-align:right;font-variant-numeric:tabular-nums}
.pc small{display:block;font-size:11px;color:var(--soft);font-weight:400}

/* ---------- textos de apoyo ---------- */
.note{font-size:12.5px;color:var(--soft);margin:12px 0 0}
.note.top{margin:0 0 14px}
.tip{font-size:13.5px;color:var(--brand-ink);background:var(--brand-soft);padding:11px 13px;border-radius:var(--r1);margin-top:12px;
  border:1px solid transparent}
@media (prefers-color-scheme:dark){.tip{border-color:var(--line)}}

/* ---------- tripleta y fichas ---------- */
.tri{border:1px solid var(--line);border-radius:var(--r1);padding:12px 14px;margin-bottom:10px}
.tri h3{margin:0 0 9px;font-size:12.5px;color:var(--muted);font-weight:700;letter-spacing:.04em;text-transform:uppercase}
.chips{display:flex;flex-wrap:wrap;gap:7px}
.chip{display:inline-flex;align-items:baseline;gap:6px;padding:6px 12px;border-radius:var(--pil);background:var(--brand-soft);font-size:14px;color:var(--ink)}
.chip b{color:var(--brand-ink);font-size:16px;font-variant-numeric:tabular-nums}
.chip.si{background:var(--ok-soft)}.chip.si b{color:var(--ok)}
.chip small{color:var(--soft);font-size:11px}

/* ---------- formularios ---------- */
form.reg{display:flex;gap:9px}
input[type=text]{flex:1;min-width:0;padding:13px 15px;font-size:18px;color:var(--ink);border:1px solid var(--line);
  border-radius:var(--r1);background:var(--bg-2);font-variant-numeric:tabular-nums}
input[type=text]::placeholder{color:var(--soft)}
button{min-height:44px;padding:11px 19px;font-size:15px;font-weight:600;border:1px solid transparent;border-radius:var(--r1);
  background:var(--ink);color:var(--card);cursor:pointer;transition:opacity .15s,background .15s}
button:hover{opacity:.87}
button:active{transform:translateY(1px)}
button.sec{background:var(--card);color:var(--ink);border-color:var(--line)}
button.sec:hover{border-color:var(--soft);opacity:1}
button.link{min-height:36px;background:none;color:var(--bad);padding:8px 0;font-size:13px;font-weight:500;text-decoration:underline;border:none}
.acciones{display:flex;flex-wrap:wrap;align-items:center;gap:14px;margin-top:14px}
.acciones form{margin:0}
select{min-height:44px;padding:10px 12px;font-size:14px;color:var(--ink);border:1px solid var(--line);border-radius:var(--r1);background:var(--bg-2)}

/* ---------- avisos y estado del anotado automático ---------- */
.msg{font-size:14px;padding:12px 15px;border-radius:var(--r1);margin-bottom:var(--gap);border:1px solid transparent}
.msg.ok{background:var(--ok-soft);color:var(--ok)}
.msg.no{background:var(--bg-2);color:var(--muted)}
.msg.bad{background:var(--bad-soft);color:var(--bad)}
.auto,.hh span.auto{display:inline-flex;align-items:center;gap:7px;font-size:12px;font-weight:600;color:var(--ok);
  background:var(--ok-soft);padding:5px 11px;border-radius:var(--pil);line-height:1.2}
.auto::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor;flex:0 0 auto}
.auto.off,.hh span.auto.off{color:var(--soft);background:var(--bg-2)}

/* ---------- tablas ---------- */
table.hist{width:100%;border-collapse:collapse;font-size:13.5px}
table.hist th{text-align:left;color:var(--muted);font-weight:600;padding:7px 9px;border-bottom:1px solid var(--line);
  position:sticky;top:0;background:var(--card)}
table.hist td{padding:7px 9px;border-bottom:1px solid var(--line-soft);font-variant-numeric:tabular-nums}
table.hist tr:last-child td{border-bottom:none}
table.hist td.ok{color:var(--ok);font-weight:600}table.hist td.no{color:var(--soft)}
.temp{display:flex;align-items:center;gap:13px;flex-wrap:wrap;margin-top:var(--gap);
  padding:13px 15px;border:1px solid var(--line);border-radius:var(--r2);background:var(--card)}
.temp .pts{display:flex;gap:5px;flex:none}
.temp .pt{width:10px;height:10px;border-radius:50%;background:var(--pista)}
.temp .pt.on{background:currentColor}
.temp b{font-size:14px;letter-spacing:.05em;flex:none}
.temp .txt{flex:1;min-width:190px;font-size:13px;line-height:1.45;color:var(--muted)}
.temp.ok{color:var(--ok)}.temp.ojo{color:var(--brand)}.temp.alerta{color:var(--bad)}

/* ---------- indicadores ---------- */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
.kpi{border:1px solid var(--line);border-radius:var(--r1);padding:11px 13px;background:var(--card)}
.kpi small{display:block;font-size:11px;color:var(--muted)}
.kpi b{font-size:21px;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.kpi span{display:block;font-size:11px;color:var(--soft)}
.pend{font-size:13px;border-top:1px solid var(--line-soft);padding:9px 0}
.pend b{font-weight:600}

/* ---------- reparto del puesto del ganador ---------- */
.dist{display:grid;grid-template-columns:92px 1fr 84px;align-items:center;gap:10px;padding:5px 0}
.dist .dl{font-size:12.5px;color:var(--muted)}
.dist .db{position:relative;height:16px;background:var(--pista);border-radius:var(--r1);overflow:hidden}
/* sin min-width: un tramo con 0 veces no debe dejar una raya que parezca algo */
.dist .db i{display:block;height:100%;background:var(--soft);border-radius:var(--r1)}
.dist .db em{position:absolute;top:0;width:2px;height:100%;background:var(--ink);opacity:.45}
.dist .dv{font-size:13px;font-weight:600;text-align:right;font-variant-numeric:tabular-nums}
.dist .dv small{display:block;font-size:10.5px;color:var(--soft);font-weight:400}
/* tramo por encima de su cuota de azar: el color lo marca, el número lo dice */
.dist.alza .db i{background:var(--brand)}
.dist.alza .dv{color:var(--brand-ink)}
@media (max-width:560px){.dist{grid-template-columns:76px 1fr 70px;gap:8px}}

/* ---------- herramientas ---------- */
.tool{border-top:1px solid var(--line-soft);padding:16px 0}
.tool:first-of-type{border-top:none;padding-top:0}
.tool-h{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px}
.tool h3{margin:0;font-size:16px;letter-spacing:-.01em}
.tool p{margin:5px 0;font-size:13px;color:var(--muted)}
.tool .mirar{color:var(--ink);background:var(--bg-2);border-radius:var(--r1);padding:10px 12px}
.st{font-size:12px;font-weight:600;color:var(--muted)}
.st.corriendo{color:var(--brand-ink)}
pre{background:#15171c;color:#e7e4dc;font-size:12px;line-height:1.5;padding:13px;border-radius:var(--r1);overflow-x:auto;max-height:420px;white-space:pre}
details summary{cursor:pointer;font-size:13px;color:var(--muted);margin-top:8px;min-height:24px}
footer{font-size:12px;color:var(--muted);line-height:1.65;margin-top:10px}

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
        else if(a.seq>window.__autoSeq){ location.replace('/'); return; }
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
  if(calc){
    (function listo(){
      fetch('/listo.json').then(r=>r.json()).then(function(j){
        var inp=document.getElementById('num');
        if(j.listo && !(inp && inp.value)) location.replace('/');
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

def html_registro():
    a = auto_estado()
    return ('<section class="card" id="registrar"><div class="hh"><h2>¿Qué salió?</h2>'
            f'<span class="auto {a["clase"]}" id="auto-est">{esc(a["txt"])}</span></div>'
            '<p class="note top">No hace falta que lo anotes: el resultado se busca solo '
            'unos 10 minutos después de cada sorteo. Escríbelo aquí solo si quieres adelantarlo.</p>'
            '<form class="reg" method="post" action="/registrar">'
            '<label class="sr" for="num">Animal que salió</label>'
            '<input type="text" id="num" name="num" placeholder="0, 00 o 1-36" autocomplete="off" '
            'inputmode="numeric"><button type="submit">Anotar</button></form>'
            '<div class="acciones">'
            '<form method="post" action="/auto"><button class="sec" type="submit">Buscar resultado ahora</button></form>'
            '<form method="post" action="/deshacer" onsubmit="return confirm(\'¿Deshacer el último registro?\')">'
            '<button class="link" type="submit">Deshacer el último</button></form></div></section>')

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
              f'<span>{plural(m["t3"], "acierto", "aciertos")} · azar 7,9% · modelo 12,3%</span></div>'
              f'<div class="kpi"><small>Top-1</small><b>{num(m["tasa1"])}%</b>'
              f'<span>{plural(m["t1"], "acierto", "aciertos")} · umbral 30x 3,33%</span></div>')
        if m.get("n15"):
            s1 += (f'<div class="kpi"><small>Top-5</small><b>{num(m["tasa5"])}%</b>'
                   f'<span>{m["t5"]} de {m["n15"]} · azar 13,2% · modelo 19,5%</span></div>'
                   f'<div class="kpi"><small>Top-15</small><b>{num(m["tasa15"])}%</b>'
                   f'<span>{m["t15"]} de {m["n15"]} · azar 39,5% · equilibrio 50%</span></div>')
        s1 += (f'<div class="kpi"><small>Lectura</small><b style="font-size:14px">{lect}</b>'
               f'<span>factor {num(m["factor"], 2)} : 1</span></div></div>')
        if m.get("n15") and m["n15"] < m["n"]:
            s1 += (f'<p class="note">El Top-15 solo puede puntuarse en {m["n15"]} de las {m["n"]} predicciones: '
                   'las más viejas se guardaron sin el orden completo de los 38, y contarlas como fallo sería mentir.</p>')
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
            f'{html_top15_reparto(d)}'
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
    return ('<div style="margin-top:18px"><div class="hh"><h2>Cada forma de jugar, con plata</h2>'
            f'<span>{ec[0]["n"]} sorteos con orden guardado</span></div>{filas}'
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

def html_top15_reparto(d):
    """Dónde cae el ganador dentro del Top-15 congelado, contra su cuota de azar."""
    a = analisis_top15(d)
    if not a["n"]:
        return ""
    filas = ""
    for k, t in enumerate(a["tramos"]):
        ancho = min(100, t["tasa"])
        marca = min(100, t["azar"])
        # El último tramo es «fuera del Top-15»: ahí superar la cuota de azar es
        # MALO. Resaltar en el color de acierto lo que es un fallo sería mentir
        # con el color.
        fuera = k == len(a["tramos"]) - 1
        mejor = (t["ventaja"] < 0) if fuera else (t["ventaja"] > 0)
        filas += (f'<div class="dist{" alza" if mejor else ""}"><span class="dl">{t["etiqueta"]}</span>'
                  f'<span class="db"><i style="width:{ancho:.1f}%"></i>'
                  f'<em style="left:{marca:.1f}%" title="cuota de azar"></em></span>'
                  f'<span class="dv">{t["tasa"]:.0f}%'
                  f'<small>{t["veces"]} {"vez" if t["veces"] == 1 else "veces"} · '
                  f'azar {t["azar"]:.0f}%</small></span></div>')
    lectura = ("El orden completo aporta información: el ganador cae en los primeros puestos más veces "
               "de lo que daría el azar." if a["puesto_medio"] < a["puesto_azar"] - 1 else
               "Todavía no se distingue del azar: el ganador cae repartido como si el orden no informara.")
    return (f'<div style="margin-top:18px"><div class="hh"><h2>Dónde cae el ganador</h2>'
            f'<span>{a["n"]} sorteos con orden guardado</span></div>{filas}'
            f'<p class="note">Puesto medio del ganador: <b>{num(a["puesto_medio"])}</b> de 38 '
            f'(al azar sería {num(a["puesto_azar"])}). La raya marca la cuota de azar de cada tramo. {lectura}</p></div>')

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
            f'<span>{plural(a["t3"], "acierto", "aciertos")} · por azar tocarían {num(a["esp3"])}</span></div>'
            f'<div class="kpi"><small>Top-1</small><b>{num(a["tasa1"])}%</b>'
            f'<span>{plural(a["t1"], "acierto", "aciertos")} · por azar {num(a["esp1"])}</span></div>')
    if a.get("n15"):
        kpis += (f'<div class="kpi"><small>Top-15</small><b>{num(a["tasa15"])}%</b>'
                 f'<span>{a["t15"]} de {a["n15"]} · por azar {num(a["esp15"])}</span></div>')
    kpis += (f'<div class="kpi"><small>Resultado a {PAGO}x</small><b>{a["roi"]:+.0f}%</b>'
             f'<span>apostando los 3 en cada sorteo</span></div></div>')
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

def _leer_consejo():
    """Top-3 del consenso de la mesa nocturna (si el archivo es reciente)."""
    ruta = os.path.join(HERR, "resultados", "mesa_consejo.txt")
    try:
        if time.time() - os.path.getmtime(ruta) > 36 * 3600:
            return None
        raw = open(ruta, "rb").read()
        for enc in ("utf-8", "utf-16"):
            try:
                txt = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            return None
        if "CONSENSO" not in txt:
            return None
        picks = []
        for ln in txt.splitlines():
            p = ln.split()
            if len(p) >= 3 and p[0] == "#" and p[1].isdigit():
                picks.append(p[2])
            if len(picks) == 3:
                break
        return picks or None
    except OSError:
        return None

def html_resumen(e, d, modelo, calculando):
    """Panel 'En palabras claras': qué jugar, cómo vas y qué hacer, sin tecnicismos."""
    partes = []
    if calculando:
        partes.append("<p>⏳ Calculando la jugada del próximo sorteo; en unos segundos te la digo en claro.</p>")
    else:
        orden = e["orden"][:5]
        trio = ", ".join(f"<b>{POS[i]}</b> {ANIM[POS[i]].title()}" for i in orden[:3])
        par = " y ".join(f"<b>{POS[i]}</b> {ANIM[POS[i]].title()}" for i in orden[3:5])
        if modelo != "hazard_actual":
            partes.append(
                f"<p>🎯 <b>La jugada de ahora:</b> 2 fichas a {trio}; 1 ficha a {par}. Son 8 fichas. "
                f"Si sale uno de los 3 primeros cobras {2*PAGO}; si sale el 4º o el 5º, {PAGO}. "
                f"En prueba ciega esto cobró 1 de cada 5 sorteos y dejó ≈ +19% de lo apostado (entre +10% y +28%). "
                f"Lo probado de verdad es el Top-3; el 4º y 5º son refuerzo.</p>")
        else:
            partes.append(f"<p>🎯 <b>La jugada de ahora:</b> {trio} (modelo antiguo, sin porcentajes calibrados).</p>")
    m = marcador(d)
    if m["n"] == 0:
        partes.append("<p>📊 <b>Cómo vas:</b> todavía no hay predicciones resueltas. Registra cada resultado y aquí te diré si vas ganando o si es espejismo.</p>")
    else:
        roi = (PAGO * m["t3"] - 3 * m["n"]) / (3 * m["n"]) * 100
        equi = 3 / PAGO * 100
        if roi >= 0 and m["factor"] >= 3:
            cara = "✅ Vas en <b>positivo</b> y la evidencia empieza a favorecer al modelo."
        elif roi >= 0:
            cara = "🟡 Vas en <b>positivo</b>, pero todavía puede ser suerte."
        else:
            cara = "🔴 Vas en <b>negativo</b>: con estos números estarías perdiendo plata."
        partes.append(
            f"<p>📊 <b>Cómo vas (sorteo):</b> {m['t3']} aciertos Top-3 en {m['n']} sorteos ({m['tasa3']:.1f}%). "
            f"El azar da 7,9%, el punto de equilibrio es {equi:.1f}% y el modelo promete ~12,3%. "
            f"Si hubieras jugado el Top-3 plano: <b>{roi:+.0f}%</b>. {cara} "
            f"Para jurarlo de verdad hacen falta ~1.000 sorteos; llevas {m['n']}.</p>")
    mt = marcador_tripleta(d)
    pend = sum(1 for t in d["tripletas"] if vigente(t) and t.get("estado") == "pendiente")
    if mt["n"] == 0:
        partes.append(f"<p>🎲 <b>Tripleta:</b> ninguna ventana cerrada todavía ({pend} en curso). Sin evidencia de que gane: juégala en papel y mira su marcador.</p>")
    else:
        partes.append(
            f"<p>🎲 <b>Tripleta:</b> {mt['aciertos']} de {mt['jugadas']} ganadoras ({mt['tasa']:.1f}%; necesitas más de 2,22%). "
            f"A 45x habrías sacado <b>{mt['ganancia']:+d}</b> unidades. Con {mt['n']} ventanas cerradas aún es pura suerte.</p>")
    cons = _leer_consejo()
    if cons:
        partes.append(f"<p>🧠 <b>El consejo de las 5 estrategias</b> (corre solo cada noche) vota: <b>{', '.join(cons)}</b> para el próximo sorteo.</p>")
    partes.append('<p class="note">Reglas: juega el Top-5 escalonado en TODOS los sorteos · no pases del 5º (del 6º al 15º '
                  "cada animal pierde plata) · no subas el monto cuando el porcentaje se vea alto ni saltes sorteos que se "
                  "ven «fríos» (probado en prueba ciega: no acierta más) · el tamaño de la ficha lo dice gestion_banca.py.</p>")
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

def render(banca=None):
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

    f, h, v = e["ult"]
    ultimos = "".join(f'<div class="res"><small>{esc(fecha_corta(fl))} {HORAS[hl]}</small><b>{POS[vl]}</b>'
                      f'<span>{ANIM[POS[vl]].title()}</span></div>' for fl, hl, vl in reversed(filas[-12:]))
    if calculando:
        estado_pill = '<span class="pill warn">calculando…</span>'
    elif modelo == "hazard_actual":
        estado_pill = '<span class="pill warn">modelo antiguo</span>'
    else:
        estado_pill = '<span class="pill">ensamble activo</span>'
    aviso = ""
    if AVISO["texto"]:
        aviso = f'<div class="msg {AVISO["clase"]}">{AVISO["texto"]}</div>'
        AVISO["texto"] = ""

    cuerpo = (
        f'<div class="w"><header><div><h1>Lotto Activo</h1>'
        f'<div class="sub">Último: {esc(fecha_corta(f))} {HORAS[h]} → <b>{POS[v]} {ANIM[POS[v]].title()}</b> · '
        f'{e["n"]:,} sorteos en el histórico</div></div>{estado_pill}</header>'
        '<nav><a href="#resumen">En claro</a><a href="#sorteo">Próximo sorteo</a><a href="#tripleta">Tripleta</a><a href="#registrar">Registrar</a>'
        '<a href="#mesa">Mesa</a><a href="#marcadores">Marcadores</a><a href="#ultimas">Últimas 48</a>'
        '<a href="#historico">Histórico</a><a href="#herramientas">Herramientas</a></nav>'
        f'{aviso}{html_resumen(e, d, modelo, calculando)}<div class="strip">{ultimos}</div>'
        f'<div class="grid"><div>{html_prediccion(e, calculando, pend, aviso_modelo)}<div style="height:14px"></div>{html_registro()}'
        f'<div style="height:14px"></div>{html_banca(e, banca)}</div>'
        f'<div>{html_tripleta(e, tri_mostrada, d, filas, calculando, PRED is None, faltan_h)}</div></div>'
        f'<div style="height:14px"></div>{html_mesa()}{html_marcadores(d)}{html_ultimas(d, filas)}'
        f'{html_historico(d)}{html_herramientas()}'
        '<footer>Azar puro: 2,63% por animal. En prueba ciega (3.122 sorteos) el ensamble acertó Top-1 4,00% '
        '(IC 95%: 3,37–4,75) y Top-3 12,27%; el umbral con pago 30x es 3,33%. Ningún modelo garantiza ganar y el '
        'operador puede cambiar su mecanismo. Tus datos: historial.txt y predicciones.json.</footer></div>')
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
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
        '<section class="card" id="mesa">'
        '<div class="hh"><h2>Mesa de probabilidades</h2>'
        '<span id="mesa-slot">cargando…</span></div>'
        '<div class="mesa-bar">'
        '<div class="mesa-nav"><button type="button" class="sec" id="mesa-prev">←</button>'
        '<span id="mesa-pos" class="st"></span>'
        '<button type="button" class="sec" id="mesa-next">→</button></div>'
        '<div class="mesa-modos">'
        '<button type="button" class="sec on" data-modo="rango">Por rango</button>'
        '<button type="button" class="sec" data-modo="rank">Por rank</button>'
        '<button type="button" class="sec" data-modo="hueco">Por hueco</button>'
        '</div></div>'
        '<div id="mesa-aviso"></div>'
        '<div id="mesa-cuerpo" class="mesa-cuerpo"></div>'
        '<details style="margin-top:14px"><summary>Dónde cayó el ganador (muestra en vivo)</summary>'
        '<div id="mesa-stats" class="mesa-stats">cargando…</div>'
        '<p class="tip" style="margin-top:10px"><b>Muestra en vivo, n pequeño — esto NO es '
        'validación.</b> Es un termómetro de lo que está pasando ahora, no evidencia. '
        'Cualquier cambio de apuesta necesita validación walk-forward en desarrollo.</p>'
        '</details>'
        '<p class="note">La mesa no mejora la predicción: muestra completa la distribución que el '
        'modelo ya calculaba. Solo lectura — no altera pronósticos, marcador ni tripletas.</p>'
        '</section>')

CSS_MESA = """
.mesa-bar{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px;margin-bottom:12px}
.mesa-nav{display:flex;align-items:center;gap:8px}
.mesa-nav button{padding:6px 13px;font-size:15px;line-height:1}
.mesa-nav button[disabled]{opacity:.35;cursor:default}
.mesa-modos{display:flex;gap:6px;flex-wrap:wrap}
.mesa-modos button{padding:6px 12px;font-size:13px;font-weight:600}
.mesa-modos button.on{background:var(--ink);color:var(--card);border-color:var(--ink)}
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
        x.classList.remove('on'); });
      b.classList.add('on'); modo = b.getAttribute('data-modo'); pinta();
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
JS = JS + JS_MESA

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
            self._send(render(banca))
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
