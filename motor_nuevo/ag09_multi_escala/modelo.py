# -*- coding: utf-8 -*-
"""ag09_multi_escala / V1: ensamble_v2 (herramientas/modelos) + corrección multi-escala congelada de la curva de
reciclaje: P ∝ P_ens · exp(f(x)), con x = nucleo.construir (spline de log-hueco en sorteos, superficies
hora-última × hora-actual para huecos de 1 y 2 días, hueco en días, veces en 3 días, 'ya salió hoy', animal).
w en parametros.json, ajustado solo con filas < 9357. Fila j usa solo datos[:desde+j].
Funciona con jornadas de 11 o 12 sorteos (usa hora y día reales)."""
import importlib.util, json, os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
import nucleo as N  # noqa: E402


def _ensamble():
    ruta = os.path.join(RAIZ, "herramientas", "modelos", "ensamble_v2.py")
    spec = importlib.util.spec_from_file_location("ensamble_v2", ruta)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.Modelo()


class Modelo:
    nombre = "ag09_multi_escala_V1"

    def __init__(self, parametros=os.path.join(AQUI, "parametros.json"), P_ens=None):
        cfg = json.load(open(parametros, encoding="utf-8"))
        assert cfg["P"] == N.P
        self.w = np.array(cfg["w"], float)
        self.P_ens = P_ens

    def predecir(self, datos, desde):
        P = self.P_ens if self.P_ens is not None else _ensamble().predecir(datos, desde)
        P = np.clip(np.asarray(P, float), 1e-12, None)
        off = np.log(P / P.sum(1, keepdims=True))
        X = N.construir(datos, desde)
        return N.predecir_log(X, off, self.w)
