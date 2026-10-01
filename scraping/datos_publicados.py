# -*- coding: utf-8 -*-
"""Guarda cada mañana, ANTES del primer sorteo (8:00), las páginas de "datos" que publican los
pronosticadores (pirámide del día, foros, listas de datos). Solo guarda el HTML crudo, sin interpretarlo:
dentro de ~2 meses se extraen los animales recomendados y se prueba si el operador los esquiva
(herramientas/exploracion/top15_70/INFORME.md, §4.2). No toca el historial ni el pronóstico.

Archivos: <DATOS>/datos_publicados/AAAA-MM-DD/<fuente>.html y meta.json (hora de descarga, estado, bytes).
Se descarga una vez por fuente y día, entre las 6:00 y las 7:55 (hora de Caracas).
"""
import json, os, threading, time, urllib.request
from datetime import datetime

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


def carpeta(base, fecha):
    c = os.path.join(base, "datos_publicados", fecha)
    os.makedirs(c, exist_ok=True)
    return c


def pasada(base, ahora=None):
    """Descarga las fuentes que falten hoy si estamos en la ventana. Devuelve lo que hizo."""
    ahora = ahora or datetime.now()
    if not (DESDE <= (ahora.hour, ahora.minute) <= HASTA):
        return {}
    fecha = ahora.date().isoformat(); c = carpeta(base, fecha)
    ruta_meta = os.path.join(c, "meta.json")
    meta = json.load(open(ruta_meta, encoding="utf-8")) if os.path.exists(ruta_meta) else {}
    hecho = {}
    for nombre, url in FUENTES.items():
        if meta.get(nombre, {}).get("ok"):
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "es-VE,es"})
            with urllib.request.urlopen(req, timeout=30) as r:
                crudo = r.read()
            with open(os.path.join(c, nombre + ".html"), "wb") as f:
                f.write(crudo)
            meta[nombre] = {"ok": True, "cuando": ahora.isoformat(timespec="seconds"), "bytes": len(crudo), "url": url}
        except Exception as ex:  # noqa: BLE001  (una fuente caída no frena a las demás)
            meta[nombre] = {"ok": False, "cuando": ahora.isoformat(timespec="seconds"), "error": repr(ex)[:200],
                            "url": url}
        hecho[nombre] = meta[nombre]
    with open(ruta_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return hecho


def resumen(base):
    """{fecha: {fuente: ok}} de los últimos 30 días guardados (para /api/datos_publicados)."""
    raiz = os.path.join(base, "datos_publicados")
    if not os.path.isdir(raiz):
        return {"dias": 0, "ultimos": {}}
    dias = sorted(d for d in os.listdir(raiz) if os.path.isdir(os.path.join(raiz, d)))
    out = {}
    for d in dias[-30:]:
        m = os.path.join(raiz, d, "meta.json")
        meta = json.load(open(m, encoding="utf-8")) if os.path.exists(m) else {}
        out[d] = {k: bool(v.get("ok")) for k, v in meta.items()}
    return {"dias": len(dias), "ultimos": out}


def iniciar(base):
    def bucle():
        while True:
            try:
                pasada(base)
            except Exception as ex:  # noqa: BLE001
                print(f"[datos_publicados] fallo: {ex!r}", flush=True)
            time.sleep(INTERVALO)
    threading.Thread(target=bucle, daemon=True).start()
