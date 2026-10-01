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


# Regla B de herramientas/exploracion/top15_tarde/PREREGISTRO_vivo.md: Top-21 de las 18:30 (hora 10),
# SOLO seguimiento, sin plata. Cuenta desde 2026-09-30 y se juzga una vez a los 150 sorteos de las 18:30.
TOP21_DESDE, TOP21_HORA, TOP21_N, TOP21_JUICIO = "2026-09-30", 10, 21, 150


def _wilson(k, n, z=1.959964):
    if not n:
        return None
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return [round(c - h, 4), round(c + h, 4)]


def seguimiento_top21(d):
    """Aciertos del Top-21 congelado a las 18:30 contra el resto de horas (control). Empate: 70 %."""
    out = {"desde": TOP21_DESDE, "hora": HORAS_RD[TOP21_HORA], "juicio_en": TOP21_JUICIO, "empate": 0.70}
    for clave, sel in (("hora_1830", lambda h: h == TOP21_HORA), ("resto", lambda h: h != TOP21_HORA)):
        ps = [r["puesto"] for r in d["registros"]
              if r.get("puesto") and r["fecha"] >= TOP21_DESDE and sel(r["hora"])]
        k = sum(p <= TOP21_N for p in ps)
        out[clave] = {"n": len(ps), "aciertos": k, "tasa": round(k / len(ps), 4) if ps else None,
                      "ic95": _wilson(k, len(ps)), "neto_fichas": PAGO * k - TOP21_N * len(ps)}
    a = out["hora_1830"]
    out["veredicto"] = ("pendiente" if a["n"] < TOP21_JUICIO else
                        "CONFIRMADA" if a["ic95"][0] > 0.70 else "NO CONFIRMADA")
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
            "ultimos": [list(r) for r in x["filas"][-24:]],   # [fecha, h, código]: regla de cambio en LA
            "marcador": marcador(x["d"]), "seguimiento_top21": seguimiento_top21(x["d"]), "estado": ESTADO}


def _e(s):
    return _html.escape(str(s))


def _chip(cod, extra=""):
    return '<span class="chip %s"><b>%s</b> %s</span>' % (extra, _e(cod), _e(NOMBRE[cod]))


# --- solo presentación: mismo sistema visual que la pestaña Lotto Activo (servidor.py)
_DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def _fecha(f):
    d = date.fromisoformat(f); hoy = date.today()
    if d == hoy:
        return "hoy"
    if d == hoy + timedelta(days=1):
        return "mañana"
    return "%s %d/%d" % (_DIAS[d.weekday()], d.day, d.month)


def _fx(n, clase):
    if not n:
        return '<span class="fx z" aria-label="sin fichas">–</span>'
    return '<span class="fx %s" aria-label="%d ficha%s">%d</span>' % (clase, n, "s" if n != 1 else "", n)


def _fila(k, cod, pct):
    return ('<li><span class="rk">%d</span><span class="n">%s</span><span class="nm">%s<small>%s %%</small></span>%s%s</li>'
            % (k, _e(cod), _e(NOMBRE[cod]), ("%.2f" % pct).replace(".", ","),
               _fx(PLANES[0][1][k - 1], "a"), _fx(PLANES[1][1][k - 1], "b")))


def _compartir(titulo, animales):
    """Igual que html_compartir de servidor.py (el JS vive allí)."""
    return ('<div class="compartir" data-t="%s" data-a="%s"><select aria-label="Cuántos animales">'
            '<option value="5">Top 5</option><option value="15">Top 15</option></select>'
            '<input type="text" inputmode="decimal" placeholder="$ por animal" aria-label="Monto por animal">'
            '<button type="button" class="sec">Compartir</button></div>' % (_e(titulo), _e("|".join(animales))))


def _sec(id_, titulo, meta, cuerpo):
    return ('<details class="sec" id="%s" data-rec><summary><span class="st"><h2>%s</h2><span class="meta">%s</span>'
            '</span><span class="chev" aria-hidden="true"></span></summary><div class="cuerpo">%s</div></details>'
            % (id_, titulo, _e(meta), cuerpo))


_COLS = ('<li class="cols" aria-hidden="true"><span></span><span></span><span>Animal</span>'
         '<span>Top-5</span><span>Ponde&shy;rado</span></li>')


