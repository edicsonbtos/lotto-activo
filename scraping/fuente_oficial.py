# -*- coding: utf-8 -*-
"""Fuente OFICIAL de resultados: lottoactivo.com (Operadora Juegos Activos).

Por que existe: hasta ahora el resultado se leia de tuazar.com, que es un
espejo. Un espejo siempre publica DESPUES del original, y el 2026-09-20 el
sorteo de las 3:00 PM todavia no estaba en tuazar a las 15:12 (12 min despues
del sorteo), asi que el anotado automatico se rindio y hubo que teclearlo a
mano a las 15:14. Este modulo lee la misma fuente que mira el publico.

Como se lee: la pagina /resultados/animalitos/ no trae los resultados en el
HTML; los pide por AJAX a /core/process.php con tres campos (option, loteria,
fecha). `option` es un token que viene escrito en la propia pagina y cambia en
cada carga, asi que hay que leerlo primero. La respuesta es JSON.

Cuidado con estas cuatro trampas (las cuatro estan cubiertas en
scraping/test_fuente_oficial.py, con respuestas reales guardadas):

  1. La respuesta trae CUATRO loterias a la vez (Lotto Activo, RD
     Internacional, Republica Dominicana y Monje Millonario). La nuestra es
     id_game == "1"; quedarse con otra meteria animales ajenos al historial.
  2. Los nombres vienen acentuados (Aguila, Raton), por eso se comparan sin
     acentos.
  3. El numero viene a veces con cero delante ("09") y a veces no ("0" es
     Delfin y "00" es Ballena). Manda el NOMBRE, no el numero.
  4. La hora viene como "08:00 AM"; el calendario del proyecto la escribe
     "8:00 AM".

Certificado vencido: a 2026-09-20 el certificado TLS de lottoactivo.com esta
caducado, asi que la verificacion normal falla. Se intenta primero verificado
y, si el fallo es ese, se reintenta sin verificar dejandolo dicho en el log.
Aqui no se manda ningun dato propio (solo se leen numeros publicos) y todo lo
que llega se valida contra el tablero de 38 animales antes de usarse, asi que
lo peor que puede colar un intermediario es un resultado falso, que es el
mismo riesgo que ya se corria con el espejo.
"""
import json
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

CARACAS = timezone(timedelta(hours=-4))

BASE = "https://www.lottoactivo.com"
PAGINA = BASE + "/resultados/animalitos/"
API = BASE + "/core/process.php"
JUEGO = "1"                       # Lotto Activo (Venezuela)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")

HORAS = ["8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM",
         "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM", "6:00 PM", "7:00 PM"]
POS = ["0", "00"] + [str(i) for i in range(1, 37)]
IDX = {p: i for i, p in enumerate(POS)}

# nombre sin acentos -> codigo del tablero. "0" DELFIN y "00" BALLENA solo se
# distinguen por el nombre.
ANIMALES = {
    "DELFIN": "0", "BALLENA": "00", "CARNERO": "1", "TORO": "2", "CIEMPIES": "3",
    "ALACRAN": "4", "LEON": "5", "RANA": "6", "PERICO": "7", "RATON": "8",
    "AGUILA": "9", "TIGRE": "10", "GATO": "11", "CABALLO": "12", "MONO": "13",
    "PALOMA": "14", "ZORRO": "15", "OSO": "16", "PAVO": "17", "BURRO": "18",
    "CHIVO": "19", "COCHINO": "20", "GALLO": "21", "CAMELLO": "22", "CEBRA": "23",
    "IGUANA": "24", "GALLINA": "25", "VACA": "26", "PERRO": "27", "ZAMURO": "28",
    "ELEFANTE": "29", "CAIMAN": "30", "LAPA": "31", "ARDILLA": "32", "PESCADO": "33",
    "VENADO": "34", "JIRAFA": "35", "CULEBRA": "36",
}

VIDA_TOKEN = 10 * 60              # el token se recicla 10 min y luego se repide
_token = {"valor": None, "hasta": 0.0}
_aviso = {"cert": False}          # avisos que solo valen la pena una vez


def log(msg):
    ahora = datetime.now(CARACAS).isoformat(timespec="seconds")
    sys.stderr.write("[oficial] %s %s\n" % (ahora, msg))
    sys.stderr.flush()


