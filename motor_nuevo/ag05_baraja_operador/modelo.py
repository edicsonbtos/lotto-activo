# -*- coding: utf-8 -*-
"""ag05_baraja_operador: ensamble_v2 (walk-forward, del repo) + corrección de la mejor "baraja"
(elegida por BIC en los 5 bloques de entrenamiento: G1 = mazo diario, [salió hoy]) con theta CONGELADO
en parametros.json (ajustado solo con filas [2000, 9357)). P ∝ P_ens · exp(theta · f).
Fila j usa solo datos[:desde+j]. Admite jornadas de 11 o 12 sorteos (el día se toma de la fecha).
OJO: en desarrollo este modelo es PEOR que el ensamble (−1,21 mbits); se entrega por completitud."""
import importlib.util, json, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
import baraja as B  # noqa: E402


def _ensamble():
    ruta = os.path.join(RAIZ, "herramientas", "modelos", "ensamble_v2.py")
    spec = importlib.util.spec_from_file_location("ensamble_v2", ruta)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.Modelo()


class Modelo:
    nombre = "ag05_baraja_operador_G1"

    def __init__(self, parametros=os.path.join(AQUI, "parametros.json"), P_ens=None):
        cfg = json.load(open(parametros, encoding="utf-8"))
        self.cfg = tuple(cfg["config"]); self.theta = np.array(cfg["theta"], float)
        self.P_ens = P_ens

    def predecir(self, datos, desde):
        P = self.P_ens if self.P_ens is not None else _ensamble().predecir(datos, desde)
        P = np.clip(np.asarray(P, float), 1e-12, None)
        X = B.construir(datos, desde, self.cfg)
        Q = B.logp(X, self.theta, np.log(P / P.sum(1, keepdims=True)))
        return np.exp(Q)