def _resultados(d, limite=100):
    """Lista de resultados RD con el puesto que tenía el ganador en el Top congelado (como en Lotto Activo)."""
    vistos = [r for r in d["registros"] if r.get("salio") and r.get("puesto")]
    if not vistos:
        return '<p class="note">Todavía no hay resultados RD con pronóstico guardado antes del sorteo.</p>', "aún vacío"
    filas = ""; dia = None
    for r in reversed(vistos[-limite:]):
        if r["fecha"] != dia:
            dia = r["fecha"]
            filas += '<tr><th colspan="3" scope="rowgroup">%s</th></tr>' % _e(_fecha(dia).capitalize())
        p = r["puesto"]
        clase = "p5" if p <= 5 else "p15" if p <= 15 else "fuera"
        tramo = "del Top-5" if p <= 5 else "del Top-15" if p <= 15 else "fuera del Top-15"
        filas += ('<tr><td class="h">%s</td><td class="s"><b>%s</b>%s</td>'
                  '<td class="p"><span class="puesto %s" title="%s">%dº<span class="sr"> %s</span></span></td></tr>'
                  % (HORAS_RD[r["hora"]], _e(r["salio"]), _e(NOMBRE[r["salio"]]), clase, tramo, p, tramo))
    ult = [r["puesto"] for r in vistos[-48:]]
    meta = "último: %dº · Top-5 en %d y Top-15 en %d de los últimos %d" % (
        vistos[-1]["puesto"], sum(x <= 5 for x in ult), sum(x <= 15 for x in ult), len(ult))
    nota = ('<p class="note">Se muestran los últimos %d de %d.</p>' % (limite, len(vistos))
            if len(vistos) > limite else "")
    clave = ('<p class="clave"><span><span class="puesto p5">1º-5º</span>dentro de la jugada</span>'
             '<span><span class="puesto p15">6º-15º</span>solo ponderado</span>'
             '<span><span class="puesto fuera">16º+</span>fuera del Top-15</span></p>')
    return ('%s<table class="lista"><thead><tr><th scope="col">Hora</th><th scope="col">Salió</th>'
            '<th scope="col" style="text-align:right">Puesto</th></tr></thead><tbody>%s</tbody></table>%s'
            '<p class="note">Solo cuentan pronósticos guardados antes de conocer el resultado.</p>'
            % (clave, filas, nota)), meta


def _nav(atras, total):
    """Flechas para ver sorteos RD anteriores (mismo estilo .histnav de servidor.py)."""
    def enlace(n, txt):
        return '<a href="/?tab=rd%s">%s</a>' % ("&amp;atras=%d" % n if n else "", txt)
    ant = enlace(atras + 1, "‹ Anterior") if atras < total else '<span class="off">‹ Anterior</span>'
    sig = enlace(atras - 1, "Siguiente ›") if atras > 0 else '<span class="off">Siguiente ›</span>'
    pos = "próximo sorteo" if atras == 0 else "hace %d sorteo%s" % (atras, "s" if atras > 1 else "")
    return '<nav class="histnav" aria-label="Sorteos anteriores">%s<span class="pos">%s</span>%s</nav>' % (ant, pos, sig)


def _pasado(vistos, atras):
    """Top-15 congelado de un sorteo RD ya jugado, con el ganador marcado."""
    atras = max(1, min(atras, len(vistos)))
    r = vistos[-atras]; o = r["orden"]; pr = r.get("prob", {}); p = r["puesto"]
    def fila(k, cod):
        li = _fila(k, cod, 100 * pr.get(cod, 0))
        return li.replace("<li>", '<li class="gana">', 1) if cod == r["salio"] else li
    tramo = "Top-5" if p <= 5 else "Top-15" if p <= 15 else "fuera del Top-15"
    return ('<section class="card jugada" id="rd-jugada" aria-labelledby="rd-t">%s'
            '<div class="jh"><h2 id="rd-t">Sorteo RD · <span>%s</span></h2><span class="pill gris">jugado</span></div>'
            '<p class="ult">%s · salió <b>%s %s</b> · puesto %dº (%s)</p>'
            '<ol class="jug">%s%s</ol><ol class="jug resto" start="6">%s</ol>'
            '<p class="note">Es el Top congelado antes del sorteo, el mismo que se puntúa en el marcador.</p></section>'
            % (_nav(atras, len(vistos)), _e(HORAS_RD[r["hora"]]), _e(_fecha(r["fecha"]).capitalize()),
               _e(r["salio"]), _e(NOMBRE[r["salio"]]), p, tramo, _COLS,
               "".join(fila(k, c) for k, c in enumerate(o[:5], 1)),
               "".join(fila(k, c) for k, c in enumerate(o[5:15], 6))))


