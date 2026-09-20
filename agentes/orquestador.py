# -*- coding: utf-8 -*-
"""Orquestador de la competencia de agentes.

Cada sorteo, los 4 agentes (hazard, antirep, markov, momentum) emiten su
top-15. Todos se guardan ANTES de conocer el resultado (mismo registro de
solo-añadir que el ensamble) y al resolverse el sorteo cada agente suma
acierto o fallo a su marcador. La web muestra la tabla de posiciones.

El "capitan" del proximo sorteo es el agente con mejor tasa top-3 (minimo 20
sorteos resueltos; antes de eso, el consenso: votos ponderados de todos).

Honestidad: idem que el ensamble — pronostico congelado en predicciones.json
bajo cada registro, campo "agentes": {nombre: [top15 indices]}.
"""
import importlib
import math
import os
import sys
import threading

# Permite usarlo como paquete (agentes.orquestador desde servidor.py) o en
# plano dentro de agentes/ (los scripts _eval_*).
try:
    from agentes.base import K, POS, cargar_historial  # noqa: F401
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from base import K, POS, cargar_historial  # noqa: F401

AGENTES = ["agente_hazard", "agente_antirep", "agente_markov", "agente_momentum"]
MIN_SORTEOS_CAPITAN = 20
AZAR_T3 = 3.0 / K

_cache_lock = threading.Lock()
_instancias = None
_cache_pred = {}          # clave (n_sorteos, hora_sig) -> {nombre: [top15]}


def _cargar_instancias():
    global _instancias
    with _cache_lock:
        if _instancias is not None:
            return _instancias
        try:
            from agentes.base import Agente                       # paquete
        except ImportError:
            from base import Agente                               # plano
        inst = []
        for nombre in AGENTES:
            try:
                mod = importlib.import_module(nombre)              # plano (scripts)
            except ImportError:
                mod = importlib.import_module("agentes." + nombre)  # paquete (servidor)
            for valor in vars(mod).values():
                if isinstance(valor, type) and issubclass(valor, Agente) and valor is not Agente:
                    inst.append(valor())
                    break
        _instancias = inst
        return inst


def top15_agentes(seq, horas, dweek, hora_sig):
    """Ejecuta los 4 agentes y devuelve {nombre: [top15 indices ordenados]}."""
    clave = (len(seq), hora_sig)
    with _cache_lock:
        if clave in _cache_pred:
            return _cache_pred[clave]
    resultado = {}
    for ag in _cargar_instancias():
        scores = ag.predecir(seq, horas, dweek)
        orden = sorted(range(K), key=lambda i: (-scores[i], i))
        resultado[ag.nombre] = orden[:15]
    with _cache_lock:
        _cache_pred[clave] = resultado
        if len(_cache_pred) > 4:
            _cache_pred.clear()
            _cache_pred[clave] = resultado
    return resultado


def votos_consenso(tops):
    """Combina los top-15 de los agentes: rank 1 da 15 puntos ... rank 15 da 1."""
    total = [0.0] * K
    for top in tops.values():
        for rango, idx in enumerate(top):
            total[idx] += 15 - rango
    return total


def capitan(d, tops):
    """Devuelve (nombre, motivo): que agente lidera la recomendacion hoy."""
    marc = marcador_agentes(d)
    mejores = [m for m in marc if m["n"] >= MIN_SORTEOS_CAPITAN]
    if mejores:
        lider = max(mejores, key=lambda m: (m["t3"] / m["n"], m["n"]))
        return lider["nombre"], "lider del marcador"
    return None, "consenso (aun sin lider, min %d sorteos)" % MIN_SORTEOS_CAPITAN


def marcador_agentes(d):
    """Tasa top-1/top-3 por agente usando solo pronosticos ya resueltos."""
    stats = {}
    for r in d.get("registros", []):
        if r.get("anulado") or r.get("salio") is None or "agentes" not in r:
            continue
        salio = r["salio"]
        for nombre, top in r["agentes"].items():
            s = stats.setdefault(nombre, dict(n=0, t1=0, t3=0, racha=0, ultimo="—"))
            s["n"] += 1
            if salio == top[0]:
                s["t1"] += 1
            if salio in top[:3]:
                s["t3"] += 1
                s["ultimo"] = "acierto"
                s["racha"] = 0
            else:
                s["racha"] += 1
                s["ultimo"] = "fallo"
    filas = []
    for nombre, s in stats.items():
        n = max(1, s["n"])
        filas.append(dict(nombre=nombre, n=s["n"], t1=s["t1"], t3=s["t3"],
                          tasa1=s["t1"] / n * 100, tasa3=s["t3"] / n * 100,
                          racha=s["racha"], ultimo=s["ultimo"]))
    filas.sort(key=lambda m: (-(m["t3"] / max(1, m["n"])), -m["n"]))
    return filas


def bayes_factor_t3(t3, n):
    """Factor de Bayes vs azar con tasa alternativa 12% (la del ensamble en dev)."""
    if n == 0:
        return 1.0
    p1, p0 = 0.1227, AZAR_T3
    lo = 0.0
    lo += t3 * math.log(p1 / p0) + (n - t3) * math.log((1 - p1) / (1 - p0))
    return math.exp(lo)
