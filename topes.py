# -*- coding: utf-8 -*-
"""Topes de la taquilla: animales que la agencia limitó o cerró para un sorteo.

Hipótesis (pendiente, sin probar): si el tope refleja lo más jugado, el operador podría esquivar esos
animales (O/E < 1) o, como vio el usuario en 5 ocasiones, salir de más (O/E > 1). Aquí solo se anota y se
cuenta; la prueba se hace cuando haya volumen (≈ 330 animal-sorteos para ver un ×2; ≈ 3.700 para un −30 %).

Cada anotación: {"creado", "fecha", "juego" ("la"|"rd"), "hora" (0..11 = 8:00..19:00 o 8:30..19:30),
"animales" (códigos "0", "00", "1".."36"), "agencia"}. Archivo: <DATOS>/topes.json (lista, escritura atómica).
Las anotadas DESPUÉS del sorteo se guardan pero no cuentan en el O/E (podrían elegirse sabiendo el resultado).
"""
import json
import os
import re
from datetime import datetime

from comun import IDX, K, guardar_json

JUEGOS = ("la", "rd")
MAX_ANIMALES = 10


def cargar(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def leer_animales(texto):
    """'5, 12 00' -> ['5', '12', '00'] (sin repetir, en orden). Devuelve (lista, inválidos)."""
    vistos, malos = [], []
    for t in re.split(r"[\s,;/.-]+", texto or ""):
        if not t:
            continue
        c = t if t in ("0", "00") else t.lstrip("0") or "0"
        if c in IDX:
            if c not in vistos:
                vistos.append(c)
        else:
            malos.append(t)
    return vistos, malos


def anotar(ruta, fecha, juego, hora, texto, agencia="", ahora=None):
    """Valida y guarda una anotación. Devuelve (texto para el aviso, clase)."""
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except (TypeError, ValueError):
        return "Fecha no válida.", "bad"
    if juego not in JUEGOS:
        return "Juego no válido.", "bad"
    if not isinstance(hora, int) or not 0 <= hora <= 11:
        return "Hora no válida.", "bad"
    animales, malos = leer_animales(texto)
    if malos:
        return f"No reconozco: {', '.join(malos[:5])}. Usa 0, 00 o 1–36.", "bad"
    if not animales:
        return "Escribe al menos un animal limitado.", "bad"
    if len(animales) > MAX_ANIMALES:
        return f"Máximo {MAX_ANIMALES} animales por anotación.", "bad"
    d = cargar(ruta)
    d.append({"creado": (ahora or datetime.now()).isoformat(timespec="seconds"), "fecha": fecha, "juego": juego,
              "hora": hora, "animales": animales, "agencia": (agencia or "").strip()[:60]})
    guardar_json(ruta, d, indent=1)
    return f"Tope anotado: {', '.join(animales)} ({len(d)} anotaciones en total).", "ok"


def resumen(entradas, resultado, prob=None, hora_sorteo=None):
    """O/E de los animales con tope.

    resultado(juego, fecha, hora) -> código ganador o None si aún no salió.
    prob(juego, fecha, hora) -> lista de 38 probabilidades del pronóstico congelado, o None (se usa 1/38).
    hora_sorteo(juego, fecha, hora) -> datetime del sorteo; si se da, las anotaciones creadas después no cuentan.
    """
    filas, obs, esp, var, tarde, pend = [], 0, 0.0, 0.0, 0, 0
    for e in entradas:
        try:
            juego, fecha, hora, animales = e["juego"], e["fecha"], int(e["hora"]), list(e["animales"])
        except (KeyError, TypeError, ValueError):
            continue
        gano = resultado(juego, fecha, hora)
        cuenta = True
        if hora_sorteo is not None:
            try:
                cuenta = datetime.fromisoformat(e["creado"]) < hora_sorteo(juego, fecha, hora)
            except (KeyError, TypeError, ValueError):
                cuenta = False
        p = prob(juego, fecha, hora) if prob else None
        if not p or len(p) != K or sum(p) <= 0:
            p = [1.0 / K] * K
        s = float(sum(p))
        masa = sum(p[IDX[a]] for a in animales if a in IDX) / s
        salio = gano is not None and gano in animales
        filas.append({"fecha": fecha, "juego": juego, "hora": hora, "animales": animales, "salio": gano,
                      "acierto": salio, "prob_tope": round(masa, 4), "cuenta": cuenta and gano is not None,
                      "agencia": e.get("agencia", "")})
        if gano is None:
            pend += 1
        elif not cuenta:
            tarde += 1
        else:
            obs += int(salio); esp += masa; var += masa * (1 - masa)
    out = {"anotaciones": len(filas), "resueltas": sum(f["cuenta"] for f in filas), "pendientes": pend,
           "anotadas_tarde": tarde,
           "animal_sorteos": sum(len(f["animales"]) for f in filas if f["cuenta"]),
           "salieron": obs, "esperado": round(esp, 2), "oe": round(obs / esp, 3) if esp > 0 else None,
           "z": round((obs - esp) / var ** 0.5, 2) if var > 0 else None, "filas": filas[-50:][::-1]}
    return out
