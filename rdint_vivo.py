# -*- coding: utf-8 -*-
"""Lotto Activo RD Internacional (sorteos h:30) en vivo — hilo 7.

Validado a ciegas (herramientas/resultados/hilo7_prueba_ciega.md): RD Int casi nunca repite el
animal que Lotto Activo sacó a las h:00. El modelo es el mismo que se midió:
  B0 = secuencia_v3 corrido solo con RD Int (reajuste en fronteras 2000 + k·250, igual que
       en la evaluación walk-forward);
  B1 = B0 · exp(b · x), x = [LA h:00 == i, LA (h−1):00 == i, salió hoy en LA sin h ni h−1],
       con b congelado en herramientas/rdint/coef_b1.json.

Qué hace este módulo (lo arranca servidor.py con iniciar()):
  * anota solo los resultados de RD Int desde la fuente oficial (juego id 2);
  * congela el pronóstico del próximo sorteo RD ANTES de las h:30. Se crea en cuanto hay
    cálculo y se ACTUALIZA una vez cuando llega Lotto Activo de las h:00; después de la
    hora del sorteo ya no se toca;
  * puntúa y lleva su propio marcador;
  * html() da el fragmento de la pestaña «RD Internacional».

Archivos (en el volumen de Railway si existe): rdint_historial.txt («fecha h código», h 0..11 =
8:30..19:30) y rdint_predicciones.json. Si falta el historial, se siembra con
datos_multiloteria/rdint_hist.csv del repo.
"""
import csv, html as _html, io, json, os, re, sys, threading, time, unicodedata
from datetime import date, datetime, timedelta

RUTA = os.path.dirname(os.path.abspath(__file__))
DATOS = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH") or RUTA
HERR = os.path.join(RUTA, "herramientas")
RD_HIST = os.path.join(DATOS, "rdint_historial.txt")
RD_LOG = os.path.join(DATOS, "rdint_predicciones.json")
LA_HIST = os.path.join(DATOS, "historial.txt")
SEMILLA = os.path.join(RUTA, "datos_multiloteria", "rdint_hist.csv")
COEF = os.path.join(HERR, "rdint", "coef_b1.json")
JUEGO_RD = "2"
PAGO = 30
DESDE, R = 2000, 250                      # fronteras de reajuste de B0, como en la evaluación
INTERVALO = 60                            # segundos entre pasadas del bucle

POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}
K = len(POS)
NOMBRE = {"0": "Delfín", "00": "Ballena", "1": "Carnero", "2": "Toro", "3": "Ciempiés", "4": "Alacrán",
          "5": "León", "6": "Rana", "7": "Perico", "8": "Ratón", "9": "Águila", "10": "Tigre",
          "11": "Gato", "12": "Caballo", "13": "Mono", "14": "Paloma", "15": "Zorro", "16": "Oso",
          "17": "Pavo", "18": "Burro", "19": "Chivo", "20": "Cochino", "21": "Gallo", "22": "Camello",
          "23": "Cebra", "24": "Iguana", "25": "Gallina", "26": "Vaca", "27": "Perro", "28": "Zamuro",
          "29": "Elefante", "30": "Caimán", "31": "Lapa", "32": "Ardilla", "33": "Pescado",
          "34": "Venado", "35": "Jirafa", "36": "Culebra"}
_POR_NOMBRE = {re.sub(r"[^A-Z]", "", unicodedata.normalize("NFD", v.upper())): k for k, v in NOMBRE.items()}
HORAS_RD = ["8:30 AM", "9:30 AM", "10:30 AM", "11:30 AM", "12:30 PM", "1:30 PM",
            "2:30 PM", "3:30 PM", "4:30 PM", "5:30 PM", "6:30 PM", "7:30 PM"]
HORAS_LA = [h.replace(":30", ":00") for h in HORAS_RD]

# Planes de fichas por puesto (1..15): (nombre, fichas)
PLANES = [("Top-5 escalonado 2-2-2-1-1", [2, 2, 2, 1, 1] + [0] * 10),
          ("Top-15 ponderado 3-2-1", [3, 3, 3, 2, 2] + [1] * 10),
          ("Top-3 plano", [1, 1, 1] + [0] * 12),
          ("Top-15 plano", [1] * 15)]

CERROJO = threading.RLock()
ESTADO = {"mensaje": "sin revisar", "revisado": None, "error": None, "calculando": False}
_B0 = {"clave": None, "p": None}           # caché del cálculo B0 del próximo sorteo


