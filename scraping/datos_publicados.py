# -*- coding: utf-8 -*-
"""Guarda cada mañana, ANTES del primer sorteo (8:00), las páginas de "datos" que publican los
pronosticadores (pirámide del día, foros, listas de datos). Solo guarda el HTML crudo, sin interpretarlo:
dentro de ~2 meses se extraen los animales recomendados y se prueba si el operador los esquiva
(herramientas/exploracion/top15_70/INFORME.md, §4.2). No toca el historial ni el pronóstico.

Archivos: <DATOS>/datos_publicados/AAAA-MM-DD/<fuente>.html y meta.json (hora de descarga, estado, bytes).
Se descarga una vez por fuente y día, entre las 6:00 y las 7:55 (hora de Caracas).

Endurecido tras la revisión de seguridad/código (2026-10-01): tope de tamaño, redirecciones solo a https
del mismo dominio, meta.json atómico y tolerante a corrupción, máximo de intentos por fuente y poda de
carpetas viejas para no llenar el volumen donde vive el marcador.
"""
import json, os, shutil, threading, time, urllib.error, urllib.request
from datetime import datetime, timedelta
from urllib.parse import urlparse

FUENTES = {
    "tuazar_piramide": "https://www.tuazar.com/loteria/animalitos/datos/lapiramidedehoy/",
    "juegoactivo_piramide": "https://juegoactivo.com/datos/animalitos/la-piramide-de-hoy",
    "juegoactivo_datos_lotto": "https://juegoactivo.com/datos/lotto-activo",
    "loteriadehoy_datos": "https://loteriadehoy.com/datos/animalitos/",
    "lotoven_datos": "https://lotoven.com/datos/",
    "grupo_sortario_foro": "https://elgruposortario.mforos.com/2147714/",
}
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Mobile Safari/537.36"
DESDE, HASTA = (6, 0), (7, 55)
INTERVALO = 300
MAX_BYTES = 3_000_000          # una página de datos pesa 0,3-1 MB; más que esto se trata como fallo
MIN_BYTES = 2_000              # menos que esto es una página vacía o de bloqueo, no datos
MAX_INTENTOS = 3               # por fuente y día (evita ~24 golpes a un sitio caído)
RETENCION_DIAS = 90


class _MismoDominioHttps(urllib.request.HTTPRedirectHandler):
    """Solo sigue redirecciones https dentro del mismo dominio (sin saltos a hosts internos ni http)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        a, b = urlparse(req.full_url), urlparse(newurl)
        if b.scheme != "https" or b.hostname is None or a.hostname is None:
            return None
        base = lambda h: ".".join(h.lower().split(".")[-2:])
        if base(a.hostname) != base(b.hostname):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_ABRIR = urllib.request.build_opener(_MismoDominioHttps()).open


def carpeta(base, fecha):
    c = os.path.join(base, "datos_publicados", fecha)
    os.makedirs(c, exist_ok=True)
    return c


def _leer_meta(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            m = json.load(f)
        return m if isinstance(m, dict) else {}
    except (OSError, ValueError):
        return {}


def _guardar_meta(ruta, meta):
    with open(ruta + ".tmp", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    os.replace(ruta + ".tmp", ruta)


def _descargar(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "es-VE,es"})
    with _ABRIR(req, timeout=30) as r:
        if getattr(r, "status", 200) != 200:
            raise OSError(f"HTTP {r.status}")
        crudo = r.read(MAX_BYTES + 1)
    if len(crudo) > MAX_BYTES:
        raise OSError(f"respuesta de más de {MAX_BYTES} bytes")
    if len(crudo) < MIN_BYTES:
        raise OSError(f"respuesta de solo {len(crudo)} bytes (¿página vacía o de bloqueo?)")
    return crudo


def pasada(base, ahora=None):
    """Descarga las fuentes que falten hoy si estamos en la ventana. Devuelve lo que hizo."""
    ahora = ahora or datetime.now()
    if not (DESDE <= (ahora.hour, ahora.minute) <= HASTA):
        return {}
    fecha = ahora.date().isoformat(); c = carpeta(base, fecha)
    ruta_meta = os.path.join(c, "meta.json")
    meta = _leer_meta(ruta_meta)
    hecho = {}
    for nombre, url in FUENTES.items():
        previo = meta.get(nombre, {})
        if previo.get("ok") or previo.get("intentos", 0) >= MAX_INTENTOS:
            continue
        intentos = previo.get("intentos", 0) + 1
        try:
            crudo = _descargar(url)
            with open(os.path.join(c, nombre + ".html"), "wb") as f:
                f.write(crudo)
            meta[nombre] = {"ok": True, "cuando": ahora.isoformat(timespec="seconds"), "bytes": len(crudo),
                            "url": url, "intentos": intentos}
        except Exception as ex:  # noqa: BLE001  (una fuente caída no frena a las demás)
            meta[nombre] = {"ok": False, "cuando": ahora.isoformat(timespec="seconds"), "error": repr(ex)[:200],
                            "url": url, "intentos": intentos}
        hecho[nombre] = meta[nombre]
        _guardar_meta(ruta_meta, meta)      # tras cada fuente: un deploy a mitad no pierde lo ya bajado
    return hecho


def podar(base, hoy=None):
    """Borra las carpetas de más de RETENCION_DIAS (el volumen es finito y se comparte con el marcador)."""
    raiz = os.path.join(base, "datos_publicados")
    if not os.path.isdir(raiz):
        return 0
    limite = ((hoy or datetime.now()).date() - timedelta(days=RETENCION_DIAS)).isoformat()
    n = 0
    for d in os.listdir(raiz):
        ruta = os.path.join(raiz, d)
        if os.path.isdir(ruta) and len(d) == 10 and d < limite:
            shutil.rmtree(ruta, ignore_errors=True); n += 1
    return n


def resumen(base):
    """{fecha: {fuente: ok}} de los últimos 30 días guardados (para /api/datos_publicados)."""
    raiz = os.path.join(base, "datos_publicados")
    if not os.path.isdir(raiz):
        return {"dias": 0, "ultimos": {}}
    dias = sorted(d for d in os.listdir(raiz) if os.path.isdir(os.path.join(raiz, d)))
    out = {}
    for d in dias[-30:]:
        meta = _leer_meta(os.path.join(raiz, d, "meta.json"))
        out[d] = {k: bool(v.get("ok")) for k, v in meta.items() if isinstance(v, dict)}
    return {"dias": len(dias), "ultimos": out}


def iniciar(base):
    def bucle():
        while True:
            try:
                pasada(base)
                podar(base)
            except Exception as ex:  # noqa: BLE001
                print(f"[datos_publicados] fallo: {ex!r}", flush=True)
            time.sleep(INTERVALO)
    threading.Thread(target=bucle, daemon=True).start()
