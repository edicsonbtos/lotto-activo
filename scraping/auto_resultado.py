# -*- coding: utf-8 -*-
"""Auto-resultado: busca el resultado de cada sorteo en la fuente publica y lo
anota solo, con el MISMO codigo del boton manual (servidor.registrar), unos
10 minutos despues de la hora del sorteo. No hay que teclear nada.

Honestidad: el pronostico del slot ya quedo guardado como pendiente ANTES de
que este script mirara el resultado (igual que el registro manual), asi que el
marcador sigue midiendo pronosticos hechos a ciegas.

Fuentes (tuazar, en este orden):
  1. Tabla SEMANAL (`.../resultados/anteriores/?d=AAAA-MM-DD`): trae lun-dom con
     la fecha en cada columna. Es la fuente principal porque permite recuperar
     dias atrasados sin ambiguedad.
  2. Portada (`.../resultados/`): solo la jornada de hoy, sin fecha en la
     casilla. Se usa como respaldo para el sorteo recien salido, por si la
     tabla semanal va con retraso.

Orden estricto: los sorteos se anotan del mas viejo al mas nuevo y solo si el
servidor espera exactamente ese slot; servidor.registrar() siempre llena el
primer hueco, asi que saltarse uno pondria el animal en la hora equivocada.

Uso:
  python scraping/auto_resultado.py            # una pasada (la usa el planificador)
  python scraping/auto_resultado.py --demo     # dice que haria, sin anotar nada

El planificador vive en servidor.py (hilo daemon `auto_bucle`) y llama a
una_pasada() cada 5 minutos en horario de sorteo; la web tiene ademas el boton
"Buscar resultado ahora". Todo se loguea a stderr (visible en Railway).
"""
import os
import re
import sys
import time

# Todo el calendario de sorteos es hora de Caracas (UTC-4, sin DST), igual que
# servidor.py. En vez de depender de la zona del sistema, se calcula con UTC
# real menos 4 h: deterministico en Windows, Railway y cualquier contenedor.
from datetime import date, datetime, timedelta, timezone
CARACAS = timezone(timedelta(hours=-4))

RUTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RUTA)

HORAS = ["8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM",
         "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM", "6:00 PM", "7:00 PM"]
# La fuente publica el resultado ~10 min despues de la hora del sorteo; se
# consulta a partir de ahi y se reintenta en cada pasada hasta que aparezca.
ESPERA_TRAS_SORTEO = 10 * 60
MAX_POR_PASADA = 60            # tope de sorteos a recuperar de una sola vez
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")

POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}

# animales tal como los escribe tuazar (mayusculas, sin acentos) -> codigo POS.
# El nombre manda sobre el numero: es lo unico que distingue "0" DELFIN de
# "00" BALLENA cuando la fuente escribe el numero sin el cero de adelante.
A_TZ = {
    "DELFIN": "0", "BALLENA": "00", "CARNERO": "1", "TORO": "2", "CIEMPIES": "3",
    "ALACRAN": "4", "LEON": "5", "RANA": "6", "PERICO": "7", "RATON": "8",
    "AGUILA": "9", "TIGRE": "10", "GATO": "11", "CABALLO": "12", "MONO": "13",
    "PALOMA": "14", "ZORRO": "15", "OSO": "16", "PAVO": "17", "BURRO": "18",
    "CHIVO": "19", "COCHINO": "20", "GALLO": "21", "CAMELLO": "22", "CEBRA": "23",
    "IGUANA": "24", "GALLINA": "25", "VACA": "26", "PERRO": "27", "ZAMURO": "28",
    "ELEFANTE": "29", "CAIMAN": "30", "LAPA": "31", "ARDILLA": "32", "PESCADO": "33",
    "VENADO": "34", "JIRAFA": "35", "CULEBRA": "36",
}


def log(msg):
    ahora = datetime.now(CARACAS).isoformat(timespec="seconds")
    sys.stderr.write("[auto] %s %s\n" % (ahora, msg))
    sys.stderr.flush()