def html(atras=0):
    with CERROJO:
        x = preparar()
    if x is None:
        return '<div class="card"><p>RD Internacional: todavía no hay historial.</p></div>'
    f, h = x["sig"]; pend = x["pend"]; d = x["d"]
    hoy = [r for r in x["filas"] if r[0] == f]
    la = la_del_dia(f)
    partes = []
    vistos = [r for r in d["registros"] if r.get("salio") and r.get("puesto")]
    if atras > 0 and vistos:
        partes.append(_pasado(vistos, atras))
        partes.append('<div style="height:14px"></div>')
        cuerpo_r, meta_r = _resultados(d)
        partes.append(_sec("rd-historico", "Resultados y puestos en el Top", meta_r, cuerpo_r))
        return "".join(partes)
    # --- jugada (abierta, arriba)
    jugado = datetime.now() >= hora_sorteo(f, h)
    if pend is None:
        pill = ('<span class="pill warn">calculando…</span>' if not jugado
                else '<span class="pill gris">sin pronóstico</span>')
        linea = "%s · RD Internacional" % _fecha(f).capitalize()
        cuerpo = ('<div class="tip">Calculando el pronóstico (tarda 1-2 min tras cada resultado). Se actualiza sola.</div>'
                  if not jugado else
                  '<div class="tip">El servidor no llegó a congelar este sorteo a tiempo; no se puntúa.</div>')
    else:
        o = pend["orden"]; pr = pend.get("prob", {})
        if jugado:
            pill = '<span class="pill gris">jugado</span>'
            estado = "esperando el resultado de RD"
        elif pend.get("con_la_h"):
            pill = '<span class="pill">listo</span>'
            estado = ("incluye Lotto Activo de las %s: <b>%s</b>"
                      % (HORAS_LA[h], _e(NOMBRE[pend["la_h"]]) if pend.get("la_h") else "—"))
        else:
            pill = '<span class="pill warn">esperando LA</span>'
            estado = "esperando Lotto Activo de las %s · se actualiza sola" % HORAS_LA[h]
        linea = "%s · %s" % (_fecha(f).capitalize(), estado)
        top5 = "".join(_fila(k, cod, 100 * pr.get(cod, 0)) for k, cod in enumerate(o[:5], 1))
        resto = "".join(_fila(k, cod, 100 * pr.get(cod, 0)) for k, cod in enumerate(o[5:15], 6))
        cuerpo = ('<ol class="jug">%s%s</ol>'
                  '<details class="mas" id="rd-resto" data-rec><summary><span class="chev" aria-hidden="true"></span>'
                  'Del 6º al 15º · solo para el ponderado</summary><ol class="jug resto" start="6">%s</ol></details>'
                  '%s<div class="leyenda"><p><i class="a"></i><b>Top-5 escalonado</b> (2-2-2-1-1) o '
                  '<i class="b" style="margin-left:4px"></i><b>Top-15 ponderado</b> (3-2-1).</p>'
                  '<p>Casi descartados: los que ya salieron hoy en RD y el de Lotto Activo de la misma hora. '
                  'Juega <b>después</b> de ver Lotto Activo de las %s y antes de las %s.</p></div>'
                  % (_COLS, top5, resto, _compartir("RD Internacional %s %s" % (_fecha(f), HORAS_RD[h]),
                                                    ["%s %s" % (c, NOMBRE[c]) for c in o[:15]]),
                     HORAS_LA[h], HORAS_RD[h]))
    partes.append('<section class="card jugada" id="rd-jugada" aria-labelledby="rd-t">%s'
                  '<div class="jh"><h2 id="rd-t">Próximo RD · <span>%s</span></h2>%s</div>'
                  '<p class="ult">%s</p>%s</section>'
                  % (_nav(0, len(vistos)), _e(HORAS_RD[h]), pill, linea, cuerpo))
    partes.append('<div style="height:14px"></div>')
    # --- resultados con su puesto en el Top (misma lista que Lotto Activo)
    cuerpo_r, meta_r = _resultados(d)
    partes.append(_sec("rd-historico", "Resultados y puestos en el Top", meta_r, cuerpo_r))
    # --- hoy
    tira = "".join('<span class="chip"><small>%s</small> <b>%s</b> %s</span>' % (HORAS_RD[hh], cod, _e(NOMBRE[cod]))
                   for _, hh, cod in hoy) or '<span class="note">Aún no hay sorteos RD hoy.</span>'
    tira_la = "".join('<span class="chip"><small>%s</small> <b>%s</b> %s</span>' % (HORAS_LA[hh], cod, _e(NOMBRE[cod]))
                      for hh, cod in sorted(la.items())) or '<span class="note">—</span>'
    partes.append(_sec("rd-hoy", "Resultados de hoy", "RD %d · Lotto Activo %d" % (len(hoy), len(la)),
                       '<h3>RD Internacional</h3><div class="tira">%s</div>'
                       '<h3>Lotto Activo</h3><div class="tira">%s</div>' % (tira, tira_la)))
    # --- marcador
    m = marcador(d)
    if m["n"]:
        filas_m = "".join('<tr><td>%s</td><td>%d</td><td class="%s">%+d</td><td>%s %%</td></tr>'
                          % (_e(p["plan"]), p["apostado"], "ok" if p["neto"] >= 0 else "bad", p["neto"],
                             ("%+.1f" % (100 * p["retorno"])).replace(".", ",")) for p in m["planes"])
        cuerpo_m = ('<div class="cifras"><div><small>Sorteos</small><b>%d</b></div>'
                    '<div><small>Top-3</small><b>%d</b></div><div><small>Top-5</small><b>%d</b></div>'
                    '<div><small>Top-15</small><b>%d</b></div></div>'
                    '<div class="desliza"><table class="tabla"><thead><tr><th>Plan (1 ficha = 1 $)</th><th>Apostado</th>'
                    '<th>Neto</th><th>Retorno</th></tr></thead><tbody>%s</tbody></table></div>'
                    '<p class="note">Puesto del ganador, del más reciente al más viejo: %s</p>'
                    % (m["n"], m["top3"], m["top5"], m["top15"], filas_m, ", ".join(map(str, m["puestos"]))))
    else:
        cuerpo_m = '<p class="note">Todavía no hay sorteos RD puntuados en vivo.</p>'
    resumen = ("%d sorteos · Top-3 %d · Top-15 %d" % (m["n"], m["top3"], m["top15"])
               if m["n"] else "aún vacío")
    t21 = seguimiento_top21(d)["hora_1830"]
    cuerpo_m += ('<p class="note"><b>En observación, sin plata:</b> Top-21 de las 18:30 desde el 30-sep. '
                 + ("Lleva %d de %d (%s %%; empata al 70 %%), neto %+d fichas a 1 por animal. Se juzga a los %d sorteos."
                    % (t21["aciertos"], t21["n"], ("%.1f" % (100 * t21["tasa"])).replace(".", ","), t21["neto_fichas"], TOP21_JUICIO)
                    if t21["n"] else "Aún sin sorteos puntuados.") + '</p>')
    partes.append(_sec("rd-marcador", "Marcador RD", resumen, cuerpo_m))
    # --- evidencia
    partes.append(_sec(
        "rd-evidencia", "Por qué funciona", "prueba ciega · 3.237 sorteos no vistos",
        '<p>RD Internacional casi nunca repite el animal que Lotto Activo acaba de sacar (5 veces menos de lo normal) '
        'ni los que ya salieron hoy en RD. En la prueba ciega (3.237 sorteos no vistos, jul-2025 a abr-2026) el Top-3 '
        'acertó 12,05 %% (equilibrio 10 %%) y el Top-5 escalonado ganó +20 %% por ficha. Es una sola prueba: '
        'confírmalo en este marcador antes de subir la apuesta.</p>'
        '<p class="note">Anotado automático: %s%s.</p>'
        % (_e(ESTADO["mensaje"]), (" · error: " + _e(ESTADO["error"])) if ESTADO["error"] else "")))
    return "".join(partes)
