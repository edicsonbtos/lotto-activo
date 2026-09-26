# -*- coding: utf-8 -*-
"""ag04_no_estacionario / V1: ensamble_v2 con pesos seguidos por un filtro de Kalman (paseo aleatorio,
actualización de Laplace sorteo a sorteo). Submodelos del repo (herramientas/modelos) walk-forward desde
`arranque`; q y s0 congelados en parametros.json (elegidos solo con filas < 9357).
La fila j usa solo datos[:desde+j]. Vale para jornadas de 11 o 12 sorteos (no depende del nº de sorteos)."""
import importlib.util, json, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
import nucleo as N  # noqa: E402


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(RAIZ, "herramientas", "modelos", nombre + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.Modelo()


class Modelo:
    nombre = "ag04_kalman_ensamble"

    def __init__(self, parametros=os.path.join(AQUI, "parametros.json")):
        self.cfg = json.load(open(parametros, encoding="utf-8"))

    def predecir(self, datos, desde):
        a = min(self.cfg["arranque"], desde)
        L = np.stack([np.log(np.clip(_cargar(b).predecir(datos, a), 1e-9, None)) for b in self.cfg["base"]], axis=1)
        L -= np.log(np.exp(L).sum(2, keepdims=True))
        y = np.asarray(datos.seq)[a:]
        P, self.trayectoria = N.kalman(L, y, q=self.cfg["q"], s0=self.cfg["s0"])
        return P[desde - a:]