def log(msg):
    sys.stderr.write("[rdint] %s %s\n" % (datetime.now().isoformat(timespec="seconds"), msg))
    sys.stderr.flush()


def codigo_de_nombre(nombre):
    return _POR_NOMBRE.get(re.sub(r"[^A-Z]", "", unicodedata.normalize("NFD", (nombre or "").upper())))


# ------------------------------------------------------------------ datos
def _sembrar():
    if os.path.exists(RD_HIST) or not os.path.exists(SEMILLA):
        return
    filas = []
    with io.open(SEMILLA, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cod = codigo_de_nombre(r["animal"]); h = int(r["hora"][:2]) - 8
            if cod is not None and r["hora"].endswith(":30") and 0 <= h <= 11:
                filas.append((r["fecha"], h, cod))
    _escribir(sorted(set(filas), key=lambda x: (x[0], x[1])))
    log("historial RD sembrado con %d sorteos" % len(filas))


def _escribir(filas):
    tmp = RD_HIST + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        for fe, h, cod in filas:
            f.write("%s %d %s\n" % (fe, h, cod))
    os.replace(tmp, RD_HIST)


def cargar_rd():
    _sembrar()
    filas = []
    if os.path.exists(RD_HIST):
        with io.open(RD_HIST, encoding="utf-8") as f:
            for ln in f:
                p = ln.split()
                if len(p) == 3 and p[2] in IDX:
                    filas.append((p[0], int(p[1]), p[2]))
    return filas


def la_del_dia(fecha):
    """{h: código} de Lotto Activo ese día, leído del historial del servidor."""
    d = {}
    if os.path.exists(LA_HIST):
        with io.open(LA_HIST, encoding="utf-8") as f:
            for ln in f:
                if ln.startswith(fecha):
                    p = ln.split()
                    if len(p) == 3 and p[2] in IDX:
                        d[int(p[1])] = p[2]
    return d


def log_cargar():
    try:
        with io.open(RD_LOG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"registros": []}


def log_guardar(d):
    tmp = RD_LOG + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tmp, RD_LOG)


def siguiente(filas, hoy=None):
    """Próximo slot RD por jugar: el siguiente al último anotado, sin saltar al pasado."""
    hoy = hoy or date.today().isoformat()
    f, h, _ = filas[-1]
    if h < 11:
        f2, h2 = f, h + 1
    else:
        f2, h2 = (date.fromisoformat(f) + timedelta(days=1)).isoformat(), 0
    if f2 < hoy:                          # días sin datos (feriado, caída): se sigue desde hoy
        f2, h2 = hoy, 0
    return f2, h2


def hora_sorteo(f, h):
    return datetime.fromisoformat(f) + timedelta(hours=8 + h, minutes=30)


# ------------------------------------------------------------------ fuente
def resultados_oficiales(fecha):
    """{h: código} de RD Int ese día desde lottoactivo.com, o None si no responde."""
    sys.path.insert(0, os.path.join(RUTA, "scraping"))
    import fuente_oficial as F
    for i in range(2):
        try:
            js = F._pedir(fecha, F.token(refrescar=i > 0))
            break
        except Exception as e:  # noqa: BLE001
            log("fuente oficial fallo (%r)" % e)
            js = None
            time.sleep(2)
    if not isinstance(js, dict):
        return None
    out = {}
    for juego in js.get("datos") or []:
        if str(juego.get("id")) != JUEGO_RD:
            continue
        for r in juego.get("resultados") or []:
            m = re.match(r"\s*(\d{1,2}):(\d{2})\s*([AP]M)", str(r.get("time_s", "")), re.I)
            if not m or m.group(2) != "30":
                continue
            h = int(m.group(1)) % 12 + (12 if m.group(3).upper() == "PM" else 0) - 8
            cod = codigo_de_nombre(r.get("name_animal"))
            if cod is None:
                num = str(r.get("number_animal", "")).strip()
                cod = num if num in IDX else None
            if cod is not None and 0 <= h <= 11:
                out[h] = cod
    return out


def sincronizar():
    """Anota en orden los resultados RD que falten, desde el último día anotado hasta hoy."""
    filas = cargar_rd()
    hoy = date.today()
    f = date.fromisoformat(filas[-1][0])
    nuevos = 0
    while f <= hoy:
        fe = f.isoformat()
        res = resultados_oficiales(fe)
        if res is None:
            break
        ult = (filas[-1][0], filas[-1][1])
        for h in sorted(res):
            if (fe, h) > ult:
                filas.append((fe, h, res[h])); nuevos += 1
        f += timedelta(days=1)
    if nuevos:
        _escribir(filas)
    return nuevos, filas


