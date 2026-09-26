# -*- coding: utf-8 -*-
"""ag07 V1 congelado: log-lineal de intradia_v2 + secuencia_v3 + haz_v1 + recencia con pesos que dependen
del contexto (k del día, repeticiones del día, dispersión). Parámetros en parametros.json (filas [1000, 9357))."""
import os, sys, json, importlib.util
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import nucleo as N  # noqa
MOD = os.path.join(os.path.dirname(os.path.dirname(AQUI)), "herramientas", "modelos")


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(MOD, nombre + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.Modelo()


class Modelo:
    nombre = "ag07_mezcla_expertos_V1"

    def __init__(self, ruta=os.path.join(AQUI, "parametros.json")):
        p = json.load(open(ruta, encoding="utf-8"))
        self.expertos = p["expertos"]; self.W = np.array(p["W"])

    def predecir(self, datos, desde):
        n = len(datos)
        repo = [e for e in self.expertos if e != "recencia"]
        Lrepo = np.stack([N.lognorm(_cargar(e).predecir(datos, desde)) for e in repo], 1)   # (n-desde, 3, 38)
        Lrec = N.lognorm(N.recencia(datos.seq)[desde:])[:, None, :]
        pad = np.zeros((desde, len(repo), 38))
        X = N.contexto(datos.seq, datos.dia, np.concatenate([pad, Lrepo], 0))[desde:]
        return N.predecir_loglineal(np.concatenate([Lrepo, Lrec], 1), X, self.W)
