# -*- coding: utf-8 -*-
"""Nucleo de scraping multi-loteria con Scrapling.

Fuentes:
  - loteriadehoy.com (LH): tabla semanal por loteria (POST fecha=ini/fin).
    Devuelve ANIMALES por hora (sin numero).
  - tuazar.com (TZ): semana completa de TODAS las loterias (?d=fecha).
    Devuelve NUMERO + ANIMAL por celda.

Independencia: LH y lotoven.com comparten datos (misma BD, verificado) -> se
cuentan como UNA sola fuente. tuazar es independiente. Arbitros oficiales:
selvaplus.com, guacharoactivo.com.ve.

Todo lo descargado se cachea en datos_multiloteria/crudos/<fuente>/ para
auditoria y re-parseo sin volver a golpear los sitios.
"""
import io
import json
import os
import re
import time
import unicodedata
from datetime import date, timedelta

from scrapling import Fetcher, Selector

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRUDOS = os.path.join(RAIZ, "datos_multiloteria", "crudos")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")

MIN_INTERVALO = 2.4          # segundos minimos entre requests (mision: 1 req/2s)
ULTIMA_REQ = {"t": 0.0}

# ---------------------------------------------------------------- utilidades

def norm(txt):
    """Normaliza nombre de animal: mayusculas, sin acentos, sin espacios."""
    if not txt:
        return ""
    t = unicodedata.normalize("NFKD", txt)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^A-Z0-9]", "", t.upper())
    return t


# Aliases observados entre fuentes (LH usa otro nombre que tuazar para el
# mismo numero). Se ampliaran de forma documentada si aparecen mas.
ALIAS_A_TZ = {
    "CERDO": "COCHINO",   # La Granjita tuazar dice CERDO; LH dice Cochino
    "CABRA": "CHIVO",     # La Granjita tuazar dice CABRA; LH dice Chivo
    "CARPA": "PESCADO",   # posible: La Granjita usa CARPA donde LH usa Pescado
    "ZEBRA": "CEBRA",     # LH (La Granjita) escribe ZEBRA; tuazar CEBRA
}


def norm_animal(txt):
    n = norm(txt)
    return ALIAS_A_TZ.get(n, n)


def esperar():
    dt = time.time() - ULTIMA_REQ["t"]
    if dt < MIN_INTERVALO:
        time.sleep(MIN_INTERVALO - dt)
    ULTIMA_REQ["t"] = time.time()


def cache_ruta(fuente, nombre):
    d = os.path.join(CRUDOS, fuente)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, nombre)


def leer_cache(fuente, nombre):
    p = cache_ruta(fuente, nombre)
    if os.path.exists(p):
        with io.open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    return None


def guardar_cache(fuente, nombre, html):
    with io.open(cache_ruta(fuente, nombre), "w", encoding="utf-8") as f:
        f.write(html)


def fetch(url, fuente, nombre_cache, method="GET", data=None, params=None,
          reintentos=3, usar_cache=True):
    """Descarga con Scrapling (curl_cffi), cache en disco y rate limit."""
    if usar_cache:
        c = leer_cache(fuente, nombre_cache)
        if c is not None:
            return c
    ultimo = None
    for i in range(reintentos):
        try:
            esperar()
            if method == "POST":
                page = Fetcher.post(url, data=data, headers={"User-Agent": UA},
                                    stealthy_headers=True, timeout=45)
            else:
                page = Fetcher.get(url, params=params,
                                   headers={"User-Agent": UA},
                                   stealthy_headers=True, timeout=45)
            html = page.body.decode("utf-8", errors="replace")
            if page.status != 200 or len(html) < 2000:
                ultimo = "HTTP %s, %d bytes" % (page.status, len(html))
                time.sleep(3 * (i + 1))
                continue
            guardar_cache(fuente, nombre_cache, html)
            return html
        except Exception as e:  # noqa: BLE001
            ultimo = repr(e)
            time.sleep(4 * (i + 1))
    raise RuntimeError("fallo fetch %s: %s" % (url, ultimo))


# ------------------------------------------------------------------ semanas

def lunes(d):
    return d - timedelta(days=d.weekday())


def semana_rango(ini):
    """ini debe ser lunes. Devuelve (lunes, domingo) de esa semana."""
    assert ini.weekday() == 0
    return ini, ini + timedelta(days=6)


def semanas_entre(ini, fin):
    d = lunes(ini)
    out = []
    while d <= fin:
        out.append(d)
        d += timedelta(days=7)
    return out


# ------------------------------------------------------------ parser LoteriaDeHoy

RE_IMG_ANIMAL = re.compile(r"animals_img/([A-Za-z]+)_2\.webp")