# ------------------------------------------------------------------ modelo
def _coef():
    with io.open(COEF, encoding="utf-8") as f:
        return json.load(f)["b"]


def _b0(filas, f_sig, h_sig):
    """P0 del slot (f_sig, h_sig) con secuencia_v3, igual que en la evaluación. Cacheado."""
    clave = (len(filas), filas[-1][0], filas[-1][1], f_sig, h_sig)
    if _B0["clave"] == clave:
        return _B0["p"]
    import numpy as np
    sys.path.insert(0, HERR)
    import lotto_eval as LE
    fechas = [x[0] for x in filas] + [f_sig]
    d0 = date.fromisoformat(fechas[0])
    datos = LE.Datos(np.array([IDX[x[2]] for x in filas] + [0]),
                     np.array([x[1] for x in filas] + [h_sig]),
                     np.array([date.fromisoformat(x).weekday() for x in fechas]),
                     np.array([(date.fromisoformat(x) - d0).days for x in fechas]), fechas)
    n = len(filas)
    T = DESDE + ((n - DESDE) // R) * R
    modelo = LE.cargar_modelo(os.path.join(HERR, "modelos", "secuencia_v3.py"))
    P = LE.normalizar(modelo.predecir(datos, T))
    p = [float(x) for x in P[n - T]]
    _B0.update(clave=clave, p=p)
    return p


def b1(p0, la_dia, h):
    """Aplica la memoria cruzada de Lotto Activo del mismo día (h:00 y antes)."""
    import math
    b = _coef()
    la_h = la_dia.get(h); la_h1 = la_dia.get(h - 1) if h > 0 else None
    antes = {c for hh, c in la_dia.items() if hh <= h}
    z = []
    for i, cod in enumerate(POS):
        x0 = cod == la_h; x1 = cod == la_h1
        x2 = cod in antes and not x0 and not x1
        z.append(math.log(max(p0[i], 1e-9)) + b[0] * x0 + b[1] * x1 + b[2] * x2)
    m = max(z); e = [math.exp(v - m) for v in z]; s = sum(e)
    return [v / s for v in e]


# ------------------------------------------------------------------ congelado
def preparar(calcular=False):
    """Crea o actualiza el pronóstico congelado del próximo sorteo RD y puntúa los resueltos.

    Solo el bucle (calcular=True) corre B0, que tarda; la página nunca espera por él."""
    filas = cargar_rd()
    if not filas:
        return None
    d = log_cargar(); cambio = False
    hechos = {(x[0], x[1]): x[2] for x in filas}
    for r in d["registros"]:
        if r.get("salio") is None and (r["fecha"], r["hora"]) in hechos:
            r["salio"] = hechos[(r["fecha"], r["hora"])]
            r["puesto"] = r["orden"].index(r["salio"]) + 1
            cambio = True
    f, h = siguiente(filas)
    ahora = datetime.now()
    pend = next((r for r in d["registros"] if (r["fecha"], r["hora"]) == (f, h)), None)
    clave = (len(filas), filas[-1][0], filas[-1][1], f, h)
    if ahora < hora_sorteo(f, h) and (calcular or _B0["clave"] == clave):
        ESTADO["calculando"] = True
        try:
            p0 = _b0(filas, f, h)
        finally:
            ESTADO["calculando"] = False
        la = la_del_dia(f)
        con_la = h in la
        if pend is None or (con_la and not pend.get("con_la_h")):
            p = b1(p0, la, h)
            orden = sorted(POS, key=lambda c: (-p[IDX[c]], IDX[c]))
            nuevo = {"fecha": f, "hora": h, "orden": orden,
                     "prob": {c: round(p[IDX[c]], 5) for c in orden[:15]},
                     "con_la_h": con_la, "la_h": la.get(h), "la_h1": la.get(h - 1),
                     "creado": (pend or {}).get("creado") or ahora.isoformat(timespec="seconds"),
                     "actualizado": ahora.isoformat(timespec="seconds"),
                     "modelo": "rdint_b1", "salio": None}
            if pend is None:
                d["registros"].append(nuevo)
            else:
                pend.update(nuevo)
            pend = nuevo; cambio = True
    if cambio:
        log_guardar(d)
    return dict(filas=filas, d=d, sig=(f, h), pend=pend)


def marcador(d):
    puestos = [r["puesto"] for r in d["registros"] if r.get("puesto")]
    n = len(puestos)
    out = {"n": n, "puestos": puestos[::-1][:30],
           "top3": sum(p <= 3 for p in puestos), "top5": sum(p <= 5 for p in puestos),
           "top15": sum(p <= 15 for p in puestos), "planes": []}
    for nombre, fichas in PLANES:
        apost = sum(fichas) * n
        cobro = sum(PAGO * fichas[p - 1] for p in puestos if p <= 15)
        out["planes"].append({"plan": nombre, "apostado": apost, "neto": cobro - apost,
                              "retorno": (cobro - apost) / apost if apost else 0.0})
    return out


def pasada():
    """Una vuelta del bucle: resultados nuevos + congelado."""
    with CERROJO:
        try:
            nuevos, _ = sincronizar()
            preparar(calcular=True)
            ESTADO["mensaje"] = ("%d resultado%s anotado%s" % (nuevos, "s" * (nuevos != 1), "s" * (nuevos != 1))
                                 if nuevos else "sin novedad")
            ESTADO["error"] = None
        except Exception as ex:  # noqa: BLE001
            ESTADO["error"] = "%s: %s" % (type(ex).__name__, ex)
            log("pasada fallo: %r" % ex)
        ESTADO["revisado"] = datetime.now().isoformat(timespec="seconds")


def bucle():
    while True:
        t = datetime.now()
        if (8, 0) <= (t.hour, t.minute) and t.hour < 21:
            pasada()
        time.sleep(INTERVALO)


def iniciar():
    threading.Thread(target=bucle, daemon=True).start()


# ------------------------------------------------------------------ API / HTML
def api():
    with CERROJO:
        x = preparar()
    if x is None:
        return {"error": "sin historial RD"}
    f, h = x["sig"]
    return {"sorteo": {"fecha": f, "hora": HORAS_RD[h]}, "pronostico": x["pend"],
            "marcador": marcador(x["d"]), "estado": ESTADO}


def _e(s):
    return _html.escape(str(s))


def _chip(cod, extra=""):
    return '<span class="chip %s"><b>%s</b> %s</span>' % (extra, _e(cod), _e(NOMBRE[cod]))


def html():
    with CERROJO:
        x = preparar()
    if x is None:
        return '<div class="card"><p>RD Internacional: todavía no hay historial.</p></div>'
    f, h = x["sig"]; pend = x["pend"]; d = x["d"]
    hoy = [r for r in x["filas"] if r[0] == f]
    la = la_del_dia(f)
    partes = []
    # --- jugada
    if pend is None:
        cuerpo = ('<p class="muted">Calculando el pronóstico (tarda 1-2 min tras cada resultado)…</p>'
                  if datetime.now() < hora_sorteo(f, h) else
                  '<p class="muted">El servidor no llegó a congelar este sorteo a tiempo; no se puntúa.</p>')
    else:
        o = pend["orden"]; pr = pend.get("prob", {})
        if datetime.now() >= hora_sorteo(f, h):
            nota = '<span class="pill">jugado · esperando el resultado de RD</span>'
        elif pend.get("con_la_h"):
            nota = ('<span class="pill ok">con Lotto Activo de las %s: %s</span>'
                    % (HORAS_LA[h], _e(NOMBRE[pend["la_h"]]) if pend.get("la_h") else "—"))
        else:
            nota = ('<span class="pill warn">esperando Lotto Activo de las %s · se actualiza sola</span>'
                    % HORAS_LA[h])
        filas_j = []
        for k, cod in enumerate(o[:15], 1):
            f5 = PLANES[0][1][k - 1]; f15 = PLANES[1][1][k - 1]
            filas_j.append('<li class="%s"><span class="rk">%d</span>%s<span class="muted">%.1f %%</span>'
                           '<span class="fx">%s</span><span class="fx muted">%d</span></li>'
                           % ("top5" if k <= 5 else "", k, _chip(cod), 100 * pr.get(cod, 0),
                              ("%d" % f5) if f5 else "·", f15))
        cuerpo = ('<div class="kpis"><div class="kpi"><small>Sorteo</small><b>%s</b></div>'
                  '<div class="kpi"><small>Estado</small>%s</div></div>'
                  '<ol class="jugada"><li class="cab"><span class="rk">#</span><span>Animal</span>'
                  '<span class="muted">Prob.</span><span class="fx">Top-5</span><span class="fx muted">Top-15</span></li>%s</ol>'
                  '<p class="muted">Fichas: <b>Top-5 escalonado</b> (2-2-2-1-1) o <b>Top-15 ponderado</b> (3-2-1). '
                  'Casi descartados: los que ya salieron hoy en RD y el de Lotto Activo de la misma hora. '
                  'Juega DESPUÉS de ver Lotto Activo de las %s y antes de las %s.</p>'
                  % (_e(HORAS_RD[h]), nota, "".join(filas_j), HORAS_LA[h], HORAS_RD[h]))
    partes.append('<section class="card" id="rd-jugada"><h2 class="card-h">Jugada RD Internacional · %s %s</h2>%s</section>'
                  % (_e(f), _e(HORAS_RD[h]), cuerpo))
    # --- hoy
    tira = "".join('<span class="chip"><small>%s</small> <b>%s</b> %s</span>' % (HORAS_RD[hh], cod, _e(NOMBRE[cod]))
                   for _, hh, cod in hoy) or '<span class="muted">Aún no hay sorteos RD hoy.</span>'
    tira_la = "".join('<span class="chip"><small>%s</small> <b>%s</b> %s</span>' % (HORAS_LA[hh], cod, _e(NOMBRE[cod]))
                      for hh, cod in sorted(la.items())) or '<span class="muted">—</span>'
    partes.append('<details class="sec" id="rd-hoy"><summary>Resultados de hoy · RD %d · Lotto Activo %d</summary>'
                  '<div class="card"><h3 class="card-h">RD Internacional</h3><div class="tira">%s</div>'
                  '<h3 class="card-h">Lotto Activo</h3><div class="tira">%s</div></div></details>'
                  % (len(hoy), len(la), tira, tira_la))
    # --- marcador
    m = marcador(d)
    if m["n"]:
        filas_m = "".join('<tr><td>%s</td><td>%d</td><td class="%s">%+d</td><td>%+.1f %%</td></tr>'
                          % (_e(p["plan"]), p["apostado"], "ok" if p["neto"] >= 0 else "bad", p["neto"],
                             100 * p["retorno"]) for p in m["planes"])
        cuerpo_m = ('<div class="kpis"><div class="kpi"><small>Sorteos</small><b>%d</b></div>'
                    '<div class="kpi"><small>Top-3</small><b>%d</b></div><div class="kpi"><small>Top-5</small><b>%d</b></div>'
                    '<div class="kpi"><small>Top-15</small><b>%d</b></div></div>'
                    '<table class="tabla"><tr><th>Plan (1 ficha = 1 $)</th><th>Apostado</th><th>Neto</th><th>Retorno</th></tr>%s</table>'
                    '<p class="muted">Puesto del ganador, del más reciente al más viejo: %s</p>'
                    % (m["n"], m["top3"], m["top5"], m["top15"], filas_m, ", ".join(map(str, m["puestos"]))))
    else:
        cuerpo_m = '<p class="muted">Todavía no hay sorteos RD puntuados en vivo.</p>'
    resumen = ("Marcador RD · %d sorteos · Top-3 %d · Top-15 %d" % (m["n"], m["top3"], m["top15"])
               if m["n"] else "Marcador RD · aún vacío")
    partes.append('<details class="sec" id="rd-marcador"><summary>%s</summary><div class="card">%s</div></details>'
                  % (_e(resumen), cuerpo_m))
    # --- evidencia
    partes.append(
        '<details class="sec" id="rd-evidencia"><summary>Por qué funciona · prueba ciega</summary><div class="card">'
        '<p>RD Internacional casi nunca repite el animal que Lotto Activo acaba de sacar (5 veces menos de lo normal) '
        'ni los que ya salieron hoy en RD. En la prueba ciega (3.237 sorteos no vistos, jul-2025 a abr-2026) el Top-3 '
        'acertó 12,05 %% (equilibrio 10 %%) y el Top-5 escalonado ganó +20 %% por ficha. Es una sola prueba: '
        'confírmalo en este marcador antes de subir la apuesta.</p>'
        '<p class="muted">Anotado automático: %s%s.</p></div></details>'
        % (_e(ESTADO["mensaje"]), (" · error: " + _e(ESTADO["error"])) if ESTADO["error"] else ""))
    return "".join(partes)