def hoy_iso():
    return datetime.now(CARACAS).date().isoformat()


def sin_acentos(txt):
    """AGUILA a partir de 'Aguila', 'AGUILA' acentuada o ' aguila '."""
    plano = unicodedata.normalize("NFD", txt.upper())
    return re.sub(r"[^A-Z]", "", plano)


def codigo_de(numero, nombre):
    """(codigo, nombre bonito) o (None, None) si no es del tablero."""
    cod = ANIMALES.get(sin_acentos(nombre or ""))
    if cod is None:                       # respaldo por numero, si trae uno util
        num = (numero or "").strip()
        if num in IDX:
            cod = num
        elif num.lstrip("0") in IDX:      # "09" -> "9"
            cod = num.lstrip("0")
    if cod is None:
        return None, None
    return cod, (nombre or "").strip().title()


def parse(js, fecha):
    """JSON de /core/process.php -> {(fecha ISO, h): (codigo, animal)}."""
    out = {}
    if not isinstance(js, dict):
        return out
    for juego in js.get("datos") or []:
        if str(juego.get("id")) != JUEGO:
            continue                      # otra loteria: no es la nuestra
        for r in juego.get("resultados") or []:
            hora = str(r.get("time_s", "")).strip().lstrip("0")
            if hora not in HORAS:
                continue                  # sorteo fuera del calendario de 12
            cod, nombre = codigo_de(r.get("number_animal"), r.get("name_animal"))
            if cod:
                out[(fecha, HORAS.index(hora))] = (cod, nombre)
    return out


# ------------------------------------------------------------------- red
def _abrir(req, timeout=30):
    """urlopen verificando el certificado; si esta vencido, sin verificar."""
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.URLError as e:
        if not isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError):
            raise
        if not _aviso["cert"]:          # una vez por arranque, no en cada peticion
            _aviso["cert"] = True
            log("certificado de lottoactivo.com invalido (%s); se sigue sin "
                "verificar: los numeros se validan igual contra el tablero"
                % e.reason.verify_message)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return urllib.request.urlopen(req, timeout=timeout, context=ctx)


def token(refrescar=False):
    """El campo `option` que la pagina escribe en su propio JavaScript."""
    if not refrescar and _token["valor"] and time.time() < _token["hasta"]:
        return _token["valor"]
    req = urllib.request.Request(PAGINA, headers={"User-Agent": UA})
    with _abrir(req) as r:
        html = r.read().decode("utf-8", "replace")
    m = re.search(r"""['"]option['"]\s*:\s*['"]([^'"]+)['"]""", html)
    if not m:
        raise ValueError("no se encontro el token `option` en %s "
                         "(cambio la pagina?)" % PAGINA)
    _token["valor"] = m.group(1)
    _token["hasta"] = time.time() + VIDA_TOKEN
    return _token["valor"]


def _pedir(fecha, tok):
    cuerpo = urllib.parse.urlencode(
        {"option": tok, "loteria": "animalitos", "fecha": fecha}).encode()
    req = urllib.request.Request(API, data=cuerpo, headers={
        "User-Agent": UA,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": PAGINA})
    with _abrir(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def resultados(fecha, intentos=2):
    """Resultados de ese dia, o None si la fuente no responde.

    {} (vacio) significa "la fuente contesto y ese dia no tiene nada todavia",
    que no es lo mismo que None ("no se pudo preguntar"): quien llama decide.
    """
    for i in range(intentos):
        try:
            return parse(_pedir(fecha, token(refrescar=i > 0)), fecha)
        except Exception as e:  # noqa: BLE001
            log("fallo al pedir %s (intento %d): %r" % (fecha, i + 1, e))
            time.sleep(3 * (i + 1))
    return None


if __name__ == "__main__":
    f = sys.argv[1] if len(sys.argv) > 1 else hoy_iso()
    r = resultados(f)
    if r is None:
        print("la fuente oficial no respondio")
        sys.exit(1)
    print("%s: %d sorteos" % (f, len(r)))
    for (_, h), (cod, nombre) in sorted(r.items()):
        print("  %-8s %-3s %s" % (HORAS[h], cod, nombre))