def parse_lh_semana(html, slug):
    """Tabla semanal LH -> filas {fecha, hora, animal, fuente}."""
    sel = Selector(html)
    tabla = sel.css("table.table-semanal") or sel.css("table#table")
    if not tabla:
        return []
    tabla = tabla[0]
    fechas = []
    for th in tabla.css("thead th")[1:]:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", th.get() or "")
        fechas.append(m.group(1) if m else None)
    filas = []
    for tr in tabla.css("tbody tr"):
        celdas = tr.css("th, td")
        if not celdas:
            continue
        hora_txt = (celdas[0].get() or "").strip()
        m = re.search(r"(\d{1,2}):(\d{2})\s*([AP]M)", hora_txt, re.I)
        if not m:
            continue
        hh = int(m.group(1)) % 12 + (12 if m.group(3).upper() == "PM" else 0)
        hora = "%02d:%02d" % (hh, int(m.group(2)))
        for i, td in enumerate(celdas[1:]):
            if i >= len(fechas) or not fechas[i]:
                continue
            txt = (td.get() or "").strip()
            if not txt:
                continue
            mimg = RE_IMG_ANIMAL.search(txt)
            animal = mimg.group(1) if mimg else re.sub(r"<[^>]+>", "", txt).strip()
            if not animal:
                continue
            filas.append({
                "fecha": fechas[i], "hora": hora, "animal": animal,
                "n_sorteo_dia": None, "fuente": "loteriadehoy",
                "loteria": slug,
            })
    return filas


def lh_historico(slug, ini, fin):
    url = "https://www.loteriadehoy.com/animalito/%s/historico/" % slug
    rango = "%s/%s" % (ini.isoformat(), fin.isoformat())
    html = fetch(url, "loteriadehoy", "%s__%s.html" % (slug, rango.replace("/", "_")),
                 method="POST", data={"fecha": rango})
    return parse_lh_semana(html, slug)


# ---------------------------------------------------------------- parser tuazar

# nombre de tabla tuazar -> slug nuestro (se compara ya normalizado)
TZ_A_SLUG = {norm(k): v for k, v in {
    "Lotto Activo": "lottoactivo",
    "Lotto Activo RD Internacional": "lottoactivordint",
    "La Granjita": "lagranjita",
    "Selva Plus": "selvaplus",
    "Guacharo Activo": "guacharoactivo",
    "Loto Chaima": "lotochaima",
    "Monje Millonario": "lottoactivo2(monjemillonario)",
    "El Guacharito Millonario": "elguacharitomillonario",
    "Mega Animal 40": "megaanimal40",
    "Ruleta Royal": "ruletaroyal",
    "Gatazo": "gatazo",
    "Lotto Gato": "lottogato",
    "Jungla Dinamica": "jungladinamica",
    "Animalitos del Oriente - Bichitos": "adobichitos",
    "Animalitos del Oriente - Fieras": "adofieras",
    "Animalitos del Oriente - Mascotas": "adomascotas",
    "Chance Con Animalitos A": "chancea",
    "Chance Con Animalitos B": "chanceb",
    "El Arrejuntao": "elarrejuntao",
    "Tropi Gana": "tropigana",
    "Triple Popular": "triplepopular",
}.items()}

FECHA_TZ = re.compile(r"(\d{2}/\d{2}/\d{4})")


def _hora24(txt):
    m = re.search(r"(\d{1,2}):(\d{2})\s*([AP]M)", txt or "", re.I)
    if not m:
        return None
    hh = int(m.group(1)) % 12 + (12 if m.group(3).upper() == "PM" else 0)
    return "%02d:%02d" % (hh, int(m.group(2)))


def parse_tuazar_semana(html, solo_slugs=None):
    """Semana tuazar -> filas {fecha, hora, numero, animal, loteria, fuente}."""
    sel = Selector(html)
    filas = []
    for tabla in sel.css("table"):
        dias = []
        for th in tabla.css("thead th.lw-day"):
            m = FECHA_TZ.search(th.get() or "")
            if m:
                dd, mm, aa = m.group(1).split("/")
                dias.append("%s-%s-%s" % (aa, mm, dd))
            else:
                dias.append(None)
        if not dias:
            continue
        for tr in tabla.css("tbody tr"):
            celdas = tr.css("th, td")
            if len(celdas) < 3:
                continue
            hora = _hora24(celdas[0].get())
            juego = norm(re.sub(r"<[^>]+>", "", celdas[1].get() or ""))
            slug = TZ_A_SLUG.get(juego)
            if not slug:
                continue
            if solo_slugs and slug not in solo_slugs:
                continue
            for i, td in enumerate(celdas[2:]):
                if i >= len(dias) or not dias[i]:
                    continue
                txt = td.get() or ""
                if "lw-animal-cell" not in txt and not txt.strip():
                    continue
                m = re.search(r'alt="(\d{1,3})\s+([^"]+?)"', txt)
                num_s, animal = (m.group(1), m.group(2)) if m else (None, None)
                if num_s is None:
                    m2 = re.search(
                        r'lw-animal-num">\s*(\d{1,3})\s*<.*?lw-animal">\s*([^<]+?)<',
                        txt, re.S)
                    if m2:
                        num_s, animal = m2.group(1), m2.group(2)
                if num_s is None or not animal:
                    continue
                filas.append({
                    "fecha": dias[i], "hora": hora,
                    "numero": int(num_s), "animal": animal.strip(),
                    "loteria": slug, "n_sorteo_dia": None,
                    "fuente": "tuazar",
                })
    return filas


def tuazar_semana(d):
    """d: cualquier fecha de la semana; tuazar devuelve lun-dom."""
    url = "https://tuazar.com/loteria/animalitos/resultados/anteriores/"
    return fetch(url, "tuazar", "semana_%s.html" % lunes(d).isoformat(),
                 params={"d": d.isoformat()})