def servidor_vivo():
    """El modulo servidor YA cargado, no una segunda copia.

    Cuando el servidor corre como script vive en sys.modules['__main__']; un
    `import servidor` a secas volveria a ejecutar el archivo, con su propio
    cache del modelo y su propio estado.
    """
    for clave in ("servidor", "__main__"):
        m = sys.modules.get(clave)
        if m is not None and hasattr(m, "registrar") and hasattr(m, "estado"):
            return m
    import servidor  # ejecucion suelta desde la linea de comandos
    return servidor


# ---------------------------------------------------------------- descarga
def bajar(url, intentos=3):
    """Descarga una pagina de tuazar. Devuelve el HTML o None.

    urllib con User-Agent de navegador basta (probado 2026-09-20). Si el sitio
    empieza a filtrar, scrapling (ya usado en scraping/core.py) toma el relevo
    cuando esta instalado.
    """
    for i in range(intentos):
        try:
            try:
                from scrapling import Fetcher
                page = Fetcher.get(url, stealthy_headers=True, timeout=45)
                html = page.body.decode("utf-8", "replace")
                if page.status == 200 and len(html) > 20000:
                    return html
                log("tuazar HTTP %s (%d bytes), reintento %d" % (page.status, len(html), i + 1))
            except ImportError:
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=45) as r:
                    html = r.read().decode("utf-8", "replace")
                if len(html) > 20000:
                    return html
                log("tuazar respuesta corta (%d bytes), reintento %d" % (len(html), i + 1))
        except Exception as e:  # noqa: BLE001
            log("fallo al bajar %s (intento %d): %r" % (url, i + 1, e))
        time.sleep(5 * (i + 1))
    return None


# ---------------------------------------------------------------- parseo
def _codigo(num_txt, animal_txt):
    """(codigo POS, nombre bonito) o (None, None) si no se reconoce."""
    animal_n = re.sub(r"[^A-Z]", "", animal_txt.upper())
    codigo = A_TZ.get(animal_n)
    if codigo is None:
        num = num_txt.strip()
        codigo = num if num in IDX else None
    if codigo is None:
        return None, None
    return codigo, animal_txt.strip().title()


RE_DIA = re.compile(r'lw-day-num">(\d{2})/(\d{2})/(\d{4})')
RE_FILA = re.compile(r"<tr>(.*?)</tr>", re.S)
RE_HORA = re.compile(r'lw-time"[^>]*>([^<]+)<')
RE_CELDA = re.compile(r"<td\b[^>]*>(.*?)</td>", re.S)
RE_ANIMAL = re.compile(r'lw-animal-num">\s*([^<]*?)\s*</span>\s*'
                       r'<span class="lw-animal">\s*([^<]+?)\s*</span>', re.S)


def _seccion_lotto(html):
    """Trozo de HTML de la tarjeta 'Lotto Activo' (hay varias loterias)."""
    i = html.find('<h3 class="lw-title">Lotto Activo</h3>')
    if i < 0:
        return ""
    j = html.find('<div class="lw-card"', i)
    return html[i:j if j > i else len(html)]


def parse_semana(html):
    """Tabla semanal -> {(fecha ISO, h): (codigo, animal)}."""
    sec = _seccion_lotto(html)
    if not sec:
        return {}
    dias = ["%s-%s-%s" % (a, m, d) for d, m, a in RE_DIA.findall(sec)]
    if not dias:
        return {}
    out = {}
    for fila in RE_FILA.findall(sec):
        mh = RE_HORA.search(fila)
        if not mh or mh.group(1).strip() not in HORAS:
            continue
        h = HORAS.index(mh.group(1).strip())
        for i, celda in enumerate(RE_CELDA.findall(fila)):
            if i >= len(dias):
                break
            ma = RE_ANIMAL.search(celda)
            if not ma:
                continue                      # casilla vacia: sorteo sin publicar
            codigo, animal = _codigo(ma.group(1), ma.group(2))
            if codigo:
                out[(dias[i], h)] = (codigo, animal)
    return out


RE_PORTADA = re.compile(
    r'lc-tile-time">([^<]+)</div><div class="lc-tile-label">'
    r'<span class="lc-tile-num">([^<]*)</span>'
    r'<span class="lc-tile-animal">([^<]+)</span>')


def parse_portada(html, fecha):
    """Portada (solo la jornada de hoy) -> {(fecha, h): (codigo, animal)}."""
    i = html.find('<h3 class="lc-title">LOTTO ACTIVO</h3>')
    if i < 0:
        return {}
    j = html.find("lc-head", i + 100)
    sec = html[i:j if j > i else i + 12000]
    out = {}
    for hora_txt, num, animal in RE_PORTADA.findall(sec):
        hora_txt = hora_txt.strip()
        if hora_txt not in HORAS:
            continue
        codigo, nombre = _codigo(num, animal)
        if codigo:
            out[(fecha, HORAS.index(hora_txt))] = (codigo, nombre)
    return out


# ------------------------------------------------------- calendario y pasada
def lunes(d):
    return d - timedelta(days=d.weekday())


def slots_pendientes(servidor, ahora=None):
    """Slots (fecha ISO, h) que faltan por anotar, del mas viejo al mas nuevo.

    Arranca donde el servidor espera llenar (su primer hueco) y avanza por el
    calendario hasta el ultimo sorteo cuya hora + ESPERA_TRAS_SORTEO ya paso.
    """
    ahora = ahora or datetime.now(CARACAS)
    e = servidor.estado(servidor.cargar())
    f, h = e["pf"], e["ph"]
    pend = []
    while len(pend) < MAX_POR_PASADA:
        cuando = datetime.combine(date.fromisoformat(f), datetime.min.time(),
                                  tzinfo=CARACAS) + timedelta(hours=8 + h)
        if ahora < cuando + timedelta(seconds=ESPERA_TRAS_SORTEO):
            break
        pend.append((f, h))
        f, h = servidor.siguiente(f, h)
    return pend


def una_pasada(demo=False):
    """Busca los resultados que faltan y los anota en orden. Devuelve cuantos."""
    servidor = servidor_vivo()
    pend = slots_pendientes(servidor)
    if not pend:
        log("al dia: no falta ningun resultado")
        return 0
    log("faltan %d: %s%s" % (len(pend),
                             ", ".join("%s %s" % (f, HORAS[h]) for f, h in pend[:4]),
                             " …" if len(pend) > 4 else ""))

    hoy = datetime.now(CARACAS).date().isoformat()
    cache_semana, portada = {}, None

    def buscar(f, h):
        """Resultado del slot, de la tabla semanal o (respaldo) de la portada."""
        nonlocal portada
        sem = lunes(date.fromisoformat(f)).isoformat()
        if sem not in cache_semana:
            html = bajar("https://tuazar.com/loteria/animalitos/resultados/"
                         "anteriores/?d=" + f)
            cache_semana[sem] = parse_semana(html) if html else {}
            if html and not cache_semana[sem]:
                log("semana %s: parseo vacio, ¿cambio el HTML de tuazar?" % sem)
        r = cache_semana[sem].get((f, h))
        if r is None and f == hoy:
            if portada is None:
                html = bajar("https://tuazar.com/loteria/animalitos/resultados/")
                portada = parse_portada(html, hoy) if html else {}
            r = portada.get((f, h))
        return r

    anotados = 0
    for f, h in pend:
        r = buscar(f, h)
        if r is None:
            log("%s %s todavia no esta publicado; se reintenta luego" % (f, HORAS[h]))
            break          # nunca saltarse un slot: se anotaria en la hora equivocada
        codigo, animal = r
        # Cinturon de seguridad: el hueco que el servidor va a llenar tiene que
        # ser exactamente este (reloj corrido, jornada corta, edicion a mano).
        # En demo no se escribe, asi que el hueco no avanza: solo se comprueba
        # el primero.
        e = servidor.estado(servidor.cargar())
        if (e["pf"], e["ph"]) != (f, h) and not (demo and anotados):
            log("DESFASE: el servidor espera %s h%d y tocaba %s h%d; no se anota "
                "nada (revisalo a mano)" % (e["pf"], e["ph"], f, h))
            break
        if demo:
            log("[demo] anotaria %s %s -> %s %s" % (f, HORAS[h], codigo, animal))
            anotados += 1
            continue
        texto, _clase = servidor.registrar(codigo)
        log("ANOTADO %s %s -> %s %s | %s" % (f, HORAS[h], codigo, animal,
                                             re.sub(r"<[^>]+>", "", texto)))
        anotados += 1
    return anotados


if __name__ == "__main__":
    n = una_pasada(demo="--demo" in sys.argv)
    print("anotados: %d" % n)
